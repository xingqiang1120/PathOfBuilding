"""Gap report: what a generated build lacks against a real build (the author's), and what each missing part is worth.

    python tools/gap.py <author library id> <generated build .xml> [--out report.md]
    python tools/gap.py --benchmark            every author pair of the last benchmark run (library/benchmark/)
    python tools/gap.py --benchmark --holdout  the same for the hold-out exam

1. Differences: the main skill's supports, other skills (auras, curses, buffs), keystones, notables and masteries,
   ascendancy notables, Config values.
2. Transplant: each part the author has and the generated build lacks is added to the generated build alone, and the
   change in DPS and defence is measured (PoB, the generator's own score parts). The biggest gains are what the
   generator should learn to find. Adding a support makes a 7th link when the group is full: an upper bound.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benchmark  # noqa: E402
import generate  # noqa: E402
import library  # noqa: E402

W = generate.WORKER
SKIP_CONFIG = {"bandit", "pantheonMajorGod", "pantheonMinorGod"}  # searched by the generator anyway


def main_group(summary):
    name = (summary.get("primarySkill") or {}).get("name")
    for s in summary["skills"]:
        if s.get("enabled") and s.get("activeSkill") == name:
            return s
    return summary["skills"][0] if summary["skills"] else {"gems": []}


def parts(summary):
    main = main_group(summary)
    supports = {g["name"] for g in main["gems"] if g.get("support") and g.get("enabled")}
    actives = set()
    for s in summary["skills"]:
        if s is main or not s.get("enabled"):
            continue
        actives |= {g["name"] for g in s["gems"] if not g.get("support") and g.get("enabled") and not s.get("source")}
    p = summary["passives"]
    return {"supports": supports, "skills": actives, "keystones": set(p.get("keystones", [])),
            "notables": set(p.get("notables", [])), "masteries": set(p.get("masteries", [])),
            "ascendancy": set(p.get("ascendancy", [])), "config": dict(summary["config"].get("set", {}))}


def transplants(a, g):
    """[(kind, label, change)] - each part of the author's build the generated one lacks."""
    out = [("support", s, {"type": "gem_add", "group": 1, "gem": s}) for s in sorted(a["supports"] - g["supports"])]
    out += [("skill", s, {"type": "group_add", "gems": [s]}) for s in sorted(a["skills"] - g["skills"])]
    out += [("keystone", k, {"type": "passive_add", "node": k}) for k in sorted(a["keystones"] - g["keystones"])]
    out += [("notable", n, {"type": "passive_add", "node": n}) for n in sorted(a["notables"] - g["notables"])]
    for key, value in sorted(a["config"].items()):
        if key not in SKIP_CONFIG and g["config"].get(key) != value:
            out.append(("config", f"{key} = {value} (generated: {g['config'].get(key)})", {"type": "config_set", "key": key, "value": value}))
    return out


def gap(author_key, generated_xml, label=None):
    axml, aname, build_id = library.resolve(author_key)
    with open(generated_xml, encoding="utf-8") as f:
        gxml = f.read()
    A = W.call("summary", {"xml": axml, "name": aname})
    G = W.call("summary", {"xml": gxml, "name": "generated"})
    a, g = parts(A), parts(G)
    minion = bool((A.get("primarySkill") or {}).get("minion"))
    sc = benchmark.scorer(minion, generate.worn_profile(build_id)[1])
    moves = transplants(a, g)
    res = W.call("try", {"xml": gxml, "name": "generated", "infer": True, "inferCharges": True,
                         "candidates": [[]] + [[c] for _, _, c in moves]})
    base = res[0]["metrics"]
    rows = []
    for (kind, what, _), r in zip(moves, res[1:]):
        if "metrics" not in r:
            rows.append((kind, what, None, None, r.get("error", "")[:80]))
            continue
        m = r["metrics"]
        rows.append((kind, what, sc.dps(m) / max(sc.dps(base), 1) - 1, sc.defence(m) - sc.defence(base),
                     f"{m.get('passivePointsUsed')}/{m.get('passivePointsAvailable')} points" if kind in ("keystone", "notable") else ""))
    ok = sorted((r for r in rows if r[2] is not None), key=lambda r: -(r[2] + r[3]))
    label = label or aname
    lines = [f"# Gap: {label}", "", f"Author DPS {sc.dps(A['stats']) if False else (A.get('primarySkill') or {}).get('dps') or 0:,.0f}; "
             f"generated DPS {sc.dps(base):,.0f}, defence {sc.defence(base):.2f}.", "",
             "## Differences", ""]
    for key in ("supports", "skills", "keystones", "ascendancy", "masteries"):
        only_a, only_g = sorted(a[key] - g[key]), sorted(g[key] - a[key])
        if only_a or only_g:
            lines.append(f"- **{key}**: author only: {', '.join(only_a) or '-'}; generated only: {', '.join(only_g) or '-'}")
    lines.append(f"- **notables**: author {len(a['notables'])}, generated {len(g['notables'])}, shared {len(a['notables'] & g['notables'])}")
    lines += ["", "## Each author part added alone to the generated build", "",
              "| Kind | Part | DPS | Defence | Note |", "|---|---|---|---|---|"]
    lines += [f"| {k} | {w} | {d:+.0%} | {f:+.2f} | {n} |" for k, w, d, f, n in ok if abs(d) > 0.005 or abs(f) > 0.005]
    failed = [r for r in rows if r[2] is None]
    if failed:
        lines += ["", "Not applicable: " + "; ".join(f"{k} {w} ({e})" for k, w, _, _, e in failed)]
    return "\n".join(lines) + "\n", ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("author", nargs="?")
    ap.add_argument("generated", nargs="?")
    ap.add_argument("--benchmark", action="store_true")
    ap.add_argument("--holdout", action="store_true", help="with --benchmark: the hold-out exam's results (not for whoever tunes the generator)")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.benchmark:
        name = "holdout" if args.holdout else ""
        files = benchmark.result_files(name)
        if not files:
            raise SystemExit("no benchmark results: run python tools/benchmark.py run" + (" --holdout" if name else ""))
        latest = files[max(files)]
        with open(latest, encoding="utf-8") as f:
            data = json.load(f)
        texts = []
        for r in data["results"]:
            if r.get("gearFrom") and r.get("build") and os.path.exists(r["build"]):
                text, _ = gap(r["gearFrom"], r["build"], r["label"])
                texts.append(text)
                print(text, flush=True)
        out = args.out or latest[:-5] + "-gap.md"
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(texts))
        print(f"written {out}")
        return
    text, _ = gap(args.author, args.generated)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
