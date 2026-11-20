"""Goal-driven build optimizer: start from a build, search changes until target numbers are met.

    python tools/optimize.py goal.json

goal.json:
    {
      "base": "MeiMax",                       library build (id prefix / name) or a .xml path
      "group": 11, "minionSkill": "Physical Projectile",   optional; default: saved settings
      "summonRate": 8,                                       optional: minions summoned per second (Fresh Meat uptime)
      "lock": ["Weapon 1"],                   slots whose item must stay (e.g. a required unique)
      "targets": {                            metric: minimum value
        "minionDPS": 50000, "Life": 3000, "PhysicalMaximumHitTaken": 10000,
        "FireMaximumHitTaken": 20000, "ColdMaximumHitTaken": 20000,
        "LightningMaximumHitTaken": 20000, "ChaosMaximumHitTaken": 20000
      },
      "name": "Soulwrest 50k test",           output file name
      "rounds": 12                            optional search rounds
    }

Moves the search tries (each judged by Path of Building, with condition inference):
  - replace a support gem linked to the main skill
  - add a skill group (auras, banners, guards, minion buffs); reservation must still fit
  - allocate a reachable notable / keystone with free points, or swap one for another
  - replace an unlocked item with a unique from the database (level requirement respected)
Always required: unreserved mana and life >= 0, passive points used <= available, and the number of
minions the build can have does not drop (per-minion targets could otherwise hide a halved army).

Output: src/Builds/generated/<name>.xml (open it in PoB) and library/reports/optimize-<name>.md.
The search is greedy: it finds a good build, not a proven best one. Sockets, gem colours and how easy an
item is to obtain are not checked; new skill groups need free sockets in game.
"""
import datetime
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library  # noqa: E402
import simlog  # noqa: E402
from pob_worker import WORKER  # noqa: E402

ROOT = library.ROOT
OUT_DIR = os.path.join(ROOT, "src", "Builds", "generated")
ALWAYS = {"ManaUnreserved": 0, "LifeUnreserved": 1}


def log(*args):
    print(*args, flush=True)


class Optimizer:
    def __init__(self, goal):
        self.goal = goal
        xml, name, build_id = library.resolve(goal["base"])
        settings = library.get_settings(build_id)
        self.params = library.apply_settings({"xml": xml, "name": name}, settings,
                                             {"group": goal.get("group"), "minionSkill": goal.get("minionSkill"),
                                              "summonRate": goal.get("summonRate"), "mercenary": goal.get("mercenary")})
        self.base_changes = self.params.pop("changes")
        self.base_name = name
        self.targets = goal["targets"]
        self.locked = set(goal.get("lock") or [])
        self.state = []          # accepted changes
        self.history = []
        self.evaluations = 0
        self.recorder = simlog.Recorder("optimize", skill=name, gear=f"from {goal['base']}", focus="targets",
                                        skill_info={"targets": self.targets}, versions=WORKER.call("ping", {}))

    # --- evaluation -------------------------------------------------------
    def evaluate(self, candidates):
        out = []
        for i in range(0, len(candidates), 25):
            chunk = candidates[i:i + 25]
            res = WORKER.call("evaluate", dict(self.params, changes=self.base_changes + self.state, candidates=chunk))
            self.evaluations += len(chunk)
            out.extend(res)
        before = getattr(self, "current", None)
        if before:
            self.recorder.record("optimize", self.base_changes + self.state, before, candidates, out, self.dps, score=lambda m: -self.penalty(m))
        return out

    def dps(self, m):
        return max(m.get("playerDPS") or 0, m.get("minionDPS") or 0)

    def value(self, m, key):
        return self.dps(m) if key in ("minionDPS", "playerDPS", "DPS") else (m.get(key) or 0)

    def penalty(self, m):
        """0 when every target is met; otherwise the summed relative shortfall (hard limits weigh 10x)."""
        p = 0.0
        for key, target in self.targets.items():
            v = self.value(m, key)
            if v < target:
                p += (target - v) / max(abs(target), 1)
        for key, minimum in ALWAYS.items():
            if (m.get(key) if m.get(key) is not None else minimum) < minimum:
                p += 10
        if (m.get("passivePointsUsed") or 0) > (m.get("passivePointsAvailable") or 999):
            p += 10
        # Never trade away minions: per-minion numbers can rise while the number of minions falls
        start_limit = (getattr(self, "start", None) or {}).get("minionLimit")
        if start_limit and (m.get("minionLimit") or 0) < start_limit:
            p += 10
        return p

    def margin(self, m):
        """Tie-breaker once targets are met: smallest relative surplus over all targets."""
        return min((self.value(m, k) / t - 1) for k, t in self.targets.items() if t)

    def better(self, a, b):
        pa, pb = self.penalty(a), self.penalty(b)
        if abs(pa - pb) > 1e-9:
            return pa < pb
        return self.margin(a) > self.margin(b) + 1e-6

    # --- candidate moves --------------------------------------------------
    def prepare(self):
        log("collecting candidates ...")
        c = WORKER.call("candidates", dict(self.params, changes=self.base_changes, lockedSlots={s: True for s in self.locked}))
        self.points = c["points"]
        base = self.evaluate([[]])[0]["metrics"]
        self.current = base
        self.start = base
        # Supports linked to the main skill: the main group plus groups socketed in the same item
        summary = WORKER.call("summary", {"xml": self.params["xml"], "name": self.base_name})
        main_group = self.params.get("group") or (summary.get("primarySkill") or {}).get("group")
        groups = summary["skills"]
        main_slot = next((g.get("slot") for g in groups if g["index"] == main_group), None)
        self.linked = [(g["index"], gem["name"]) for g in groups if g.get("slot") == main_slot
                       for gem in g["gems"] if gem.get("support") and gem.get("enabled")]
        # Rank supports by their value when added on top (one evaluation each)
        log(f"screening {len(c['supports'])} supports ...")
        main_link_group = self.linked[0][0] if self.linked else main_group
        res = self.evaluate([[{"type": "gem_add", "group": main_link_group, "gem": s}] for s in c["supports"]])
        scored = [(self.dps(r["metrics"]), s) for r, s in zip(res, c["supports"]) if "metrics" in r]
        current_names = {name.lower() for _, name in self.linked}
        self.top_supports = [s for d, s in sorted(scored, reverse=True) if s.lower() not in current_names][:10]
        log("  best supports: " + ", ".join(self.top_supports))
        self.skills = [s["name"] for s in c["skills"]]
        # Rank passives by score gain per point
        log(f"screening {len(c['passives'])} passives ...")
        res = self.evaluate([[{"type": "passive_add", "node": p["id"]}] for p in c["passives"]])
        gains = []
        for r, p in zip(res, c["passives"]):
            if "metrics" in r:
                gains.append((self.gain(base, r["metrics"]) / max(p["cost"], 1), p))
        self.top_passives = [p for g, p in sorted(gains, key=lambda x: -x[0]) if g > 0][:15]
        log("  best passives: " + ", ".join(f"{p['name']} ({p['cost']})" for p in self.top_passives[:8]))
        self.removable = c["removable"]
        # Rank uniques per slot
        self.top_uniques = {}
        for slot, names in c["uniques"].items():
            if not names or slot in self.locked:
                continue
            log(f"screening {len(names)} uniques for {slot} ...")
            res = self.evaluate([[{"type": "item_equip", "slot": slot, "unique": n}] for n in names])
            ranked = sorted(((self.gain(base, r["metrics"]), n) for r, n in zip(res, names) if "metrics" in r), reverse=True)
            self.top_uniques[slot] = [n for g, n in ranked if g > 0][:4]
            if self.top_uniques[slot]:
                log(f"  {slot}: " + ", ".join(self.top_uniques[slot]))

    def gain(self, before, after):
        """Positive when `after` is closer to the goal (less penalty), with DPS/defence surplus as a small bonus."""
        return (self.penalty(before) - self.penalty(after)) + 0.01 * (self.margin(after) - self.margin(before))

    def moves(self):
        moves = []
        for group, gem in self.linked:
            for s in self.top_supports:
                moves.append([{"type": "gem_replace", "group": group, "gem": gem, "with": s}])
        for name in self.skills:
            moves.append([{"type": "group_add", "gems": [name]}])
        free = self.points[1] - self.current.get("passivePointsUsed", self.points[0])
        for p in self.top_passives:
            if p["cost"] <= free:
                moves.append([{"type": "passive_add", "node": p["id"], "name": p["name"]}])
        weakest = sorted(self.removable, key=lambda r: r["frees"])[:6]
        for r in weakest:
            for p in self.top_passives[:6]:
                if p["cost"] <= free + r["frees"]:
                    moves.append([{"type": "passive_remove", "node": r["id"], "name": r["name"]},
                                  {"type": "passive_add", "node": p["id"], "name": p["name"]}])
        for slot, names in self.top_uniques.items():
            for n in names:
                moves.append([{"type": "item_equip", "slot": slot, "unique": n}])
        return moves

    def apply_move(self, move):
        """Keep state consistent: drop earlier changes the move supersedes."""
        for change in move:
            if change["type"] == "item_equip":
                self.state = [c for c in self.state if not (c["type"] == "item_equip" and c["slot"] == change["slot"])]
        self.state.extend(move)
        for change in move:
            if change["type"] == "gem_replace":
                self.linked = [(g, change["with"] if (g == change["group"] and n == change["gem"]) else n) for g, n in self.linked]
                if change["with"] in self.top_supports:
                    self.top_supports.remove(change["with"])
            if change["type"] == "group_add":
                self.skills = [s for s in self.skills if s not in change["gems"]]
            if change["type"] == "passive_add":
                self.top_passives = [p for p in self.top_passives if p["id"] != change["node"]]

    def run(self):
        started = time.time()
        self.prepare()
        for round_no in range(1, self.goal.get("rounds", 12) + 1):
            if self.penalty(self.current) == 0 and round_no > self.goal.get("polishRounds", 3) + 1:
                break
            moves = self.moves()
            log(f"round {round_no}: {len(moves)} moves, penalty {self.penalty(self.current):.3f}, DPS {self.dps(self.current):,.0f}")
            res = self.evaluate(moves)
            best, best_m = None, self.current
            for move, r in zip(moves, res):
                if "metrics" in r and self.better(r["metrics"], best_m):
                    best, best_m = move, r["metrics"]
            if best is None:
                log("  no move improves the build any more")
                break
            self.apply_move(best)
            self.history.append({"round": round_no, "move": best, "metrics": best_m})
            self.current = best_m
            log("  accepted: " + "; ".join(describe(c) for c in best) + f"  -> penalty {self.penalty(best_m):.3f}, DPS {self.dps(best_m):,.0f}")
        self.elapsed = time.time() - started
        self.recorder.finish(self.current)
        return self.current

    def export(self):
        os.makedirs(OUT_DIR, exist_ok=True)
        name = re.sub(r"[^\w\- ]+", "_", self.goal.get("name") or "optimized").strip()
        notes = self.notes()
        res = WORKER.call("export", dict(self.params, changes=self.base_changes + self.state, notes=notes))
        path = os.path.join(OUT_DIR, name + ".xml")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(res["xml"])
        report = os.path.join(library.LIBRARY, "reports", f"optimize-{name.replace(' ', '_')}.md")
        os.makedirs(os.path.dirname(report), exist_ok=True)
        with open(report, "w", encoding="utf-8") as f:
            f.write(self.report(res["metrics"]))
        return path, report, res["metrics"]

    def table(self, final):
        rows = []
        for key, target in self.targets.items():
            start, end = self.value(self.start, key), self.value(final, key)
            rows.append((key, target, start, end, "OK" if end >= target else "NOT MET"))
        return rows

    def notes(self):
        lines = [f"Generated by tools/optimize.py on {datetime.datetime.now():%Y-%m-%d %H:%M} from {self.base_name}.", "",
                 "Targets (start -> result):"]
        for key, target, start, end, ok in self.table(self.current):
            lines.append(f"  {key}: {start:,.0f} -> {end:,.0f} (target {target:,}) {ok}")
        lines += ["", "Changes:"]
        lines += [f"  {i}. {describe(c)}" for i, c in enumerate(self.state, 1)]
        inferred = self.current.get("inferred") or []
        if inferred:
            lines += ["", "Inferred conditions (saved in Config):"]
            lines += [f"  {i['label']} = {i['value']} ({'; '.join(i.get('assumptions') or [])})" for i in inferred if i.get("applied")]
        lines += ["", "Not checked: sockets and gem colours, item availability. New skill groups need free sockets."]
        return "\n".join(lines)

    def report(self, final):
        lines = [f"# 目標配裝：{self.goal.get('name')}", "", f"起點：{self.base_name} · 評估 {self.evaluations} 次 · 耗時 {self.elapsed / 60:.1f} 分鐘", "",
                 "| 目標 | 要求 | 起點 | 結果 | |", "|---|---|---|---|---|"]
        for key, target, start, end, ok in self.table(final):
            lines.append(f"| {key} | ≥ {target:,} | {start:,.0f} | {end:,.0f} | {'✅' if ok == 'OK' else '❌'} |")
        lines.append(f"| 未保留魔力 / 生命 | ≥ 0 | {self.start.get('ManaUnreserved')} / {self.start.get('LifeUnreserved')} | {final.get('ManaUnreserved')} / {final.get('LifeUnreserved')} | |")
        lines.append(f"| 天賦點 | ≤ {final.get('passivePointsAvailable')} | {self.start.get('passivePointsUsed')} | {final.get('passivePointsUsed')} | |")
        if self.start.get("minionLimit"):
            lines.append(f"| 召喚物上限 | 不可減少 | {self.start.get('minionLimit')} | {final.get('minionLimit')} | |")
        lines += ["", "## 變更（依採用順序）", ""]
        for h in self.history:
            lines.append(f"{h['round']}. " + "；".join(describe(c) for c in h["move"]) +
                         f" → DPS {self.dps(h['metrics']):,.0f}，物理承受 {h['metrics'].get('PhysicalMaximumHitTaken'):,.0f}，生命 {h['metrics'].get('Life'):,.0f}")
        inferred = [i for i in final.get("inferred") or [] if i.get("applied")]
        if inferred:
            lines += ["", "## 推算的條件", ""]
            lines += [f"- {i['label']} = {i['value']}（估計 {i['estimate']}；{'；'.join(i.get('assumptions') or [])}）" for i in inferred]
        lines += ["", "## 沒有檢查的部分", "", "- 插槽數量與寶石顏色：新增的技能組需要空插槽",
                  "- 裝備取得難度與價格", "- 搜尋是逐步貪婪法：找到的是「好的」配置，不保證是最佳解"]
        return "\n".join(lines) + "\n"


def describe(c):
    t = c["type"]
    if t == "gem_replace":
        return f"寶石 {c['gem']} → {c['with']}（第 {c['group']} 組）"
    if t == "gem_add":
        return f"加寶石 {c['gem']}（第 {c['group']} 組）"
    if t == "group_add":
        return f"新增技能組 {', '.join(c['gems'])}"
    if t == "passive_add":
        return f"點天賦 {c.get('name') or c['node']}"
    if t == "passive_remove":
        return f"移除天賦 {c.get('name') or c['node']}"
    if t == "item_equip":
        return f"{c['slot']} 換成 {c.get('unique') or '自訂物品'}"
    return json.dumps(c, ensure_ascii=False)


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        goal = json.load(f)
    opt = Optimizer(goal)
    opt.run()
    path, report, final = opt.export()
    log(f"\nbuild: {path}\nreport: {report}")
    for key, target, start, end, ok in opt.table(final):
        log(f"  {key:<26} {start:>10,.0f} -> {end:>10,.0f}  (target {target:,})  {ok}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
