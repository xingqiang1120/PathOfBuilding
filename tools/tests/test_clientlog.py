"""Tests for tools/clientlog.py (no game or PoB needed).

    python -m unittest tools.tests.test_clientlog
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import clientlog  # noqa: E402

LOG = """\
2026/11/20 20:00:00 ***** LOG FILE OPENING *****
2026/11/20 20:00:05 1000 abc [DEBUG Client 1] Generating level 1 area "HideoutFelled" with seed 1
2026/11/20 20:00:06 1001 abc [INFO Client 1] : You have entered Felled Hideout.
2026/11/20 20:01:00 1002 abc [DEBUG Client 1] Generating level 83 area "MapWorldsStrand" with seed 111
2026/11/20 20:01:02 1003 abc [INFO Client 1] [SCENE] Set Source [Strand]
2026/11/20 20:01:02 1004 abc [INFO Client 1] : You have entered Strand.
2026/11/20 20:01:30 1005 abc [INFO Client 1] : @From Someone: wtb your stuff
2026/11/20 20:01:40 1006 abc [INFO Client 1] #Trader: Meimax has been slain.
2026/11/20 20:04:00 1007 abc [INFO Client 1] : Meimax has been slain.
2026/11/20 20:04:10 1008 abc [DEBUG Client 1] Generating level 1 area "HideoutFelled" with seed 1
2026/11/20 20:04:11 1009 abc [INFO Client 1] : You have entered Felled Hideout.
2026/11/20 20:05:00 1010 abc [INFO Client 1] : You have entered Strand.
2026/11/20 20:07:00 1011 abc [INFO Client 1] : Meimax (Necromancer) is now level 96
2026/11/20 20:09:00 1012 abc [DEBUG Client 1] Generating level 1 area "HideoutFelled" with seed 1
2026/11/20 20:09:01 1013 abc [INFO Client 1] : You have entered Felled Hideout.
2026/11/20 20:10:00 1014 abc [DEBUG Client 1] Generating level 84 area "MapWorldsCrimsonTownship" with seed 222
2026/11/20 20:10:01 1015 abc [INFO Client 1] : You have entered Crimson Township.
2026/11/20 20:15:01 1016 abc [INFO Client 1] : Friend has been slain.
2026/11/20 20:16:01 1017 abc [INFO Client 1] : AFK mode is now ON. Autoreply "This player is AFK."
2026/11/20 21:30:00 1018 abc [INFO Client 1] : You have entered Felled Hideout.
"""


class ClientLogTest(unittest.TestCase):
    def setUp(self):
        self.data = clientlog.parse(LOG.splitlines(True))

    def test_map_runs(self):
        maps = [i for i in self.data["instances"] if i["kind"] == "map"]
        self.assertEqual([m["name"] for m in maps], ["Strand", "Crimson Township"])
        strand, township = maps
        self.assertEqual((strand["level"], strand["entries"], strand["deaths"]), (83, 2, 1))
        # 20:01:02-20:04:11 plus 20:05:00-20:09:01 (back in through the same portal)
        self.assertEqual(strand["seconds"], 189 + 241)
        # the last gap (20:16 -> 21:30) is longer than the AFK cap: the clock stops at the last event
        self.assertEqual(township["seconds"], 360)

    def test_chat_is_ignored(self):
        self.assertEqual([d["character"] for d in self.data["deaths"]], ["Meimax", "Friend"])
        self.assertNotIn("wtb", repr(self.data))

    def test_summary(self):
        s = clientlog.summarize(self.data)
        self.assertEqual(s["character"], "Meimax")  # the only character that levelled
        self.assertEqual(s["characters"]["Meimax"], {"class": "Necromancer", "level": 96, "time": "2026-11-20 20:07:00"})
        self.assertEqual((s["maps"]["runs"], s["maps"]["deaths"], s["maps"]["mapsWithDeath"]), (2, 1, 1))
        self.assertEqual(s["maps"]["slowest"][0]["map"], "Strand")
        self.assertEqual(clientlog.summarize(self.data, level=84)["maps"]["deaths"], 0)
        self.assertEqual(s["unrecognisedMessages"], 1)  # the AFK line, listed by "templates"


if __name__ == "__main__":
    unittest.main()
