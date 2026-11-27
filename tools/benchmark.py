"""Acceptance test for the build generator: one fixed exam, run after every generator version.

    python tools/benchmark.py run [--jobs 4] [--only authors|template]   run the suite (heavy: about 10 minutes a build)
    python tools/benchmark.py report                                       rewrite the report from the last results
    python tools/benchmark.py run --holdout [--jobs 4]                     the hold-out exam (see below)

Suite: tools/data/benchmark.json. Results: library/benchmark/v<version>.json and .md (library/ is git-ignored).

Hold-out exam (--holdout, agreed 2026-11-27): a second suite of real builds that the generator is NOT tuned against,
kept in the private data repo (pob-lab-data/holdout/holdout.json, same format). Results: v<version>-holdout.json and .md.
Whoever changes the generator must not open it or tune for it: it checks that a gain on the main exam is real and not
learned from those seven builds.

Three checks (agreed 2026-11-26):
  1. Authors: with the author's own items (--gear-from), the generator rebuilds tree, gems, auras and config, and is
     compared with the author's build. Pass: DPS at least 80% of the author's and defence (the score's defence part)
     no more than 0.1 below. Not the whole score: the authors often leave resistances uncapped, which the score's
     penalties punish so hard that the generator "won" while dealing a ninth of the damage (first run, 2026-11-26). Tree jewels and cluster jewels are dropped (the generator cannot
     place them yet), so a gap there is expected and reported. The author's Vaal skills are removed before scoring
     (2026-11-27): PoB counts them as always up and the generator does not choose them.
  2. Floors: every template run must be playable for mapping at level 95 - elemental resistances capped, chaos
     resistance >= 0 (or immune), life + energy shield and the smallest max hit above the floors in the suite file.
  3. No regression: each template run's score against the previous version's result. A drop of more than 0.05 is
     flagged (to be explained, or fixed).
"""
import argparse
import concurrent.futures
import datetime
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generate  # noqa: E402
import labdata  # noqa: E402
import library  # noqa: E402
import re  # noqa: E402

ROOT = library.ROOT
SUITE = os.path.join(ROOT, "tools", "data", "benchmark.json")
OUT = os.path.join(ROOT, "library", "benchmark")
HOLDOUT = os.path.join(labdata.DATA, "holdout", "holdout.json")


def result_files(name=""):
    """{version: path} of the results of one suite (name "" = the main exam, "holdout" = the hold-out exam)."""
    pattern = re.compile(r"v(\d+)" + (f"-{re.escape(name)}" if name else "") + r"\.json")
    return {int(m.group(1)): os.path.join(OUT, f) for f in os.listdir(OUT) if (m := re.fullmatch(pattern, f))} if os.path.isdir(OUT) else {}
AUTHOR_DPS = 0.8  # the generator's DPS at least 80% of the author's
AUTHOR_MARGIN = 0.1  # and its defence (the score's defence part) at most 0.1 below
REGRESSION = 0.05


def scorer(minion=False, profile=None):
    """A Generator used only for its score (balanced focus)."""
    g = generate.Generator.__new__(generate.Generator)
    g.weight, g.profile, g.attributes_later, g.info = generate.FOCUS["balanced"], profile, False, {"minion": minion}
    g.resists_later = False  # v13 flag read by penalty(); __init__ is bypassed here, so set it (v13 first run skipped every author)
    return g


def run_one(job, out_dir):
    name = "bench " + job["key"].replace("/", "-")
    result = os.path.join(out_dir, name + ".json")
    cmd = [sys.executable, os.path.join(ROOT, "tools", "generate.py"), job["skill"], job["ascendancy"], "--name", name]
    if job.get("archetype"):
        cmd += ["--archetype", job["archetype"]]
    if job.get("buildAround"):
        cmd += ["--build-around", job["buildAround"]]
    if job.get("gearFrom"):
        cmd += ["--gear-from", job["gearFrom"]]
    env = dict(os.environ, POB_GENERATE_DIR=out_dir, POB_RESULT_JSON=result, PYTHONIOENCODING="utf-8")
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    if os.path.exists(result):
        with open(result, encoding="utf-8") as f:
            return dict(job, **json.load(f))
    return dict(job, error=(p.stdout + p.stderr)[-1500:])


def author_job(entry):
    """The author's build scored as it is, and the generator's job with its items."""
    xml, name, build_id = library.resolve(entry["build"])
    # the author's Vaal skills are taken out: PoB counts their buff as always up (Vaal Arctic Armour +1.17 defence for
    # Storm Call / Assassin, v13 gap report), and the generator may not choose them (decision 2026-11-27), so with them
    # the author would be scored on something neither side can really keep up
    summary = generate.WORKER.call("summary", {"xml": xml, "name": name})
    vaal = [g["name"] for sk in summary["skills"] if not sk.get("source") for g in sk["gems"]  # one remove per gem
            if not g.get("support") and g["name"].startswith("Vaal ")]
    r = generate.WORKER.call("try", {"xml": xml, "name": name, "infer": True, "inferCharges": True,
                                     "candidates": [[{"type": "gem_remove", "gem": v} for v in vaal]]})[0]
    if "metrics" not in r:
        raise RuntimeError(f"author build without its Vaal skills ({', '.join(vaal)}): {r.get('error', '')[:200]}")
    m = r["metrics"]
    s = generate.WORKER.call("strip_build", {"xml": xml, "name": name})
    minion = bool(s["skillInfo"].get("minion"))
    sc = scorer(minion, generate.worn_profile(build_id)[1])
    author = {"metrics": m, "dps": sc.dps(m), "score": sc.score(m), "defence": sc.defence(m), "penalty": sc.penalty(m)}
    return {"key": "author " + entry["label"], "label": entry["label"], "skill": s["skill"], "ascendancy": s["ascendancy"],
            "gearFrom": entry["build"], "author": author, "jewelsDropped": s.get("jewelsDropped", 0), "vaalRemoved": vaal}


def template_jobs(suite):
    jobs = []
    for t in suite.get("template", []):
        key = f"{t['skill']} / {t['ascendancy']}" + (f" ({t['archetype']})" if t.get("archetype") else "") + (
            f" around {t['buildAround']}" if t.get("buildAround") else "")
        jobs.append(dict(t, key=key, label=key))
    return jobs


def floors(m, f, ignored=()):
    """[(check, value, ok)] against the playable floors; ignored: resistances a build-around profile makes irrelevant."""
    hits = [m.get(k) for k in ("PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken",
                               "ChaosMaximumHitTaken")]
    hits = [h for h in hits if h]
    ele = min(m.get(k) or 0 for k in ("FireResist", "ColdResist", "LightningResist") if k not in ignored)
    chaos = m.get("ChaosResist") or 0
    immune = not m.get("ChaosMaximumHitTaken")
    pool = (m.get("Life") or 0) + (m.get("EnergyShield") or 0)
    small = min(hits) if hits else 0
    return [("elemental res", ele, ele >= f["ElementalResist"]),
            ("chaos res", "immune" if immune else chaos, immune or chaos >= f["ChaosResist"]),
            ("life+ES", pool, pool >= f["LifePlusES"]),
            ("smallest max hit", small, small >= f["SmallestMaxHit"])]


def suite_floors(suite):
    """The suite's floors; a suite without them (the hold-out exam) uses the main exam's."""
    if "floors" in suite:
        return suite["floors"]
    with open(SUITE, encoding="utf-8") as f:
        return json.load(f)["floors"]


def previous_results(version, name=""):
    older = [v for v in result_files(name) if v < version]
    if not older:
        return None, {}
    with open(result_files(name)[max(older)], encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version"), {r["key"]: r for r in data["results"]}


def fmt(x):
    return f"{x:,.0f}" if isinstance(x, (int, float)) else str(x)


def report(data):
    suite = data["suite"]
    name = data.get("name", "")
    prev_version, prev = previous_results(data["version"], name)
    title = "Hold-out exam" if name == "holdout" else "Generator benchmark"
    lines = [f"# {title}: version {data['version']}", "", f"Run {data['date']}. Suite: {data.get('suitePath', 'tools/data/benchmark.json')}.", ""]
    authors = [r for r in data["results"] if r.get("gearFrom")]
    templ = [r for r in data["results"] if not r.get("gearFrom")]
    summary = []
    if authors:
        lines += ["## 1. Same items as the author", "",
                  f"Pass: DPS >= {AUTHOR_DPS:.0%} of the author's and defence >= author's - {AUTHOR_MARGIN}. "
                  "Shown as generator / author. The author is scored without Vaal skills (PoB counts them always up).", "",
                  "| Build | DPS gen / author | Defence gen / author | Score gen / author | Jewels dropped | Pass |",
                  "|---|---|---|---|---|---|"]
        passed = 0
        for r in authors:
            a = r["author"]
            if r.get("error"):
                lines.append(f"| {r['label']} | error | | | | no |")
                continue
            ok = r["dps"] >= AUTHOR_DPS * a["dps"] and r["defence"] >= a["defence"] - AUTHOR_MARGIN
            passed += ok
            lines.append(f"| {r['label']} | {r['dps'] / max(a['dps'], 1):.0%} ({fmt(r['dps'])} / {fmt(a['dps'])}) | "
                         f"{r['defence']:.2f} / {a['defence']:.2f} | {r['score']:.2f} / {a['score']:.2f} | {r.get('jewelsDropped', 0)} | "
                         f"{'yes' if ok else 'no'} |")
        summary.append(f"authors {passed}/{len(authors)}")
    if templ:
        lines += ["", "## 2. Playable floors and 3. regression (template gear)", "",
                  f"Floors: {', '.join(f'{k} {v}' for k, v in suite_floors(suite).items() if not k.startswith('_'))}. "
                  f"Regression: score drop over {REGRESSION} against version {prev_version}.", "",
                  "| Run | DPS | Life+ES | Smallest hit | Chaos res | Floors | Score | vs previous |", "|---|---|---|---|---|---|---|---|"]
        floor_ok = reg_ok = 0
        for r in templ:
            if r.get("error"):
                lines.append(f"| {r['label']} | error | | | | no | | |")
                continue
            prof = generate.unique_profile(r["buildAround"]) if r.get("buildAround") else None
            checks = floors(r["metrics"], suite_floors(suite), (prof or {}).get("ignoreResistPenalty", ()))
            failed = [c for c, _, ok in checks if not ok]
            floor_ok += not failed
            p = prev.get(r["key"])
            delta = r["score"] - p["score"] if p and "score" in p else None
            reg = delta is None or delta >= -REGRESSION
            reg_ok += reg
            val = {c: v for c, v, _ in checks}
            lines.append(f"| {r['label']} | {fmt(r['dps'])} | {fmt(val['life+ES'])} | {fmt(val['smallest max hit'])} | "
                         f"{val['chaos res']} | {'ok' if not failed else 'fails: ' + ', '.join(failed)} | {r['score']:.2f} | "
                         f"{'-' if delta is None else f'{delta:+.2f}'}{'' if reg else ' REGRESSION'} |")
        summary += [f"floors {floor_ok}/{len(templ)}", f"no regression {reg_ok}/{len(templ)}"]
    lines[3:3] = ["**Result: " + " · ".join(summary) + "**", ""]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["run", "report"])
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", choices=["authors", "template"])
    ap.add_argument("--holdout", action="store_true", help="the hold-out exam from the private data repo")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    version = generate.GENERATOR_VERSION
    name, suite_path = ("holdout", HOLDOUT) if args.holdout else ("", SUITE)
    path = os.path.join(OUT, f"v{version}" + (f"-{name}" if name else "") + ".json")
    if not os.path.exists(suite_path):
        raise SystemExit(f"no suite at {suite_path}" + (" (python tools/labdata.py pull first)" if args.holdout else ""))
    with open(suite_path, encoding="utf-8") as f:
        suite = json.load(f)
    if args.command == "run":
        jobs = []
        if args.only != "template":
            for e in suite.get("authors", []):
                try:
                    jobs.append(author_job(e))
                except Exception as exc:  # a build PoB cannot load: reported, not fatal
                    print(f"skip {e['label']}: {exc}")
        if args.only != "authors":
            jobs += template_jobs(suite)
        out_dir = tempfile.mkdtemp(prefix="pob-bench-")
        print(f"{len(jobs)} runs, {args.jobs} at a time (builds in {out_dir})", flush=True)
        results = []
        with concurrent.futures.ThreadPoolExecutor(args.jobs) as ex:
            for r in ex.map(lambda j: run_one(j, out_dir), jobs):
                print(f"  {r['label']}: " + (f"score {r['score']:.2f}, DPS {r['dps']:,.0f}" if "score" in r else "error"), flush=True)
                results.append(r)
        old = {}
        if os.path.exists(path):  # a partial run (--only) keeps the other half
            with open(path, encoding="utf-8") as f:
                old = {r["key"]: r for r in json.load(f)["results"]}
        old.update({r["key"]: r for r in results})
        data = {"version": version, "name": name, "suitePath": os.path.relpath(suite_path, ROOT).replace(os.sep, "/"),
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "suite": suite,
                "results": list(old.values())}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    text = report(data)
    with open(path[:-5] + ".md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
