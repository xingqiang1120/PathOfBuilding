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


if __name__ == "__main__":
    unittest.main()
