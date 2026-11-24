#!/usr/bin/env python3
"""Build the static site (site/) from site-src/: one layout, five pages, shared assets.

    python tools/build_site.py           # write site/*.html and site/assets/*
    python tools/build_site.py --check   # exit 1 if site/ differs from what the sources build (CI)

Sources:
  site-src/layout.html      header, menu (desktop list, mobile dropdown), footer
  site-src/pages/*.html     each page's main content
  site-src/base.css + layout.css -> site/assets/site.css
  site-src/nav.js, spot.js  -> site/assets/
  site-src/spot-data.json   the Spot the Flaw cases, written by tools/build_spot_flaw.py

Pages are served with clean URLs (site/vercel.json): /evaluators serves evaluators.html. Old
single-page links (/#apps, /#game, /#c-<case>) are forwarded by a small script on the home page.
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC, OUT = ROOT / "site-src", ROOT / "site"

# (file, path, menu label, hint shown in the mobile menu, page title, description)
PAGES = [
    ("index.html", "/", "Overview", "What this is and the key results",
     "AdversarialEval: security answers you can check",
     "Evaluation material, an evaluator, a paid benchmark of Telegraph's security miners, and Dependency.Guard, which checks paid answers before acting on them."),
    ("evaluators.html", "/evaluators", "Evaluators", "Spot the Flaw, test results, the dataset",
     "Evaluators: Spot the Flaw | AdversarialEval",
     "Two security reviews of the same request, one plausible but wrong in one decisive fact. Play the test, then see how shortcut judges and our evaluator did."),
    ("dependency-guard.html", "/dependency-guard", "Dependency.Guard", "The app: how it works and its evidence",
     "Dependency.Guard | AdversarialEval",
     "A Mind that buys one security answer per package from Telegraph, checks it for free against public sources, and decides PASS, BLOCK or FLAG with the evidence."),
    ("benchmark.html", "/benchmark", "Benchmark", "What a paid answer is worth",
     "Paid market benchmark | AdversarialEval",
     "3,680 paid calls to Telegraph's security miners under rules fixed in advance: accuracy, cost per correct answer, rank agreement and provider independence."),
    ("evidence.html", "/evidence", "Evidence", "Reports, signed results, limits",
     "Evidence and limits | AdversarialEval",
     "Every report, how to verify the signed results and on-chain payments yourself, and what this project does not claim."),
]

LEGACY = """<script>
// Links to the old single-page site keep working: forward them to the page that now holds them.
(function () {
  var h = location.hash, map = { "#evaluators": "/evaluators", "#game": "/evaluators#game", "#numbers": "/evaluators#numbers",
    "#how": "/evaluators#how", "#families-sec": "/evaluators#families-sec", "#apps": "/dependency-guard",
    "#guard": "/dependency-guard", "#market": "/benchmark", "#limits": "/evidence" };
  if (/^#c-[0-9a-f]{10}$/.test(h)) location.replace("/evaluators" + h);
  else if (map[h]) location.replace(map[h]);
})();
</script>"""


def assets() -> dict[str, str]:
    return {
        "site.css": (SRC / "base.css").read_text() + "\n" + (SRC / "layout.css").read_text(),
        "nav.js": (SRC / "nav.js").read_text(),
        "spot.js": (SRC / "spot.js").read_text(),
    }


def render() -> dict[str, str]:
    files = {f"assets/{k}": v for k, v in assets().items()}
    version = hashlib.sha256("".join(files[k] for k in sorted(files)).encode()).hexdigest()[:10]
    layout = (SRC / "layout.html").read_text()
    spot_data = (SRC / "spot-data.json").read_text().strip().replace("</", "<\\/")
    for file, path, label, hint, title, desc in PAGES:
        current = ' aria-current="page"'
        nav = "\n".join(
            f'        <li><a href="{p}"{current if f == file else ""}>{l}<span class="hint">{h}</span></a></li>'
            for f, p, l, h, *_ in PAGES)
        footer_nav = "\n".join(f'        <li><a href="{p}">{l}</a></li>' for _, p, l, *_ in PAGES)
        body = (SRC / "pages" / file).read_text().replace("{{spot_data}}", spot_data)
        scripts = []
        if file == "index.html":
            scripts.append(LEGACY)
        if file == "evaluators.html":
            scripts.append(f'<script src="/assets/spot.js?v={version}" defer></script>')
        page = (layout.replace("{{title}}", html.escape(title)).replace("{{description}}", html.escape(desc))
                .replace("{{nav}}", nav).replace("{{footer_nav}}", footer_nav).replace("{{asset_version}}", version)
                .replace("{{scripts}}", "\n".join(scripts)).replace("{{body}}", body.rstrip("\n")))
        left = [k for k in ("title", "description", "nav", "footer_nav", "asset_version", "scripts", "body", "spot_data")
                if "{{" + k + "}}" in page]
        assert not left, f"unfilled placeholder(s) {left} in {file}"
        files[file] = page
    return files


def main() -> int:
    files = render()
    if "--check" in sys.argv:
        bad = [f for f, c in files.items() if not (OUT / f).exists() or (OUT / f).read_text() != c]
        if bad:
            print(f"site/ is out of date: {', '.join(bad)}. Run python tools/build_site.py")
            return 1
        print(f"site/ matches site-src/ ({len(files)} files)")
        return 0
    for f, c in files.items():
        (OUT / f).parent.mkdir(parents=True, exist_ok=True)
        (OUT / f).write_text(c)
    print(f"wrote {len(files)} files to site/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
