"""Tests for tools/library.py. Runs Path of Building headless (Windows, see tools/README.md).

    python -m unittest discover tools/tests
"""
import contextlib
import io
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
SAMPLES = os.path.join(ROOT, "spec", "TestBuilds", "3.13")


class LibraryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="pob-library-")
        cls.samples = os.path.join(cls.tmp, "in")
        os.makedirs(cls.samples)
        for name in ("OccVortex.xml", "Generals Perforate Zerker.xml"):
            shutil.copy(os.path.join(SAMPLES, name), cls.samples)
        os.environ["POB_LIBRARY"] = os.path.join(cls.tmp, "lib")
        import library
        library.LIBRARY = os.environ["POB_LIBRARY"]
        cls.library = library
        cls.run_cmd(["add", cls.samples, "--source", "test", "--tag", "Sample"])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def run_cmd(cls, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            cls.library.main(argv)
        return out.getvalue()

    def db(self):
        return sqlite3.connect(os.path.join(self.library.LIBRARY, "builds.db"))

    def test_share_code_roundtrip(self):
        with open(os.path.join(SAMPLES, "OccVortex.xml"), encoding="utf-8") as f:
            xml = f.read()
        self.assertEqual(xml, self.library.decode_share_code(self.library.encode_share_code(xml)))

    def test_add_indexes_builds(self):
        rows = self.db().execute("SELECT name, ascendancy, primary_skill, error FROM builds ORDER BY name").fetchall()
        self.assertEqual([r[0] for r in rows], ["Generals Perforate Zerker", "OccVortex"])
        self.assertEqual(rows[1][1], "Occultist")
        self.assertEqual(rows[1][2], "Vortex")
        self.assertIsNone(rows[1][3])
        self.assertTrue(os.path.exists(os.path.join(self.library.LIBRARY, "raw")))

    def test_duplicates_are_skipped(self):
        out = self.run_cmd(["add", self.samples])
        self.assertIn("already in the library", out)
        self.assertEqual(self.db().execute("SELECT COUNT(*) FROM builds").fetchone()[0], 2)

    def test_user_and_auto_tags(self):
        db = self.db()
        user = db.execute("SELECT COUNT(DISTINCT build_id) FROM build_tags WHERE tag = 'sample' AND origin = 'user'").fetchone()[0]
        self.assertEqual(user, 2)
        vortex = [r[0] for r in db.execute("SELECT tag FROM build_tags b JOIN builds x ON x.id = b.build_id WHERE x.name = 'OccVortex' AND origin = 'auto'")]
        self.assertIn("cold", vortex)
        self.assertNotIn("flask", vortex)

    def test_search_and_common(self):
        out = self.run_cmd(["search", "--skill", "Vortex"])
        self.assertIn("1 build(s)", out)
        self.assertIn("OccVortex", out)
        out = self.run_cmd(["common", "--tag", "sample", "--top", "3"])
        self.assertIn("2 matching build(s)", out)
        self.assertIn("Unique items", out)

    def test_show_and_note(self):
        self.run_cmd(["note", "OccVortex", "freeze league starter"])
        out = self.run_cmd(["show", "OccVortex"])
        self.assertIn("note: freeze league starter", out)
        self.assertIn("ascendancy:", out)


if __name__ == "__main__":
    unittest.main()
