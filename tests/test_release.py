#!/usr/bin/env python3
"""The committed dataset release matches what tools/build_release.py builds (no drift).

    python tests/test_release.py
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REL = ROOT / "release" / "adversarialeval-security-review-v1"


class Release(unittest.TestCase):
    def test_rebuild_matches_committed(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "rel"
            subprocess.run([sys.executable, str(ROOT / "tools/build_release.py"), "--out", str(out)], check=True, capture_output=True)
            self.assertEqual((out / "SHA256SUMS").read_text(), (REL / "SHA256SUMS").read_text())

    def test_no_private_material(self):
        for f in REL.rglob("*"):
            self.assertNotIn("data/private", f.as_posix())


if __name__ == "__main__":
    unittest.main(verbosity=1)
