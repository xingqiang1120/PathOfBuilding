"""Tests for the MCP server (tools/pob_mcp.py) and the PoB worker it drives.

    python -m unittest discover tools/tests
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
SAMPLE = os.path.join(ROOT, "spec", "TestBuilds", "3.13", "OccVortex.xml")


class McpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pob-mcp-")
        import library
        import pob_mcp
        library.LIBRARY = os.path.join(cls.tmp, "lib")
        with contextlib.redirect_stdout(io.StringIO()):
            library.main(["add", SAMPLE, "--source", "test"])
        cls.mcp = pob_mcp

    @classmethod
    def tearDownClass(cls):
        worker = cls.mcp.WORKER
        if worker.proc is not None:
            worker.proc.stdin.close()
            worker.proc.wait(timeout=30)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def rpc(self, method, params=None, msg_id=1):
        return self.mcp.handle({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})

    def call(self, name, **args):
        result = self.rpc("tools/call", {"name": name, "arguments": args})["result"]
        text = result["content"][0]["text"]
        return result["isError"], (text if result["isError"] else json.loads(text))

    def test_initialize_and_list_tools(self):
        init = self.rpc("initialize", {"protocolVersion": "2025-06-18"})["result"]
        self.assertEqual(init["protocolVersion"], "2025-06-18")
        self.assertIn("tools", init["capabilities"])
        names = [t["name"] for t in self.rpc("tools/list")["result"]["tools"]]
        self.assertIn("pob_simulate", names)
        self.assertIsNone(self.mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(self.rpc("nope")["error"]["code"], -32601)

    def test_list_and_summary(self):
        err, builds = self.call("pob_list_builds", skill="Vortex")
        self.assertFalse(err)
        self.assertEqual(builds[0]["name"], "OccVortex")
        err, summary = self.call("pob_build_summary", build="OccVortex")
        self.assertFalse(err)
        self.assertEqual(summary["character"]["ascendancy"], "Occultist")
        self.assertNotIn("tagInfo", summary)

    def test_simulate_reports_changes(self):
        err, result = self.call("pob_simulate", build="OccVortex", changes=[{"type": "gem_level", "gem": "Vortex", "level": 1}])
        self.assertFalse(err, result)
        self.assertIn("playerDPS", result["changed"])
        self.assertLess(result["after"]["playerDPS"], result["before"]["playerDPS"])
        # The saved build is untouched: metrics afterwards equal the "before" numbers
        err, metrics = self.call("pob_metrics", build="OccVortex")
        self.assertEqual(metrics["playerDPS"], result["before"]["playerDPS"])

    def test_errors_are_reported_to_the_ai(self):
        err, text = self.call("pob_simulate", build="OccVortex", changes=[{"type": "gem_replace", "gem": "Fireball", "with": "Vortex"}])
        self.assertTrue(err)
        self.assertIn("no socket group contains gem", text)
        err, text = self.call("pob_build_summary", build="does-not-exist")
        self.assertTrue(err)

    def test_find_uniques_by_tags(self):
        err, result = self.call("pob_find_uniques", tags=["minion", "zombie"], limit=50)
        self.assertFalse(err)
        self.assertIn("The Baron", [i["name"] for i in result["items"]])

    def test_item_usage(self):
        err, usage = self.call("library_item_usage", item="Heretic's Veil")
        self.assertFalse(err)
        self.assertEqual(usage["librarySize"], 1)
        self.assertEqual(usage["buildsUsing"], 1)
        self.assertEqual(usage["byAscendancy"][0]["name"], "Occultist")


if __name__ == "__main__":
    unittest.main()
