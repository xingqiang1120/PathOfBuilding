"""tools/runlua.py: compressed data PoB ships (timeless jewel look-up tables) must be readable headless.

    python -m unittest tools.tests.test_runlua
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRIPT = """
dofile("HeadlessWrapper.lua")
local load = LoadModule("Modules/DataJewelFileLoader")
for _, name in ipairs({ "ElegantHubris", "BrutalRestraint", "LethalPride", "MilitantFaith" }) do
    local d = load(name)
    print(name, d and #d or 0)
end
"""


class RunLuaTest(unittest.TestCase):
    def test_timeless_jewel_tables_load(self):
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as f:
            f.write(SCRIPT)
        try:
            out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "runlua.py"), f.name],
                                 capture_output=True, text=True, timeout=300).stdout
        finally:
            os.unlink(f.name)
        sizes = dict(line.split("\t") for line in out.splitlines() if line.count("\t") == 1)
        for name in ("ElegantHubris", "BrutalRestraint", "LethalPride", "MilitantFaith"):
            self.assertGreater(int(sizes.get(name, 0)), 1_000_000, f"{name} look-up table is empty: {out[-500:]}")


if __name__ == "__main__":
    unittest.main()
