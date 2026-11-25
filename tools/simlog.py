"""Simulation log: every candidate the build generator and optimizer try in Path of Building, kept as data.

Each try is one sample: the context (skill, ascendancy, focus, gear mode, PoB and tree version), the build state it
started from, the change, and the numbers before and after. Over many runs this shows which changes are worth what
in which kind of build (e.g. "Wandslinger, wand attack skills: +x% DPS per point"), and later trains a fast model
that suggests which candidates to try first. Answers still come from PoB; the log only guides the search.

Stored in library/simdata.db (git-ignored, local).

    python tools/simlog.py summary                       runs and samples so far
    python tools/simlog.py compact                       convert an old (format 1) database to the compact format
    python tools/simlog.py stats [--kind passive_add] [--skill wand] [--ascendancy Necromancer] [--top 20]
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("POB_LIBRARY", os.path.join(ROOT, "library"))

# Numbers kept for every sample (before and after)
METRICS = ["playerDPS", "minionDPS", "Life", "EnergyShield", "Mana", "TotalEHP", "PhysicalMaximumHitTaken", "FireMaximumHitTaken",
           "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken", "FireResist", "ColdResist", "LightningResist",
           "ChaosResist", "EffectiveBlockChance", "EffectiveSpellBlockChance", "EffectiveSpellSuppressionChance", "Armour", "Evasion",
           "ManaUnreserved", "LifeUnreserved", "attributeShortfall", "passivePointsUsed", "passivePointsAvailable", "minionLimit",
           "Speed", "CritChance", "HitChance"]

# Format 2: the numbers of a state ("before") are stored once in states; a sample keeps only the numbers that the change
# altered ("after" = before + delta). runs.generator: version of the generator's rules (results of different versions
# are not comparable); runs.outcome: e.g. "no damage" when a run stopped early; runs.guide: the weights that ordered
# and narrowed the candidates (NULL = every candidate tried).
FORMAT = 2
SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, started TEXT, tool TEXT, skill TEXT, ascendancy TEXT, class TEXT, focus TEXT, gear TEXT,
    pob_version TEXT, tree_version TEXT, skill_info TEXT, finished TEXT, final TEXT, generator INTEGER, outcome TEXT, guide TEXT);
CREATE TABLE IF NOT EXISTS states (
    run_id TEXT, state_hash TEXT, metrics TEXT, PRIMARY KEY (run_id, state_hash)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step TEXT, state_hash TEXT, state_size INTEGER,
    kind TEXT, key TEXT, label TEXT, change TEXT, cost INTEGER,
    dps_before REAL, dps_after REAL, ehp_before REAL, ehp_after REAL, score_before REAL, score_after REAL,
    delta TEXT, error TEXT);
CREATE INDEX IF NOT EXISTS samples_key ON samples(kind, key);
CREATE INDEX IF NOT EXISTS samples_run ON samples(run_id);
"""


def db_path():
    return os.path.join(LIBRARY, "simdata.db")


def columns(db, table):
    return [r[1] for r in db.execute(f"PRAGMA table_info({table})")]


def connect(migrate=False):
    os.makedirs(LIBRARY, exist_ok=True)
    db = sqlite3.connect(db_path(), timeout=120)  # several generators may write at the same time
    if "before" in columns(db, "samples"):
        if not migrate:
            raise SystemExit(f"{db_path()} is in the old, large format: run  python tools/simlog.py compact  first")
        return db
    db.executescript(SCHEMA)
    for col, typ in (("generator", "INTEGER"), ("outcome", "TEXT"), ("guide", "TEXT")):
        if col not in columns(db, "runs"):
            db.execute(f"ALTER TABLE runs ADD COLUMN {col} {typ}")
    db.execute(f"PRAGMA user_version = {FORMAT}")
    return db


def pick(m):
    return {k: m.get(k) for k in METRICS if m and m.get(k) is not None}


def dumps(obj):
    return json.dumps(obj, separators=(",", ":"))


def delta(before, after):
    """Numbers of after that differ from before (None = the metric disappeared)."""
    b, a = pick(before), pick(after)
    d = {k: v for k, v in a.items() if b.get(k) != v}
    d.update({k: None for k in b if k not in a})
    return d


def after_metrics(before, d):
    """Rebuild a sample's numbers after the change from its state's numbers and the stored delta."""
    m = dict(before or {})
    for k, v in (d or {}).items():
        if v is None:
            m.pop(k, None)
        else:
            m[k] = v
    return m


def compact():
    """Convert the old format (full before/after numbers in every sample) to format 2, then reclaim the space."""
    db = connect(migrate=True)
    if "before" not in columns(db, "samples"):
        print("already in the compact format")
        return
    t = time.time()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS states (run_id TEXT, state_hash TEXT, metrics TEXT, PRIMARY KEY (run_id, state_hash)) WITHOUT ROWID;
        CREATE TABLE samples2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step TEXT, state_hash TEXT, state_size INTEGER,
            kind TEXT, key TEXT, label TEXT, change TEXT, cost INTEGER,
            dps_before REAL, dps_after REAL, ehp_before REAL, ehp_after REAL, score_before REAL, score_after REAL,
            delta TEXT, error TEXT);""")
    runs = [r for (r,) in db.execute("SELECT id FROM runs")]
    for i, run in enumerate(runs):
        rows, states = [], {}
        for r in db.execute("SELECT id, run_id, step, state_hash, state_size, kind, key, label, change, cost, dps_before, dps_after, "
                            "ehp_before, ehp_after, score_before, score_after, before, after, error FROM samples WHERE run_id = ? ORDER BY id",
                            (run,)):
            before = json.loads(r[16]) if r[16] else {}
            after = json.loads(r[17]) if r[17] else None
            states.setdefault(r[3], dumps(before))
            rows.append(r[:16] + (dumps(delta(before, after)) if after is not None else None, r[18]))
        db.executemany("INSERT OR IGNORE INTO states VALUES (?,?,?)", [(run, h, m) for h, m in states.items()])
        db.executemany("INSERT INTO samples2 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        db.commit()
        if i % 50 == 0:
            print(f"  {i}/{len(runs)} runs ({time.time() - t:.0f} s)", flush=True)
    db.executescript("DROP TABLE samples; ALTER TABLE samples2 RENAME TO samples;")
    db.commit()
    db.close()
    db = connect()
    print(f"converted in {time.time() - t:.0f} s; reclaiming space (VACUUM)...", flush=True)
    db.execute("VACUUM")
    db.close()
    print(f"done: {os.path.getsize(db_path()) / 2**20:,.0f} MB")


def seed(path):
    """Write a small file with this computer's list of runs (no samples) for another computer: copied to that
    computer's library/simdata.db, it makes self-play there skip the pairs already done here. Merging that computer's
    log back later skips these runs, since this computer has them in full."""
    if os.path.exists(path):
        raise SystemExit(f"already exists: {path}")
    db = connect()
    out = sqlite3.connect(path)
    out.executescript(SCHEMA)
    out.execute(f"PRAGMA user_version = {FORMAT}")
    cols = [c for c in columns(db, "runs") if c in columns(out, "runs")]
    rows = db.execute(f"SELECT {', '.join(cols)} FROM runs WHERE finished IS NOT NULL").fetchall()
    out.executemany(f"INSERT INTO runs ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", rows)
    out.commit()
    out.close()
    db.close()
    print(f"wrote {len(rows)} finished runs (no samples) to {path}: {os.path.getsize(path) / 2**20:.1f} MB")
    return len(rows)


def merge(path):
    """Copy the finished runs of another computer's simulation log into this one. Run ids are random, so runs from
    different computers never clash; runs already here are skipped, so merging the same file twice is harmless.
    Unfinished runs are left out (they are copied by a later merge, once finished)."""
    if not os.path.exists(path):
        raise SystemExit(f"not found: {path}")
    if os.path.abspath(path) == os.path.abspath(db_path()):
        raise SystemExit("that is this computer's own simulation log")
    src = sqlite3.connect(pathlib.Path(os.path.abspath(path)).as_uri() + "?mode=ro", uri=True)
    if "before" in columns(src, "samples"):
        raise SystemExit(f"{path} is in the old, large format: run  python tools/simlog.py compact  on that computer first")
    db = connect()
    run_cols = [c for c in columns(db, "runs") if c in columns(src, "runs")]
    sample_cols = [c for c in columns(db, "samples") if c != "id" and c in columns(src, "samples")]
    here = {r for (r,) in db.execute("SELECT id FROM runs")}
    rows = src.execute(f"SELECT {', '.join(run_cols)} FROM runs WHERE finished IS NOT NULL").fetchall()
    unfinished = src.execute("SELECT COUNT(*) FROM runs WHERE finished IS NULL").fetchone()[0]
    new = [r for r in rows if r[0] not in here]
    t, samples = time.time(), 0
    for i, run in enumerate(new):
        rid = run[0]
        db.execute(f"INSERT INTO runs ({', '.join(run_cols)}) VALUES ({', '.join('?' * len(run_cols))})", run)
        db.executemany("INSERT OR IGNORE INTO states VALUES (?,?,?)",
                       src.execute("SELECT run_id, state_hash, metrics FROM states WHERE run_id = ?", (rid,)))
        cur = db.executemany(f"INSERT INTO samples ({', '.join(sample_cols)}) VALUES ({', '.join('?' * len(sample_cols))})",
                             src.execute(f"SELECT {', '.join(sample_cols)} FROM samples WHERE run_id = ? ORDER BY id", (rid,)))
        samples += cur.rowcount
        db.commit()  # one run at a time: generators running here wait at most a moment
        if i % 50 == 49:
            print(f"  {i + 1}/{len(new)} runs ({time.time() - t:.0f} s)", flush=True)
    src.close()
    db.close()
    print(f"merged {len(new)} runs ({samples:,} samples) in {time.time() - t:.0f} s; "
          f"{len(rows) - len(new)} were already here, {unfinished} unfinished left out")
    return len(new)


def state_hash(state):
    return hashlib.sha1(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]


def change_key(change):
    """(kind, key, label) of a candidate: the type and what it touches, e.g. ("passive_add", "41476", ...)."""
    if not change:
        return "none", "", ""
    if len(change) > 1 and all(c["type"] == "item_equip" for c in change):
        kind = "item_set"
    else:
        kind = "+".join(c["type"] for c in change)
    keys = []
    for c in change:
        if c.get("raw"):
            lines = c["raw"].splitlines()
            keys.append(f"{c.get('slot')}:{lines[1] if len(lines) > 1 else ''}")
        else:
            keys.append(str(c.get("with") or c.get("gem") or c.get("node") or c.get("unique") or c.get("slot") or
                            ",".join(c.get("gems") or []) or c.get("key") or ""))
    labels = [str(c.get("name") or "") for c in change if c.get("name")]
    return kind, "|".join(keys), "|".join(labels)


class Recorder:
    """One run of a search tool. Disabled with POB_SIMLOG=0."""

    def __init__(self, tool, skill=None, ascendancy=None, cls=None, focus=None, gear=None, skill_info=None, versions=None, generator=None, guide=None):
        self.enabled = os.environ.get("POB_SIMLOG", "1") != "0"
        self.id = uuid.uuid4().hex[:12]
        self.count = 0
        self.states = set()
        if not self.enabled:
            return
        self.db = connect()
        versions = versions or {}
        self.db.execute("INSERT INTO runs (id, started, tool, skill, ascendancy, class, focus, gear, pob_version, tree_version, skill_info, "
                        "generator, guide) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (self.id, datetime.datetime.now().isoformat(timespec="seconds"), tool, skill, ascendancy, cls, focus, gear,
                         versions.get("pobVersion"), versions.get("treeVersion"), json.dumps(skill_info or {}), generator, guide))
        self.db.commit()

    def update(self, **fields):
        if not self.enabled:
            return
        for key, value in fields.items():
            if key in ("skill", "ascendancy", "class", "skill_info", "gear"):
                self.db.execute(f"UPDATE runs SET {key} = ? WHERE id = ?", (json.dumps(value) if key == "skill_info" else value, self.id))
        self.db.commit()

    def record(self, step, state, before, candidates, results, dps, ehp=None, score=None, costs=None):
        """Store one sample per candidate. dps/ehp/score: functions of a metrics dict."""
        if not self.enabled:
            return
        ehp = ehp or (lambda m: m.get("TotalEHP"))
        h, size = state_hash(state), len(state)
        if h not in self.states:
            self.db.execute("INSERT OR IGNORE INTO states VALUES (?,?,?)", (self.id, h, dumps(pick(before))))
            self.states.add(h)
        rows = []
        for i, (change, res) in enumerate(zip(candidates, results)):
            kind, key, label = change_key(change)
            after = res.get("metrics")
            if not label and res.get("applied"):
                label = "; ".join(str(a) for a in res["applied"])
            rows.append((self.id, step, h, size, kind, key, label, json.dumps(change), costs[i] if costs else None,
                         dps(before) if before else None, dps(after) if after else None,
                         ehp(before) if before else None, ehp(after) if after else None,
                         score(before) if (score and before) else None, score(after) if (score and after) else None,
                         dumps(delta(before, after)) if after else None, res.get("error")))
        self.db.executemany("INSERT INTO samples (run_id, step, state_hash, state_size, kind, key, label, change, cost, dps_before, "
                            "dps_after, ehp_before, ehp_after, score_before, score_after, delta, error) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        self.db.commit()
        self.count += len(rows)

    def finish(self, final=None, outcome=None):
        if not self.enabled:
            return
        self.db.execute("UPDATE runs SET finished = ?, final = ?, outcome = ? WHERE id = ?",
                        (datetime.datetime.now().isoformat(timespec="seconds"), json.dumps(pick(final or {})), outcome, self.id))
        self.db.commit()


# --- queries ---------------------------------------------------------------------------------------------------------
def summary():
    db = connect()
    runs = db.execute("SELECT COUNT(*), COUNT(finished) FROM runs").fetchone()
    samples = db.execute("SELECT COUNT(*), COUNT(error) FROM samples").fetchone()
    by_tool = db.execute("SELECT tool, COUNT(*) FROM runs GROUP BY tool").fetchall()
    by_kind = db.execute("SELECT kind, COUNT(*) FROM samples GROUP BY kind ORDER BY 2 DESC").fetchall()
    recent = db.execute("SELECT id, started, tool, skill, ascendancy, focus, gear, (SELECT COUNT(*) FROM samples s WHERE s.run_id = r.id) "
                        "FROM runs r ORDER BY started DESC LIMIT 10").fetchall()
    return {"runs": runs[0], "finishedRuns": runs[1], "samples": samples[0], "failedSamples": samples[1],
            "byTool": dict(by_tool), "byKind": dict(by_kind),
            "recent": [dict(zip(("id", "started", "tool", "skill", "ascendancy", "focus", "gear", "samples"), r)) for r in recent]}


def stats(kind=None, skill=None, ascendancy=None, top=20, min_samples=2):
    """Average effect of each change (by kind and key) over every sample matching the filters: DPS and EHP change in
    percent of the state it was tried in, per point for passives. Context matters: filter by skill / ascendancy."""
    db = connect()
    where, args = ["s.error IS NULL", "s.dps_after IS NOT NULL", "s.kind != 'none'"], []
    if kind:
        where.append("s.kind = ?")
        args.append(kind)
    if skill:
        where.append("(r.skill LIKE ? OR r.skill_info LIKE ?)")
        args += [f"%{skill}%", f"%{skill}%"]
    if ascendancy:
        where.append("r.ascendancy LIKE ?")
        args.append(f"%{ascendancy}%")
    rows = db.execute("SELECT s.kind, s.key, s.label, s.cost, s.dps_before, s.dps_after, s.ehp_before, s.ehp_after, s.run_id "
                      "FROM samples s JOIN runs r ON r.id = s.run_id WHERE " + " AND ".join(where), args).fetchall()
    groups = {}
    for kind_, key, label, cost, d0, d1, e0, e1, run in rows:
        g = groups.setdefault((kind_, key), {"kind": kind_, "key": key, "label": label, "n": 0, "runs": set(), "dps": [], "ehp": []})
        g["n"] += 1
        g["runs"].add(run)
        if label and len(label) > len(g["label"] or ""):
            g["label"] = label
        per = max(cost or 1, 1) if kind_ == "passive_add" else 1
        if d0:
            g["dps"].append((d1 / d0 - 1) * 100 / per)
        if e0 and e1:
            g["ehp"].append((e1 / e0 - 1) * 100 / per)
    out = []
    for g in groups.values():
        if g["n"] < min_samples:
            continue
        out.append({"kind": g["kind"], "key": g["key"], "label": g["label"], "samples": g["n"], "runs": len(g["runs"]),
                    "dpsPct": round(sum(g["dps"]) / len(g["dps"]), 2) if g["dps"] else None,
                    "ehpPct": round(sum(g["ehp"]) / len(g["ehp"]), 2) if g["ehp"] else None,
                    "perPoint": g["kind"] == "passive_add"})
    out.sort(key=lambda r: -((r["dpsPct"] or 0) + (r["ehpPct"] or 0)))
    return out[:top]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    sub.add_parser("compact", help="convert an old, large database to the compact format")
    p = sub.add_parser("seed", help="write the list of finished runs (small, no samples) for another computer to skip them")
    p.add_argument("file")
    p = sub.add_parser("merge", help="copy the finished runs of another computer's simdata.db into this one")
    p.add_argument("file")
    p = sub.add_parser("stats")
    p.add_argument("--kind")
    p.add_argument("--skill")
    p.add_argument("--ascendancy")
    p.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    if args.cmd == "compact":
        compact()
    elif args.cmd == "seed":
        seed(args.file)
    elif args.cmd == "merge":
        merge(args.file)
    elif args.cmd == "summary":
        json.dump(summary(), sys.stdout, ensure_ascii=False, indent=1)
    else:
        for r in stats(args.kind, args.skill, args.ascendancy, args.top):
            print(f"{r['kind']:14} {r['label'] or r['key']:60.60} n={r['samples']:4} runs={r['runs']:3} "
                  f"DPS {r['dpsPct'] if r['dpsPct'] is not None else '-':>8}% EHP {r['ehpPct'] if r['ehpPct'] is not None else '-':>8}%"
                  f"{' /point' if r['perPoint'] else ''}")
    print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
