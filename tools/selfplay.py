"""Self-play: run the build generator over many skill x ascendancy pairs, unattended, to grow the simulation log.

    python tools/selfplay.py --hours 9 --jobs 2            run overnight with two generators in parallel (in the background:
                                                           the window can be closed)
    python tools/selfplay.py --dry-run --runs 20           show what would run
    python tools/selfplay.py --skills "Arc,Kinetic Blast" --runs 6
    python tools/selfplay.py --hours 9 --jobs 4 --shard 2/2   run only share 2 of 2 (two computers: tools/MULTI_PC.zh-TW.md)
    python tools/selfplay.py --hours 9 --foreground        run in this window instead (a click or closing it stops it)
    python tools/selfplay.py --status                          progress of a running (or the last) session
    python tools/selfplay.py --stop                            finish the runs in progress, start no new ones

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
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate  # noqa: E402
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


STATUS = os.path.join(LOG_DIR, "status.json")
STOP = os.path.join(LOG_DIR, "stop")
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW: generator processes never open a console


def disable_quick_edit():
    """A click in a console window with QuickEdit on pauses the program until a key is pressed (that stopped the first
    overnight run). Turn QuickEdit off for this window only."""
    if os.name != "nt":
        return
    k = ctypes.windll.kernel32
    handle = k.GetStdHandle(-10)  # STD_INPUT_HANDLE
    mode = ctypes.c_uint32()
    if handle and k.GetConsoleMode(handle, ctypes.byref(mode)):
        k.SetConsoleMode(handle, (mode.value & ~0x0040) | 0x0080)  # clear ENABLE_QUICK_EDIT_MODE, set ENABLE_EXTENDED_FLAGS


def write_status(**fields):
    fields["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    tmp = STATUS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(fields, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STATUS)


def read_status():
    try:
        with open(STATUS, encoding="utf-8") as f:
            st = json.load(f)
        return st, (datetime.datetime.now() - datetime.datetime.fromisoformat(st["updated"])).total_seconds()
    except (OSError, ValueError, KeyError):
        return None, None


def running_session():
    """Session id of a session that is running now (status written in the last 3 minutes), else None."""
    st, age = read_status()
    if st and st.get("state") in ("running", "starting") and age < 180:
        return st.get("session") or "?"
    return None


def show_status():
    s = simlog.summary()
    print(f"simulation log: {s['runs']} runs ({s['finishedRuns']} finished), {s['samples']:,} samples")
    st, age = read_status()
    if not st:
        print("no self-play session found")
        return
    if st.get("state") == "running":
        state = "RUNNING" if age < 180 else "NOT RUNNING (stopped without finishing - start it again to continue)"
    elif st.get("state") == "starting":
        state = "STARTING" if age < 180 else f"STUCK WHILE STARTING (process {st.get('pid')} never began a run - stop it and start again)"
    else:
        state = st.get("state", "?").upper()
    print(f"session {st.get('session')}: {state}; started {st.get('started')}, until {st.get('deadline')}, {st.get('jobs')} jobs"
          + (f", share {st['shard']}" if st.get("shard") else ""))
    print(f"  finished {st.get('finished', 0)}, failed {st.get('failed', 0)}, left in queue {st.get('queued', 0)}; last update {st['updated']}")
    for r in st.get("running", []):
        print(f"  running: {r}")
    for line in st.get("recent", [])[-8:]:
        print(f"  {line}")


def main_attribute(skill):
    reqs = {"Str": skill["reqStr"], "Dex": skill["reqDex"], "Int": skill["reqInt"]}
    return max(reqs, key=reqs.get) if any(reqs.values()) else None


def in_shard(skill, shard):
    """shard = (k, n): this computer runs share k of n. Split by skill name with a fixed hash, so every computer gets
    the same split without talking to the others, and all ascendancies of a skill stay on one computer."""
    if not shard:
        return True
    k, n = shard
    return zlib.crc32(skill.encode("utf-8")) % n == k - 1


def parse_shard(text):
    try:
        k, n = (int(x) for x in text.split("/"))
    except ValueError:
        raise SystemExit(f"--shard needs the form K/N, e.g. 2/2 (got {text!r})")
    if not 1 <= k <= n:
        raise SystemExit(f"--shard {text}: K must be between 1 and N")
    return k, n


DEFAULT_ARCHETYPES = "none,crit,armour,block,evasion,es,takenas"
DEFENCE_ASCENDANCIES = 2  # defence archetypes run only for each skill's best ascendancies with the plain gear


def best_ascendancies(focus, keep=DEFENCE_ASCENDANCIES):
    """skill -> the ascendancies whose plain-gear run (current generator) dealt the most damage."""
    db = simlog.connect()
    rows = db.execute("SELECT skill, ascendancy, final FROM runs WHERE tool = 'generate' AND finished IS NOT NULL AND gear = 'template' "
                      "AND guide IS NULL AND focus = ? AND generator >= ? AND final IS NOT NULL",
                      (focus, generate.GENERATOR_VERSION)).fetchall()
    by_skill = {}
    for skill, asc, final in rows:
        m = json.loads(final)
        by_skill.setdefault(skill, []).append((m.get("minionDPS") or m.get("playerDPS") or 0, asc))
    return {skill: {a for d, a in sorted(v, reverse=True)[:keep] if d > 0} for skill, v in by_skill.items()}


def plan(seed=None, skill_filter=None, focus="balanced", shard=None, archetypes=DEFAULT_ARCHETYPES):
    WORKER.call("create_build", {"ascendancy": "Witch", "skill": "Fireball"})  # any build: skill_list reads PoB data
    data = WORKER.call("skill_list", {})
    versions = WORKER.call("ping", {})
    skills = [s for s in data["skills"] if " of Trarthus" not in s["name"]]  # mercenary-only versions
    if skill_filter:
        wanted = [w.strip().lower() for w in skill_filter.split(",") if w.strip()]
        skills = [s for s in skills if any(w in s["name"].lower() for w in wanted)]
    skills = [s for s in skills if in_shard(s["name"], shard)]
    done, tried = finished_pairs(versions.get("pobVersion"), focus)
    rng = random.Random(seed)
    queue = []
    best = best_ascendancies(focus)
    # every pair with the template gear first; then the crit archetype for skills that hit (not minions), which
    # builds for crit with crit gear and a Diamond Flask - the greedy search does not get there from hybrid gear
    # then the defence archetypes (armour, block, evasion, energy shield, physical taken as elemental): one row per
    # defence for every pair, to find the balance of damage and defence per skill
    for archetype in [None if a == "none" else a for a in archetypes.split(",")]:
        per_skill = []
        for s in skills:
            if archetype == "crit" and (s["minion"] or not (s["attack"] or s["spell"])):
                continue
            attr = main_attribute(s)
            ascs = [a for a in data["ascendancies"] if attr is None or attr in CLASS_ATTRIBUTES.get(a["class"], set())]
            if archetype not in (None, "crit"):  # a defence: only where the plain gear did best (known once that ran)
                ascs = [a for a in ascs if a["name"] in best.get(s["name"], set())]
            rng.shuffle(ascs)
            pairs = [(s["name"], a["name"], archetype) for a in ascs if (s["name"], a["name"], archetype) not in done]
            if pairs:
                per_skill.append(pairs)
        rng.shuffle(per_skill)
        part = []
        depth = 0
        while any(depth < len(p) for p in per_skill):
            part.extend(p[depth] for p in per_skill if depth < len(p))
            depth += 1
        part.sort(key=lambda pair: pair in tried)  # stable: pairs never run first, then re-runs of older generator results
        queue += part
    return queue, len(done), versions


def finished_pairs(pob_version, focus):
    """(done, tried): pairs finished by the current generator version, and pairs finished by any version. Results of an
    older generator stay in the log as data, but the pair is run again (after the pairs never run at all)."""
    db = simlog.connect()
    rows = db.execute("SELECT skill, ascendancy, generator, gear, skill_info, outcome FROM runs WHERE tool = 'generate' "
                      "AND finished IS NOT NULL AND gear LIKE 'template%' AND gear NOT LIKE 'template around%' AND guide IS NULL AND focus = ? "
                      "AND (pob_version = ? OR ? IS NULL)", (focus, pob_version, pob_version)).fetchall()
    done, tried = set(), set()
    for skill, asc, version, gear, info, outcome in rows:
        key = (skill, asc, gear.split(" ", 1)[1] if " " in gear else None)
        tried.add(key)
        version = version or 1
        if version >= generate.GENERATOR_VERSION or (
                version >= generate.STILL_VALID_FROM and outcome != "no damage"
                and not generate.changed_since_valid(skill, json.loads(info or "{}"))):
            done.add(key)
    return done, tried


def label(skill, asc, archetype):
    return f"{skill} / {asc}" + (f" ({archetype})" if archetype else "")


def start(skill, asc, focus, log_file, archetype=None):
    env = dict(os.environ, POB_GENERATE_DIR=OUT_DIR, PYTHONIOENCODING="utf-8")
    cmd = [sys.executable, os.path.join(ROOT, "tools", "generate.py"), skill, asc, "--focus", focus,
           "--name", f"{skill} - {asc}" + (f" - {archetype}" if archetype else "")]
    if archetype:
        cmd += ["--archetype", archetype]
    out = open(log_file, "a", encoding="utf-8")
    out.write(f"\n===== {datetime.datetime.now():%Y-%m-%d %H:%M:%S} {label(skill, asc, archetype)}\n")
    out.flush()
    return subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=ROOT, env=env, creationflags=NO_WINDOW), out


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
    ap.add_argument("--shard", help="K/N: run only share K of N, to split the work over N computers (e.g. 1/2 here, 2/2 on the "
                                     "other one); merge their results with  python tools/simlog.py merge <file>")
    ap.add_argument("--archetypes", default=DEFAULT_ARCHETYPES,
                    help=f"comma-separated, in queue order (default {DEFAULT_ARCHETYPES}); none = the plain template gear")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--timeout", type=float, default=40, help="minutes before one run is stopped")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--background", action="store_true", help="(default) run without a window (output in library/selfplay/)")
    ap.add_argument("--foreground", action="store_true", help="run in this window (a click or a closed window can stop it)")
    ap.add_argument("--status", action="store_true", help="show progress and exit")
    ap.add_argument("--stop", action="store_true", help="ask a running session to start no new runs")
    args = ap.parse_args()
    if args.status:
        show_status()
        return
    if args.stop:
        os.makedirs(LOG_DIR, exist_ok=True)
        open(STOP, "w").close()
        print("asked the running session to stop: runs in progress finish first (a few minutes)")
        return
    active = running_session()
    if active and not args.dry_run:
        print(f"a self-play session is already running (session {active}): see  python tools/selfplay.py --status")
        return
    if not args.foreground and not args.dry_run:
        # Always detached from the window: a run started in a console window stopped twice (a click paused it,
        # once it never started), so the window only launches it
        os.makedirs(LOG_DIR, exist_ok=True)
        argv = [a for a in sys.argv[1:] if a != "--background"] + ["--foreground"]
        out = open(os.path.join(LOG_DIR, "background.log"), "a", encoding="utf-8")
        flags = (0x00000008 | 0x00000200 | NO_WINDOW) if os.name == "nt" else 0  # DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
        proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), *argv], stdout=out, stderr=subprocess.STDOUT, cwd=ROOT,
                                env=dict(os.environ, PYTHONIOENCODING="utf-8"), creationflags=flags)
        print(f"self-play started in the background (process {proc.pid}). Windows can be closed.")
        print("  progress: python tools/selfplay.py --status")
        print("  stop:     python tools/selfplay.py --stop")
        return
    disable_quick_edit()
    if not args.dry_run:
        os.makedirs(LOG_DIR, exist_ok=True)
        # written before anything slow, so --status can tell a session that never got going
        write_status(state="starting", session="-", pid=os.getpid(), jobs=args.jobs, started=datetime.datetime.now().isoformat(timespec="seconds"))

    shard = parse_shard(args.shard) if args.shard else None
    queue, skipped, versions = plan(args.seed, args.skills, args.focus, shard, args.archetypes)
    if args.runs:
        queue = queue[:args.runs]
    print(f"PoB {versions.get('pobVersion')}, tree {versions.get('treeVersion')}: {len(queue)} pairs to run, {skipped} already done"
          + (f" (share {shard[0]} of {shard[1]})" if shard else ""))
    if args.dry_run:
        for skill, asc, archetype in queue[:50]:
            print(f"  {label(skill, asc, archetype)}")
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    session = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    summary_path = os.path.join(LOG_DIR, f"selfplay-{session}.txt")
    deadline = time.time() + args.hours * 3600
    running, finished, failed, recent = [], 0, 0, []
    free_slots = list(range(args.jobs))  # one log file per parallel job, so runs never share a log
    if os.path.exists(STOP):
        os.remove(STOP)
    common = {"session": session, "pid": os.getpid(), "started": datetime.datetime.now().isoformat(timespec="seconds"),
              "deadline": datetime.datetime.fromtimestamp(deadline).isoformat(timespec="minutes"), "jobs": args.jobs, "shard": args.shard}
    keep_awake(True)
    try:
        with open(summary_path, "a", encoding="utf-8") as summary:
            while queue or running:
                if os.path.exists(STOP):
                    queue.clear()
                while queue and free_slots and time.time() < deadline:
                    skill, asc, archetype = queue.pop(0)
                    slot = free_slots.pop(0)
                    log_file = os.path.join(LOG_DIR, f"run-{session}-{slot}.log")
                    proc, out = start(skill, asc, args.focus, log_file, archetype)
                    running.append({"proc": proc, "out": out, "skill": skill, "asc": asc, "label": label(skill, asc, archetype),
                                    "log": log_file, "t": time.time(), "slot": slot})
                    print(f"{datetime.datetime.now():%H:%M} start  {label(skill, asc, archetype)}", flush=True)
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
                    free_slots.append(r["slot"])
                    minutes = (time.time() - r["t"]) / 60
                    ok = code == 0
                    finished += ok
                    failed += not ok
                    line = f"{datetime.datetime.now():%H:%M} {'done ' if ok else 'FAIL '} {r['label']} " \
                           f"({minutes:.1f} min) {result_line(r['log']) if ok else 'exit ' + str(code)}"
                    print(line, flush=True)
                    summary.write(line + "\n")
                    summary.flush()
                    recent = (recent + [line])[-20:]
                write_status(state="running", finished=finished, failed=failed, queued=len(queue), recent=recent,
                             running=[f"{r['label']} ({(time.time() - r['t']) / 60:.0f} min)" for r in running], **common)
                if time.time() >= deadline:
                    queue.clear()
    except KeyboardInterrupt:
        print("stopping: waiting runs are killed; finished runs are kept and skipped next time")
        for r in running:
            r["proc"].kill()
    finally:
        keep_awake(False)
        write_status(state="finished", finished=finished, failed=failed, queued=len(queue), recent=recent, running=[], **common)
    s = simlog.summary()
    print(f"\n{finished} runs finished, {failed} failed. Simulation log: {s['runs']} runs, {s['samples']:,} samples. Summary: {summary_path}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
