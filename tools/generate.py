"""Build generator: from a skill and an ascendancy to a playable build, judged by Path of Building.

    python tools/generate.py "Kinetic Blast of Clustering" Necromancer [--focus balanced] [--level 95] [--name ...]

Steps (each step tries candidates in PoB and keeps the best by the score below):
  1. character: class and ascendancy, level, the skill in a 6-link body armour, template rare gear
  2. weapon: one template per weapon type the skill can use (attack), or a spell / minion weapon
  3. supports: five, picked one at a time from every support PoB says can support the skill
  4. ascendancy: up to 8 points of ascendancy notables
  5. auras and buffs (while reservation allows), then curses, marks and exposure - before the tree, so the tree
     sees what they reserve and add
  6. passive tree: grow from the class start, best score gain per point, until the points run out; masteries
     (one point, next to an allocated notable) and jewel sockets with a template rare jewel (the best of six kinds for
     the build) compete with the notables
  5b. utility flasks (slots 2-5, always on), and charges when the build has a source (inferred)
  7. auras and curses again, flasks swapped, the pantheon (major and minor god), then supports again, now that the tree is known
--archetype crit: weapons and amulet with crit rolls instead of the hybrid template, so the search builds for crit.
Score = ln(DPS) + w x defence - penalties, defence = (ln(EHP) + ln(smallest max hit)) / 2, w by --focus
(damage 0.5, balanced 1, defence 2). Penalties: fire/cold/lightning resistance under 75%, missing attribute
points, reserved more than available, more passive points than the character has.

Template gear is an assumption, stated in the report: good but ordinary rares (life, two resistances, an
attribute; weapons with typical damage rolls). No uniques, jewels, flasks or cluster jewels yet.
Output: src/Builds/generated/<name>.xml (open in PoB) and library/reports/generate-<name>.md.
"""
import argparse
import datetime
import json
import math
import os
import re
import sys
import random
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import library  # noqa: E402
import simlog  # noqa: E402
import weights as weightlib  # noqa: E402
from pob_worker import WORKER  # noqa: E402

OUT_DIR = os.environ.get("POB_GENERATE_DIR") or os.path.join(library.ROOT, "src", "Builds", "generated")
FOCUS = {"damage": 0.5, "balanced": 1.0, "defence": 2.0}
# Version of the generator's rules, kept with every run: results of different versions are not comparable.
# 2: realistic skill stages (Blade Blast, Explosive Arrow), dual-wield weapons, runs stop when the skill deals no damage.
GENERATOR_VERSION = 6


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


def armour_set(attribute, archetype=None):
    b = ARMOUR_BASES[attribute]
    amulet_extra = CRIT_AMULET if archetype == "crit" else []
    return {
        "Helmet": item("Template Helmet", b["Helmet"], "+90 to maximum Life", "+40% to Fire Resistance", "+40% to Cold Resistance"),
        "Body Armour": item("Template Body Armour", b["Body Armour"], "+110 to maximum Life", "+40% to Fire Resistance", "+40% to Cold Resistance"),
        "Gloves": item("Template Gloves", b["Gloves"], "+80 to maximum Life", "+40% to Cold Resistance", "+40% to Lightning Resistance"),
        "Boots": item("Template Boots", b["Boots"], "+80 to maximum Life", "+40% to Fire Resistance", "+40% to Lightning Resistance",
                      "30% increased Movement Speed"),
        "Amulet": item("Template Amulet", "Onyx Amulet", "+70 to maximum Life", "+40% to Lightning Resistance", "+40 to Strength",
                       *amulet_extra, implicits=("+16 to all Attributes",)),
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
# The crit archetype: the same weapons with crit rolls instead of the hybrid ones, and crit on the amulet. Without it the
# greedy search never commits to crit (each crit node alone is weak until the others are there).
CRIT_ONE_HAND = ["Adds 25 to 50 Physical Damage", "150% increased Physical Damage", "15% increased Attack Speed",
                 "38% increased Critical Strike Chance", "+38% to Global Critical Strike Multiplier", "+400 to Accuracy Rating"]
CRIT_TWO_HAND = ["Adds 45 to 95 Physical Damage", "150% increased Physical Damage", "12% increased Attack Speed",
                 "38% increased Critical Strike Chance", "+38% to Global Critical Strike Multiplier", "+400 to Accuracy Rating"]
CRIT_AMULET = ["+35% to Global Critical Strike Multiplier", "30% increased Global Critical Strike Chance"]
CRIT_SPELL_WEAPON = item("Template Sceptre", "Void Sceptre", "70% increased Spell Damage", "20% increased Cast Speed",
                         "120% increased Critical Strike Chance for Spells", "+38% to Global Critical Strike Multiplier",
                         "+40 to Intelligence")
ARCHETYPES = {None: "template gear (hybrid weapon rolls)", "crit": "crit: weapon and amulet with crit rolls"}
NEVER_CRIT = {"Precise Technique", "Resolute Technique", "Elemental Overload"}  # keystones the crit archetype leaves out

SPELL_WEAPON = item("Template Sceptre", "Void Sceptre", "90% increased Spell Damage", "20% increased Cast Speed",
                    "80% increased Critical Strike Chance for Spells", "+30% to Global Critical Strike Multiplier", "+40 to Intelligence")
SPELL_SHIELD = item("Template Shield", "Titanium Spirit Shield", "+80 to maximum Life", "60% increased Spell Damage",
                    "+40% to Fire Resistance", "+40% to Cold Resistance")
MINION_WEAPON = item("Template Wand", "Convoking Wand", "+1 to Level of all Minion Skill Gems", "Minions deal 60% increased Damage",
                     "Minions have 25% increased Attack Speed", "Minions have 25% increased Cast Speed")


def weapon_options(info, attribute, archetype=None):
    """[(label, [changes])] - weapon (and shield) setups the skill can use."""
    armour, shield = armour_set(attribute)
    crit = archetype == "crit"
    spell_weapon = CRIT_SPELL_WEAPON if crit else SPELL_WEAPON
    shield_change = {"type": "item_equip", "slot": "Weapon 2", "raw": shield}
    options = []
    if info["minion"]:
        options.append(("minion wand + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": MINION_WEAPON}, shield_change]))
    if info["spell"] and not info["attack"]:
        options.append(("spell sceptre + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": spell_weapon},
                                                    {"type": "item_equip", "slot": "Weapon 2", "raw": SPELL_SHIELD}]))
    if info["attack"]:
        types = [t for t in (info["weaponTypes"] or list(WEAPONS)) if t in WEAPONS]
        one_handed = [t for t in types if not WEAPONS[t][1]]

        def weapon(t, slot="Weapon 1"):
            base, two_handed = WEAPONS[t]
            lines = (CRIT_TWO_HAND if two_handed else CRIT_ONE_HAND) if crit else (TWO_HAND if two_handed else ONE_HAND)
            return {"type": "item_equip", "slot": slot, "raw": item(f"Template {t}", base, *lines)}

        for t in types:
            two_handed = WEAPONS[t][1]
            if info.get("dualWield"):
                # dual wield only (Dual Strike, Swordstorm, Cleave of Rage...): a second one-handed weapon, of another
                # type when the skill needs different types. The off-hand has no resistances, unlike the shield.
                if two_handed:
                    continue
                others = [o for o in one_handed if o != t] if info.get("dualWieldDifferent") else [t]
                if others:
                    options.append((f"{t} + {others[0]}", [weapon(t), weapon(others[0], "Weapon 2")]))
            else:
                options.append((t, [weapon(t)] if two_handed else [weapon(t), shield_change]))
    if not options:
        options.append(("spell sceptre + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": spell_weapon},
                                                    {"type": "item_equip", "slot": "Weapon 2", "raw": SPELL_SHIELD}]))
    return options


BUFF_SKILLS = ["Hatred", "Anger", "Wrath", "Zealotry", "Malevolence", "Pride", "Haste", "Grace", "Determination", "Discipline",
               "Precision", "Purity of Elements", "Herald of Ash", "Herald of Ice", "Herald of Thunder", "Herald of Agony",
               "Herald of Purity", "War Banner", "Dread Banner", "Defiance Banner", "Arctic Armour", "Tempest Shield",
               "Flesh and Stone", "Vitality", "Enduring Cry"]  # Enduring Cry: endurance charges (inferred from the skill)


# Curses, marks and exposure: applied to the enemy as if always up (self-cast, on hit or by aura - not modelled which).
# PoB's curse limit (one curse, one mark by default) decides how many count.
DEBUFF_SKILLS = ["Elemental Weakness", "Frostbite", "Flammability", "Conductivity", "Vulnerability", "Punishment", "Despair",
                 "Temporal Chains", "Enfeeble", "Assassin's Mark", "Warlord's Mark", "Sniper's Mark", "Poacher's Mark",
                 "Frost Bomb", "Wave of Conviction"]


# Utility flasks in slots 2-5 (slot 1 is left for a life flask, which PoB's numbers do not use): quality 20, no
# mods, switched on - PoB then counts their effect all the time (an assumption: real uptime depends on charges).
FLASKS = ["Diamond Flask", "Granite Flask", "Jade Flask", "Silver Flask", "Sulphur Flask", "Basalt Flask", "Bismuth Flask",
          "Ruby Flask", "Sapphire Flask", "Topaz Flask", "Amethyst Flask", "Quartz Flask", "Stibnite Flask", "Corundum Flask",
          "Aquamarine Flask", "Iron Flask"]
FLASK_SLOTS = ["Flask 2", "Flask 3", "Flask 4", "Flask 5"]


def flask_item(base):
    return f"Rarity: MAGIC\n{base}\nQuality: 20\nImplicits: 0"


# Template rare jewels for the tree's jewel sockets (not cluster jewels): good ordinary rolls, one kind per build
# type; the generator finds the best kind once, then a socket plus that jewel competes with the passives.
def jewel_item(name, *lines):
    return "\n".join(["Rarity: RARE", f"Template {name} Jewel", "Crimson Jewel", "Item Level: 86", "Implicits: 0", *lines])


JEWELS = {
    "Attack": jewel_item("Attack", "7% increased maximum Life", "5% increased Attack Speed", "16% increased Attack Damage",
                         "+15% to Global Critical Strike Multiplier"),
    "Spell": jewel_item("Spell", "7% increased maximum Life", "5% increased Cast Speed", "16% increased Spell Damage",
                        "+15% to Global Critical Strike Multiplier"),
    "Crit": jewel_item("Crit", "7% increased maximum Life", "16% increased Global Critical Strike Chance",
                       "+15% to Global Critical Strike Multiplier", "12% increased Damage"),
    "Minion": jewel_item("Minion", "7% increased maximum Life", "Minions deal 16% increased Damage", "Minions have 10% increased maximum Life",
                         "Minions have 5% increased Attack Speed", "Minions have 5% increased Cast Speed"),
    "Damage over Time": jewel_item("Damage over Time", "7% increased maximum Life", "16% increased Damage over Time",
                                   "8% increased Skill Effect Duration", "12% increased Damage"),
    "Defence": jewel_item("Defence", "7% increased maximum Life", "+12% to all Elemental Resistances", "12% increased Armour",
                          "12% increased Evasion Rating"),
}


# Pantheon powers (Config): the best major and minor god for the score. The bandit quest stays "Kill all" (2 points).
PANTHEON = {"pantheonMajorGod": ["TheBrineKing", "Lunaris", "Solaris", "Arakaali"],
            "pantheonMinorGod": ["Gruthkul", "Yugul", "Abberath", "Tukohama", "Garukhan", "Ralakesh", "Ryslatha", "Shakari"]}


# Supports that change how the skill is used (trap, mine, totem, trigger, another minion): not the build asked for
DELIVERY = re.compile(r"Trap|Mine|Totem|Ballista|Cast On|Cast on|Cast when|Cast while|Spellslinger|Summon Phantasm|Trigger|"
                      r"Automation|Autoexertion|Mark On Hit|Arcanist|Blessing|Call to Arms|Manaforged|Kinetic Instability", re.I)


# Guided search (--guided; library/weights.db from tools/weights.py). Off by default: tested 2026-11-25 on three skills
# the weights had not seen, it tried 37% fewer candidates but lost 27% and 13% DPS on two of them - supports that are
# only strong in one combination (Cold to Fire + Fire Penetration for Ice Crash, Brutality for Lacerate) have low
# average weights and were cut. When on: supports are tried in weight order, the best GUIDE_TOP
# plus GUIDE_EXPLORE others at random (so the data keeps learning about the rest); passives never tried before are
# tried in weight order. Auras, curses, ascendancy nodes and weapons are few: all of them are always tried.
GUIDE_TOP = 15
GUIDE_EXPLORE = 5


def log(*args):
    print(*args, flush=True)


class Generator:
    def __init__(self, skill, ascendancy, focus="balanced", level=95, name=None, infer=True, gear_from=None, archetype=None,
                 guided=False, seed=None):
        self.skill, self.ascendancy, self.level = skill, ascendancy, level
        self.guided = guided
        self.rng = random.Random(seed)
        self.weights, self.guide = {}, None
        self.jewel = None  # the template jewel kind that suits this build best (found at the first socket)
        self.archetype = archetype
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
        self.attributes_later = False

    # --- PoB calls ---------------------------------------------------------------------------------------------------
    def params(self):
        # inferCharges: power/frenzy/endurance charges on when the build has a source (tools/PobWorker.lua)
        return {"xml": self.xml, "name": self.name, "infer": self.infer, "inferCharges": self.infer}

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

    # --- guide -------------------------------------------------------------------------------------------------------
    def load_weights(self):
        """{category: {key: weight}} for this skill and ascendancy, or nothing (every candidate tried)."""
        if not self.guided or not os.path.exists(weightlib.db_path()):
            return
        try:
            db = weightlib.open_weights()
            r = weightlib.suggest(self.skill, self.ascendancy, top=100000, db=db)
            meta = {k: json.loads(v) for k, v in db.execute("SELECT key, value FROM meta")}
        except (SystemExit, Exception) as e:  # an unknown gem name or an old file: search unguided
            log(f"  (weights not used: {e})")
            return
        self.weights = {cat: {x["key"]: x["weight"] for x in rows} for cat, rows in r["suggestions"].items()}
        self.guide = f"weights {meta.get('built')} ({meta.get('runs')} runs)"

    def narrow(self, cat, keys):
        """The best GUIDE_TOP by weight plus GUIDE_EXPLORE random others; all of them when unguided."""
        w = self.weights.get(cat)
        if not w or len(keys) <= GUIDE_TOP + GUIDE_EXPLORE:
            return list(keys)
        order = sorted(keys, key=lambda k: -w.get(str(k), 0.5))  # never seen: in the middle
        rest = order[GUIDE_TOP:]
        return order[:GUIDE_TOP] + self.rng.sample(rest, min(GUIDE_EXPLORE, len(rest)))

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
        # before the tree, missing attributes are left to the tree (a curse needing Int would never be tried otherwise)
        p += (m.get("attributeShortfall") or 0) * (0 if self.attributes_later else 0.02)
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
        armour, _ = armour_set(self.attribute, self.archetype)
        self.xml = r["xml"]
        self.state = [{"type": "item_equip", "slot": slot, "raw": raw} for slot, raw in armour.items()]
        self.current = self.try_all([[]])[0]["metrics"]
        log(f"{r['class']} / {r['ascendancy']}, {r['skill']} ({', '.join(k for k in ('attack', 'spell', 'minion') if self.info[k])})")

    def pick_weapon(self):
        self.step = "weapon"
        options = weapon_options(self.info, self.attribute, self.archetype)
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
            pool = self.narrow("support", [s for s in self.support_pool if s not in self.links])
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
            passives = [p for p in cands["passives"] if p["cost"] <= free
                        and not (self.archetype == "crit" and p["name"] in NEVER_CRIT)]
            if free >= 1:
                # masteries next to allocated notables: one point, one effect each (an effect is taken only once)
                passives += [{"id": f"m{m['id']}:{m['effect']}", "node": m["id"], "effect": m["effect"], "cost": 1,
                              "name": f"{m['name']}: {m['text']}", "mastery": True} for m in cands.get("masteries", [])]
            sockets = [j for j in cands.get("jewelSockets", []) if j["cost"] <= free]
            if sockets and self.jewel is None:
                self.pick_jewel_kind(min(sockets, key=lambda j: j["cost"]))
            if self.jewel:
                passives += [{"id": f"j{j['id']}", "node": j["id"], "slot": j["slot"], "cost": j["cost"], "jewel": self.jewel,
                              "name": f"jewel socket {j['id']} with a {self.jewel} jewel"} for j in sockets]
            if not passives:
                break
            # Re-try the best-known candidates and every candidate never tried
            ranked = sorted(passives, key=lambda p: -(known.get(p["id"], (math.inf,))[0]))
            untried = [p for p in ranked if p["id"] not in known]
            if self.weights.get("passive"):  # the 80 never tried: best weights first (some at random, to keep learning)
                w = self.weights["passive"]
                by_weight = sorted(untried, key=lambda p: -w.get(str(p["id"]), 0.5))
                head, rest = by_weight[:70], by_weight[70:]
                untried = head + self.rng.sample(rest, min(10, len(rest)))
            batch = untried[:80] + [p for p in ranked if p["id"] in known][:shortlist]
            moves = [self.socket_move(p) if p.get("jewel") else
                     [{"type": "mastery_add", "node": p["node"], "effect": p["effect"]} if p.get("mastery") else
                      {"type": "passive_add", "node": p["id"]}] for p in batch]
            found, res = self.best(moves, self.current, per_point=[p["cost"] for p in batch])
            base = self.score(self.current)
            for p, r in zip(batch, res):
                if "metrics" in r:
                    known[p["id"]] = ((self.score(r["metrics"]) - base) / max(p["cost"], 1), p["name"], p["cost"])
            if not found:
                break
            move, metrics, _ = found
            node = batch[moves.index(move)]
            known.pop(node["id"], None)
            what = "mastery" if node.get("mastery") else "jewel" if node.get("jewel") else "passive"
            self.accept("tree", move, metrics, f"{what}: {node['name']} ({node['cost']} points, {metrics.get('passivePointsUsed')}/{available})")

    def socket_move(self, sock, kind=None):
        """Allocate a jewel socket (unless it already is) and put a template jewel in it."""
        move = [{"type": "passive_add", "node": sock["node"] if "node" in sock else sock["id"]}] if sock["cost"] else []
        return move + [{"type": "item_equip", "slot": sock["slot"], "raw": JEWELS[kind or sock.get("jewel") or self.jewel]}]

    def pick_jewel_kind(self, sock):
        """Try every template jewel in the cheapest socket once; the best kind is used for every socket after."""
        step, self.step = self.step, "jewel kind"
        kinds = list(JEWELS)
        res = self.try_all([self.socket_move(sock, k) for k in kinds])
        scored = [(self.score(r["metrics"]), k) for k, r in zip(kinds, res) if "metrics" in r]
        self.jewel = max(scored)[1] if scored else None
        self.step = step
        if self.jewel:
            log(f"  [jewel] template jewel for this build: {self.jewel}")

    def retune_jewels(self):
        """Once the tree is done: each placed jewel may be better as another kind (e.g. defence once damage is high)."""
        self.step = "jewel"
        placed = {}
        for c in self.state:
            if c["type"] == "item_equip" and c["slot"].startswith("Jewel "):
                placed[c["slot"]] = c["raw"].splitlines()[1]
        for slot, name in placed.items():
            others = [k for k in JEWELS if f"Template {k} Jewel" != name]
            found = self.best([[{"type": "item_equip", "slot": slot, "raw": JEWELS[k]}] for k in others], self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                self.accept("jewel", move, metrics, f"jewel: {slot} -> {move[0]['raw'].splitlines()[1]}")

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

    def add_debuffs(self):
        self.step = "curse"
        present = {c.get("gems", [None])[0] for c in self.state if c["type"] == "group_add"}
        pool = [s for s in DEBUFF_SKILLS if s not in present]
        while pool:
            found = self.best([[{"type": "group_add", "gems": [s]}] for s in pool], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            pool.remove(move[0]["gems"][0])
            self.accept("curse", move, metrics, f"curse/exposure: {move[0]['gems'][0]}")

    def flasks_in(self):
        """{slot: base} of the flasks in the current state (the last one equipped in each slot)."""
        out = {}
        for c in self.state:
            if c["type"] == "item_equip" and c["slot"] in FLASK_SLOTS:
                out[c["slot"]] = c["raw"].splitlines()[1]
        return out

    def pick_flasks(self):
        """Fill the empty utility slots one at a time; once full, try swapping each flask for an unused one."""
        self.step = "flask"
        for slot in FLASK_SLOTS:
            have = self.flasks_in()
            pool = [b for b in FLASKS if b not in have.values()]  # a flask is only useful once
            found = self.best([[{"type": "item_equip", "slot": slot, "raw": flask_item(b)}] for b in pool], self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                base = move[0]["raw"].splitlines()[1]
                note = f"flask: {base}" + (f" (instead of {have[slot]})" if slot in have else "")
                self.accept("flask", move, metrics, note)

    def pick_pantheon(self):
        self.step = "pantheon"
        for key, gods in PANTHEON.items():
            found = self.best([[{"type": "config_set", "key": key, "value": g}] for g in gods], self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                self.accept("pantheon", move, metrics, f"pantheon: {move[0]['value']}")

    def retune_supports(self):
        self.step = "support swap"
        for gem in list(self.links):
            pool = self.narrow("support", [s for s in self.support_pool if s not in self.links])
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
        self.load_weights()
        self.recorder = simlog.Recorder("generate", skill=self.skill, ascendancy=self.ascendancy, cls=self.class_name, focus=self.focus,
                                        gear=f"from {self.gear_from}" if self.gear_from else gear_label(self.archetype), skill_info=self.info,
                                        versions=WORKER.call("ping", {}), generator=GENERATOR_VERSION,
                                        guide=self.guide)
        if not self.gear_from:
            self.pick_weapon()
        self.pick_supports()
        if self.dps(self.current) <= 0:
            # nothing the search does can be measured (PoB calculates no damage for this skill with this setup):
            # stop instead of building a tree for defence only
            self.elapsed = time.time() - started
            self.outcome = "no damage"
            self.recorder.finish(self.current, outcome=self.outcome)
            return None
        self.pick_ascendancy()
        # auras and curses before the tree, so the tree sees what they reserve and add (a keystone such as Blood
        # Magic looked free while no aura reserved life yet), then again once the tree is known
        self.attributes_later = True
        self.add_buffs()
        self.add_debuffs()
        self.pick_flasks()
        self.attributes_later = False
        self.current = self.try_all([[]])[0]["metrics"]  # same build, scored again with the attribute penalty
        self.grow_tree()
        self.add_buffs()
        self.add_debuffs()
        self.pick_flasks()  # swaps, now that the tree is known
        self.retune_jewels()
        self.pick_pantheon()
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
        res["metrics"]["inferred"] = res.get("inferred") or None  # estimates applied (stages, withered stacks...) go in the report
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
            "Template rare gear (life, two resistances, an attribute; typical weapon rolls) - an assumption, not real items."
            + (f" Archetype {ARCHETYPES[self.archetype]}." if self.archetype else ""),
            "Curses, marks and exposure count as always applied (how they are applied is not modelled).",
            "Utility flasks (quality 20, no mods) count as always on; flask slot 1 is left for a life flask.",
            "Tree jewel sockets hold template rare jewels (life plus three good rolls of one kind); no cluster, abyss or unique jewels.",
            "Power, frenzy and endurance charges count at their maximum when the build has a source (none against a lone boss "
            "if every source needs kills).",
            (f"Search guided by {self.guide}: supports tried in weight order (top {GUIDE_TOP} + {GUIDE_EXPLORE} at random)."
             if self.guide else "Search not guided: every candidate tried."),
            "No uniques, cluster or abyss jewels yet. Sockets and gem colours are not checked.",
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
            lines += ["", "## Inferred conditions", ""] + [
                f"- {i.get('label')}: {i.get('value') if i.get('applied') else 'not changed (' + str(i.get('skipped')) + ')'}"
                + (f" (PoB's default: {i['maximum']})" if i.get("maximum") else "")
                + (f" - {'; '.join(i['assumptions'])}" if i.get("assumptions") else "") for i in m["inferred"]]
        return "\n".join(lines) + "\n"


def gear_label(archetype):
    """runs.gear in the simulation log: 'template' (hybrid rolls) or 'template crit'."""
    return "template" + (f" {archetype}" if archetype else "")


def describe(move):
    return "; ".join(f"{c['type']} {c.get('gem') or c.get('with') or c.get('node') or c.get('slot') or ''}" for c in move)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("skill")
    ap.add_argument("ascendancy")
    ap.add_argument("--focus", choices=list(FOCUS), default="balanced")
    ap.add_argument("--level", type=int, default=95)
    ap.add_argument("--name")
    ap.add_argument("--archetype", choices=["crit"], help="crit: weapon and amulet with crit rolls, so the search builds for crit")
    ap.add_argument("--guided", action="store_true", help="experimental: try supports in library/weights.db order, only the best "
                                                          f"{GUIDE_TOP} + {GUIDE_EXPLORE} at random")
    ap.add_argument("--gear-from", help="library build whose items to use (tests the tree and gem search against its author)")
    args = ap.parse_args()
    g = Generator(args.skill, args.ascendancy, args.focus, args.level, args.name, gear_from=args.gear_from, archetype=args.archetype,
                  guided=args.guided)
    if g.run() is None:
        log(f"\nDPS 0 · no damage: PoB calculates no damage for {args.skill} with weapon '{g.weapon}' - run stopped "
            f"({g.elapsed / 60:.1f} min)")
        return
    path, report, m = g.export()
    log(f"\nDPS {g.dps(m):,.0f} · life {m.get('Life')} · EHP {m.get('TotalEHP'):,.0f} · {g.elapsed / 60:.1f} min")
    log(f"build:  {path}\nreport: {report}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
