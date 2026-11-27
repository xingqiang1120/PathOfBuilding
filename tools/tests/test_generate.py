"""Build generator building blocks (tools/generate.py, worker methods create_build and try).

    python -m unittest tools.tests.test_generate
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import generate  # noqa: E402
from pob_worker import WORKER  # noqa: E402


class GenerateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new = WORKER.call("create_build", {"ascendancy": "Necromancer", "skill": "Kinetic Blast of Clustering", "level": 90})

    def test_create_build(self):
        r = self.new
        self.assertEqual((r["class"], r["ascendancy"]), ("Witch", "Necromancer"))
        self.assertTrue(r["skillInfo"]["attack"])
        self.assertEqual(r["skillInfo"]["weaponTypes"], ["Wand"])
        self.assertGreaterEqual(r["metrics"]["passivePointsAvailable"], 89 + 23)  # level - 1 + quest points (+ tree extras)

    def test_template_gear_caps_resistances(self):
        armour, _ = generate.armour_set("Int")
        weapon = generate.weapon_options(self.new["skillInfo"], "Int")[0][1]
        changes = [{"type": "item_equip", "slot": s, "raw": raw} for s, raw in armour.items()] + weapon
        r = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "candidates": [changes]})[0]
        self.assertIn("metrics", r, r)
        m = r["metrics"]
        for res in ("FireResist", "ColdResist", "LightningResist"):
            self.assertGreaterEqual(m[res], 75)
        self.assertGreater(m["playerDPS"], 0)

    def test_try_undoes_each_candidate(self):
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t"})
        node = c["passives"][0]["id"]
        res = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "candidates": [
            [], [{"type": "passive_add", "node": node}], [{"type": "gem_add", "group": 1, "gem": "Added Fire Damage"}], []]})
        first, added, gem, last = (r["metrics"] for r in res)
        self.assertGreater(added["passivePointsUsed"], 0)
        self.assertEqual(last["passivePointsUsed"], first["passivePointsUsed"])
        self.assertEqual(last["playerDPS"], first["playerDPS"])

    def test_passive_remove_frees_the_path(self):
        # v18 tree swap: PoB alone frees the notable's own point and keeps its path (still connected); with prune the
        # dead-end travel nodes go too, so the whole cost comes back. The worker lists the notable as removable.
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t"})
        node = next(p for p in c["passives"] if p["cost"] >= 3)
        add = [{"type": "passive_add", "node": node["id"]}]
        after = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": add})
        self.assertEqual([str(r["id"]) for r in after["removable"]], [str(node["id"])])
        kept, plain, pruned = (r["metrics"] for r in WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": add, "candidates": [
            [], [{"type": "passive_remove", "node": node["id"]}], [{"type": "passive_remove", "node": node["id"], "prune": True}]]}))
        self.assertEqual(kept["passivePointsUsed"] - plain["passivePointsUsed"], 1)
        self.assertEqual(kept["passivePointsUsed"] - pruned["passivePointsUsed"], node["cost"])
        self.assertEqual(pruned["passivePointsUsed"], self.new["metrics"]["passivePointsUsed"])
        # v19: prune only takes the dead end this removal made. A chain of small nodes that was a dead end already (here:
        # the path left behind by a plain removal) stays when another notable is removed with prune. The other notable's
        # path must not lean on the chain: a path that joins it (or merely touches its tip) makes the chain part of the
        # way to that notable, and removing the notable leaves the whole of it as the new dead end. Since v21 the paths
        # are canonical, so the first notable found this way is always the same one.
        chain = add + [{"type": "passive_remove", "node": node["id"]}]  # node's cost - 1 small nodes, a dead end
        far = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": chain, "maxPath": 10})
        before = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": chain, "candidates": [[]]})[0]["metrics"]["passivePointsUsed"]
        self.assertEqual(before, self.new["metrics"]["passivePointsUsed"] + node["cost"] - 1)
        kept = []
        for other in [p for p in far["passives"] if p["cost"] >= 2 and p["id"] != node["id"]][:40]:
            both, after = (r["metrics"]["passivePointsUsed"] for r in WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": chain, "candidates": [
                [{"type": "passive_add", "node": other["id"]}],
                [{"type": "passive_add", "node": other["id"]}, {"type": "passive_remove", "node": other["id"], "prune": True}]]}))
            self.assertEqual(both - before, other["cost"], other["name"])  # the cost listed is the cost paid (v21)
            if after == before:
                kept.append(other["name"])
                break
        self.assertTrue(kept, "no notable whose path leaves the old dead end alone")

    def test_a_candidate_measures_the_same_in_a_batch_as_alone(self):
        # v21: the generator measures its candidates forty at a time and keeps the metrics of the one it accepts, so
        # a candidate tried after others in the same request must give what it gives alone, and what the saved state
        # gives when it is replayed. Before canonicalPaths, PoB broke the tie between equal-cost paths by the order of
        # its allocated-nodes table, which the earlier candidates had changed: on this tree 16 of 162 candidates
        # measured differently in a batch (other travel nodes for the same cost).
        state = []
        for _ in range(12):
            c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": state, "maxPath": 10})
            cheap = min((p for p in c["passives"] if p["type"] == "Notable"), key=lambda p: (p["cost"], p["id"]))
            state.append({"type": "passive_add", "node": cheap["id"]})
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": state, "maxPath": 10})
        moves = [[{"type": "passive_add", "node": p["id"]}] for p in c["passives"]]
        batch = []
        for i in range(0, len(moves), 40):
            batch.extend(WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": state, "candidates": moves[i:i + 40]}))
        base = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": state, "candidates": [[]]})[0]["metrics"]
        differ = []
        for p, move, b in zip(c["passives"], moves, batch):
            alone = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": state, "candidates": [move]})[0]
            # the metrics of the state with the candidate accepted (replayed, as export does) are the metrics measured
            replayed = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": state + move, "candidates": [[]]})[0]
            if not (alone["metrics"] == b["metrics"] == replayed["metrics"]):
                differ.append(p["name"])
            self.assertEqual(b["metrics"]["passivePointsUsed"] - base["passivePointsUsed"], p["cost"], p["name"])  # the cost listed
        self.assertEqual(differ, [])

    def test_group_replace_swaps_an_aura_and_undoes(self):
        # v20 buff swap: the group that holds one aura holds another instead; a try puts the first one back
        add = [{"type": "group_add", "gems": ["Zealotry"]}]
        res = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "changes": add, "candidates": [
            [], [{"type": "group_replace", "gem": "Zealotry", "with": "Tempest Shield"}], []]})
        first, swapped, last = res
        self.assertIn("group 2: Zealotry -> Tempest Shield", swapped["applied"][0])
        self.assertNotEqual(swapped["metrics"]["ManaUnreserved"], first["metrics"]["ManaUnreserved"])
        self.assertEqual(last["metrics"]["ManaUnreserved"], first["metrics"]["ManaUnreserved"])
        self.assertEqual(last["metrics"]["playerDPS"], first["metrics"]["playerDPS"])
        g = generate.Generator("Kinetic Blast of Clustering", "Necromancer")
        g.state = [{"type": "group_add", "gems": ["Zealotry"]}, {"type": "group_add", "gems": ["Steelskin"]},
                   {"type": "group_replace", "gem": "Zealotry", "with": "Tempest Shield"}]
        self.assertEqual(g.skill_groups(), ["Tempest Shield", "Steelskin"])

    def gear(self, r, attribute="Dex"):
        armour, _ = generate.armour_set(attribute)
        return [{"type": "item_equip", "slot": s, "raw": raw} for s, raw in armour.items()] + \
            generate.weapon_options(r["skillInfo"], attribute)[0][1]

    def test_stages_without_a_source_are_not_counted(self):
        # PoB counts all 10 Blade Vortex blades when no stage count is set, even with no Blade Vortex in the build
        r = WORKER.call("create_build", {"ascendancy": "Assassin", "skill": "Blade Blast of Unloading", "level": 90})
        on, off = (WORKER.call("try", {"xml": r["xml"], "name": "t", "infer": infer, "candidates": [self.gear(r)]})[0]["metrics"]
                   for infer in (True, False))
        stages = [i for i in on["inferred"] if i.get("kind") == "stages"]
        self.assertEqual((stages[0]["value"], stages[0]["maximum"], stages[0]["applied"]), (1, 10, True))
        self.assertLess(on["playerDPS"], off["playerDPS"] / 5)
        # with Blade Vortex in the build the blades exist: PoB's count is kept and reported
        with_bv = self.gear(r) + [{"type": "group_add", "gems": ["Blade Vortex"]}]
        m = WORKER.call("try", {"xml": r["xml"], "name": "t", "candidates": [with_bv]})[0]["metrics"]
        stages = [i for i in m["inferred"] if i.get("kind") == "stages"]
        self.assertFalse(stages[0]["applied"])
        self.assertAlmostEqual(m["playerDPS"], off["playerDPS"], delta=off["playerDPS"] * 0.2)

    def test_dual_wield_skills_get_two_weapons(self):
        r = WORKER.call("create_build", {"ascendancy": "Slayer", "skill": "Dual Strike", "level": 90})
        self.assertTrue(r["skillInfo"]["dualWield"])
        options = generate.weapon_options(r["skillInfo"], "Str")
        self.assertTrue(all(len(ch) == 2 and ch[1]["slot"] == "Weapon 2" and "Shield" not in ch[1]["raw"] for _, ch in options))
        m = WORKER.call("try", {"xml": r["xml"], "name": "t", "candidates": [self.gear(r, "Str")]})[0]["metrics"]
        self.assertGreater(m["playerDPS"], 0)

    def test_skill_list_has_only_damaging_skills(self):
        names = {s["name"] for s in WORKER.call("skill_list", {})["skills"]}
        for gone in ("Flesh Offering", "Convocation", "Raise Spectre"):
            self.assertNotIn(gone, names)
        for kept in ("Raise Zombie", "Arc", "Dual Strike"):
            self.assertIn(kept, names)


    def test_every_curse_and_buff_gem_exists(self):
        names = generate.DEBUFF_SKILLS + generate.BUFF_SKILLS + [n for _, group, _ in generate.UTILITY for n in group]
        res = WORKER.call("try", {"xml": self.new["xml"], "name": "t", "candidates": [[{"type": "group_add", "gems": [g]}] for g in names]})
        self.assertEqual([n for n, r in zip(names, res) if "metrics" not in r], [])

    def test_crit_archetype_gear(self):
        hybrid = generate.weapon_options(self.new["skillInfo"], "Int")[0][1][0]["raw"]
        crit = generate.weapon_options(self.new["skillInfo"], "Int", "crit")[0][1][0]["raw"]
        self.assertIn("37% increased Critical Strike Chance", crit)
        self.assertNotIn("38% increased Critical Strike Chance", hybrid)
        self.assertIn("Global Critical Strike Chance", generate.armour_set("Int", "crit")[0]["Amulet"])
        self.assertEqual(generate.gear_label("crit"), "template crit")

    def test_flasks_count_when_equipped_and_undo(self):
        r = WORKER.call("create_build", {"ascendancy": "Slayer", "skill": "Cleave", "level": 90})
        jade = [{"type": "item_equip", "slot": "Flask 2", "raw": generate.flask_item("Jade Flask")}]
        base, on, after = (x["metrics"] for x in WORKER.call("try", {"xml": r["xml"], "name": "t", "candidates": [[], jade, []]}))
        self.assertGreater(on["Evasion"], base["Evasion"])
        self.assertEqual(after["Evasion"], base["Evasion"])

    def test_charges_need_a_source(self):
        r = WORKER.call("create_build", {"ascendancy": "Slayer", "skill": "Cleave", "level": 90})
        cry = [{"type": "group_add", "gems": ["Enduring Cry"]}]
        res = WORKER.call("try", {"xml": r["xml"], "name": "t", "inferCharges": True, "candidates": [[], cry]})
        flags = [{i["key"]: i["value"] for i in x["metrics"]["inferred"] if i.get("kind") == "config"} for x in res]
        self.assertFalse(flags[0]["useEnduranceCharges"])
        self.assertTrue(flags[1]["useEnduranceCharges"])

    def test_jewel_counts_only_in_an_allocated_socket(self):
        r = WORKER.call("create_build", {"ascendancy": "Slayer", "skill": "Cleave", "level": 90})
        sock = min(WORKER.call("candidates", {"xml": r["xml"], "name": "t", "maxPath": 12})["jewelSockets"], key=lambda j: j["cost"])
        jewel = {"type": "item_equip", "slot": sock["slot"], "raw": generate.JEWELS["Defence"]}
        base, loose, socketed = (x["metrics"] for x in WORKER.call("try", {"xml": r["xml"], "name": "t", "candidates": [
            [], [jewel], [{"type": "passive_add", "node": sock["id"]}, jewel]]}))
        self.assertEqual(loose["FireResist"], base["FireResist"])  # not allocated: the jewel does nothing
        self.assertEqual(socketed["FireResist"], base["FireResist"] + 12)

    def test_enchant_lines_replace_each_other(self):
        armour, _ = generate.armour_set("Str")
        once = generate.with_enchant(armour["Amulet"], "Allocates Eagle Eye")
        twice = generate.with_enchant(once, "Allocates Acuity")
        self.assertIn("Implicits: 2", twice)
        self.assertEqual([x for x in twice.splitlines() if x.startswith("{enchant}")], ["{enchant}Allocates Acuity"])
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t"})
        self.assertIn("Eagle Eye", c["anoints"])

    def test_unique_keeps_the_rares_resistances(self):
        armour, _ = generate.armour_set("Str")
        self.assertEqual(generate.moved_lines(generate.with_enchant(armour["Helmet"], "40% increased Cleave Damage")),
                         ["40% increased Cleave Damage", "+40% to Fire Resistance", "+40% to Cold Resistance",
                          "+35 to Intelligence"])
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": self.gear(self.new, "Int")})
        self.assertNotIn("Natural Hierarchy", c["uniques"]["Amulet"])  # Talisman league only
        self.assertTrue(all(n for n in c["uniques"]["Weapon 1"]))

    def test_defence_archetype_gear(self):
        es, _ = generate.armour_set("Str", "es")
        self.assertIn("Vaal Regalia", es["Body Armour"])  # energy shield bases whatever the class
        self.assertNotIn("to maximum Life", es["Body Armour"])
        self.assertIn("+95 to maximum Energy Shield", es["Body Armour"])
        _, shield = generate.armour_set("Int", "block")
        self.assertIn("Mirrored Spiked Shield", shield)  # a spirit shield cannot roll block
        self.assertIn("+14% Chance to Block", shield)
        self.assertNotIn("+30 to Intelligence", shield)
        r = WORKER.call("create_build", {"ascendancy": "Deadeye", "skill": "Tornado Shot", "level": 90})
        self.assertEqual(generate.weapon_options(r["skillInfo"], "Dex", "block"), [])  # bow only: no shield
        self.assertLess(generate.recovery({"Life": 1000, "LifeRegenRecovery": 10}),
                        generate.recovery({"Life": 1000, "LifeRegenRecovery": 50}))
        # v15: the net regeneration counts when PoB gives it (Righteous Fire burns 20% of life a second here)
        self.assertEqual(generate.recovery({"Life": 1000, "LifeRegenRecovery": 300, "NetLifeRegen": 100}),
                         generate.recovery({"Life": 1000, "LifeRegenRecovery": 100}))
        self.assertEqual(generate.recovery({"Life": 1000, "LifeRegenRecovery": 100, "NetLifeRegen": -100}), 0)
        self.assertEqual(generate.unsustainable({"Life": 1000, "LifeRegenRecovery": 100, "NetLifeRegen": 100}), 0)
        self.assertGreater(generate.unsustainable({"Life": 1000, "LifeRegenRecovery": 100, "NetLifeRegen": -100}), 1)  # 10% a second
        self.assertGreater(generate.unsustainable({"Life": 1000, "NetLifeRegen": -300}),
                           generate.unsustainable({"Life": 1000, "NetLifeRegen": -100}))
        # leech and life on hit (half) can carry a negative net regeneration
        self.assertEqual(generate.unsustainable({"Life": 1000, "NetLifeRegen": -100, "LifeLeechGainRate": 400}), 0)

    def test_build_around_profile(self):
        prof = generate.unique_profile("Doryani's Prototype")
        self.assertEqual(prof["slot"], "Body Armour")
        g = generate.Generator("Storm Call", "Assassin", build_around="Doryani's Prototype")
        g.life_floor_later = False  # v19: as from the tree swap on
        full = {"Life": 4000}  # v19: life + energy shield at the floor
        self.assertEqual(g.penalty(dict(full, FireResist=75, ColdResist=75, LightningResist=-160)), 0)  # lightning ignored
        # v17: chaos below 0 costs like an uncapped element (0.05 a point) on top of the soft term; immune (no max hit) costs nothing
        capped = dict(full, FireResist=75, ColdResist=75, LightningResist=-160, ChaosMaximumHitTaken=5000)
        self.assertAlmostEqual(g.penalty(dict(capped, ChaosResist=0)), 60 * generate.CHAOS_PENALTY)
        self.assertAlmostEqual(g.penalty(dict(capped, ChaosResist=-8)), 68 * generate.CHAOS_PENALTY + 8 * generate.CHAOS_FLOOR_PENALTY)
        self.assertEqual(g.penalty(dict(full, FireResist=75, ColdResist=75, LightningResist=-160, ChaosResist=-60)), 0)  # immune
        # v19: life + energy shield below the floor costs LIFE_FLOOR_PENALTY a point once the tree has grown; energy
        # shield counts; with an author's items the floor may be lower
        immune = {"FireResist": 75, "ColdResist": 75, "LightningResist": -160, "ChaosResist": -60}
        self.assertAlmostEqual(g.penalty(dict(immune, Life=3600)), 400 * generate.LIFE_FLOOR_PENALTY)
        self.assertAlmostEqual(g.penalty(dict(immune, Life=1, EnergyShield=3999)), 0)
        self.assertAlmostEqual(g.penalty(dict(immune, Life=5000)), 0)
        g.life_floor = 3400
        self.assertAlmostEqual(g.penalty(dict(immune, Life=3300)), 100 * generate.LIFE_FLOOR_PENALTY)
        g.life_floor_later = True  # while the tree grows the pool is not penalised
        self.assertAlmostEqual(g.penalty(dict(immune, Life=1000)), 0)
        g.resists_later = True  # while supports are chosen only the soft term counts
        self.assertAlmostEqual(g.penalty(dict(capped, ChaosResist=-8)), 68 * generate.CHAOS_PENALTY)
        g.resists_later = False
        with self.assertRaises(SystemExit):
            generate.Generator("Storm Call", "Assassin", build_around="No Such Unique")

    def test_skills_that_need_a_special_weapon_setup(self):
        for skill, asc, attribute, label in (("Explosive Concoction", "Trickster", "Dex", "empty main hand + shield"),
                                             ("Mana-Infused Staff", "Elementalist", "Int", "spell staff")):
            r = WORKER.call("create_build", {"ascendancy": asc, "skill": skill, "level": 90})
            options = generate.weapon_options(r["skillInfo"], attribute)
            self.assertEqual([lab for lab, _ in options], [label])
            m = WORKER.call("try", {"xml": r["xml"], "name": "t", "candidates": [self.gear(r, attribute)]})[0]["metrics"]
            self.assertGreater(m["playerDPS"], 0, skill)

    def test_minion_skill_choice_is_undone(self):
        r = WORKER.call("create_build", {"ascendancy": "Necromancer", "skill": "Summon Reaper", "level": 90})
        gear = self.gear(r, "Int")
        first, combo, after = (x["metrics"] for x in WORKER.call("try", {"xml": r["xml"], "name": "t", "changes": gear, "candidates": [
            [], [{"type": "minion_skill", "skill": "Combo Slash"}], []]}))
        self.assertEqual(first["minionDPS"], 0)  # Consume: a heal
        self.assertGreater(combo["minionDPS"], 0)
        self.assertEqual(after["minionSkill"], first["minionSkill"])

if __name__ == "__main__":
    unittest.main()
