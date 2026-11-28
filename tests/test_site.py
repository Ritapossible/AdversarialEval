#!/usr/bin/env python3
"""Site checks: every recent report is listed on the Evidence page, and every video file exists.

    python tests/test_site.py
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Site(unittest.TestCase):
    def test_every_recent_report_is_listed(self):
        page = (ROOT / "site-src/pages/evidence.html").read_text()
        missing = [p.name for p in sorted((ROOT / "eval/reports").glob("2026-11-*.md"))
                   if p.name >= "2026-11-21" and p.name not in page]
        self.assertEqual(missing, [], "add these reports to site-src/pages/evidence.html")

    def test_videos_and_posters_exist(self):
        page = (ROOT / "site-src/pages/videos.html").read_text()
        for ref in re.findall(r'(?:src|poster)="/(videos/[^"]+)"', page):
            self.assertTrue((ROOT / "site" / ref).exists(), ref)


if __name__ == "__main__":
    unittest.main(verbosity=1)
