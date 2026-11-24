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

    def test_state_numbers_stored_once_and_rebuilt(self):
        before = {"playerDPS": 1000, "TotalEHP": 5000, "Life": 3000}
        rec = simlog.Recorder("generate", skill="Arc", generator=2)
        moves = [[{"type": "passive_add", "node": 1}], [{"type": "passive_add", "node": 2}]]
        results = [{"metrics": {"playerDPS": 1100, "TotalEHP": 5000, "Life": 3000}}, {"metrics": {"playerDPS": 1000, "TotalEHP": 5200}}]
        rec.record("tree", [], before, moves, results, lambda m: m.get("playerDPS") or 0)
        rec.finish(results[0]["metrics"], outcome="test")
        db = simlog.connect()
        self.assertEqual(db.execute("SELECT COUNT(*) FROM states").fetchone()[0], 1)
        state = __import__("json").loads(db.execute("SELECT metrics FROM states").fetchone()[0])
        deltas = [__import__("json").loads(d) for (d,) in db.execute("SELECT delta FROM samples ORDER BY id")]
        self.assertEqual(deltas[0], {"playerDPS": 1100})  # only what changed
        self.assertEqual(simlog.after_metrics(state, deltas[1]), {"playerDPS": 1000, "TotalEHP": 5200})  # Life gone
        self.assertEqual(db.execute("SELECT generator, outcome FROM runs").fetchone(), (2, "test"))

    def test_compact_converts_old_format(self):
        import json
        import sqlite3
        os.makedirs(simlog.LIBRARY, exist_ok=True)
        db = sqlite3.connect(simlog.db_path())
        db.executescript("""
            CREATE TABLE runs (id TEXT PRIMARY KEY, started TEXT, tool TEXT, skill TEXT, ascendancy TEXT, class TEXT, focus TEXT, gear TEXT,
                pob_version TEXT, tree_version TEXT, skill_info TEXT, finished TEXT, final TEXT);
            CREATE TABLE samples (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, step TEXT, state_hash TEXT, state_size INTEGER,
                kind TEXT, key TEXT, label TEXT, change TEXT, cost INTEGER, dps_before REAL, dps_after REAL, ehp_before REAL,
                ehp_after REAL, score_before REAL, score_after REAL, before TEXT, after TEXT, error TEXT);""")
        db.execute("INSERT INTO runs (id, tool, skill, finished) VALUES ('r1', 'generate', 'Arc', 'x')")
        b = json.dumps({"playerDPS": 10, "Life": 5})
        for after in (json.dumps({"playerDPS": 12, "Life": 5}), None):
            db.execute("INSERT INTO samples (run_id, state_hash, kind, dps_before, before, after) VALUES ('r1', 'h', 'passive_add', 10, ?, ?)",
                       (b, after))
        db.commit()
        db.close()
        with self.assertRaises(SystemExit):
            simlog.connect()
        simlog.compact()
        db = simlog.connect()
        self.assertEqual([json.loads(d) if d else d for (d,) in db.execute("SELECT delta FROM samples ORDER BY id")], [{"playerDPS": 12}, None])
        self.assertEqual(json.loads(db.execute("SELECT metrics FROM states").fetchone()[0]), {"playerDPS": 10, "Life": 5})
        self.assertIn("generator", simlog.columns(db, "runs"))

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
