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
  5a. a guard skill (Steelskin, Molten Shell), a golem and up to three warcries, while they help
  5b. utility flasks (slots 2-5, always on), and charges when the build has a source (inferred)
  7. auras and curses again, flasks swapped, an amulet anoint and the skill's helmet enchant, unique items (each that
     fits screened once, the best three per slot added while they help), the pantheon (major and minor god), then supports again, now that the tree is known
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
# 14: the support pool is refreshed after every support taken (a support that needs another one linked first, e.g.
#     Overloaded Intensity after Intensify, was never in the pool), and the final swaps repeat until none improves.
# 15: recovery counts the net regeneration (PoB's NetLifeRegen: regeneration minus the build's own degeneration, e.g.
#     Righteous Fire, Blood Rage); a build that loses life every second is penalised. Righteous Fire (both), Pact of
#     Beidat and Blood and Sand may be chosen as buffs.
# 16: deterministic: every candidate list is sorted before it is tried (PoB's pairs() order differs between processes;
#     the tree step tries only the first 80 untried passives - now the cheapest first, then by id - and of equal gains
#     the first is kept), so the same version gives the same build twice (v15 gave Storm Call / Assassin 84% and 100%
#     of the author's DPS in two runs). PoB producing no output once is retried.
# 17: chaos resistance below 0 is penalised like an uncapped elemental resistance (CHAOS_FLOOR_PENALTY a point), on top
#     of the soft term; the playable floor says chaos >= 0 and Glacial Hammer / Champion sat at -8 for three versions.
# 18: tree swap: once the tree is full, the allocated notables / keystones cheapest to remove (score lost per point freed)
#     are each taken out in turn and their points spent again on the best candidates of the finished build; a swap is
#     kept when the build scores higher. A probe of v17 (Cyclone, Glacial Hammer, Storm Call / Hierophant) showed every
#     tree candidate is tried in every round (the 80-untried cap never cut one), so breadth was not what the greedy
#     growth lacked: it had no way back from a node chosen for the gain it had when the tree was small.
# 19: life + energy shield below LIFE_FLOOR (the playable floor, 4000) costs LIFE_FLOOR_PENALTY a point: the score had
#     no floor, so Cyclone / Slayer sat at 3,600 for versions and the v18 tree swap traded Glacial Hammer's life for DPS.
GENERATOR_VERSION = 19
# Results of older versions from STILL_VALID_FROM on still count as done in self-play, except for the skills a later
# version changed (changed_since_valid). Version 9 only changed minion skills (the minion's skill is now chosen),
# unarmed attacks (empty main hand) and spells that need a staff.
STILL_VALID_FROM = 19


def changed_since_valid(skill, info):
    return bool(info.get("minion") or skill.startswith("Explosive Concoction") or skill.startswith("Mana-Infused Staff"))


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


# Template rares at a mid budget (about 1-5 divine a week into a league; research 2026-11-26 from PoB's mod tiers and
# 15 real builds): at most 3 prefixes and 3 suffixes, T2-T3 rolls. Each armour piece has life, a local defence of its
# base's kind, two resistances and an attribute, so the tree does not have to buy attributes or all of the defence.
DEFENCE = {"Str": ("Armour", "+100 to Armour"), "Dex": ("Evasion Rating", "+100 to Evasion Rating"),
           "Int": ("Energy Shield", "+40 to maximum Energy Shield")}
BASE_STAT = {"Str": "Strength", "Dex": "Dexterity", "Int": "Intelligence"}


def armour_set(attribute, archetype=None):
    if archetype in DEFENCES:
        armour, shield = armour_set(DEFENCES[archetype].get("bases") or attribute)
        return {slot: defend(slot, raw, archetype) for slot, raw in armour.items()}, defend("Shield", shield, archetype)
    b = ARMOUR_BASES[attribute]
    local, flat = DEFENCE[attribute]
    stat = BASE_STAT[attribute]
    if archetype == "crit":  # crit on the amulet instead of its attributes (the +16 all implicit stays)
        amulet_suffixes = ["+40% to Lightning Resistance", *CRIT_AMULET]
    else:
        amulet_suffixes = ["+40% to Lightning Resistance", "+40 to Strength", "+30 to Dexterity"]
    return {
        "Helmet": item("Template Helmet", b["Helmet"], "+110 to maximum Life", f"60% increased {local}",
                       "+40% to Fire Resistance", "+40% to Cold Resistance", "+35 to Intelligence"),
        "Body Armour": item("Template Body Armour", b["Body Armour"], "+150 to maximum Life", f"70% increased {local}",
                            "+40% to Fire Resistance", "+40% to Cold Resistance", f"+30 to {stat}"),
        "Gloves": item("Template Gloves", b["Gloves"], "+100 to maximum Life", flat,
                       "+40% to Cold Resistance", "+40% to Lightning Resistance", "+35 to Dexterity"),
        "Boots": item("Template Boots", b["Boots"], "+100 to maximum Life", "30% increased Movement Speed",
                      "+40% to Fire Resistance", "+40% to Lightning Resistance", f"+35 to {stat}"),
        "Amulet": item("Template Amulet", "Onyx Amulet", "+90 to maximum Life", *amulet_suffixes,
                       implicits=("+16 to all Attributes",)),
        "Ring 1": item("Template Ring", "Two-Stone Ring", "+75 to maximum Life", "+40% to Lightning Resistance", "+35 to Dexterity",
                       "+30 to Intelligence", implicits=("+16% to Fire and Cold Resistances",)),
        "Ring 2": item("Template Ring", "Two-Stone Ring", "+75 to maximum Life", "+40% to Lightning Resistance", "+35 to Intelligence",
                       "+30 to Strength", implicits=("+16% to Fire and Cold Resistances",)),
        "Belt": item("Template Belt", "Leather Belt", "+100 to maximum Life", "+40% to Cold Resistance", "+40% to Lightning Resistance",
                     "+35 to Strength", implicits=("+40 to maximum Life",)),
    }, item("Template Shield", b["Shield"], "+120 to maximum Life", f"70% increased {local}", "+40% to Fire Resistance",
            "+40% to Cold Resistance", f"+30 to {stat}")


# 3 suffixes: attack speed, crit chance, accuracy (the crit archetype takes crit multiplier instead of accuracy)
ONE_HAND = ["Adds 19 to 40 Physical Damage", "150% increased Physical Damage", "22% increased Attack Speed",
            "30% increased Critical Strike Chance", "+400 to Accuracy Rating"]
TWO_HAND = ["Adds 30 to 65 Physical Damage", "150% increased Physical Damage", "22% increased Attack Speed",
            "30% increased Critical Strike Chance", "+400 to Accuracy Rating"]
WEAPONS = {  # PoB weapon type -> (base, two-handed)
    "Wand": ("Prophecy Wand", False), "Claw": ("Imperial Claw", False), "Dagger": ("Ambusher", False),
    "One Handed Sword": ("Corsair Sword", False), "Thrusting One Handed Sword": ("Jewelled Foil", False),
    "One Handed Axe": ("Runic Hatchet", False), "One Handed Mace": ("Behemoth Mace", False), "Sceptre": ("Void Sceptre", False),
    "Bow": ("Thicket Bow", True), "Staff": ("Eclipse Staff", True), "Two Handed Sword": ("Reaver Sword", True),
    "Two Handed Axe": ("Vaal Axe", True), "Two Handed Mace": ("Coronal Maul", True),
}
# The crit archetype: the same weapons with crit rolls instead of the hybrid ones, and crit on the amulet. Without it the
# greedy search never commits to crit (each crit node alone is weak until the others are there).
CRIT_ONE_HAND = ["Adds 19 to 40 Physical Damage", "150% increased Physical Damage", "16% increased Attack Speed",
                 "37% increased Critical Strike Chance", "+37% to Global Critical Strike Multiplier"]
CRIT_TWO_HAND = ["Adds 30 to 65 Physical Damage", "150% increased Physical Damage", "16% increased Attack Speed",
                 "37% increased Critical Strike Chance", "+37% to Global Critical Strike Multiplier"]
CRIT_AMULET = ["+35% to Global Critical Strike Multiplier", "30% increased Global Critical Strike Chance"]
CRIT_SPELL_WEAPON = item("Template Sceptre", "Void Sceptre", "80% increased Spell Damage", "20% increased Cast Speed",
                         "100% increased Spell Critical Strike Chance", "+35% to Global Critical Strike Multiplier")
ARCHETYPES = {None: "template gear (hybrid weapon rolls)", "crit": "crit: weapon and amulet with crit rolls",
              "armour": "armour: armour bases with flat armour added, Determination",
              "block": "block: shield with attack and spell block (a spell build gives up its spirit shield)",
              "evasion": "evasion: evasion bases, spell suppression instead of the armour pieces' attributes, Grace",
              "es": "energy shield: energy shield instead of life, Chaos Inoculation, Discipline",
              "takenas": "physical taken as elemental: body armour (16% as fire) and Taste of Hate (20% as cold)"}

# Defence archetypes (like crit: a defence only pays off as a set, which the greedy search never builds one step at a
# time; 2026-11-26 the 15 real builds had 73-98% attack and spell block, ours 37-45% and 0-9%). Each starts from its gear,
# buffs and keystones; the search does the rest, so every skill gets a DPS / defence row per archetype.
# gear: slot -> {template line -> new line}, "+N to maximum Life" may be written as a regex key starting with "re:".
DEFENCES = {
    "armour": {"bases": "Str", "buffs": ["Determination"],
               "add": {"Body Armour": ["+400 to Armour"], "Helmet": ["+150 to Armour"], "Shield": ["+300 to Armour"]}},
    "block": {"shield": True,
              "add": {"Shield": ["14% Chance to Block Spell Damage"]},
              # a spirit shield cannot roll block: an Int build gets an evasion / energy shield base instead
              "gear": {"Shield": {"re:\\+30 to \\w+$": "+14% Chance to Block", "Titanium Spirit Shield": "Mirrored Spiked Shield"}}},
    "evasion": {"bases": "Dex", "buffs": ["Grace"],
                "gear": {"Helmet": {"+35 to Intelligence": "+13% chance to Suppress Spell Damage"},
                         "Gloves": {"+35 to Dexterity": "+13% chance to Suppress Spell Damage"},
                         "Boots": {"+35 to Dexterity": "+16% chance to Suppress Spell Damage"},
                         "Body Armour": {"+30 to Dexterity": "+20% chance to Suppress Spell Damage"}}},
    "es": {"bases": "Int", "buffs": ["Discipline"], "keystones": ["Chaos Inoculation"],
           "never": ["The Agnostic"],  # energy shield to 0: with Chaos Inoculation nothing is left
           "gear": {"Helmet": {"re:^\\+\\d+ to maximum Life$": "+55 to maximum Energy Shield"},
                    "Body Armour": {"re:^\\+\\d+ to maximum Life$": "+95 to maximum Energy Shield"},
                    "Gloves": {"re:^\\+\\d+ to maximum Life$": "+45 to maximum Energy Shield"},
                    "Boots": {"re:^\\+\\d+ to maximum Life$": "+45 to maximum Energy Shield"},
                    "Amulet": {"re:^\\+\\d+ to maximum Life$": "+50 to maximum Energy Shield"},
                    "Ring 1": {"re:^\\+\\d+ to maximum Life$": "+40 to maximum Energy Shield"},
                    "Ring 2": {"re:^\\+\\d+ to maximum Life$": "+40 to maximum Energy Shield"},
                    "Belt": {"re:^\\+\\d+ to maximum Life$": "+45 to maximum Energy Shield"},
                    "Shield": {"re:^\\+\\d+ to maximum Life$": "+80 to maximum Energy Shield"}}},
    "takenas": {"add": {"Body Armour": ["16% of Physical Damage from Hits taken as Fire Damage"]},
                "flasks": {"Flask 2": "Taste of Hate"}},
}


def defend(slot, raw, defence):
    """A template item changed for a defence archetype (DEFENCES)."""
    d = DEFENCES.get(defence) or {}
    lines = raw.split("\n")
    for old, new in d.get("gear", {}).get(slot, {}).items():
        if old.startswith("re:"):
            lines = [new if re.search(old[3:], x) and not x.startswith(("Rarity", "Item Level", "Implicits")) else x for x in lines]
        else:
            lines = [new if x == old else x for x in lines]
    return "\n".join(lines + d.get("add", {}).get(slot, []))
NEVER_CRIT = {"Precise Technique", "Resolute Technique", "Elemental Overload"}  # keystones the crit archetype leaves out

SPELL_WEAPON = item("Template Sceptre", "Void Sceptre", "80% increased Spell Damage", "22% increased Cast Speed",
                    "80% increased Spell Critical Strike Chance", "+30% to Global Critical Strike Multiplier")
SPELL_SHIELD = item("Template Shield", "Titanium Spirit Shield", "+100 to maximum Life", "60% increased Spell Damage",
                    "+40% to Fire Resistance", "+40% to Cold Resistance", "+30 to Intelligence")
# A staff for spells that need one (e.g. Mana-Infused Staff)
SPELL_STAFF = item("Template Spell Staff", "Eclipse Staff", "120% increased Spell Damage", "30% increased Cast Speed",
                   "+80 to maximum Mana", "+40 to Intelligence")
MINION_WEAPON = item("Template Wand", "Convoking Wand", "+1 to Level of all Minion Skill Gems", "Minions deal 80% increased Damage",
                     "Minions have 20% increased Attack and Cast Speed")


def weapon_options(info, attribute, archetype=None):
    """[(label, [changes])] - weapon (and shield) setups the skill can use."""
    armour, shield = armour_set(attribute, archetype if archetype in DEFENCES else None)
    crit = archetype == "crit"
    spell_weapon = CRIT_SPELL_WEAPON if crit else SPELL_WEAPON
    shield_change = {"type": "item_equip", "slot": "Weapon 2", "raw": shield}
    options = []
    if info["minion"]:
        options.append(("minion wand + shield", [{"type": "item_equip", "slot": "Weapon 1", "raw": MINION_WEAPON}, shield_change]))
    if info.get("requiresStaff"):
        options.append(("spell staff", [{"type": "item_equip", "slot": "Weapon 1", "raw": SPELL_STAFF}]))
    if info["attack"] and info.get("weaponTypes") == ["None"]:
        # an unarmed attack that needs an empty main hand (e.g. Explosive Concoction): only a shield
        options.append(("empty main hand + shield", [shield_change]))
    if info["spell"] and not info["attack"] and not info.get("requiresStaff"):
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
    if archetype in DEFENCES and DEFENCES[archetype].get("shield"):
        # block: only setups with a shield, and that shield is the block one (a spirit shield cannot roll block)
        options = [(label, [shield_change if c.get("slot") == "Weapon 2" else c for c in changes])
                   for label, changes in options if any(c.get("slot") == "Weapon 2" and "Shield" in c.get("raw", "")
                                                        for c in changes)]
    return options


BUFF_SKILLS = ["Hatred", "Anger", "Wrath", "Zealotry", "Malevolence", "Pride", "Haste", "Grace", "Determination", "Discipline",
               "Precision", "Purity of Elements", "Herald of Ash", "Herald of Ice", "Herald of Thunder", "Herald of Agony",
               "Herald of Purity", "War Banner", "Dread Banner", "Defiance Banner", "Arctic Armour", "Tempest Shield",
               "Flesh and Stone", "Vitality", "Enduring Cry", "Blood Rage",  # Enduring Cry: endurance charges (inferred)
               # permanent buffs with a cost PoB models (v15): Righteous Fire burns the player (net regeneration, see
               # recovery()), Pact of Beidat reserves life, Blood and Sand reserves mana. The real builds of the v13
               # benchmark used them: Storm Call +41% DPS from Righteous Fire, Reave +15% from Blood and Sand.
               # Vaal skills are not offered: PoB counts their buff as always up (decision 2026-11-27).
               "Righteous Fire", "Righteous Fire of Arcane Devotion", "Pact of Beidat", "Blood and Sand"]
# Buffs that give the same buff in the game (a transfigured gem and its original): one of each set at most. PoB adds
# both (Storm Call / Hierophant with both Righteous Fires: 159% of the author's DPS, v15 check), the game does not.
EXCLUSIVE_BUFFS = [{"Righteous Fire", "Righteous Fire of Arcane Devotion"}]

# Utility skills, with how many a build uses. PoB counts each as always up, so only those where that is fair:
# - guard: Steelskin / Molten Shell absorb a hit (cast before a boss's big hit); one guard at a time in the game.
#   Immortal Call is left out (a very short buff that PoB would count as permanent), as are movement skills such as
#   Phase Run (a short buff fed by frenzy charges).
# - golem: one golem (the game's limit without special items); its buff to the player counts.
# - warcries: PoB averages exerted attacks over the warcry's cooldown (Config "warcryMode": average).
UTILITY = [("guard", ["Steelskin", "Molten Shell"], 1),
           ("golem", ["Summon Stone Golem", "Summon Flame Golem", "Summon Ice Golem", "Summon Lightning Golem",
                      "Summon Chaos Golem", "Summon Carrion Golem"], 1),
           ("warcry", ["Ancestral Cry", "Infernal Cry", "Intimidating Cry", "Rallying Cry", "Seismic Cry", "Battlemage's Cry",
                       "General's Cry"], 3)]


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
def with_enchant(raw, line):
    """The same item with one enchantment (an anoint on an amulet, a labyrinth enchant on a helmet) instead of any
    it had: PoB reads it as an implicit line marked {enchant}."""
    lines = [x for x in raw.splitlines() if not x.startswith("{enchant}")]
    i = next(k for k, x in enumerate(lines) if x.startswith("Implicits:"))
    count = int(lines[i].split(":")[1]) - sum(1 for x in raw.splitlines() if x.startswith("{enchant}"))
    return "\n".join(lines[:i] + [f"Implicits: {count + 1}", "{enchant}" + line] + lines[i + 1:])


# A unique replacing a template rare loses the rare's resistances, attributes and enchantments. Players get those
# back by re-rolling other gear (and anoint / enchant the unique), so they stay, as Config custom modifiers in a block
# of this name; the rare's life is not kept - that is the price of the unique.
MOVED_BLOCK = "Generator: kept from replaced rares"
MOVED_LINE = re.compile(r"Resistance|to (Strength|Dexterity|Intelligence|all Attributes)|^\{enchant\}")


def moved_lines(raw):
    return [x.replace("{enchant}", "") for x in (raw or "").splitlines() if MOVED_LINE.search(x)]


PROFILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "unique_profiles.json")


def worn_profile(build_id):
    """(unique, profile) of a library build's worn unique that has a build-around profile, or (None, None)."""
    if not build_id:
        return None, None
    db = library.connect()
    for (title,) in db.execute("SELECT title FROM items WHERE build_id = ? AND rarity = 'UNIQUE'", (build_id,)):
        prof = unique_profile(title)
        if prof:
            return title, prof
    return None, None


def unique_profile(name):
    """The build-around profile of a unique (tools/data/unique_profiles.json), or None."""
    with open(PROFILES, encoding="utf-8") as f:
        profiles = json.load(f)
    return profiles.get(name)


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
# Raise Spectre: every monster PoB has (src/Data/Spectres.lua, 268) is tried with its default skill; the best
# SPECTRE_SHORTLIST are then tried with each of their skills. PoB counts the chosen skill as the only one the monster
# uses, without cooldowns or AI (how often it really uses it) - a ceiling, to be checked in play.
SPECTRE_SHORTLIST = 15
GUIDE_TOP = 15
GUIDE_EXPLORE = 5


# Score terms added in version 11 (2026-11-26, with the user): chaos resistance under CHAOS_TARGET costs CHAOS_PENALTY
# per point; recovery (life and energy shield regeneration, half of leech and life on hit, which need hitting) as % of
# the pool per second counts as ln(1 + %) x RECOVERY_WEIGHT - it is what carries a build through damage over time.
CHAOS_TARGET = 60
CHAOS_PENALTY = 0.005  # 0.01 made a life build take Chaos Inoculation just to drop the penalty (2026-11-26)
# Below 0 the build is not playable for mapping (the benchmark's floor): every point under 0 costs as much as a point of
# uncapped fire / cold / lightning (v17). The soft term above still applies between 0 and CHAOS_TARGET.
# 0 was chosen by the user from a v17 comparison of 0 / 30 / 60: higher floors cost five of the ten templates life or DPS.
CHAOS_FLOOR = 0
CHAOS_FLOOR_PENALTY = 0.05
# Life + energy shield a mapping build needs (the benchmark's floor); every point below costs LIFE_FLOOR_PENALTY. 0.002 a
# point: 100 life short costs 0.2, about 16 times what 100 life is worth through ln(EHP), so it is a floor, not a weight.
LIFE_FLOOR = 4000
# POB_LIFE_FLOOR_PENALTY: experiment only (benchmark v19 compares strengths for the user to choose from)
LIFE_FLOOR_PENALTY = float(os.environ.get("POB_LIFE_FLOOR_PENALTY", "0.002"))
RECOVERY_WEIGHT = 0.2
RECOVERY_POOL_MIN = 1000


def sustain(m, hit_share=0.5):
    """(net recovery per second, pool): regeneration minus the build's own degeneration (PoB's NetLifeRegen /
    NetEnergyShieldRegen: Righteous Fire, Blood Rage, Annihilation's Approach... - the gross LifeRegenRecovery when
    PoB gives no net value), plus hit_share of leech and life on hit, which need hitting."""
    # at least RECOVERY_POOL_MIN: a tiny pool (life 1 and no energy shield) would make any regeneration look huge
    pool = max((m.get("Life") or 0) + (m.get("EnergyShield") or 0), RECOVERY_POOL_MIN)
    life = m.get("NetLifeRegen") if m.get("NetLifeRegen") is not None else (m.get("LifeRegenRecovery") or 0)
    es = m.get("NetEnergyShieldRegen") if m.get("NetEnergyShieldRegen") is not None else (m.get("EnergyShieldRegenRecovery") or 0)
    per_second = life + es + hit_share * ((m.get("LifeLeechGainRate") or 0) + (m.get("EnergyShieldLeechGainRate") or 0) + (m.get("LifeOnHitRate") or 0))
    return per_second, pool


def recovery(m):
    per_second, pool = sustain(m)
    return math.log(1 + max(per_second, 0) / pool * 100)


def unsustainable(m):
    """Penalty for a build whose own degeneration beats its recovery even while hitting (leech and life on hit in
    full: to live it must keep attacking) - v15. 1 (the same as losing 63% of the DPS) plus the rate: a build losing
    10% of its life a second is not playable, whatever it deals. Righteous Fire on a build without the regeneration
    for it, or Annihilation's Approach without leech, land here."""
    per_second, pool = sustain(m, hit_share=1.0)
    return 1 + math.log(1 - per_second / pool * 100) if per_second < 0 else 0.0


TIE = 1e-9  # score gains closer than this count as equal (v16: the first of the sorted candidates is kept)
# Tree swap (v18): per pass the SWAP_TRIALS allocated nodes cheapest to remove are tried; the freed points are spent
# with the gains measured while the tree grew (SWAP_SHORTLIST best known candidates, SWAP_UNTRIED new ones a round)
SWAP_PASSES = 3
SWAP_TRIALS = 5
SWAP_SHORTLIST = 16
SWAP_UNTRIED = 8


def log(*args):
    print(*args, flush=True)


class Generator:
    def __init__(self, skill, ascendancy, focus="balanced", level=95, name=None, infer=True, gear_from=None, archetype=None,
                 guided=False, seed=None, max_uniques=0, build_around=None, spectre=None):
        self.skill, self.ascendancy, self.level = skill, ascendancy, level
        self.guided = guided
        self.rng = random.Random(seed)
        self.weights, self.guide = {}, None
        self.jewel = None  # the template jewel kind that suits this build best (found at the first socket)
        self.moved = {}  # slot -> lines of the replaced rare kept as custom modifiers (see MOVED_BLOCK)
        self.uniques = {}  # slot -> unique worn
        # Uniques are opt-in (--uniques N): tested 2026-11-25, with no limit every slot became a unique and DPS tripled,
        # from template rares that are plain, league-only items and uniques whose conditions PoB counts as always met
        # (e.g. Flame-Touched without its fire damage taken) - and screening all of them takes minutes per run
        self.max_uniques = max_uniques
        # --build-around: a unique worn from the start, with its profile's gear changes, so the whole search builds
        # around it (a unique added at the end is only ever a stat stick)
        self.around = build_around
        self.spectre_name = spectre  # --spectre: raise this monster instead of searching
        self.spectre_table = []  # (score, DPS, monster, skill) of the best spectres tried
        self.profile = unique_profile(build_around) if build_around else None
        if build_around and not self.profile:
            raise SystemExit(f"no build-around profile for {build_around!r} in {PROFILES}")
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
        self.resists_later = False
        self.quiet = False  # accept() without a log line (tree swap trials, v18)
        self.tree_known = {}  # candidate id -> (gain per point, name, cost) measured while the tree grew (v18)

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
        ignored = set(self.profile.get("ignoreResistPenalty", [])) if self.profile else set()
        for res in ("FireResist", "ColdResist", "LightningResist"):
            if res not in ignored and not self.resists_later:
                p += max(0, 75 - (m.get(res) or 0)) * 0.05
        # chaos: softer than the elements (real builds 55-85%, gear rarely has room); none when immune (Chaos Inoculation,
        # ChaosMaximumHitTaken is nil). Below CHAOS_FLOOR it is hard, like the elements, and like them it waits for the
        # tree while supports are chosen (resists_later); a profile may list ChaosResist in ignoreResistPenalty
        if m.get("ChaosMaximumHitTaken") and "ChaosResist" not in ignored:
            chaos = m.get("ChaosResist") or 0
            p += max(0, CHAOS_TARGET - chaos) * CHAOS_PENALTY
            if not self.resists_later:
                p += max(0, CHAOS_FLOOR - chaos) * CHAOS_FLOOR_PENALTY
        # life + energy shield below the playable floor (v19); a constant offset while nothing changes the pool, so the
        # early steps (supports, ascendancy) compare as before, and the tree is drawn to life until the floor is met
        p += max(0, LIFE_FLOOR - (m.get("Life") or 0) - (m.get("EnergyShield") or 0)) * LIFE_FLOOR_PENALTY
        # before the tree, missing attributes are left to the tree (a curse needing Int would never be tried otherwise)
        p += (m.get("attributeShortfall") or 0) * (0 if self.attributes_later else 0.02)
        p += unsustainable(m)
        if (m.get("ManaUnreserved") if m.get("ManaUnreserved") is not None else 0) < 0:
            p += 5
        if (m.get("LifeUnreserved") if m.get("LifeUnreserved") is not None else 1) < 1:
            p += 5
        if (m.get("passivePointsUsed") or 0) > (m.get("passivePointsAvailable") or 999):
            p += 10
        return p

    def defence(self, m):
        """The defence part of the score: (ln EHP + ln smallest max hit) / 2 + recovery."""
        hits = [m.get(k) for k in ("PhysicalMaximumHitTaken", "FireMaximumHitTaken", "ColdMaximumHitTaken", "LightningMaximumHitTaken",
                                   "ChaosMaximumHitTaken")]
        hits = [h for h in hits if h]  # None = immune (e.g. chaos with Chaos Inoculation)
        defence = (math.log(max(m.get("TotalEHP") or 1, 1)) + math.log(max(min(hits) if hits else 1, 1))) / 2
        return defence + RECOVERY_WEIGHT * recovery(m)

    def score(self, m):
        return math.log(max(self.dps(m), 1)) + self.weight * self.defence(m) - self.penalty(m)

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
            # equal gains (within TIE) keep the earlier candidate: the lists are sorted, so this is reproducible
            if gain > 1e-6 and (best is None or gain > best[2] + TIE):
                best = (move, r["metrics"], gain)
        return best, res

    def accept(self, step, move, metrics, note=""):
        self.state.extend(move)
        self.current = metrics
        self.history.append({"step": step, "move": move, "note": note, "dps": self.dps(metrics), "score": self.score(metrics)})
        if not self.quiet:
            log(f"  [{step}] {note or describe(move)} -> DPS {self.dps(metrics):,.0f}, life {metrics.get('Life')}, "
                f"phys max hit {metrics.get('PhysicalMaximumHitTaken')}, score {self.score(metrics):.3f}")

    # --- steps -------------------------------------------------------------------------------------------------------
    def create(self):
        if self.gear_from:
            # the reference build's own items, empty tree, only the main skill
            xml, name, build_id = library.resolve(self.gear_from)
            # the author wears a unique with a profile (e.g. Doryani's Prototype): score as that profile says
            worn, prof = worn_profile(build_id)
            if prof:
                self.profile = prof
                log(f"  the author wears {worn}: scored with its profile (tools/data/unique_profiles.json)")
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
        bases = (self.profile or {}).get("armourBases") or self.attribute  # a build-around unique may ask for armour
        if self.archetype in DEFENCES:
            bases = DEFENCES[self.archetype].get("bases") or bases
        armour, _ = armour_set(bases, self.archetype)
        self.xml = r["xml"]
        self.state = [{"type": "item_equip", "slot": slot, "raw": raw} for slot, raw in armour.items()]
        if self.profile:
            self.wear_around()
        self.current = self.try_all([[]])[0]["metrics"]
        log(f"{r['class']} / {r['ascendancy']}, {r['skill']} ({', '.join(k for k in ('attack', 'spell', 'minion') if self.info[k])})"
            + (f", built around {self.around}" if self.around else ""))

    def wear_around(self):
        """Put on the build-around unique (keeping the replaced rare's resistances, like any unique) and change the
        template rares as its profile says (e.g. Doryani's Prototype: rings with negative lightning resistance)."""
        prof = self.profile
        tags = set(weightlib.gem_tags().get(self.skill, set()))
        missing = [t for t in prof.get("skillTags", []) if t not in tags]
        if missing:
            log(f"  note: {self.skill} has no {', '.join(missing)} tag - {self.around} may not suit it")
        for slot, lines in prof.get("gear", {}).items():
            raw = self.worn(slot)
            for old, new in lines.items():
                raw = raw.replace(old, new)
            self.state.append({"type": "item_equip", "slot": slot, "raw": raw})
        self.state += self.unique_move(prof["slot"], self.around)
        self.moved.setdefault(prof["slot"], moved_lines(self.worn_before_unique(prof["slot"])))
        self.uniques[prof["slot"]] = self.around

    def worn_before_unique(self, slot):
        raws = [c.get("raw") for c in self.state if c["type"] == "item_equip" and c["slot"] == slot and c.get("raw")]
        return raws[-1] if raws else None

    def pick_weapon(self):
        self.step = "weapon"
        options = weapon_options(self.info, self.attribute, self.archetype)
        res = self.try_all([changes for _, changes in options])
        ranked = sorted(((self.score(r["metrics"]), label, changes, r["metrics"]) for (label, changes), r in zip(options, res)
                         if "metrics" in r), key=lambda x: -x[0])
        if not options:  # a block archetype for a skill with no shield setup (two-handed, dual wield)
            self.weapon = None
            return
        if not ranked:
            raise SystemExit("no weapon setup could be evaluated: " + "; ".join(r.get("error", "") for r in res))
        _, label, changes, metrics = ranked[0]
        self.weapon = label
        self.accept("weapon", changes, metrics, f"weapon: {label}")

    def seed_defence(self):
        """A defence archetype's buffs, keystones and flasks, taken before the search (it may still swap a flask)."""
        d = DEFENCES.get(self.archetype)
        if not d:
            return
        self.step = "defence"
        move = [{"type": "group_add", "gems": [b]} for b in d.get("buffs", [])]
        move += [{"type": "passive_add", "node": k} for k in d.get("keystones", [])]
        move += [{"type": "item_equip", "slot": slot, "unique": name} for slot, name in d.get("flasks", {}).items()]
        if move:
            r = self.try_all([move])[0]
            if "metrics" not in r:
                raise SystemExit(f"archetype {self.archetype}: {r.get('error')}")
            self.accept("defence", move, r["metrics"], f"defence {self.archetype}: " + ", ".join(
                c.get("gems", [None])[0] or c.get("node") or c.get("unique") for c in move))

    def pick_spectre(self):
        """Raise Spectre raises nothing until a monster is chosen: try them all, then each skill of the best ones."""
        if not self.skill.startswith("Raise Spectre"):
            return
        self.step = "spectre"
        cands = WORKER.call("candidates", dict(self.params(), changes=self.state))["spectres"]
        if self.spectre_name:
            cands = [c for c in cands if c["name"].lower() == self.spectre_name.lower()]
            if not cands:
                raise SystemExit(f"no spectre named {self.spectre_name!r}")
        moves = [[{"type": "spectre", "id": c["id"]}] for c in cands]
        res = self.try_all(moves)
        first = sorted(((self.score(r["metrics"]), i) for i, r in enumerate(res) if "metrics" in r), reverse=True)
        found = []
        for _, i in first[:SPECTRE_SHORTLIST]:
            skills = res[i]["metrics"].get("minionSkills") or []
            usable = [k for k, n in enumerate(skills) if "ultimate" not in n.lower()]
            subs = [moves[i] + [{"type": "minion_skill", "skill": k + 1}] for k in usable] or [moves[i]]
            for move, r in zip(subs, self.try_all(subs)):
                if "metrics" in r:
                    skill = skills[move[1]["skill"] - 1] if len(move) > 1 else "default"
                    found.append((self.score(r["metrics"]), self.dps(r["metrics"]), cands[i]["name"], skill, move, r["metrics"]))
        if not found:
            return
        found.sort(key=lambda x: -x[0])
        seen = set()
        for sc, dps, name, skill, _, _ in found:  # best skill per monster, for the report
            if name not in seen:
                seen.add(name)
                self.spectre_table.append((sc, dps, name, skill))
        _, _, name, skill, move, metrics = found[0]
        self.accept("spectre", move, metrics, f"spectre: {name} using {skill}")

    def pick_minion_skill(self):
        """A minion with several skills: PoB starts with the first one the minion may use, which can deal no damage
        (Summon Reaper's is Consume, a heal). Try each and keep the best."""
        skills = self.current.get("minionSkills") or []
        if len(skills) < 2:
            return
        self.step = "minion skill"
        # an "Ultimate" is a cooldown special (Summon Reaper): PoB would count it as the minion's only attack
        usable = [i for i, name in enumerate(skills) if "ultimate" not in name.lower()]
        found = self.best([[{"type": "minion_skill", "skill": i + 1}] for i in usable], self.current)
        if found and found[0]:
            move, metrics, _ = found[0]
            self.accept("minion skill", move, metrics, f"minion skill: {skills[move[0]['skill'] - 1]}")

    def refresh_support_pool(self):
        """The supports PoB says can support the skill as it is linked now. Some only qualify once another support is
        linked (Overloaded Intensity needs Intensify: Storm Call / Hierophant benchmark v13, +88% DPS never tried), so
        the pool is read again after every support taken and before the final swaps."""
        cands = WORKER.call("candidates", dict(self.params(), changes=self.state))
        self.support_pool = [s for s in cands["supports"] if not DELIVERY.search(s)]
        return cands

    def pick_supports(self, count=5):
        self.step = "support"
        cands = self.refresh_support_pool()
        self.points = cands["points"]
        self.links = []
        # supports are chosen without the resistance penalty: a support only moves resistances through item mechanics
        # (e.g. The Untouched Soul, +12% per empty white socket: every support filled it, cost 1.2 score before the tree
        # and none was taken - Smite / Gladiator at 11% of the author's DPS, benchmark v12). The tree fixes resistances.
        self.resists_later = True
        try:
            self._pick_supports(pool_count=count)
        finally:
            self.resists_later = False

    def _pick_supports(self, pool_count):
        for _ in range(pool_count):
            pool = self.narrow("support", [s for s in self.support_pool if s not in self.links])
            found = self.best([[{"type": "gem_add", "group": 1, "gem": s}] for s in pool], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            self.links.append(move[0]["gem"])
            self.accept("support", move, metrics, f"support: {move[0]['gem']}")
            self.refresh_support_pool()

    def pick_ascendancy(self):
        self.step = "ascendancy"
        while True:
            a = WORKER.call("ascendancy_candidates", dict(self.params(), changes=self.state))
            free = a["available"] - a["used"]
            cands = sorted((c for c in a["candidates"] if c["cost"] <= free), key=lambda c: c["id"])
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

    def grow_tree(self, max_path=10, shortlist=30, untried_batch=80, known=None):
        self.step = "tree"
        known = {} if known is None else known  # node id -> (gain per point, name, cost) from the last time it was tried
        while True:
            cands = WORKER.call("candidates", dict(self.params(), changes=self.state, maxPath=max_path))
            used, available = self.current.get("passivePointsUsed", 0), cands["points"][1]
            free = available - used
            passives = [p for p in cands["passives"] if p["cost"] <= free
                        and not (self.archetype == "crit" and p["name"] in NEVER_CRIT)
                        and p["name"] not in DEFENCES.get(self.archetype, {}).get("never", [])
                        and not (p["name"] == "Chaos Inoculation" and self.archetype != "es")]  # life gear: CI only with es
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
            # cheapest first, then by id: fixes which 80 untried candidates are tried when there are more (v16)
            passives.sort(key=lambda p: (p["cost"], str(p["id"])))
            # Re-try the best-known candidates and every candidate never tried
            ranked = sorted(passives, key=lambda p: -(known.get(p["id"], (math.inf,))[0]))
            untried = [p for p in ranked if p["id"] not in known]
            if self.weights.get("passive"):  # the 80 never tried: best weights first (some at random, to keep learning)
                w = self.weights["passive"]
                by_weight = sorted(untried, key=lambda p: -w.get(str(p["id"]), 0.5))
                head, rest = by_weight[:70], by_weight[70:]
                untried = head + self.rng.sample(rest, min(10, len(rest)))
            batch = untried[:untried_batch] + [p for p in ranked if p["id"] in known][:shortlist]
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
        self.tree_known = known

    def retune_tree(self):
        """Once the tree is full: the allocated notables and keystones cheapest to remove (score lost per point freed)
        are each taken out in turn and their points spent again on the best candidates of the finished build; the swap
        is kept when the build scores higher (v18). The greedy growth commits to a node for the gain it had when the
        tree was small, and it had no way back: a probe of v17 showed every candidate is tried in every round, so what
        the search lacked was not more candidates. The freed points are spent with the gains measured while the tree
        grew (tree_known), so a trial costs a few dozen tries, not a full round of 80."""
        self.step = "tree swap"
        protected = set(DEFENCES.get(self.archetype, {}).get("keystones", []))  # the archetype's own keystones stay
        for _ in range(SWAP_PASSES):
            cands = WORKER.call("candidates", dict(self.params(), changes=self.state, maxPath=10))
            removable = [r for r in cands.get("removable", []) if r["name"] not in protected]
            if not removable:
                return
            # prune: the travel nodes left as a dead end go too (PoB alone frees one point and strands the path)
            res = self.try_all([[{"type": "passive_remove", "node": r["id"], "prune": True}] for r in removable])
            base, used = self.score(self.current), self.current.get("passivePointsUsed", 0)
            # cheapest removals per point freed first; ties by id, so the order is reproducible
            losses = sorted(((base - self.score(m["metrics"])) / max(used - m["metrics"].get("passivePointsUsed", used), 1),
                             str(r["id"]), dict(r, frees=used - m["metrics"].get("passivePointsUsed", used)), m["metrics"])
                            for r, m in zip(removable, res) if "metrics" in m)
            saved = (list(self.state), self.current, list(self.history), dict(self.tree_known))
            best = None
            for _, _, r, removed in losses[:SWAP_TRIALS]:
                self.state = saved[0] + [{"type": "passive_remove", "node": r["id"], "prune": True}]
                self.current, self.history = removed, []
                self.quiet = True
                try:
                    self.grow_tree(untried_batch=SWAP_UNTRIED, shortlist=SWAP_SHORTLIST, known=dict(saved[3]))
                finally:
                    self.quiet = False
                    self.step = "tree swap"
                gain = self.score(self.current) - base
                if gain > TIE and (best is None or gain > best[0] + TIE):
                    best = (gain, r, removed, list(self.state), self.current, list(self.history))
            self.state, self.current, self.history, self.tree_known = saved
            if best is None:
                return
            gain, r, removed, state, metrics, steps = best
            self.state, self.current = state, metrics
            self.history.append({"step": "tree swap", "move": [{"type": "passive_remove", "node": r["id"], "prune": True}],
                                 "note": f"tree swap: -{r['name']} ({r['frees']} points)", "dps": self.dps(removed), "score": self.score(removed)})
            self.history.extend(steps)
            added = " / ".join(s["note"].split(" (")[0].split(": ", 1)[-1] for s in steps) or "nothing"
            log(f"  [tree swap] -{r['name']} ({r['frees']} points) +{added} -> score {base:.3f} -> {self.score(metrics):.3f}, "
                f"DPS {self.dps(metrics):,.0f}, life {metrics.get('Life')}")

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
        present = {c.get("gems", [None])[0] for c in self.state if c["type"] == "group_add"} | {self.skill}
        # the main skill is not also a buff; of an exclusive set, only one (EXCLUSIVE_BUFFS)
        taken = lambda s: s in present or any(s in group and present & group for group in EXCLUSIVE_BUFFS)
        pool = [s for s in BUFF_SKILLS if not taken(s)]
        while pool:
            found = self.best([[{"type": "group_add", "gems": [s]}] for s in pool], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            present.add(move[0]["gems"][0])
            pool = [s for s in pool if not taken(s)]
            self.accept("buff", move, metrics, f"aura/buff: {move[0]['gems'][0]}")

    def add_utility(self):
        """Guard skill, golem and warcries, each kind up to its limit, while they improve the score."""
        present = {c.get("gems", [None])[0] for c in self.state if c["type"] == "group_add"}
        for kind, names, limit in UTILITY:
            self.step = kind
            have = [n for n in names if n in present]
            pool = [n for n in names if n not in present]
            while pool and len(have) < limit:
                found = self.best([[{"type": "group_add", "gems": [n]}] for n in pool], self.current)
                if not found or not found[0]:
                    break
                move, metrics, _ = found[0]
                name = move[0]["gems"][0]
                pool.remove(name)
                have.append(name)
                self.accept(kind, move, metrics, f"{kind}: {name}")

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
                out[c["slot"]] = c["raw"].splitlines()[1] if c.get("raw") else c["unique"]
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

    def worn(self, slot):
        """The raw text of the item in a slot, as the current state has it."""
        raw = None
        for c in self.state:
            if c["type"] == "item_equip" and c["slot"] == slot:
                raw = c.get("raw")
        return raw

    def pick_enchants(self):
        """An anoint on the amulet (any notable with an oil recipe) and the main skill's helmet enchant."""
        cands = WORKER.call("candidates", dict(self.params(), changes=self.state))
        for step, slot, lines, label in (("anoint", "Amulet", [f"Allocates {n}" for n in cands.get("anoints", [])], "anoint"),
                                         ("enchant", "Helmet", cands.get("helmetEnchants", []), "helmet enchant")):
            raw = self.worn(slot)
            if not raw or not lines:
                continue
            self.step = step
            found = self.best([[{"type": "item_equip", "slot": slot, "raw": with_enchant(raw, line)}] for line in lines], self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                line = next(x for x in move[0]["raw"].splitlines() if x.startswith("{enchant}"))[len("{enchant}"):]
                self.accept(step, move, metrics, f"{label}: {line}")

    def unique_move(self, slot, name):
        moved = dict(self.moved)
        if slot not in moved:
            moved[slot] = moved_lines(self.worn(slot))
        text = "\n".join(line for lines in moved.values() for line in lines)
        return [{"type": "item_equip", "slot": slot, "unique": name}, {"type": "custom_block", "title": MOVED_BLOCK, "text": text}]

    def pick_uniques(self, keep=3):
        """Every unique that fits a slot (weapons: the types the skill uses) is tried once; the best few per slot are
        then added one at a time while they improve the score, up to self.max_uniques (--uniques)."""
        if not self.max_uniques:
            return
        cands = WORKER.call("candidates", dict(self.params(), changes=self.state))
        self.step = "unique screen"
        base = self.score(self.current)
        shortlist = []
        for slot, names in sorted(cands.get("uniques", {}).items()):  # a JSON object: its order is PoB's pairs() order
            if not names or slot in self.uniques:
                continue
            res = self.try_all([self.unique_move(slot, n) for n in names])
            ranked = sorted(((self.score(r["metrics"]) - base, n) for n, r in zip(names, res) if "metrics" in r), reverse=True)
            shortlist += [(slot, n) for g, n in ranked[:keep] if g > 1e-6]
        self.step = "unique"
        while shortlist and len(self.uniques) < self.max_uniques:
            found = self.best([self.unique_move(slot, n) for slot, n in shortlist], self.current)
            if not found or not found[0]:
                break
            move, metrics, _ = found[0]
            slot, name = move[0]["slot"], move[0]["unique"]
            self.moved.setdefault(slot, moved_lines(self.worn(slot)))
            self.uniques[slot] = name
            self.accept("unique", move, metrics, f"unique: {slot} -> {name}")
            # a two-handed weapon empties the off-hand slot; a unique in one ring slot can still go in the other
            shortlist = [(s, n) for s, n in shortlist if s != slot and n != name]

    def pick_pantheon(self):
        self.step = "pantheon"
        for key, gods in PANTHEON.items():
            found = self.best([[{"type": "config_set", "key": key, "value": g}] for g in gods], self.current)
            if found and found[0]:
                move, metrics, _ = found[0]
                self.accept("pantheon", move, metrics, f"pantheon: {move[0]['value']}")

    def retune_supports(self, passes=3):
        """Each support against every other the skill can take, now that the tree is known. Repeated while a swap
        improves the score (at most `passes` rounds): one swap changes what the others are worth (Arcane Surge ->
        Awakened Empower raised Storm Call / Assassin from 5M to 122M DPS in v13, and nothing before it was re-tried)."""
        self.step = "support swap"
        for _ in range(passes):
            self.refresh_support_pool()
            swapped = False
            for gem in list(self.links):
                pool = self.narrow("support", [s for s in self.support_pool if s not in self.links])
                moves = [[{"type": "gem_replace", "group": 1, "gem": gem, "with": s}] for s in pool]
                found = self.best(moves, self.current)
                if found and found[0]:
                    move, metrics, _ = found[0]
                    new = move[0]["with"]
                    self.links[self.links.index(gem)] = new
                    self.accept("support swap", move, metrics, f"support: {gem} -> {new}")
                    self.refresh_support_pool()
                    swapped = True
            if not swapped:
                break

    def run(self):
        started = time.time()
        self.create()
        self.load_weights()
        self.recorder = simlog.Recorder("generate", skill=self.skill, ascendancy=self.ascendancy, cls=self.class_name, focus=self.focus,
                                        gear=f"from {self.gear_from}" if self.gear_from else
                                        (f"template around {self.around}" if self.around else gear_label(self.archetype)), skill_info=self.info,
                                        versions=WORKER.call("ping", {}), generator=GENERATOR_VERSION,
                                        guide=self.guide)
        # with the author's items (--gear-from) and an empty tree, missing attributes are left to the tree: every support
        # raised the shortfall penalty more than its damage, and none was taken (2026-11-26). Template gear keeps the
        # penalty from the start (deferring it there lost Glacial Hammer 0.68 score in benchmark v12)
        self.attributes_later = bool(self.gear_from)
        if not self.gear_from:
            self.pick_weapon()
            if self.weapon is None:
                self.elapsed = time.time() - started
                self.outcome = "not suited"
                log(f"archetype {self.archetype} does not suit {self.skill}: no weapon setup with a shield")
                self.recorder.finish(self.current, outcome=self.outcome)
                return None
        self.pick_spectre()
        self.pick_minion_skill()
        self.pick_supports()
        if self.dps(self.current) <= 0:
            # nothing the search does can be measured (PoB calculates no damage for this skill with this setup):
            # stop instead of building a tree for defence only
            self.elapsed = time.time() - started
            self.outcome = "no damage"
            self.recorder.finish(self.current, outcome=self.outcome)
            return None
        self.pick_ascendancy()
        self.seed_defence()
        # auras and curses before the tree, so the tree sees what they reserve and add (a keystone such as Blood
        # Magic looked free while no aura reserved life yet), then again once the tree is known
        self.attributes_later = True
        self.add_buffs()
        self.add_utility()
        self.add_debuffs()
        self.pick_flasks()
        self.attributes_later = False
        self.current = self.try_all([[]])[0]["metrics"]  # same build, scored again with the attribute penalty
        self.grow_tree()
        self.retune_tree()
        self.add_buffs()
        self.add_utility()
        self.add_debuffs()
        self.pick_flasks()  # swaps, now that the tree is known
        self.retune_jewels()
        self.pick_enchants()
        self.pick_uniques()
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
            "Template rare gear at a mid budget (life, a local defence, two resistances, an attribute; T2-T3 weapon rolls, "
            "at most 3 prefixes and 3 suffixes) - an assumption, not real items."
            + (f" Archetype {ARCHETYPES[self.archetype]}." if self.archetype else ""),
            "Curses, marks and exposure count as always applied (how they are applied is not modelled).",
            (f"Built around {self.around}: " + " ".join(self.profile.get("why", [])) +
             f" Gear changed for it: {json.dumps(self.profile.get('gear', {}))}." if self.profile else ""),
            "Utility flasks (quality 20, no mods) count as always on; flask slot 1 is left for a life flask.",
            "A guard skill counts as up when hit; a golem's buff counts; warcries count averaged over their cooldown. "
            "Immortal Call and movement skills are not used.",
            "The amulet's anoint and the helmet's labyrinth enchant are chosen for the build.",
            "Tree jewel sockets hold template rare jewels (life plus three good rolls of one kind); no cluster, abyss or unique jewels.",
            "Power, frenzy and endurance charges count at their maximum when the build has a source (none against a lone boss "
            "if every source needs kills).",
            (f"Search guided by {self.guide}: supports tried in weight order (top {GUIDE_TOP} + {GUIDE_EXPLORE} at random)."
             if self.guide else "Search not guided: every candidate tried."),
            "No cluster or abyss jewels yet. Sockets and gem colours are not checked.",
            ("A unique replacing a template rare keeps the rare's resistances, attributes and enchantment (as Config custom "
             "modifiers: other gear would carry them) but not its life. Check each unique's conditions in PoB."
             if self.max_uniques else "No unique items (--uniques N to try some)."),
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
        if self.spectre_table:
            lines += ["", "## Spectres tried (best skill each; PoB counts that skill as always used - test in play)", "",
                      "| Spectre | Skill | DPS |", "|---|---|---|"]
            lines += [f"| {n} | {k} | {d:,.0f} |" for _, d, n, k in self.spectre_table]
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
    ap.add_argument("--archetype", choices=[a for a in ARCHETYPES if a],
                    help="crit: weapon and amulet with crit rolls, so the search builds for crit; armour / block / evasion / es / "
                         "takenas: a defence archetype (gear, buffs, keystones) the search builds from")
    ap.add_argument("--build-around", metavar="UNIQUE",
                    help="wear this unique from the start and build around it (profile in tools/data/unique_profiles.json)")
    ap.add_argument("--uniques", type=int, default=0, metavar="N",
                    help="experimental: up to N unique items (each checked against the template rare it replaces)")
    ap.add_argument("--guided", action="store_true", help="experimental: try supports in library/weights.db order, only the best "
                                                          f"{GUIDE_TOP} + {GUIDE_EXPLORE} at random")
    ap.add_argument("--spectre", metavar="MONSTER", help="Raise Spectre: raise this monster (PoB name) instead of searching")
    ap.add_argument("--gear-from", help="library build whose items to use (tests the tree and gem search against its author)")
    args = ap.parse_args()
    g = Generator(args.skill, args.ascendancy, args.focus, args.level, args.name, gear_from=args.gear_from, archetype=args.archetype,
                  guided=args.guided, max_uniques=args.uniques,
                  build_around=args.build_around, spectre=args.spectre)
    if g.run() is None:
        if g.outcome == "not suited":
            return
        log(f"\nDPS 0 · no damage: PoB calculates no damage for {args.skill} with weapon '{g.weapon}' - run stopped "
            f"({g.elapsed / 60:.1f} min)")
        return
    path, report, m = g.export()
    if os.environ.get("POB_RESULT_JSON"):  # tools/benchmark.py reads the result from here
        with open(os.environ["POB_RESULT_JSON"], "w", encoding="utf-8") as f:
            json.dump({"metrics": m, "dps": g.dps(m), "score": g.score(m), "defence": g.defence(m), "penalty": g.penalty(m),
                       "build": path, "report": report, "minutes": g.elapsed / 60, "generator": GENERATOR_VERSION}, f)
    log(f"\nDPS {g.dps(m):,.0f} · life {m.get('Life')} · EHP {m.get('TotalEHP'):,.0f} · {g.elapsed / 60:.1f} min")
    log(f"build:  {path}\nreport: {report}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
