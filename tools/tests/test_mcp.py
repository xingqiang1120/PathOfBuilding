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

    def test_minion_skill_needs_a_minion(self):
        err, text = self.call("pob_metrics", build="OccVortex", minionSkill="Physical Projectile")
        self.assertTrue(err)
        self.assertIn("no minion skills", text)

    def test_saved_settings_are_applied(self):
        err, plain = self.call("pob_metrics", build="OccVortex")
        err, saved = self.call("pob_save_build_settings", build="OccVortex",
                               changes=[{"type": "gem_level", "gem": "Vortex", "level": 1}], note="test only")
        self.assertFalse(err, saved)
        try:
            err, metrics = self.call("pob_metrics", build="OccVortex")
            self.assertFalse(err, metrics)
            self.assertIn("changes", metrics["settingsApplied"])
            self.assertLess(metrics["playerDPS"], plain["playerDPS"])
            err, ignored = self.call("pob_metrics", build="OccVortex", ignoreSettings=True)
            self.assertEqual(ignored["playerDPS"], plain["playerDPS"])
            err, summary = self.call("pob_build_summary", build="OccVortex")
            self.assertEqual(summary["verifiedSettings"]["note"], "test only")
        finally:
            self.call("pob_save_build_settings", build="OccVortex", changes=[], note="")

    def test_contributions(self):
        err, result = self.call("pob_contributions", build="OccVortex", includePassives=False)
        self.assertFalse(err, result)
        roles = {p["name"]: p.get("role") for p in result["parts"]}
        self.assertTrue(any(r and "damage" in r for r in roles.values()))
        self.assertTrue(all("dpsPct" in p or "error" in p for p in result["parts"]))

    def test_wither_inference(self):
        gloves = [{"type": "item_equip", "slot": "Gloves", "unique": "Abhorrent Interrogation"}]
        err, result = self.call("pob_simulate", build="OccVortex", changes=gloves)
        self.assertFalse(err, result)
        self.assertFalse(result["inferredBefore"])
        wither = result["inferredAfter"][0]
        self.assertEqual(wither["key"], "multiplierWitheredStackCount")
        self.assertEqual(wither["parts"][0]["actor"], "player")
        self.assertTrue(wither["applied"])
        self.assertGreater(wither["value"], 0)
        # A value set explicitly is never overridden
        err, result = self.call("pob_simulate", build="OccVortex",
                                changes=gloves + [{"type": "config_set", "key": "multiplierWitheredStackCount", "value": 1}])
        self.assertFalse(result["inferredAfter"][0]["applied"])
        # infer=false switches it off
        err, result = self.call("pob_simulate", build="OccVortex", changes=gloves, infer=False)
        self.assertIsNone(result.get("inferredAfter"))

    def test_fresh_meat_uptime(self):
        zombies = [{"type": "group_add", "gems": ["Raise Zombie", "Fresh Meat"]}, {"type": "main_group", "group": "Raise Zombie"}]

        def fresh(result):
            return [i for i in result["inferredAfter"] if i["key"] == "freshMeatBuffs"][0]
        # Without a summon rate from play nothing is applied; the rate needed for full uptime is reported
        err, result = self.call("pob_simulate", build="OccVortex", changes=zombies)
        self.assertFalse(err, result)
        self.assertFalse(fresh(result)["applied"])
        self.assertGreater(fresh(result)["requiredRateForFull"], 0)
        # Slow re-summoning: part of the army has the buff, minion DPS is blended between with and without
        err, result = self.call("pob_simulate", build="OccVortex", changes=zombies, summonRate=0.05)
        inf = fresh(result)
        self.assertTrue(inf["applied"])
        self.assertLess(inf["estimate"], 1)
        self.assertLess(inf["minionDPSWithoutBuff"], result["after"]["minionDPS"])
        self.assertLess(result["after"]["minionDPS"], inf["minionDPSWithBuff"])
        # Fast re-summoning: every minion is fresh
        err, result = self.call("pob_simulate", build="OccVortex", changes=zombies, summonRate=100)
        self.assertEqual(fresh(result)["estimate"], 1)
        self.assertNotIn("blendedBy", result["after"])

    def test_mechanics_lookup(self):
        err, result = self.call("pob_mechanics", id="withered")
        self.assertFalse(err, result)
        wither = result[0]
        self.assertEqual(wither["rules"]["maxStacks"]["value"], 15)
        self.assertEqual(wither["rules"]["maxStacks"]["source"], "wiki")
        self.assertIn("chaos", wither["implies"])
        self.assertIn("Abhorrent Interrogation", wither["uniques"])
        self.assertNotIn("detect", wither)

    def test_core_parts_after_analysis(self):
        self.call("pob_contributions", build="OccVortex", includePassives=False)
        err, core = self.call("library_core_parts", skill="Vortex")
        self.assertFalse(err, core)
        self.assertEqual(core["analysedBuilds"], 1)
        self.assertTrue(core["damage"])
        self.assertTrue(all(p["avgDpsPct"] <= -2 for p in core["damage"]))

    def test_damage_breakdown(self):
        err, bd = self.call("pob_damage_breakdown", build="OccVortex")
        self.assertFalse(err, bd)
        self.assertEqual(bd["actor"], "player")
        self.assertEqual(bd["mainSkill"], "Vortex")
        types = {d["type"]: d for d in bd["damageTypes"]}
        self.assertIn("Cold", types)
        rows = [r for r in types["Cold"]["rows"] if r.get("base")]
        self.assertTrue(rows and rows[0]["increased"] > 1)
        self.assertGreater(bd["speed"]["value"], 0)

    def test_config_sensitivity(self):
        err, result = self.call("pob_config_sensitivity", build="OccVortex")
        self.assertFalse(err, result)
        self.assertTrue(all("key" in p and "dpsPct" in p for p in result["parts"]))

    def test_notes_parsing(self):
        import analysis
        xml = ('<?xml version="1.0" encoding="UTF-8"?><PathOfBuilding><Build/><Notes>^7來源: poe.ninja\n目的：看防禦\n'
               'Minion skill: Physical Projectile\nfree text</Notes></PathOfBuilding>')
        fields, text = analysis.parse_notes(xml)
        self.assertEqual(fields["source"], "poe.ninja")
        self.assertEqual(fields["purpose"], "看防禦")
        self.assertEqual(fields["minionSkill"], "Physical Projectile")
        self.assertIn("free text", text)

    def test_item_usage(self):
        err, usage = self.call("library_item_usage", item="Heretic's Veil")
        self.assertFalse(err)
        self.assertEqual(usage["librarySize"], 1)
        self.assertEqual(usage["buildsUsing"], 1)
        self.assertEqual(usage["byAscendancy"][0]["name"], "Occultist")


if __name__ == "__main__":
    unittest.main()
