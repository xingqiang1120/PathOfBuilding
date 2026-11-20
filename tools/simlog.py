"""Simulation log: every candidate the build generator and optimizer try in Path of Building, kept as data.

Each try is one sample: the context (skill, ascendancy, focus, gear mode, PoB and tree version), the build state it
started from, the change, and the numbers before and after. Over many runs this shows which changes are worth what
in which kind of build (e.g. "Wandslinger, wand attack skills: +x% DPS per point"), and later trains a fast model
that suggests which candidates to try first. Answers still come from PoB; the log only guides the search.

Stored in library/simdata.db (git-ignored, local).

    python tools/simlog.py summary                       runs and samples so far
    python tools/simlog.py stats [--kind passive_add] [--skill wand] [--ascendancy Necromancer] [--top 20]
"""
import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("POB_LIBRARY", os.path.join(ROOT, "library"))

# Numbers kept for every sample (before and after)
METRICS = ["playerDPS", "minionDPS", "Life", "EnergyShield", "Mana", "TotalEHP", "PhysicalMaximumHitTaken", "FireMaximumHitTaken",
           "ColdMaximumHitTaken", "LightningMaximumHitTaken", "ChaosMaximumHitTaken", "FireResist", "ColdResist", "LightningResist",
           "ChaosResist", "EffectiveBlockChance", "EffectiveSpellBlockChance", "EffectiveSpellSuppressionChance", "Armour", "Evasion",
           "ManaUnreserved", "LifeUnreserved", "attributeShortfall", "passivePointsUsed", "passivePointsAvailable", "minionLimit",
           "Speed", "CritChance", "HitChance"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY, started TEXT, tool TEXT, skill TEXT, ascendancy TEXT, class TEXT, focus TEXT, gear TEXT,
    pob_version TEXT, tree_version TEXT, skill_info TEXT, finished TEXT, final TEXT);
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step TEXT, state_hash TEXT, state_size INTEGER,
    kind TEXT, key TEXT, label TEXT, change TEXT, cost INTEGER,
    dps_before REAL, dps_after REAL, ehp_before REAL, ehp_after REAL, score_before REAL, score_after REAL,
    before TEXT, after TEXT, error TEXT);
CREATE INDEX IF NOT EXISTS samples_key ON samples(kind, key);
CREATE INDEX IF NOT EXISTS samples_run ON samples(run_id);
"""


def db_path():
    return os.path.join(LIBRARY, "simdata.db")


def connect():
    os.makedirs(LIBRARY, exist_ok=True)
    db = sqlite3.connect(db_path(), timeout=120)  # several generators may write at the same time
    db.executescript(SCHEMA)
    return db


def pick(m):
    return {k: m.get(k) for k in METRICS if m and m.get(k) is not None}


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

    def __init__(self, tool, skill=None, ascendancy=None, cls=None, focus=None, gear=None, skill_info=None, versions=None):
        self.enabled = os.environ.get("POB_SIMLOG", "1") != "0"
        self.id = uuid.uuid4().hex[:12]
        self.count = 0
        if not self.enabled:
            return
        self.db = connect()
        versions = versions or {}
        self.db.execute("INSERT INTO runs (id, started, tool, skill, ascendancy, class, focus, gear, pob_version, tree_version, skill_info) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (self.id, datetime.datetime.now().isoformat(timespec="seconds"), tool, skill, ascendancy, cls, focus, gear,
                         versions.get("pobVersion"), versions.get("treeVersion"), json.dumps(skill_info or {})))
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
                         json.dumps(pick(before)), json.dumps(pick(after)) if after else None, res.get("error")))
        self.db.executemany("INSERT INTO samples (run_id, step, state_hash, state_size, kind, key, label, change, cost, dps_before, "
                            "dps_after, ehp_before, ehp_after, score_before, score_after, before, after, error) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)
        self.db.commit()
        self.count += len(rows)

    def finish(self, final=None):
        if not self.enabled:
            return
        self.db.execute("UPDATE runs SET finished = ?, final = ? WHERE id = ?",
                        (datetime.datetime.now().isoformat(timespec="seconds"), json.dumps(pick(final or {})), self.id))
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
    p = sub.add_parser("stats")
    p.add_argument("--kind")
    p.add_argument("--skill")
    p.add_argument("--ascendancy")
    p.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    if args.cmd == "summary":
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
