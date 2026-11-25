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
        self.assertIn("38% increased Critical Strike Chance", crit)
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
                         ["40% increased Cleave Damage", "+40% to Fire Resistance", "+40% to Cold Resistance"])
        c = WORKER.call("candidates", {"xml": self.new["xml"], "name": "t", "changes": self.gear(self.new, "Int")})
        self.assertNotIn("Natural Hierarchy", c["uniques"]["Amulet"])  # Talisman league only
        self.assertTrue(all(n for n in c["uniques"]["Weapon 1"]))

    def test_build_around_profile(self):
        prof = generate.unique_profile("Doryani's Prototype")
        self.assertEqual(prof["slot"], "Body Armour")
        g = generate.Generator("Storm Call", "Assassin", build_around="Doryani's Prototype")
        self.assertEqual(g.penalty({"FireResist": 75, "ColdResist": 75, "LightningResist": -160}), 0)  # lightning ignored
        with self.assertRaises(SystemExit):
            generate.Generator("Storm Call", "Assassin", build_around="No Such Unique")

if __name__ == "__main__":
    unittest.main()
