"""Build generator: from a skill and an ascendancy to a playable build, judged by Path of Building.

    python tools/generate.py "Kinetic Blast of Clustering" Necromancer [--focus balanced] [--level 95] [--name ...]

Steps (each step tries candidates in PoB and keeps the best by the score below):
  1. character: class and ascendancy, level, the skill in a 6-link body armour, template rare gear
  2. weapon: one template per weapon type the skill can use (attack), or a spell / minion weapon
  3. supports: five, picked one at a time from every support PoB says can support the skill
  4. ascendancy: up to 8 points of ascendancy notables
  5. passive tree: grow from the class start, best score gain per point, until the points run out
  6. auras and buffs: added while reservation allows
  7. supports again, now that the tree and auras are known
Score = ln(DPS) + w x defence - penalties, defence = (ln(EHP) + ln(smallest max hit)) / 2, w by --focus
(damage 0.5, balanced 1, defence 2). Penalties: fire/cold/lightning resistance under 75%, missing attribute
points, reserved more than available, more passive points than the character has.

Template gear is an assumption, stated in the report: good but ordinary rares (life, two resistances, an
attribute; weapons with typical damage rolls). No uniques, jewels, flasks or cluster jewels yet.
Output: src/Builds/generated/<name>.xml (open in PoB) and library/reports/generate-<name>.md.
"""
import argparse
import datetime
import math
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library  # noqa: E402
import simlog  # noqa: E402
from pob_worker import WORKER  # noqa: E402

OUT_DIR = os.path.join(library.ROOT, "src", "Builds", "generated")
FOCUS = {"damage": 0.5, "balanced": 1.0, "defence": 2.0}


def item(name, base, *lines, implicits=()):
    text = ["Rarity: RARE", name, base, "Item Level: 86", f"Implicits: {len(implicits)}", *implicits, *lines]
    return "\n".join(text)


# --- template gear -----------------------------------------------------------------------------------------------
ARMOUR_BASES = {
    "Str": {"Helmet": "Eternal Burgonet", "Body Armour": "Glorious Plate", "Gloves": "Titan Gauntlets", "Boots": "Titan Greaves",
            "Shield": "Pinnacle Tower Shield"},
    "Dex": {"Helmet": "Lion Pelt", "Body Armour": "Assassin's Garb", "Gloves": "Slink Gloves", "Boots": "Slink Boots",
            "Shield": "Imperial Buckler"},
    "Int": {"Helmet": "Hubris Circlet", "Body Armour": "Vaal Regalia", "Gloves": "Sorcerer Gloves", "Boots": "Sorcerer Boots",
            "Shield": "Titanium Spirit Shield"},
}
CLASS_ATTRIBUTE = {"Marauder": "Str", "Ranger": "Dex", "Witch": "Int", "Duelist": "Str", "Templar": "Str", "Shadow": "Dex",
                   "Scion": "Str"}


def armour_set(attribute):
    b = ARMOUR_BASES[attribute]
    return {
        "Helmet": item("Template Helmet", b["Helmet"], "+90 to maximum Life", "+40% to Fire Resistance", "+40% to Cold Resistance"),
        "Body Armour": item("Template Body Armour", b["Body Armour"], "+110 to maximum Life", "+40% to Fire Resistance", "+40% to Cold Resistance"),
        "Gloves": item("Template Gloves", b["Gloves"], "+80 to maximum Life", "+40% to Cold Resistance", "+40% to Lightning Resistance"),
        "Boots": item("Template Boots", b["Boots"], "+80 to maximum Life", "+40% to Fire Resistance", "+40% to Lightning Resistance",
                      "30% increased Movement Speed"),
        "Amulet": item("Template Amulet", "Onyx Amulet", "+70 to maximum Life", "+40% to Lightning Resistance", "+40 to Strength",
                       implicits=("+16 to all Attributes",)),
        "Ring 1": item("Template Ring", "Two-Stone Ring", "+60 to maximum Life", "+40% to Lightning Resistance", "+40 to Dexterity",
                       implicits=("+16% to Fire and Cold Resistances",)),
        "Ring 2": item("Template Ring", "Two-Stone Ring", "+60 to maximum Life", "+40% to Lightning Resistance", "+40 to Intelligence",
                       implicits=("+16% to Fire and Cold Resistances",)),
        "Belt": item("Template Belt", "Leather Belt", "+80 to maximum Life", "+40% to Cold Resistance", "+40% to Lightning Resistance",
                     implicits=("+40 to maximum Life",)),
    }, item("Template Shield", b["Shield"], "+90 to maximum Life", "+40% to Fire Resistance", "+40% to Cold Resistance")


ONE_HAND = ["Adds 25 to 50 Physical Damage", "170% increased Physical Damage", "20% increased Attack Speed",
            "30% increased Critical Strike Chance", "+30% to Global Critical Strike Multiplier", "+400 to Accuracy Rating"]
TWO_HAND = ["Adds 45 to 95 Physical Damage", "170% increased Physical Damage", "15% increased Attack Speed",
            "30% increased Critical Strike Chance", "+35% to Global Critical Strike Multiplier", "+400 to Accuracy Rating"]
WEAPONS = {  # PoB weapon type -> (base, two-handed)
    "Wand": ("Prophecy Wand", False), "Claw": ("Imperial Claw", False), "Dagger": ("Ambusher", False),
    "One Handed Sword": ("Corsair Sword", False), "Thrusting One Handed Sword": ("Jewelled Foil", False),
    "One Handed Axe": ("Runic Hatchet", False), "One Handed Mace": ("Behemoth Mace", False), "Sceptre": ("Void Sceptre", False),
    "Bow": ("Thicket Bow", True), "Staff": ("Eclipse Staff", True), "Two Handed Sword": ("Reaver Sword", True),
    "Two Handed Axe": ("Vaal Axe", True), "Two Handed Mace": ("Coronal Maul", True),
}
SPELL_WEAPON = item("Template Sceptre", "Void Sceptre", "90% increased Spell Damage", "20% increased Cast Speed",
                    "80% increased Critical Strike Chance for Spells", "+30% to Global Critical Strike Multiplier", "+40 to Intelligence")
SPELL_SHIELD = item("Template Shield", "Titanium Spirit Shield", "+80 to maximum Life", "60% increased Spell Damage",
                    "+40% to Fire Resistance", "+40% to Cold Resistance")
MINION_WEAPON = item("Template Wand", "Convoking Wand", "+1 to Level of all Minion Skill Gems", "Minions deal 60% increased Damage",
                     "Minions have 25% increased Attack Speed", "Minions have 25% increased Cast Speed")


def weapon_options(info, attribute):
    """[(label, [changes])] - weapon (and shield) setups the skill can use."""
    armour, shield = armour_set(attribute)
    shield_change = {"type": "item_equip", "slot": "Weapon 2", "raw": shield}
    options = []
    if info["minion"]:
        options.append(("minion wand + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": MINION_WEAPON}, shield_change]))
    if info["spell"] and not info["attack"]:
        options.append(("spell sceptre + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": SPELL_WEAPON},
                                                    {"type": "item_equip", "slot": "Weapon 2", "raw": SPELL_SHIELD}]))
    if info["attack"]:
        types = info["weaponTypes"] or list(WEAPONS)
        for t in types:
            if t not in WEAPONS:
                continue
            base, two_handed = WEAPONS[t]
            weapon = {"type": "item_equip", "slot": "Weapon 1", "raw": item(f"Template {t}", base, *(TWO_HAND if two_handed else ONE_HAND))}
            options.append((t, [weapon] if two_handed else [weapon, shield_change]))
    if not options:
        options.append(("spell sceptre + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": SPELL_WEAPON},
                                                    {"type": "item_equip", "slot": "Weapon 2", "raw": SPELL_SHIELD}]))
    return options


BUFF_SKILLS = ["Hatred", "Anger", "Wrath", "Zealotry", "Malevolence", "Pride", "Haste", "Grace", "Determination", "Discipline",
               "Precision", "Purity of Elements", "Herald of Ash", "Herald of Ice", "Herald of Thunder", "Herald of Agony",
               "Herald of Purity", "War Banner", "Dread Banner", "Defiance Banner", "Arctic Armour", "Tempest Shield",
               "Flesh and Stone", "Vitality"]


# Supports that change how the skill is used (trap, mine, totem, trigger, another minion): not the build asked for
DELIVERY = re.compile(r"Trap|Mine|Totem|Ballista|Cast On|Cast on|Cast when|Cast while|Spellslinger|Summon Phantasm|Trigger|"
                      r"Automation|Autoexertion|Mark On Hit|Arcanist|Blessing|Call to Arms|Manaforged|Kinetic Instability", re.I)


def log(*args):
    print(*args, flush=True)


class Generator:
    def __init__(self, skill, ascendancy, focus="balanced", level=95, name=None, infer=True, gear_from=None):
        self.skill, self.ascendancy, self.level = skill, ascendancy, level
        self.gear_from = gear_from
        self.weight = FOCUS[focus]
        self.focus = focus
        self.name = name or f"{skill} {ascendancy}"
        self.infer = infer
        self.state = []
        self.history = []
        self.tries = 0
        self.step = "start"
        self.recorder = None

    # --- PoB calls ---------------------------------------------------------------------------------------------------
    def params(self):
        return {"xml": self.xml, "name": self.name, "infer": self.infer}

    def try_all(self, candidates, costs=None):
        out = []
        for i in range(0, len(candidates), 40):
            chunk = candidates[i:i + 40]
            out.extend(WORKER.call("try", dict(self.params(), changes=self.state, candidates=chunk)))
            self.tries += len(chunk)
        # every try is kept as data (tools/simlog.py), with the state it was tried in
        if self.recorder and getattr(self, "current", None):
            self.recorder.record(self.step, self.state, self.current, candidates, out, self.dps, score=self.score, costs=costs)
        return out

    # --- score -------------------------------------------------------------------------------------------------------
    def dps(self, m):
        # the skill's own damage: a minion skill's minions, otherwise the player (supports adding minions do not count)
        if getattr(self, "info", None) and self.info.get("minion"):
            return m.get("minionDPS") or 0
        return m.get("playerDPS") or 0

    def penalty(self, m):
        p = 0.0
        for res in ("FireResist", "ColdResist", "LightningResist"):
            p += max(0, 75 - (m.get(res) or 0)) * 0.05
        p += (m.get("attributeShortfall") or 0) * 0.02
        if (m.get("ManaUnreserved") if m.get("ManaUnreserved") is not None else 0) < 0:
            p += 5
        if (m.get("LifeUnreserved") if m.get("LifeUnreserved") is not None else 1) < 1:
            p += 5
        if (m.get("passivePointsUsed") or 0) > (m.get("passivePointsAvailable") or 999):
            p += 10
        return p

    def score(self, m):
        hits = [m.get(k) for k in ("PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken",
                                   "ChaosMaximumHitTaken")]
        hits = [h for h in hits if h]  # None = immune (e.g. chaos with Chaos Inoculation)
        defence = (math.log(max(m.get("TotalEHP") or 1, 1)) + math.log(max(min(hits) if hits else 1, 1))) / 2
        return math.log(max(self.dps(m), 1)) + self.weight * defence - self.penalty(m)

    def best(self, moves, current, per_point=None):
        """Try every move; return (move, metrics, gain) of the best one that improves the score, or None."""
        if not moves:
            return None
        res = self.try_all(moves, costs=per_point)
        base = self.score(current)
        best = None
        for i, (move, r) in enumerate(zip(moves, res)):
            if "metrics" not in r:
                continue
            gain = self.score(r["metrics"]) - base
            if per_point:
                gain /= max(per_point[i], 1)
            if gain > 1e-6 and (best is None or gain > best[2]):
                best = (move, r["metrics"], gain)
        return best, res

    def accept(self, step, move, metrics, note=""):
        self.state.extend(move)
        self.current = metrics
        self.history.append({"step": step, "move": move, "note": note, "dps": self.dps(metrics), "score": self.score(metrics)})
        log(f"  [{step}] {note or describe(move)} -> DPS {self.dps(metrics):,.0f}, life {metrics.get('Life')}, "
            f"phys max hit {metrics.get('PhysicalMaximumHitTaken')}, score {self.score(metrics):.3f}")

    # --- steps -------------------------------------------------------------------------------------------------------
    def create(self):
        if self.gear_from:
            # the reference build's own items, empty tree, only the main skill
            xml, name, _ = library.resolve(self.gear_from)
            r = WORKER.call("strip_build", {"xml": xml, "name": name, "skill": self.skill})
            self.info, self.class_name, self.ascendancy = r["skillInfo"], r["class"], r["ascendancy"]
            self.attribute = CLASS_ATTRIBUTE.get(self.class_name, "Str")
            self.xml, self.state, self.weapon = r["xml"], [], f"from {name}"
            self.current = self.try_all([[]])[0]["metrics"]
            self.jewels_dropped = r.get("jewelsDropped", 0)
            log(f"{r['class']} / {r['ascendancy']}, {r['skill']} with the gear of {name} (level {self.current.get('passivePointsAvailable')} points; "
                f"{self.jewels_dropped} tree jewels not used)")
            return
        r = WORKER.call("create_build", {"ascendancy": self.ascendancy, "skill": self.skill, "level": self.level})
        self.info, self.class_name = r["skillInfo"], r["class"]
        self.attribute = CLASS_ATTRIBUTE.get(self.class_name, "Str")
        armour, _ = armour_set(self.attribute)
        self.xml = r["xml"]
        self.state = [{"type": "item_equip", "slot": slot, "raw": raw} for slot, raw in armour.items()]
        self.current = self.try_all([[]])[0]["metrics"]
        log(f"{r['class']} / {r['ascendancy']}, {r['skill']} ({', '.join(k for k in ('attack', 'spell', 'minion') if self.info[k])})")

    def pick_weapon(self):
        self.step = "weapon"
        options = weapon_options(self.info, self.attribute)
        res = self.try_all([changes for _, changes in options])
        ranked = sorted(((self.score(r["metrics"]), label, changes, r["metrics"]) for (label, changes), r in zip(options, res)
                         if "metrics" in r), key=lambda x: -x[0])
        if not ranked:
            raise SystemExit("no weapon setup could be evaluated: " + "; ".join(r.get("error", "") for r in res))
        _, label, changes, metrics = ranked[0]
        self.weapon = label
        self.accept("weapon", changes, metrics, f"weapon: {label}")

    def pick_supports(self, count=5):
        self.step = "support"
        cands = WORKER.call("candidates", dict(self.params(), changes=self.state))
        self.support_pool = [s for s in cands["supports"] if not DELIVERY.search(s)]
        self.points = cands["points"]
        self.links = []
        for _ in range(count):
            pool = [s for s in self.support_pool if s not in self.links]
            found = self.best([[{"type": "gem_add", "group": 1, "gem": s}] for s in pool], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            self.links.append(move[0]["gem"])
            self.accept("support", move, metrics, f"support: {move[0]['gem']}")

    def pick_ascendancy(self):
        self.step = "ascendancy"
        while True:
            a = WORKER.call("ascendancy_candidates", dict(self.params(), changes=self.state))
            free = a["available"] - a["used"]
            cands = [c for c in a["candidates"] if c["cost"] <= free]
            if not cands:
                return
            moves = [[{"type": "passive_add", "node": c["id"]}] for c in cands]
            found = self.best(moves, self.current, per_point=[c["cost"] for c in cands])
            if not found or not found[0]:
                # nothing measurable: take the cheapest so the points are not wasted, reported as unmeasured
                return
            move, metrics, _ = found[0]
            node = next(c for c in cands if c["id"] == move[0]["node"])
            self.accept("ascendancy", move, metrics, f"ascendancy: {node['name']}")

    def grow_tree(self, max_path=10, shortlist=30):
        self.step = "tree"
        known = {}  # node id -> (gain per point, name, cost) from the last time it was tried
        while True:
            cands = WORKER.call("candidates", dict(self.params(), changes=self.state, maxPath=max_path))
            used, available = self.current.get("passivePointsUsed", 0), cands["points"][1]
            free = available - used
            passives = [p for p in cands["passives"] if p["cost"] <= free]
            if not passives:
                break
            # Re-try the best-known candidates and every candidate never tried
            ranked = sorted(passives, key=lambda p: -(known.get(p["id"], (math.inf,))[0]))
            batch = [p for p in ranked if p["id"] not in known][:80] + [p for p in ranked if p["id"] in known][:shortlist]
            moves = [[{"type": "passive_add", "node": p["id"]}] for p in batch]
            found, res = self.best(moves, self.current, per_point=[p["cost"] for p in batch])
            base = self.score(self.current)
            for p, r in zip(batch, res):
                if "metrics" in r:
                    known[p["id"]] = ((self.score(r["metrics"]) - base) / max(p["cost"], 1), p["name"], p["cost"])
            if not found:
                break
            move, metrics, _ = found
            node = next(p for p in batch if p["id"] == move[0]["node"])
            known.pop(node["id"], None)
            self.accept("tree", move, metrics, f"passive: {node['name']} ({node['cost']} points, {metrics.get('passivePointsUsed')}/{available})")

    def add_buffs(self):
        self.step = "buff"
        present = {c.get("gems", [None])[0] for c in self.state if c["type"] == "group_add"}
        pool = [s for s in BUFF_SKILLS if s not in present]
        while pool:
            found = self.best([[{"type": "group_add", "gems": [s]}] for s in pool], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            pool.remove(move[0]["gems"][0])
            self.accept("buff", move, metrics, f"aura/buff: {move[0]['gems'][0]}")

    def retune_supports(self):
        self.step = "support swap"
        for gem in list(self.links):
            pool = [s for s in self.support_pool if s not in self.links]
            moves = [[{"type": "gem_replace", "group": 1, "gem": gem, "with": s}] for s in pool]
            found = self.best(moves, self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                new = move[0]["with"]
                self.links[self.links.index(gem)] = new
                self.accept("support swap", move, metrics, f"support: {gem} -> {new}")

    def run(self):
        started = time.time()
        self.create()
        self.recorder = simlog.Recorder("generate", skill=self.skill, ascendancy=self.ascendancy, cls=self.class_name, focus=self.focus,
                                        gear=f"from {self.gear_from}" if self.gear_from else "template", skill_info=self.info,
                                        versions=WORKER.call("ping", {}))
        if not self.gear_from:
            self.pick_weapon()
        self.pick_supports()
        self.pick_ascendancy()
        self.grow_tree()
        self.add_buffs()
        self.retune_supports()
        self.elapsed = time.time() - started
        self.recorder.finish(self.current)
        return self.current

    # --- output ------------------------------------------------------------------------------------------------------
    def export(self):
        os.makedirs(OUT_DIR, exist_ok=True)
        safe = re.sub(r"[^\w\- ]+", "_", self.name).strip()
        notes = self.notes()
        res = WORKER.call("export", dict(self.params(), changes=self.state, notes=notes))
        path = os.path.join(OUT_DIR, safe + ".xml")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(res["xml"])
        report = os.path.join(library.LIBRARY, "reports", f"generate-{safe.replace(' ', '_')}.md")
        os.makedirs(os.path.dirname(report), exist_ok=True)
        with open(report, "w", encoding="utf-8") as f:
            f.write(self.report(res["metrics"]))
        return path, report, res["metrics"]

    def notes(self):
        return "\n".join([
            f"Generated {datetime.date.today()} by tools/generate.py: {self.skill}, {self.ascendancy}, focus {self.focus}.",
            "Template rare gear (life, two resistances, an attribute; typical weapon rolls) - an assumption, not real items.",
            "No uniques, jewels, flasks or cluster jewels yet. Sockets and gem colours are not checked.",
        ])

    def report(self, final):
        m = final
        lines = [f"# Generated build: {self.skill} / {self.ascendancy}", "",
                 f"{datetime.datetime.now():%Y-%m-%d %H:%M} · focus {self.focus} · {self.tries} tries in PoB · {self.elapsed / 60:.1f} min", "",
                 "## Result", "",
                 "| | |", "|---|---|",
                 f"| DPS | {self.dps(m):,.0f} |", f"| Life / ES | {m.get('Life')} / {m.get('EnergyShield')} |",
                 f"| Total EHP | {m.get('TotalEHP'):,.0f} |",
                 f"| Max hit phys / fire / cold / lightning / chaos | {m.get('PhysicalMaximumHitTaken')} / {m.get('FireMaximumHitTaken')} / "
                 f"{m.get('ColdMaximumHitTaken')} / {m.get('LightningMaximumHitTaken')} / {m.get('ChaosMaximumHitTaken')} |",
                 f"| Resistances | {m.get('FireResist')} / {m.get('ColdResist')} / {m.get('LightningResist')} / {m.get('ChaosResist')} |",
                 f"| Passive points | {m.get('passivePointsUsed')} / {m.get('passivePointsAvailable')} |",
                 f"| Mana unreserved | {m.get('ManaUnreserved')} |", f"| Missing attributes | {m.get('attributeShortfall')} |", "",
                 f"Weapon: {self.weapon}. Supports: {', '.join(self.links)}.", "",
                 "## Steps", "", "| Step | Change | DPS | Score |", "|---|---|---|---|"]
        for h in self.history:
            lines.append(f"| {h['step']} | {h['note']} | {h['dps']:,.0f} | {h['score']:.3f} |")
        lines += ["", "## Assumptions", "", *[f"- {n}" for n in self.notes().splitlines()[1:]],
                  "- Enemy: pinnacle boss (Config). Condition values PoB leaves at 0 are inferred (pob_scenarios explains them).",
                  "- The search is greedy: it finds a good build, not a proven best one."]
        if m.get("inferred"):
            lines += ["", "## Inferred conditions", ""] + [f"- {i.get('label')}: {i.get('value')}" for i in m["inferred"]]
        return "\n".join(lines) + "\n"


def describe(move):
    return "; ".join(f"{c['type']} {c.get('gem') or c.get('with') or c.get('node') or c.get('slot') or ''}" for c in move)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill")
    ap.add_argument("ascendancy")
    ap.add_argument("--focus", choices=list(FOCUS), default="balanced")
    ap.add_argument("--level", type=int, default=95)
    ap.add_argument("--name")
    ap.add_argument("--gear-from", help="library build whose items to use (tests the tree and gem search against its author)")
    args = ap.parse_args()
    g = Generator(args.skill, args.ascendancy, args.focus, args.level, args.name, gear_from=args.gear_from)
    g.run()
    path, report, m = g.export()
    log(f"\nDPS {g.dps(m):,.0f} · life {m.get('Life')} · EHP {m.get('TotalEHP'):,.0f} · {g.elapsed / 60:.1f} min")
    log(f"build:  {path}\nreport: {report}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
