"""Simulation log (tools/simlog.py): samples are stored and averaged per change and context.

    python -m unittest tools.tests.test_simlog
"""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import simlog  # noqa: E402


class SimLogTest(unittest.TestCase):
    def setUp(self):
        self.old = simlog.LIBRARY
        simlog.LIBRARY = tempfile.mkdtemp(prefix="pob-simlog-")

    def tearDown(self):
        simlog.LIBRARY = self.old

    def test_record_and_stats(self):
        dps = lambda m: m.get("playerDPS") or 0  # noqa: E731
        before = {"playerDPS": 1000, "TotalEHP": 5000, "Life": 3000}
        for skill, gain in (("Kinetic Blast", 1.2), ("Kinetic Blast", 1.4), ("Raise Zombie", 1.0)):
            rec = simlog.Recorder("generate", skill=skill, ascendancy="Necromancer", skill_info={"attack": True},
                                  versions={"pobVersion": "2.68.1", "treeVersion": "3_30"})
            moves = [[{"type": "passive_add", "node": 41476}], [{"type": "gem_add", "group": 1, "gem": "Added Fire Damage"}]]
            results = [{"metrics": {"playerDPS": 1000 * gain, "TotalEHP": 5000}, "applied": ["allocated Wandslinger (2 points)"]},
                       {"error": "not supported"}]
            rec.record("tree", [], before, moves, results, dps, costs=[2, 1])
            rec.finish(results[0]["metrics"])
        s = simlog.summary()
        self.assertEqual((s["runs"], s["finishedRuns"], s["samples"], s["failedSamples"]), (3, 3, 6, 3))
        rows = simlog.stats(kind="passive_add", skill="Kinetic")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["samples"], 2)
        self.assertEqual(rows[0]["dpsPct"], 15.0)  # (+20% and +40%) / 2 points, averaged
        self.assertIn("Wandslinger", rows[0]["label"])
        # Failed tries are kept but not averaged
        self.assertEqual(simlog.stats(kind="gem_add"), [])

    def test_disabled(self):
        os.environ["POB_SIMLOG"] = "0"
        try:
            rec = simlog.Recorder("generate")
            rec.record("tree", [], {}, [[]], [{}], lambda m: 0)
            self.assertFalse(os.path.exists(simlog.db_path()))
        finally:
            del os.environ["POB_SIMLOG"]


if __name__ == "__main__":
    unittest.main()
