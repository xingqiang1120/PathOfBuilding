"""Tests for the optimizer's scoring (no Path of Building needed)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import optimize  # noqa: E402


def make(targets, start=None):
    opt = optimize.Optimizer.__new__(optimize.Optimizer)
    opt.targets = targets
    opt.start = start or {}
    return opt


class ScoringTest(unittest.TestCase):
    def test_penalty_is_zero_when_targets_met(self):
        opt = make({"minionDPS": 100, "Life": 50})
        self.assertEqual(opt.penalty({"minionDPS": 120, "Life": 60, "ManaUnreserved": 5, "LifeUnreserved": 60}), 0)

    def test_penalty_is_relative_shortfall(self):
        opt = make({"minionDPS": 100})
        self.assertAlmostEqual(opt.penalty({"minionDPS": 75, "ManaUnreserved": 0, "LifeUnreserved": 1}), 0.25)

    def test_hard_limits(self):
        opt = make({"minionDPS": 100}, start={"minionLimit": 42})
        ok = {"minionDPS": 150, "ManaUnreserved": 0, "LifeUnreserved": 1, "minionLimit": 42}
        self.assertEqual(opt.penalty(ok), 0)
        self.assertGreaterEqual(opt.penalty(dict(ok, ManaUnreserved=-10)), 10)
        self.assertGreaterEqual(opt.penalty(dict(ok, minionLimit=22)), 10)
        self.assertGreaterEqual(opt.penalty(dict(ok, passivePointsUsed=113, passivePointsAvailable=112)), 10)

    def test_better_prefers_surplus_once_met(self):
        opt = make({"minionDPS": 100, "Life": 100})
        base = {"ManaUnreserved": 0, "LifeUnreserved": 1}
        a = dict(base, minionDPS=150, Life=110)
        b = dict(base, minionDPS=200, Life=105)
        self.assertTrue(opt.better(a, b))  # smallest surplus decides: 10% beats 5%


if __name__ == "__main__":
    unittest.main()
