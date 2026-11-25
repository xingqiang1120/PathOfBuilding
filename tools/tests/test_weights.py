"""Weights from the simulation log (tools/weights.py).

    python -m unittest tools/tests/test_weights.py
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import simlog  # noqa: E402
import weights  # noqa: E402


class WeightsTest(unittest.TestCase):
    def setUp(self):
        self.old = simlog.LIBRARY
        simlog.LIBRARY = tempfile.mkdtemp(prefix="pob-weights-")

    def tearDown(self):
        simlog.LIBRARY = self.old

    def run_with(self, skill, asc, gains):
        """One finished run with a support batch: gains = {support: DPS multiplier}."""
        rec = simlog.Recorder("generate", skill=skill, ascendancy=asc, focus="balanced", gear="template", generator=3)
        rec.step = "support"
        before = {"playerDPS": 1000, "TotalEHP": 5000}
        moves = [[{"type": "gem_add", "group": 1, "gem": g}] for g in gains]
        results = [{"metrics": {"playerDPS": 1000 * m, "TotalEHP": 5000}} for m in gains.values()]
        score = lambda m: (m.get("playerDPS") or 0) / 1000  # noqa: E731
        rec.record("support", [], before, moves, results, lambda m: m.get("playerDPS") or 0, score=score)
        rec.finish({"playerDPS": 1500}, None)

    def test_ranks_contexts_and_suggest(self):
        for i in range(6):
            self.run_with("Glacial Hammer", "Champion", {"Melee Physical Damage": 1.5, "Ruthless": 1.2, "Faster Attacks": 1.1, "Useless": 0.9})
        for i in range(6):  # another skill where Ruthless is the best
            self.run_with("Cleave", "Berserker", {"Melee Physical Damage": 1.1, "Ruthless": 1.6, "Faster Attacks": 1.2, "Useless": 1.0})
        weights.build()
        r = weights.suggest("Glacial Hammer", "Champion", "support")
        order = [x["label"] for x in r["suggestions"]["support"]]
        self.assertEqual(order[0], "Melee Physical Damage")  # this skill's own data wins over the other skill's
        self.assertEqual(order[-1], "Useless")
        useless = r["suggestions"]["support"][-1]
        self.assertLess(useless["weight"], 0.2)  # no score gain: rank 0, shrunk only slightly toward 0.5
        self.assertEqual(r["suggestions"]["support"][0]["mostSpecific"], "skill:Glacial Hammer|asc:Champion")
        # a skill never run falls back on its tags: Ice Crash shares attack, melee, cold with Glacial Hammer
        r = weights.suggest("Ice Crash", "Champion", "support")
        self.assertTrue(r["suggestions"]["support"])

    def test_no_gain_ranks_zero(self):
        self.run_with("Glacial Hammer", "Champion", {"A": 1.5, "B": 1.2, "C": 0.8, "D": 1.0})
        db = simlog.connect()
        rid = db.execute("SELECT id FROM runs").fetchone()[0]
        (cat, rows), = list(weights.batches(db, rid))
        rank = {k: r for k, _, r, *_ in rows}
        self.assertEqual((rank["A"], rank["B"], rank["C"], rank["D"]), (1.0, 0.5, 0.0, 0.0))

    def test_generator_narrows_supports_by_weight(self):
        import generate
        g = generate.Generator("Glacial Hammer", "Champion", seed=1)
        pool = [f"S{i}" for i in range(40)]
        self.assertEqual(g.narrow("support", pool), pool)  # no weights: everything is tried
        g.weights = {"support": {f"S{i}": i / 40 for i in range(40)}}
        picked = g.narrow("support", pool)
        self.assertEqual(len(picked), generate.GUIDE_TOP + generate.GUIDE_EXPLORE)
        self.assertEqual(picked[:generate.GUIDE_TOP], [f"S{i}" for i in range(39, 39 - generate.GUIDE_TOP, -1)])
        self.assertTrue(set(picked[generate.GUIDE_TOP:]) <= set(pool[:40 - generate.GUIDE_TOP]))  # explored at random


if __name__ == "__main__":
    unittest.main()
