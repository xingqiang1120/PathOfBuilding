"""Build library: collect builds, summarise them with Path of Building, and query them.

Builds come in by hand (no scraping):
  * a PoB build file (.xml) or a folder of them, e.g. src/Builds after importing your character
    with the official account import, or after clicking the PoB button on a poe.ninja page
  * a PoB share code (pasted text) or a text file holding one

Layout (all local; library/ is git-ignored because builds contain account and character names):
  library/raw/<id>.xml        original build, never changed; <id> = sha1 of its content
  library/summary/<id>.json   structured summary written by tools/BuildSummary.lua
  library/builds.db           SQLite index over all summaries

Usage:
  python tools/library.py add <file.xml | folder | code.txt> [--source TEXT] [--note TEXT] [--tag TAG ...]
  python tools/library.py add --code <share code> [--name NAME] [--source ...] [--note ...]
  python tools/library.py list
  python tools/library.py show <id prefix | name>
  python tools/library.py search [--ascendancy X] [--skill X] [--item X] [--passive X] [--tag X] [--text X]
  python tools/library.py common [--item X] [--skill X] [--ascendancy X] [--passive X] [--tag X] [--top N]
  python tools/library.py usage --item X  how often an item appears, by ascendancy, skill and slot
  python tools/library.py note <id prefix | name> TEXT
  python tools/library.py rebuild          re-summarise every raw build (after a PoB or data update)
  python tools/library.py settings <build> [--group N] [--minion-skill X] [--config KEY=VALUE ...] [--note TEXT] [--clear]
        play-verified settings used by every analysis of this build (e.g. the skill a minion really uses)
  python tools/library.py core [--tag X] [--ascendancy X] [--skill X] ...
        what analysed builds of a kind have as core damage, defence and functional parts
  python tools/library.py analyze <build> [--no-passives]
        remove each item, support gem and notable on its own and record what the build loses
"""
import argparse
import base64
import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("POB_LIBRARY", os.path.join(ROOT, "library"))
RUNLUA = os.path.join(ROOT, "tools", "runlua.py")
SUMMARY_SCRIPT = os.path.join(ROOT, "tools", "BuildSummary.lua")

SCHEMA = """
CREATE TABLE IF NOT EXISTS builds (
    id TEXT PRIMARY KEY, name TEXT, source TEXT, note TEXT, added_at TEXT, summarised_at TEXT, pob_version TEXT,
    class TEXT, ascendancy TEXT, level INTEGER, tree_version TEXT,
    primary_skill TEXT, primary_dps REAL, primary_is_minion INTEGER, error TEXT
);
CREATE TABLE IF NOT EXISTS build_tags (build_id TEXT, tag TEXT, origin TEXT);
CREATE TABLE IF NOT EXISTS gems (build_id TEXT, grp INTEGER, slot TEXT, gem TEXT, support INTEGER, level INTEGER, quality INTEGER, enabled INTEGER, group_dps REAL);
CREATE TABLE IF NOT EXISTS items (build_id TEXT, slot TEXT, name TEXT, title TEXT, rarity TEXT, base TEXT);
CREATE TABLE IF NOT EXISTS item_tags (build_id TEXT, slot TEXT, tag TEXT);
CREATE TABLE IF NOT EXISTS passives (build_id TEXT, kind TEXT, name TEXT);
CREATE TABLE IF NOT EXISTS stats (build_id TEXT, key TEXT, value REAL);
CREATE TABLE IF NOT EXISTS config (build_id TEXT, key TEXT, value TEXT);
CREATE TABLE IF NOT EXISTS unsupported (build_id TEXT, kind TEXT, source TEXT, line TEXT, impact TEXT, stat_ids TEXT);
CREATE TABLE IF NOT EXISTS build_settings (build_id TEXT PRIMARY KEY, settings TEXT, note TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS contributions (build_id TEXT, analyzed_at TEXT, settings TEXT, kind TEXT, name TEXT, detail TEXT,
    dps_pct REAL, ehp_pct REAL, nodes_removed INTEGER, role TEXT, also_functional INTEGER, error TEXT);
CREATE INDEX IF NOT EXISTS idx_gems ON gems(gem);
CREATE INDEX IF NOT EXISTS idx_items ON items(title, name);
CREATE INDEX IF NOT EXISTS idx_passives ON passives(name);
CREATE INDEX IF NOT EXISTS idx_tags ON build_tags(tag);
"""
BUILD_TAG_THRESHOLD = {"Mechanic": 1, "Archetype": 4, "Damage": 6, "Ailment": 4, "Minion Type": 2, "Defence": 20, "Utility": 20, "Custom": 1}
DETAIL_TABLES = ("build_tags", "gems", "items", "item_tags", "passives", "stats", "config", "unsupported")


def paths():
    raw = os.path.join(LIBRARY, "raw")
    summary = os.path.join(LIBRARY, "summary")
    os.makedirs(raw, exist_ok=True)
    os.makedirs(summary, exist_ok=True)
    return raw, summary


def connect():
    paths()
    db = sqlite3.connect(os.path.join(LIBRARY, "builds.db"))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def decode_share_code(code):
    """PoB share code = URL-safe base64 of zlib-compressed build XML."""
    code = "".join(code.split())
    data = base64.urlsafe_b64decode(code + "=" * (-len(code) % 4))
    return zlib.decompress(data).decode("utf-8")


def encode_share_code(xml_text):
    return base64.urlsafe_b64encode(zlib.compress(xml_text.encode("utf-8"), 9)).decode("ascii")


def summarise(ids):
    """Run BuildSummary.lua once for many raw builds (PoB loads once)."""
    raw_dir, summary_dir = paths()
    if not ids:
        return
    files = [os.path.join(raw_dir, i + ".xml") for i in ids]
    cmd = [sys.executable, RUNLUA, SUMMARY_SCRIPT, "--out-dir", summary_dir] + files
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in proc.stdout.splitlines():
        if line.startswith("error "):
            print("  " + line)
    if proc.returncode != 0:
        raise RuntimeError("BuildSummary failed:\n" + proc.stdout[-2000:] + proc.stderr[-2000:])


def index_build(db, build_id, meta):
    """(Re)write all rows for one build from its summary JSON."""
    _, summary_dir = paths()
    with open(os.path.join(summary_dir, build_id + ".json"), encoding="utf-8") as f:
        s = json.load(f)
    for table in DETAIL_TABLES:
        if table == "build_tags":
            db.execute("DELETE FROM build_tags WHERE build_id = ? AND origin != 'user'", (build_id,))
        else:
            db.execute(f"DELETE FROM {table} WHERE build_id = ?", (build_id,))
    ch = s.get("character", {})
    primary = s.get("primarySkill") or {}
    db.execute(
        """INSERT INTO builds (id, name, source, note, added_at, summarised_at, pob_version, class, ascendancy, level, tree_version,
                               primary_skill, primary_dps, primary_is_minion, error)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET summarised_at=excluded.summarised_at, pob_version=excluded.pob_version, class=excluded.class,
             ascendancy=excluded.ascendancy, level=excluded.level, tree_version=excluded.tree_version, primary_skill=excluded.primary_skill,
             primary_dps=excluded.primary_dps, primary_is_minion=excluded.primary_is_minion, error=excluded.error""",
        (build_id, meta.get("name") or s.get("name"), meta.get("source"), meta.get("note"), meta.get("added_at"),
         datetime.datetime.now().isoformat(timespec="seconds"), s.get("pobVersion"), ch.get("class"), ch.get("ascendancy"),
         ch.get("level"), ch.get("treeVersion"), primary.get("name"), primary.get("dpsWithInference") or primary.get("dps"),
         1 if primary.get("minion") else 0, s.get("error")))
    if s.get("error"):
        return
    tags = {}
    for skill in s.get("skills", []):
        dps = 0
        calc = skill.get("calculated") or {}
        dps = max([v for v in calc.values() if isinstance(v, (int, float))] or [0])
        for gem in skill.get("gems", []):
            db.execute("INSERT INTO gems VALUES (?,?,?,?,?,?,?,?,?)",
                       (build_id, skill["index"], skill.get("slot"), gem.get("name"), 1 if gem.get("support") else 0,
                        gem.get("level"), gem.get("quality"), 1 if gem.get("enabled") else 0, dps))
    for item in s.get("items", []):
        db.execute("INSERT INTO items VALUES (?,?,?,?,?,?)",
                   (build_id, item["slot"], item.get("name"), item.get("title"), item.get("rarity"), item.get("base")))
        for tag in item.get("tags", []):
            db.execute("INSERT INTO item_tags VALUES (?,?,?)", (build_id, item["slot"], tag))
            tags[tag] = tags.get(tag, 0) + 1
    p = s.get("passives", {})
    for kind in ("keystones", "notables", "ascendancy", "masteries"):
        for name in p.get(kind, []):
            db.execute("INSERT INTO passives VALUES (?,?,?)", (build_id, kind[:-1] if kind.endswith("s") else kind, name))
    for tag, count in (p.get("tagCounts") or {}).items():
        tags[tag] = tags.get(tag, 0) + count
    # A build carries a tag when its items and passives use it repeatedly. Defence and utility tags
    # (life, resistances, flasks ...) appear in nearly every build, so they need much more weight.
    info = s.get("tagInfo") or {}
    for tag, count in tags.items():
        category = (info.get(tag) or {}).get("category", "Custom")
        needed = BUILD_TAG_THRESHOLD.get(category, 3)
        if count >= needed:
            db.execute("INSERT INTO build_tags VALUES (?,?,?)", (build_id, tag, "auto"))
    for key, value in (s.get("stats") or {}).items():
        db.execute("INSERT INTO stats VALUES (?,?,?)", (build_id, key, value))
    for key, value in ((s.get("config") or {}).get("set") or {}).items():
        db.execute("INSERT INTO config VALUES (?,?,?)", (build_id, key, json.dumps(value)))
    for e in (s.get("coverage") or {}).get("unsupported", []):
        db.execute("INSERT INTO unsupported VALUES (?,?,?,?,?,?)",
                   (build_id, e.get("kind"), e.get("source"), e.get("line"), e.get("impact"), ",".join(e.get("statIds") or [])))


def collect_inputs(args):
    """Yield (xml_text, name) for every build given on the command line."""
    if args.code:
        yield decode_share_code(args.code), args.name or "shared build"
        return
    for target in args.paths:
        if os.path.isdir(target):
            for fname in sorted(os.listdir(target)):
                if fname.lower().endswith(".xml"):
                    with open(os.path.join(target, fname), encoding="utf-8") as f:
                        yield f.read(), fname[:-4]
        elif target.lower().endswith(".xml"):
            with open(target, encoding="utf-8") as f:
                yield f.read(), args.name or os.path.basename(target)[:-4]
        else:
            with open(target, encoding="utf-8") as f:
                yield decode_share_code(f.read()), args.name or os.path.splitext(os.path.basename(target))[0]


def cmd_add(args):
    raw_dir, _ = paths()
    db = connect()
    new = []
    metas = {}
    for xml_text, name in collect_inputs(args):
        build_id = hashlib.sha1(xml_text.encode("utf-8")).hexdigest()
        if db.execute("SELECT 1 FROM builds WHERE id = ?", (build_id,)).fetchone():
            print(f"skip  {build_id[:10]}  {name} (already in the library)")
            continue
        with open(os.path.join(raw_dir, build_id + ".xml"), "w", encoding="utf-8") as f:
            f.write(xml_text)
        metas[build_id] = {"name": name, "source": args.source, "note": args.note,
                           "added_at": datetime.datetime.now().isoformat(timespec="seconds")}
        new.append(build_id)
    if not new:
        return
    print(f"summarising {len(new)} build(s) with Path of Building ...")
    summarise(new)
    for build_id in new:
        index_build(db, build_id, metas[build_id])
        for tag in args.tag or []:
            db.execute("INSERT INTO build_tags VALUES (?,?,?)", (build_id, tag.lower(), "user"))
        row = db.execute("SELECT * FROM builds WHERE id = ?", (build_id,)).fetchone()
        print(f"added {build_id[:10]}  {row['name']}  ({row['ascendancy']} {row['level']}, {row['primary_skill']})"
              + (f"  ERROR: {row['error']}" if row["error"] else ""))
    db.commit()


def cmd_rebuild(args):
    raw_dir, _ = paths()
    db = connect()
    rows = db.execute("SELECT * FROM builds").fetchall()
    ids = [r["id"] for r in rows if os.path.exists(os.path.join(raw_dir, r["id"] + ".xml"))]
    print(f"re-summarising {len(ids)} build(s) ...")
    summarise(ids)
    for r in rows:
        if r["id"] in ids:
            index_build(db, r["id"], dict(r))
    db.commit()
    print("done")


def find_build(db, key):
    row = db.execute("SELECT * FROM builds WHERE id LIKE ? OR name LIKE ? ORDER BY name = ? DESC, added_at DESC", (key + "%", f"%{key}%", key)).fetchone()
    if not row:
        sys.exit(f"no build matches '{key}'")
    return row


def fmt(n):
    if n is None:
        return "-"
    return f"{n:,.0f}"


def cmd_list(args):
    db = connect()
    rows = db.execute("SELECT * FROM builds ORDER BY added_at DESC").fetchall()
    if not rows:
        print("library is empty")
    for r in rows:
        tags = [t[0] for t in db.execute("SELECT DISTINCT tag FROM build_tags WHERE build_id = ? ORDER BY tag", (r["id"],))]
        print(f"{r['id'][:10]}  {r['name']:<30} {r['ascendancy'] or '-':<14} lv{r['level'] or '-':<3} "
              f"{(r['primary_skill'] or '-'):<28} {fmt(r['primary_dps']):>12}  [{', '.join(tags)}]")


def cmd_show(args):
    db = connect()
    r = find_build(db, args.key)
    print(f"{r['name']}  ({r['id']})")
    print(f"  {r['class']} / {r['ascendancy']}  level {r['level']}  tree {r['tree_version']}  PoB {r['pob_version']}")
    print(f"  source: {r['source'] or '-'}   added: {r['added_at']}")
    if r["note"]:
        print(f"  note: {r['note']}")
    print(f"  primary skill: {r['primary_skill']}  DPS {fmt(r['primary_dps'])}{' (per minion)' if r['primary_is_minion'] else ''}")
    tags = db.execute("SELECT tag, origin FROM build_tags WHERE build_id = ? ORDER BY origin, tag", (r["id"],)).fetchall()
    print("  tags: " + ", ".join(t["tag"] + ("*" if t["origin"] == "user" else "") for t in tags))
    stats = {s["key"]: s["value"] for s in db.execute("SELECT key, value FROM stats WHERE build_id = ?", (r["id"],))}
    print("  life {}  ES {}  EHP {}  resists {}/{}/{}/{}".format(
        fmt(stats.get("Life")), fmt(stats.get("EnergyShield")), fmt(stats.get("TotalEHP")),
        fmt(stats.get("FireResist")), fmt(stats.get("ColdResist")), fmt(stats.get("LightningResist")), fmt(stats.get("ChaosResist"))))
    print("  items:")
    for it in db.execute("SELECT * FROM items WHERE build_id = ?", (r["id"],)):
        print(f"    {it['slot']:<14} {it['name']}")
    print("  skills (group: gems):")
    groups = {}
    for g in db.execute("SELECT * FROM gems WHERE build_id = ? ORDER BY grp", (r["id"],)):
        groups.setdefault(g["grp"], []).append(g["gem"] + ("" if g["enabled"] else " (off)"))
    for grp, gems in groups.items():
        print(f"    {grp:>2}: {', '.join(gems)}")
    asc = [p["name"] for p in db.execute("SELECT name FROM passives WHERE build_id = ? AND kind = 'ascendancy'", (r["id"],))]
    print("  ascendancy: " + ", ".join(asc))
    unsupported = db.execute("SELECT COUNT(*) FROM unsupported WHERE build_id = ? AND impact IN ('offence','defence')", (r["id"],)).fetchone()[0]
    print(f"  modifier lines PoB does not calculate (offence/defence): {unsupported}")
    settings = get_settings(r["id"])
    if settings:
        print(f"  verified settings: {json.dumps({k: v for k, v in settings.items() if k != 'note'}, ensure_ascii=False)}"
              + (f"  ({settings['note']})" if settings.get("note") else ""))
    parts = db.execute("SELECT * FROM contributions WHERE build_id = ? ORDER BY dps_pct, ehp_pct", (r["id"],)).fetchall()
    if parts:
        print(f"  contribution analysis ({parts[0]['analyzed_at']}), top parts:")
        for p in parts[:8]:
            print(describe_part({"kind": p["kind"], "name": p["name"], "dpsPct": p["dps_pct"] or 0, "ehpPct": p["ehp_pct"] or 0,
                                 "role": p["role"], "nodesRemoved": p["nodes_removed"], "alsoFunctional": p["also_functional"], "error": p["error"]}))


FILTERS = {
    "ascendancy": ("b.ascendancy LIKE ?", None),
    "skill": ("EXISTS (SELECT 1 FROM gems g WHERE g.build_id = b.id AND g.gem LIKE ?)", None),
    "item": ("EXISTS (SELECT 1 FROM items i WHERE i.build_id = b.id AND (i.title LIKE ? OR i.name LIKE ?))", 2),
    "passive": ("EXISTS (SELECT 1 FROM passives p WHERE p.build_id = b.id AND p.name LIKE ?)", None),
    "tag": ("EXISTS (SELECT 1 FROM build_tags t WHERE t.build_id = b.id AND t.tag = ?)", None),
    "text": ("(b.name LIKE ? OR b.note LIKE ? OR b.source LIKE ?)", 3),
}


def where_clause(filters):
    """filters: argparse namespace or dict with any of the FILTERS keys."""
    get = filters.get if isinstance(filters, dict) else (lambda k: getattr(filters, k, None))
    clauses, params = [], []
    for key, (sql, count) in FILTERS.items():
        value = get(key)
        if value:
            v = value.lower() if key == "tag" else f"%{value}%"
            clauses.append(sql)
            params.extend([v] * (count or 1))
    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def query_search(filters):
    db = connect()
    where, params = where_clause(filters)
    rows = db.execute(f"SELECT b.* FROM builds b{where} ORDER BY b.primary_dps DESC", params).fetchall()
    out = []
    for r in rows:
        tags = [t[0] for t in db.execute("SELECT DISTINCT tag FROM build_tags WHERE build_id = ? ORDER BY tag", (r["id"],))]
        out.append({"id": r["id"][:10], "name": r["name"], "class": r["class"], "ascendancy": r["ascendancy"], "level": r["level"],
                    "primarySkill": r["primary_skill"], "primaryDPS": r["primary_dps"], "dpsIsPerMinion": bool(r["primary_is_minion"]),
                    "source": r["source"], "note": r["note"], "tags": tags})
    return out


def query_common(filters, top=10):
    """What builds matching the filters have in common: share of matching builds per entry."""
    db = connect()
    where, params = where_clause(filters)
    ids = [r[0] for r in db.execute(f"SELECT b.id FROM builds b{where}", params)]
    result = {"matchingBuilds": len(ids), "groups": {}}
    if not ids:
        return result
    marks = ",".join("?" * len(ids))
    queries = [
        ("Unique items", f"SELECT title AS name, COUNT(DISTINCT build_id) n FROM items WHERE build_id IN ({marks}) AND rarity IN ('UNIQUE','RELIC') GROUP BY title"),
        ("Gems", f"SELECT gem AS name, COUNT(DISTINCT build_id) n FROM gems WHERE build_id IN ({marks}) GROUP BY gem"),
        ("Keystones and notables", f"SELECT name, COUNT(DISTINCT build_id) n FROM passives WHERE build_id IN ({marks}) AND kind IN ('keystone','notable') GROUP BY name"),
        ("Ascendancy nodes", f"SELECT name, COUNT(DISTINCT build_id) n FROM passives WHERE build_id IN ({marks}) AND kind = 'ascendancy' GROUP BY name"),
        ("Build tags", f"SELECT tag AS name, COUNT(DISTINCT build_id) n FROM build_tags WHERE build_id IN ({marks}) GROUP BY tag"),
    ]
    for title, sql in queries:
        rows = db.execute(sql + " ORDER BY n DESC, name LIMIT ?", ids + [top]).fetchall()
        result["groups"][title] = [{"name": r["name"], "builds": r["n"], "share": round(r["n"] / len(ids), 3)} for r in rows]
    return result


def query_item_usage(item, top=10):
    """How often an item (unique title or item name, partial match) appears, and in which builds."""
    db = connect()
    total = db.execute("SELECT COUNT(*) FROM builds").fetchone()[0]
    like = f"%{item}%"
    match = "(i.title LIKE ? OR i.name LIKE ?)"
    using = db.execute(f"SELECT COUNT(DISTINCT i.build_id) FROM items i WHERE {match}", (like, like)).fetchone()[0]
    def grouped(column):
        rows = db.execute(f"""SELECT {column} AS name, COUNT(DISTINCT i.build_id) n FROM items i JOIN builds b ON b.id = i.build_id
                              WHERE {match} GROUP BY {column} ORDER BY n DESC LIMIT ?""", (like, like, top)).fetchall()
        return [{"name": r["name"], "builds": r["n"]} for r in rows]
    builds = db.execute(f"""SELECT DISTINCT b.id, b.name, b.ascendancy, b.primary_skill, i.slot, i.name AS item FROM items i JOIN builds b ON b.id = i.build_id
                            WHERE {match} ORDER BY b.name LIMIT 50""", (like, like)).fetchall()
    return {"item": item, "librarySize": total, "buildsUsing": using, "share": round(using / total, 3) if total else 0,
            "byAscendancy": grouped("b.ascendancy"), "byPrimarySkill": grouped("b.primary_skill"), "bySlot": grouped("i.slot"),
            "builds": [{"id": r["id"][:10], "name": r["name"], "ascendancy": r["ascendancy"], "primarySkill": r["primary_skill"],
                        "slot": r["slot"], "item": r["item"]} for r in builds]}


def query_core_parts(filters, top=15):
    """Aggregate saved contribution analyses over the builds matching the filters: which items, supports and
    passives carry damage, defence or mechanics PoB cannot measure in that kind of build."""
    db = connect()
    where, params = where_clause(filters)
    joined = where.replace(" WHERE ", " AND ", 1) if where else ""
    analysed = db.execute(f"SELECT COUNT(DISTINCT c.build_id) FROM contributions c JOIN builds b ON b.id = c.build_id WHERE 1=1{joined}",
                          params).fetchone()[0]
    def group(condition, order):
        rows = db.execute(f"""SELECT c.kind, c.name, COUNT(DISTINCT c.build_id) n, AVG(c.dps_pct) dps, AVG(c.ehp_pct) ehp,
                                     GROUP_CONCAT(DISTINCT c.role) roles
                              FROM contributions c JOIN builds b ON b.id = c.build_id
                              WHERE c.error IS NULL AND {condition}{joined}
                              GROUP BY c.kind, c.name ORDER BY {order} LIMIT ?""", params + [top]).fetchall()
        return [{"kind": r["kind"], "name": r["name"], "builds": r["n"], "avgDpsPct": round(r["dps"] or 0, 1),
                 "avgEhpPct": round(r["ehp"] or 0, 1), "roles": (r["roles"] or "").split(",")} for r in rows]
    return {
        "analysedBuilds": analysed,
        "damage": group("c.dps_pct <= -2 AND c.role NOT LIKE 'tree hub%'", "AVG(c.dps_pct)"),
        "defence": group("c.ehp_pct <= -2 AND c.role NOT LIKE 'tree hub%'", "AVG(c.ehp_pct)"),
        "functional": group("(c.role LIKE 'functional%' OR c.also_functional = 1 OR c.role = 'enables main skill')", "COUNT(DISTINCT c.build_id) DESC, AVG(c.dps_pct)"),
        "note": "averages of 'remove this part alone' results; run `analyze` on more builds to make them meaningful",
    }


def cmd_core(args):
    result = query_core_parts(args, args.top)
    print(f"{result['analysedBuilds']} analysed build(s) match")
    for title, key, metric in (("Damage", "damage", "avgDpsPct"), ("Defence", "defence", "avgEhpPct"), ("Functional", "functional", "avgDpsPct")):
        print(title)
        for p in result[key]:
            print(f"  {p['kind']:<12} {p['name'][:40]:<40} in {p['builds']} build(s)  {metric} {p[metric]:+.1f}%  ({', '.join(p['roles'])})")


def cmd_search(args):
    rows = query_search(args)
    print(f"{len(rows)} build(s)")
    for r in rows:
        print(f"{r['id']}  {r['name']:<30} {r['ascendancy'] or '-':<14} {(r['primarySkill'] or '-'):<28} {fmt(r['primaryDPS']):>12}")


def cmd_common(args):
    result = query_common(args, args.top)
    if not result["matchingBuilds"]:
        print("no matching builds")
        return
    print(f"{result['matchingBuilds']} matching build(s)\n")
    for title, rows in result["groups"].items():
        print(title)
        for r in rows:
            print(f"  {r['share']:>5.0%}  {r['name']}")
        print()


def cmd_usage(args):
    u = query_item_usage(args.item, args.top)
    print(f"{args.item}: {u['buildsUsing']} of {u['librarySize']} build(s) ({u['share']:.0%})")
    for title, key in (("by ascendancy", "byAscendancy"), ("by primary skill", "byPrimarySkill"), ("by slot", "bySlot")):
        print("  " + title + ": " + ", ".join(f"{g['name']} {g['builds']}" for g in u[key]))
    for b in u["builds"]:
        print(f"    {b['id']}  {b['name']:<30} {b['ascendancy'] or '-':<14} {b['slot']:<12} {b['item']}")


def resolve(key):
    """(xml, name, build_id) for a library id prefix / name, or (xml, name, None) for an .xml path."""
    if key.lower().endswith(".xml"):
        path = key if os.path.isabs(key) else os.path.join(ROOT, key)
        if not os.path.exists(path):
            raise LookupError(f"build file not found: {key}")
        with open(path, encoding="utf-8") as f:
            return f.read(), os.path.basename(path)[:-4], None
    db = connect()
    row = db.execute("SELECT * FROM builds WHERE id LIKE ? OR name LIKE ? ORDER BY name = ? DESC, added_at DESC",
                     (key + "%", f"%{key}%", key)).fetchone()
    if not row:
        raise LookupError(f"no library build matches '{key}'")
    with open(os.path.join(LIBRARY, "raw", row["id"] + ".xml"), encoding="utf-8") as f:
        return f.read(), row["name"], row["id"]


def get_settings(build_id):
    """Play-verified settings of a build: {"group", "minionSkill", "changes": [...], "note"}."""
    if not build_id:
        return {}
    row = connect().execute("SELECT settings, note FROM build_settings WHERE build_id = ?", (build_id,)).fetchone()
    if not row:
        return {}
    settings = json.loads(row["settings"])
    if row["note"]:
        settings["note"] = row["note"]
    return settings


def save_settings(build_id, settings, note=None):
    db = connect()
    clean = {k: v for k, v in settings.items() if k in ("group", "minionSkill", "changes") and v not in (None, [], "")}
    if not clean and not note:
        db.execute("DELETE FROM build_settings WHERE build_id = ?", (build_id,))
    else:
        db.execute("INSERT INTO build_settings VALUES (?,?,?,?) ON CONFLICT(build_id) DO UPDATE SET settings=excluded.settings, "
                   "note=excluded.note, updated_at=excluded.updated_at",
                   (build_id, json.dumps(clean, ensure_ascii=False), note, datetime.datetime.now().isoformat(timespec="seconds")))
    db.commit()
    return clean


def apply_settings(params, settings, overrides=None):
    """Merge saved settings into worker params; explicit overrides win, saved config changes run first."""
    overrides = overrides or {}
    for key in ("group", "minionSkill"):
        value = overrides.get(key) if overrides.get(key) is not None else settings.get(key)
        if value is not None:
            params[key] = value
    for key in ("infer", "minionCount"):
        if overrides.get(key) is not None:
            params[key] = overrides[key]
    params["changes"] = list(settings.get("changes") or []) + list(overrides.get("changes") or [])
    return params


def run_contributions(key, include_passives=True, overrides=None, save=True):
    """Leave-one-out analysis. Conditions such as withered stacks are inferred unless overrides["infer"] is False."""
    from pob_worker import WORKER
    xml, name, build_id = resolve(key)
    settings = get_settings(build_id)
    params = apply_settings({"xml": xml, "name": name, "includePassives": include_passives}, settings, overrides)
    result = WORKER.call("contributions", params)
    result["settingsApplied"] = {k: params.get(k) for k in ("group", "minionSkill", "changes") if params.get(k)}
    if save and build_id:
        db = connect()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        db.execute("DELETE FROM contributions WHERE build_id = ?", (build_id,))
        for p in result["parts"]:
            db.execute("INSERT INTO contributions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                       (build_id, now, json.dumps(result["settingsApplied"], ensure_ascii=False), p.get("kind"), p.get("name"), p.get("detail"),
                        p.get("dpsPct"), p.get("ehpPct"), p.get("nodesRemoved"), p.get("role"), 1 if p.get("alsoFunctional") else 0, p.get("error")))
        db.commit()
    return result


def parse_value(text):
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def cmd_settings(args):
    db = connect()
    r = find_build(db, args.key)
    current = get_settings(r["id"])
    if args.clear:
        current = {}
    if args.group is not None:
        current["group"] = int(args.group) if args.group.isdigit() else args.group
    if args.minion_skill:
        current["minionSkill"] = args.minion_skill
    for item in args.config or []:
        key, _, value = item.partition("=")
        changes = [c for c in current.get("changes", []) if not (c.get("type") == "config_set" and c.get("key") == key)]
        changes.append({"type": "config_set", "key": key, "value": parse_value(value)})
        current["changes"] = changes
    note = args.note if args.note is not None else current.get("note")
    saved = save_settings(r["id"], current, note)
    print(f"settings for {r['name']}: {json.dumps(saved, ensure_ascii=False)}" + (f"  note: {note}" if note else ""))


def describe_part(p):
    extra = f" (+{p['nodesRemoved'] - 1} dependent points)" if p.get("nodesRemoved") and p["nodesRemoved"] > 1 else ""
    func = "  [also functional]" if p.get("alsoFunctional") else ""
    if p.get("error"):
        return f"  {p['kind']:<12} {p['name'][:36]:<36} error: {p['error']}"
    return (f"  {p['kind']:<12} {p['name'][:36]:<36} DPS {p['dpsPct']:>+7.1f}%  EHP {p['ehpPct']:>+6.1f}%  {p['role']}{func}{extra}")


def cmd_analyze(args):
    print("analysing (each part is removed on its own; takes about a second per part) ...")
    result = run_contributions(args.key, include_passives=not args.no_passives)
    b = result["baseline"]
    print(f"settings: {json.dumps(result['settingsApplied'], ensure_ascii=False)}")
    for inf in result.get("inferred") or []:
        state = f"applied {inf['value']}" if inf.get("applied") else f"not applied ({inf.get('skipped')})"
        print(f"inferred: {inf['label']} = {inf['estimate']} -> {state}")
    print(f"baseline: {b.get('mainSkill')}" + (f" / minion skill {b['minionSkill']}" if b.get("minionSkill") else "")
          + f"  DPS {fmt(max(b.get('playerDPS') or 0, b.get('minionDPS') or 0))}  EHP {fmt(b.get('TotalEHP'))}")
    for p in result["parts"]:
        print(describe_part(p))


def cmd_note(args):
    db = connect()
    r = find_build(db, args.key)
    db.execute("UPDATE builds SET note = ? WHERE id = ?", (args.text, r["id"]))
    db.commit()
    print(f"note saved for {r['name']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Path of Building build library", formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("paths", nargs="*")
    p.add_argument("--code")
    p.add_argument("--name")
    p.add_argument("--source")
    p.add_argument("--note")
    p.add_argument("--tag", action="append")
    sub.add_parser("list")
    sub.add_parser("rebuild")
    p = sub.add_parser("show")
    p.add_argument("key")
    p = sub.add_parser("note")
    p.add_argument("key")
    p.add_argument("text")
    p = sub.add_parser("settings")
    p.add_argument("key")
    p.add_argument("--group")
    p.add_argument("--minion-skill")
    p.add_argument("--config", action="append")
    p.add_argument("--note")
    p.add_argument("--clear", action="store_true")
    p = sub.add_parser("analyze")
    p.add_argument("key")
    p.add_argument("--no-passives", action="store_true")
    p = sub.add_parser("usage")
    p.add_argument("--item", required=True)
    p.add_argument("--top", type=int, default=10)
    for name in ("search", "common", "core"):
        p = sub.add_parser(name)
        for key in FILTERS:
            p.add_argument("--" + key)
        if name in ("common", "core"):
            p.add_argument("--top", type=int, default=10 if name == "common" else 15)
    args = parser.parse_args(argv)
    if args.cmd == "add" and not args.paths and not args.code:
        parser.error("add needs a file, folder or --code")
    {"add": cmd_add, "list": cmd_list, "rebuild": cmd_rebuild, "show": cmd_show, "search": cmd_search,
     "common": cmd_common, "note": cmd_note, "usage": cmd_usage,
     "settings": cmd_settings, "analyze": cmd_analyze, "core": cmd_core}[args.cmd](args)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
