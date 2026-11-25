"""Weights from the simulation log: how good each support, aura, curse, ascendancy node and passive tends to be, by context.

    python tools/weights.py build                 compute library/weights.db from library/simdata.db (a few minutes)
    python tools/weights.py suggest "Glacial Hammer" Champion [--category support] [--top 15]
    python tools/weights.py check                 the held-out check of the last build

How a weight is measured. Every time the generator tried candidates from one state (one "batch": e.g. all supports for
the 3rd link), each candidate gets a rank in that batch: 1.0 = the best of the batch, 0.0 = the worst (passives by score
gain per point). Ranks compare candidates fairly whether they were tried early (big gains) or late (small gains).
A candidate's weight in a context is its average rank there; DPS and EHP changes (percent of the state) are kept too.

Contexts, general to specific: all runs, the ascendancy, each gem tag of the skill (cold, melee, strike...), tag x
ascendancy, the skill, the skill x ascendancy. A suggestion starts from "all runs" and moves toward each more specific
context in proportion to how many samples it has there (shrinkage: few samples -> stays near the general weight).

Held-out check: runs are split 80/20 by a hash of their id. Weights are computed from the 80% and used to predict, in
every batch of the other 20%, which candidate PoB scores best; the hit rate is compared with picking at random. The
check is stored with the weights, so a weight table always says how well it predicts.

Excluded: unfinished runs, runs with no damage, runs not on template gear, guided runs, and generator-1 runs of the skills whose
stage counts were wrong then (Blade Blast, Blade Blast of Unloading, Explosive Arrow).
"""
import argparse
import datetime
import json
import os
import re
import sqlite3
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simlog  # noqa: E402

ROOT = simlog.ROOT
GEMS_LUA = os.path.join(ROOT, "src", "Data", "Gems.lua")
K = 10  # shrinkage: samples at which a context counts as much as everything more general
WRONG_IN_V1 = {"Blade Blast", "Blade Blast of Unloading", "Explosive Arrow"}
NOT_CONTEXT_TAGS = {"strength", "dexterity", "intelligence", "grants_active_skill", "active_skill", "vaal", "low_max_level",
                    "exceptional", "awakened", "support"}
CROSS_TAGS = {"attack", "spell", "minion", "melee", "projectile", "fire", "cold", "lightning", "physical", "chaos", "totem",
              "trap", "mine", "bow"}  # tags also combined with the ascendancy
CATEGORIES = {  # generator step -> category
    "weapon": "weapon", "support": "support", "support swap": "support", "ascendancy": "ascendancy", "tree": "passive",
    "buff": "aura", "curse": "curse", "pantheon": "pantheon", "flask": "flask", "jewel kind": "jewel", "jewel": "jewel",
    "guard": "utility", "golem": "utility", "warcry": "utility"}
ALL_CATEGORIES = sorted(set(CATEGORIES.values()) | {"mastery"})  # masteries are tried in the tree step


def db_path():
    return os.path.join(simlog.LIBRARY, "weights.db")


def gem_tags():
    """{gem name: set of tags} from PoB's gem data."""
    with open(GEMS_LUA, encoding="utf-8") as f:
        text = f.read()
    out = {}
    for m in re.finditer(r'name = "([^"]+)",.*?tags = \{(.*?)\}', text, re.S):
        out.setdefault(m.group(1), {t for t in re.findall(r"(\w+) = true", m.group(2)) if t not in NOT_CONTEXT_TAGS})
    return out


def contexts(skill, asc, tags, archetype=None):
    """Context ids from general to specific. The crit archetype (crit gear, no never-crit keystones) has its own set,
    prefixed "crit:", so crit and non-crit builds do not blur each other's weights."""
    out = ["all", f"asc:{asc}"]
    out += [f"tag:{t}" for t in sorted(tags)]
    out += [f"tag:{t}|asc:{asc}" for t in sorted(tags & CROSS_TAGS)]
    out += [f"skill:{skill}", f"skill:{skill}|asc:{asc}"]
    return [f"{archetype}:{c}" for c in out] if archetype else out


def candidate(kind, key, label, step):
    """(category, key, readable label) of one sample."""
    cat = CATEGORIES.get(step)
    if not cat:
        return None
    if "item_equip" in kind and ("Jewel " in key):
        name = re.search(r"Template ([\w ]+?) Jewel", key)
        return "jewel", name.group(1) if name else key, (name.group(1) + " jewel") if name else key
    if kind == "mastery_add":
        return "mastery", key, label or key  # label: "Two Hand Mastery: 3% chance to deal Triple Damage"
    if cat == "flask":
        return cat, key.split(":", 1)[-1], key.split(":", 1)[-1]  # "Flask 3:Jade Flask" -> the base, whatever the slot
    if cat == "weapon":
        key = "|".join(re.sub(r"^Weapon \d:", "", p) for p in key.split("|"))
        return cat, key, key.replace("Template ", "")
    if cat in ("passive", "ascendancy"):
        name = re.sub(r"^allocated ", "", label or "")
        name = re.sub(r" \(\d+ points?\)$", "", name)
        return cat, key, name
    return cat, key, key  # gems: the key is the gem (for a swap, the gem swapped in)


def holdout(run_id):
    return zlib.crc32(run_id.encode()) % 5 == 0


def usable_runs(db):
    out = []
    for rid, skill, asc, gen, outcome, final, gear in db.execute(
            "SELECT id, skill, ascendancy, generator, outcome, final, gear FROM runs WHERE tool = 'generate' AND finished IS NOT NULL "
            "AND gear IN ('template', 'template crit') AND guide IS NULL"):  # a guided run tried only what the weights liked
        m = json.loads(final or "{}")
        if outcome == "no damage" or not ((m.get("playerDPS") or 0) > 0 or (m.get("minionDPS") or 0) > 0):
            continue
        if (gen or 1) < 2 and skill in WRONG_IN_V1:
            continue
        out.append((rid, skill, asc, "crit" if gear == "template crit" else None))
    return out


def batches(db, run_id):
    """Yield (category, [(key, label, rank, dps%, ehp%)]) for each batch of a run."""
    groups = {}
    for step, h, kind, key, label, cost, d0, d1, e0, e1, s0, s1 in db.execute(
            "SELECT step, state_hash, kind, key, label, cost, dps_before, dps_after, ehp_before, ehp_after, score_before, score_after "
            "FROM samples WHERE run_id = ? AND error IS NULL AND score_after IS NOT NULL ORDER BY id", (run_id,)):
        c = candidate(kind, key, label, step)
        if not c:
            continue
        cat, k, lab = c
        per = max(cost or 1, 1) if cat == "passive" else 1
        gain = (s1 - s0) / per
        dps = ((d1 / d0 - 1) * 100 / per) if d0 else None
        ehp = ((e1 / e0 - 1) * 100 / per) if e0 and e1 else None
        g = groups.setdefault((step, h, kind if cat != "weapon" else "w"), [cat, {}])
        g[1].setdefault(k, (lab, gain, dps, ehp))  # a candidate tried twice in one state counts once
    for cat, cands in groups.values():
        if len(cands) < 3:
            continue
        # rank among the candidates that improve the score (the generator keeps only those); the others rank 0, so a
        # candidate doing nothing is not rated well just because the rest of its batch made things worse
        order = sorted(cands.items(), key=lambda kv: kv[1][1])
        better = [kv for kv in order if kv[1][1] > 1e-6]
        n = len(order) - 1
        rows = []
        for i, (k, (lab, gain, dps, ehp)) in enumerate(order):
            if gain > 1e-6:
                j = better.index((k, (lab, gain, dps, ehp)))
                rank = 0.5 + 0.5 * (j / (len(better) - 1) if len(better) > 1 else 1.0)
            else:
                rank = 0.0
            rows.append((k, lab, rank, dps, ehp, gain))
        yield cat, rows


class Table:
    """Sums per (context, category, key), for all runs and for the training runs only (one entry, to save memory):
    [label, n, runs, last run, rank sum, dps sum, dps n, ehp sum, ehp n, train n, train rank sum]."""

    def __init__(self):
        self.s = {}
        self.train = True  # mean() reads the training sums while validating, all sums afterwards

    def add(self, ctxs, cat, rows, run_id, train):
        for k, lab, rank, dps, ehp, _ in rows:
            for ctx in ctxs:
                e = self.s.get((ctx, cat, k))
                if e is None:
                    e = self.s[(ctx, cat, k)] = [lab, 0, 0, None, 0.0, 0.0, 0, 0.0, 0, 0, 0.0]
                e[1] += 1
                if e[3] != run_id:
                    e[2] += 1
                    e[3] = run_id
                e[4] += rank
                if dps is not None:
                    e[5] += dps
                    e[6] += 1
                if ehp is not None:
                    e[7] += ehp
                    e[8] += 1
                if train:
                    e[9] += 1
                    e[10] += rank

    def mean(self, ctx, cat, k):
        e = self.s.get((ctx, cat, k))
        if not e:
            return None, 0
        n, total = (e[9], e[10]) if self.train else (e[1], e[4])
        return (total / n, n) if n else (None, 0)


def estimate(table, ctxs, cat, k):
    """Shrunk rank: from the most general context toward the specific ones, weighted by their sample counts."""
    est, n_used = 0.5, 0
    for ctx in ctxs:
        m, n = table.mean(ctx, cat, k)
        if n:
            est = (n * m + K * est) / (n + K)
            n_used = n
    return est, n_used


def build(exclude=(), path=None):
    """exclude: skills left out (to test the guided generator on skills the weights have not seen); path: output file."""
    t0 = time.time()
    src = simlog.connect()
    tags = gem_tags()
    runs = [r for r in usable_runs(src) if r[1] not in set(exclude)]
    table, test = Table(), []
    for i, (rid, skill, asc, archetype) in enumerate(runs):
        ctxs = contexts(skill, asc, tags.get(skill, set()), archetype)
        held = holdout(rid)
        for cat, rows in batches(src, rid):
            table.add(ctxs, cat, rows, rid, train=not held)
            if held:
                test.append((ctxs, cat, rows))
        if i % 100 == 99:
            print(f"  {i + 1}/{len(runs)} runs ({time.time() - t0:.0f} s)", flush=True)
    check = validate(table, test)

    path = path or db_path()
    tmp = path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    out = sqlite3.connect(tmp)
    out.executescript("""
        CREATE TABLE weights (ctx TEXT, category TEXT, key TEXT, label TEXT, n INTEGER, runs INTEGER, rank REAL, dps REAL, ehp REAL,
                              PRIMARY KEY (ctx, category, key)) WITHOUT ROWID;
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);""")
    out.executemany("INSERT INTO weights VALUES (?,?,?,?,?,?,?,?,?)",
                    [(ctx, cat, k, e[0], e[1], e[2], e[4] / e[1], e[5] / e[6] if e[6] else None, e[7] / e[8] if e[8] else None)
                     for (ctx, cat, k), e in table.s.items()])
    meta = {"built": datetime.datetime.now().isoformat(timespec="seconds"), "runs": len(runs),
            "holdoutRuns": sum(1 for r in runs if holdout(r[0])), "check": check, "shrinkageK": K}
    out.executemany("INSERT INTO meta VALUES (?,?)", [(k, json.dumps(v)) for k, v in meta.items()])
    out.commit()
    out.close()
    os.replace(tmp, path)
    print(f"built {path} from {len(runs)} runs in {time.time() - t0:.0f} s")
    print_check(check)


def validate(train, test):
    """Per category: how often the predicted best candidate is PoB's best, against random; and the average real rank
    of the predicted best (0.5 = random)."""
    res = {}
    for ctxs, cat, rows in test:
        r = res.setdefault(cat, {"batches": 0, "hit": 0, "random": 0.0, "top3": 0, "random3": 0.0, "pickedRank": 0.0})
        pred = sorted(rows, key=lambda row: -estimate(train, ctxs, cat, row[0])[0])
        best = max(rows, key=lambda row: row[5])[0]
        r["batches"] += 1
        r["hit"] += pred[0][0] == best
        r["top3"] += best in {row[0] for row in pred[:3]}
        r["random"] += 1 / len(rows)
        r["random3"] += min(3, len(rows)) / len(rows)
        r["pickedRank"] += pred[0][2]
    out = {}
    for cat, r in res.items():
        b = r["batches"]
        out[cat] = {"batches": b, "bestFirst": round(r["hit"] / b, 3), "bestFirstRandom": round(r["random"] / b, 3),
                    "bestInTop3": round(r["top3"] / b, 3), "bestInTop3Random": round(r["random3"] / b, 3),
                    "pickedRank": round(r["pickedRank"] / b, 3)}
    return out


def print_check(check):
    print("\nheld-out check (20% of runs never used for the weights):")
    print(f"  {'category':11} {'batches':>8}  {'best first':>16}  {'best in top 3':>16}  {'rank of the pick':>16}")
    for cat, c in sorted(check.items()):
        print(f"  {cat:11} {c['batches']:8}  {c['bestFirst']:7.1%} vs {c['bestFirstRandom']:5.1%}  "
              f"{c['bestInTop3']:7.1%} vs {c['bestInTop3Random']:5.1%}  {c['pickedRank']:16.2f}")
    print("  (vs = picking at random; rank of the pick: 1 = always the best, 0.5 = random)")


# --- queries ---------------------------------------------------------------------------------------------------------
class Loaded:
    """Rows of some contexts, read in one query: {(ctx, category, key): (label, n, rank, dps, ehp)}."""

    def __init__(self, db, ctxs, cats=None):
        q = f"SELECT ctx, category, key, label, n, rank, dps, ehp FROM weights WHERE ctx IN ({','.join('?' * len(ctxs))})"
        self.rows = {(c, cat, k): rest for c, cat, k, *rest in db.execute(q, ctxs) if not cats or cat in cats}

    def mean(self, ctx, cat, k):
        r = self.rows.get((ctx, cat, k))
        return (r[2], r[1]) if r else (None, 0)

    def keys(self, ctx, cat):
        return [(k, r[0]) for (c, ct, k), r in self.rows.items() if c == ctx and ct == cat]


def open_weights():
    if not os.path.exists(db_path()):
        raise SystemExit("no weights yet: run  python tools/weights.py build")
    return sqlite3.connect(db_path())


def pools(cat, skill, ascendancy, ctxs):
    """Where the usable candidates are listed, first match wins: tried for this skill (or, never run, for its tags);
    ascendancy nodes from this ascendancy."""
    if cat == "ascendancy":
        return [f"asc:{ascendancy}"]
    if cat in ("support", "weapon"):
        return [f"skill:{skill}|asc:{ascendancy}", f"skill:{skill}"] + [c for c in reversed(ctxs) if c.startswith("tag:") and "|" not in c]
    return [f"skill:{skill}", "all"]


def suggest(skill, ascendancy, category=None, top=15, db=None, tags=None):
    """Candidates ranked by their shrunk weight for this skill and ascendancy, with where the weight comes from."""
    db = db or open_weights()
    tags = tags if tags is not None else gem_tags().get(skill)
    if tags is None:
        raise SystemExit(f"unknown skill gem: {skill}")
    ctxs = contexts(skill, ascendancy, tags)
    cats = [category] if category else ALL_CATEGORIES
    data = Loaded(db, ctxs, cats)
    out = {}
    for cat in cats:
        keys = []
        for pool in pools(cat, skill, ascendancy, ctxs):
            keys = data.keys(pool, cat)
            if keys:
                break
        rows = []
        for k, label in keys:
            est, _ = estimate(data, ctxs, cat, k)
            where = next((c for c in reversed(ctxs) if (c, cat, k) in data.rows), "all")
            _, n, _, dps, ehp = data.rows[(where, cat, k)]
            if cat == "weapon":
                dps = None  # DPS against no weapon at all: not meaningful
            rows.append({"key": k, "label": label, "weight": round(est, 3), "mostSpecific": where, "samplesThere": n,
                         "dpsPct": round(dps, 1) if dps is not None else None, "ehpPct": round(ehp, 1) if ehp is not None else None})
        rows.sort(key=lambda r: -r["weight"])
        if rows:
            out[cat] = rows[:top]
    return {"skill": skill, "ascendancy": ascendancy, "tags": sorted(tags), "contexts": ctxs, "suggestions": out}


TOP_EXPORT = {"support": 10, "ascendancy": 8, "aura": 6, "curse": 6, "passive": 12, "mastery": 8, "pantheon": 4, "flask": 6, "jewel": 6, "utility": 6, "weapon": 4}


def export(out_dir):
    """Data for the weights page: every skill x ascendancy pair with runs, suggestions per category (compact rows)."""
    db = open_weights()
    tags = gem_tags()
    meta = {k: json.loads(v) for k, v in db.execute("SELECT key, value FROM meta")}
    pairs = sorted({tuple(c[len("skill:"):].split("|asc:")) for (c,) in db.execute(
        "SELECT DISTINCT ctx FROM weights WHERE ctx LIKE 'skill:%|asc:%'")})
    t0 = time.time()
    records = []
    for i, (skill, asc) in enumerate(pairs):
        r = suggest(skill, asc, db=db, tags=tags.get(skill, set()))
        sug = {cat: [[x["label"], x["weight"], x["dpsPct"], x["ehpPct"], x["samplesThere"], level(x["mostSpecific"])]
                     for x in rows[:TOP_EXPORT.get(cat, 8)]] for cat, rows in r["suggestions"].items()}
        records.append({"s": skill, "a": asc, "t": r["tags"], "g": sug})
        if i % 200 == 199:
            print(f"  {i + 1}/{len(pairs)} pairs ({time.time() - t0:.0f} s)", flush=True)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "weights-data.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "pairs": records}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"exported {len(records)} pairs to {out_dir}")


def level(ctx):
    """Short name of how specific a context is."""
    if ctx.startswith("skill:"):
        return "skill+asc" if "|asc:" in ctx else "skill"
    if ctx.startswith("tag:"):
        return "tag+asc" if "|asc:" in ctx else "tag:" + ctx[4:]
    return "asc" if ctx.startswith("asc:") else "all"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("--exclude", help="comma-separated skills to leave out (for tests)")
    p.add_argument("--out", help="write to this file instead of library/weights.db")
    sub.add_parser("check")
    p = sub.add_parser("suggest")
    p.add_argument("skill")
    p.add_argument("ascendancy")
    p.add_argument("--category", choices=ALL_CATEGORIES)
    p.add_argument("--top", type=int, default=15)
    p = sub.add_parser("export", help="data for the weights page")
    p.add_argument("dir")
    args = ap.parse_args()
    if args.cmd == "build":
        build([x.strip() for x in (args.exclude or "").split(",") if x.strip()], args.out)
    elif args.cmd == "export":
        export(args.dir)
    elif args.cmd == "check":
        db = open_weights()
        meta = {k: json.loads(v) for k, v in db.execute("SELECT key, value FROM meta")}
        print(f"built {meta['built']} from {meta['runs']} runs ({meta['holdoutRuns']} held out)")
        print_check(meta["check"])
    else:
        r = suggest(args.skill, args.ascendancy, args.category, args.top)
        print(f"{r['skill']} / {r['ascendancy']}  tags: {', '.join(r['tags'])}")
        for cat, rows in r["suggestions"].items():
            print(f"\n{cat}:")
            for x in rows:
                print(f"  {x['weight']:.2f}  {x['label'][:42]:42}  DPS {x['dpsPct'] if x['dpsPct'] is not None else '-':>7}%  "
                      f"EHP {x['ehpPct'] if x['ehpPct'] is not None else '-':>6}%  from {x['mostSpecific']} (n={x['samplesThere']})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
