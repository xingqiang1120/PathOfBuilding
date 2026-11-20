"""Self-play: run the build generator over many skill x ascendancy pairs, unattended, to grow the simulation log.

    python tools/selfplay.py --hours 9 --jobs 2            run overnight with two generators in parallel
    python tools/selfplay.py --dry-run --runs 20           show what would run
    python tools/selfplay.py --skills "Arc,Kinetic Blast" --runs 6

Pairs: every damaging skill gem (PoB data) with the ascendancies whose class uses the gem's main attribute
(Str: Marauder, Duelist, Templar, Scion; Dex: Ranger, Duelist, Shadow, Scion; Int: Witch, Templar, Shadow, Scion).
Order: shuffled, one pair per skill before any skill gets a second one, so the data covers many skills early.
Pairs already finished for this PoB version, focus and gear are skipped, so it can be stopped (Ctrl+C) and resumed.

While it runs, Windows is asked not to go to sleep (the same request a video player makes; the screen may still turn
off). Each run's build goes to src/Builds/generated/selfplay/, its log to library/selfplay/.
"""
import argparse
import ctypes
import datetime
import json
import os
import random
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library  # noqa: E402
import simlog  # noqa: E402
from pob_worker import WORKER  # noqa: E402

ROOT = library.ROOT
OUT_DIR = os.path.join(ROOT, "src", "Builds", "generated", "selfplay")
LOG_DIR = os.path.join(library.LIBRARY, "selfplay")
CLASS_ATTRIBUTES = {"Marauder": {"Str"}, "Ranger": {"Dex"}, "Witch": {"Int"}, "Duelist": {"Str", "Dex"}, "Templar": {"Str", "Int"},
                    "Shadow": {"Dex", "Int"}, "Scion": {"Str", "Dex", "Int"}}


def keep_awake(on=True):
    if os.name != "nt":
        return
    ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))


def main_attribute(skill):
    reqs = {"Str": skill["reqStr"], "Dex": skill["reqDex"], "Int": skill["reqInt"]}
    return max(reqs, key=reqs.get) if any(reqs.values()) else None


def plan(seed=None, skill_filter=None, focus="balanced"):
    WORKER.call("create_build", {"ascendancy": "Witch", "skill": "Fireball"})  # any build: skill_list reads PoB data
    data = WORKER.call("skill_list", {})
    versions = WORKER.call("ping", {})
    skills = [s for s in data["skills"] if " of Trarthus" not in s["name"]]  # mercenary-only versions
    if skill_filter:
        wanted = [w.strip().lower() for w in skill_filter.split(",") if w.strip()]
        skills = [s for s in skills if any(w in s["name"].lower() for w in wanted)]
    done = finished_pairs(versions.get("pobVersion"), focus)
    rng = random.Random(seed)
    per_skill = []
    for s in skills:
        attr = main_attribute(s)
        ascs = [a for a in data["ascendancies"] if attr is None or attr in CLASS_ATTRIBUTES.get(a["class"], set())]
        rng.shuffle(ascs)
        pairs = [(s["name"], a["name"]) for a in ascs if (s["name"], a["name"]) not in done]
        if pairs:
            per_skill.append(pairs)
    rng.shuffle(per_skill)
    queue = []
    depth = 0
    while any(depth < len(p) for p in per_skill):
        queue.extend(p[depth] for p in per_skill if depth < len(p))
        depth += 1
    return queue, len(done), versions


def finished_pairs(pob_version, focus):
    db = simlog.connect()
    rows = db.execute("SELECT skill, ascendancy FROM runs WHERE tool = 'generate' AND finished IS NOT NULL AND gear = 'template' "
                      "AND focus = ? AND (pob_version = ? OR ? IS NULL)", (focus, pob_version, pob_version)).fetchall()
    return {(s, a) for s, a in rows}


def start(skill, asc, focus, log_file):
    env = dict(os.environ, POB_GENERATE_DIR=OUT_DIR, PYTHONIOENCODING="utf-8")
    cmd = [sys.executable, os.path.join(ROOT, "tools", "generate.py"), skill, asc, "--focus", focus, "--name", f"{skill} - {asc}"]
    out = open(log_file, "a", encoding="utf-8")
    out.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M:%S} {skill} / {asc}\n")
    out.flush()
    return subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=ROOT, env=env), out


def result_line(log_file):
    try:
        with open(log_file, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    except OSError:
        return ""
    for line in reversed(lines):
        if line.startswith("DPS "):
            return line
        if line.startswith("=====") or "Error" in line or "error" in line:
            return line[:160]
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=8, help="stop starting new runs after this long")
    ap.add_argument("--runs", type=int, help="stop after this many runs")
    ap.add_argument("--jobs", type=int, default=1, help="generators running at the same time (each uses one CPU core)")
    ap.add_argument("--focus", default="balanced", choices=["damage", "balanced", "defence"])
    ap.add_argument("--skills", help="comma-separated parts of skill names to limit the run to")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--timeout", type=float, default=40, help="minutes before one run is stopped")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    queue, skipped, versions = plan(args.seed, args.skills, args.focus)
    if args.runs:
        queue = queue[:args.runs]
    print(f"PoB {versions.get('pobVersion')}, tree {versions.get('treeVersion')}: {len(queue)} pairs to run, {skipped} already done")
    if args.dry_run:
        for skill, asc in queue[:50]:
            print(f"  {skill} / {asc}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    session = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    summary_path = os.path.join(LOG_DIR, f"selfplay-{session}.txt")
    deadline = time.time() + args.hours * 3600
    running, finished, failed = [], 0, 0
    keep_awake(True)
    try:
        with open(summary_path, "a", encoding="utf-8") as summary:
            while queue or running:
                while queue and len(running) < args.jobs and time.time() < deadline:
                    skill, asc = queue.pop(0)
                    log_file = os.path.join(LOG_DIR, f"run-{session}-{len(running) % max(args.jobs, 1)}.log")
                    proc, out = start(skill, asc, args.focus, log_file)
                    running.append({"proc": proc, "out": out, "skill": skill, "asc": asc, "log": log_file, "t": time.time()})
                    print(f"{datetime.datetime.now():%H:%M} start  {skill} / {asc}", flush=True)
                if not running:
                    break
                time.sleep(5)
                for r in list(running):
                    code = r["proc"].poll()
                    if code is None and time.time() - r["t"] > args.timeout * 60:
                        r["proc"].kill()
                        code = "timeout"
                    if code is None:
                        continue
                    r["out"].close()
                    running.remove(r)
                    minutes = (time.time() - r["t"]) / 60
                    ok = code == 0
                    finished += ok
                    failed += not ok
                    line = f"{datetime.datetime.now():%H:%M} {'done ' if ok else 'FAIL '} {r['skill']} / {r['asc']} " \
                           f"({minutes:.1f} min) {result_line(r['log']) if ok else 'exit ' + str(code)}"
                    print(line, flush=True)
                    summary.write(line + "\n")
                    summary.flush()
                if time.time() >= deadline:
                    queue.clear()
    except KeyboardInterrupt:
        print("stopping: waiting runs are killed; finished runs are kept and skipped next time")
        for r in running:
            r["proc"].kill()
    finally:
        keep_awake(False)
    s = simlog.summary()
    print(f"\n{finished} runs finished, {failed} failed. Simulation log: {s['runs']} runs, {s['samples']:,} samples. Summary: {summary_path}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
