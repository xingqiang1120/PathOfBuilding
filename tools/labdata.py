"""Share exam data between the PCs through the private repo xingqiang1120/pob-lab-data.

The build library holds account and character names, so it is not in this (public) repo. The private repo holds:
    inputs/            builds.db, raw/, summary/ - what the benchmark needs (from the office PC)
    results/v<N>/<pc>/ v<N>.md, v<N>.json, v<N>-gap.md - each PC's benchmark and gap report

    python tools/labdata.py pull                    get the data repo (clone the first time); copy inputs/ into library/
    python tools/labdata.py push --pc home          put this PC's latest benchmark results in results/ and push
    python tools/labdata.py push --pc pc2 --version 13
    python tools/labdata.py publish-inputs          office PC only: put library/ inputs into the data repo and push
    python tools/labdata.py status                  which versions each PC has results for

The data repo lives next to this repo (../pob-lab-data) unless POB_LABDATA says otherwise. Each PC must be logged in to
GitHub once (gh auth login) with the account that owns the private repo.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.environ.get("POB_LIBRARY", os.path.join(ROOT, "library"))
DATA = os.environ.get("POB_LABDATA", os.path.join(os.path.dirname(ROOT), "pob-lab-data"))
URL = "https://github.com/xingqiang1120/pob-lab-data.git"
INPUTS = ["builds.db", "raw", "summary"]
PCS = ["office", "pc2", "home"]
TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def git(*args, cwd=DATA, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stdout}{r.stderr}")
    return r.stdout.strip()


def ensure_repo():
    if not os.path.isdir(os.path.join(DATA, ".git")):
        print(f"cloning the data repo into {DATA}")
        git("clone", URL, DATA, cwd=os.path.dirname(DATA))
        # same identity as this repo (the GitHub no-reply address), so personal addresses never reach a commit
        for key in ("user.name", "user.email"):
            value = git("config", key, cwd=ROOT, check=False)
            if value:
                git("config", key, value)
    elif git("remote", "get-url", "origin", check=False):
        git("pull", "--ff-only", check=False)


def copy(src, dst):
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def commit_push(paths, message):
    git("add", *paths)
    if not git("status", "--porcelain", *paths):
        print("nothing new to push")
        return
    git("commit", "-m", message + TRAILER)
    git("push", "-q", "origin", "HEAD")
    print("pushed")


def latest_version():
    out = os.path.join(LIBRARY, "benchmark")
    versions = [int(m.group(1)) for f in os.listdir(out) if (m := re.fullmatch(r"v(\d+)\.json", f))] if os.path.isdir(out) else []
    if not versions:
        raise SystemExit(f"no benchmark results in {out}: run python tools/benchmark.py run first")
    return max(versions)


def pull(_):
    ensure_repo()
    src = os.path.join(DATA, "inputs")
    if not os.path.isdir(src):
        raise SystemExit("the data repo has no inputs/ yet: the office PC runs publish-inputs first")
    os.makedirs(LIBRARY, exist_ok=True)
    for name in INPUTS:
        copy(os.path.join(src, name), os.path.join(LIBRARY, name))
    print(f"inputs copied into {LIBRARY}")
    # earlier versions' results, so the benchmark's regression check has a previous version on every PC (home had none
    # and showed "version None", 2026-11-27). This PC's own results are never overwritten.
    base, out = os.path.join(DATA, "results"), os.path.join(LIBRARY, "benchmark")
    added = []
    for v in (os.listdir(base) if os.path.isdir(base) else []):
        for pc in sorted(os.listdir(os.path.join(base, v)), key=lambda p: PCS.index(p) if p in PCS else 99):
            src = os.path.join(base, v, pc, f"{v}.json")
            if os.path.exists(src) and not os.path.exists(os.path.join(out, f"{v}.json")):
                for name in (f"{v}.json", f"{v}.md"):
                    copy(os.path.join(base, v, pc, name), os.path.join(out, name))
                added.append(f"{v} ({pc})")
    if added:
        print("earlier results copied into library/benchmark: " + ", ".join(added))


def push(args):
    ensure_repo()
    version = args.version or latest_version()
    out = os.path.join(LIBRARY, "benchmark")
    dst = os.path.join(DATA, "results", f"v{version}", args.pc)
    names = [f"v{version}.md", f"v{version}.json", f"v{version}-gap.md"]
    found = [n for n in names if os.path.exists(os.path.join(out, n))]
    if not found:
        raise SystemExit(f"no results for version {version} in {out}")
    for n in found:
        copy(os.path.join(out, n), os.path.join(dst, n))
    missing = sorted(set(names) - set(found))
    print(f"version {version} from {args.pc}: {', '.join(found)}" + (f" (missing: {', '.join(missing)})" if missing else ""))
    commit_push([os.path.relpath(dst, DATA)], f"Results v{version} from {args.pc}")


def publish_inputs(_):
    ensure_repo()
    dst = os.path.join(DATA, "inputs")
    for name in INPUTS:
        copy(os.path.join(LIBRARY, name), os.path.join(dst, name))
    commit_push(["inputs"], "Build library inputs")


def status(_):
    ensure_repo()
    base = os.path.join(DATA, "results")
    if not os.path.isdir(base):
        print("no results yet")
        return
    for v in sorted(os.listdir(base), key=lambda s: int(s[1:]) if s[1:].isdigit() else 0):
        pcs = sorted(os.listdir(os.path.join(base, v)))
        print(f"{v}: " + ", ".join(f"{pc} ({len(os.listdir(os.path.join(base, v, pc)))} files)" for pc in pcs))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("pull").set_defaults(fn=pull)
    p = sub.add_parser("push")
    p.add_argument("--pc", required=True, choices=PCS)
    p.add_argument("--version", type=int)
    p.set_defaults(fn=push)
    sub.add_parser("publish-inputs").set_defaults(fn=publish_inputs)
    sub.add_parser("status").set_defaults(fn=status)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
