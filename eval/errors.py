#!/usr/bin/env python3
"""Error mining (audit item U6): turn an adapter's held-out mistakes into an authoring worksheet.

Reads the per-pair scores eval/score.py wrote (--json), joins them with the data and the
sidecar meta, and lists every pair the adapter got wrong, grouped by failure family and
sorted by how confidently wrong it was (rejected score minus chosen score). Each entry shows
the prompt, both answers and the flaw note, plus a prompt for what counterexample to write.

    python eval/errors.py runs/SECURITY_REVIEW-cpu-v1/scores.json \
        --data data/validation/security_review.val.jsonl [--md eval/reports/<date>-errors-<run>.md]

Use the worksheet to write NEW pairs for the training set that target the same failure.
Never copy a validation or test pair into training: write a fresh case with the same flaw.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "eval"))
from common import read_jsonl, row_id  # noqa: E402
from score import meta_for  # noqa: E402

HINTS = {
    "F1": "a real-looking but wrong advisory id for the same bug class, in a new package",
    "F2": "the same version-range mistake on a different advisory; quote the range in the prompt for half of them",
    "F3": "a new target where the incomplete answer is longer and cites more ids than the complete one",
    "F4": "a new snippet where one line of context flips the verdict, plus its twin without that line",
    "F5": "vulnerable code with a confident, short 'Secure' answer, in another language or framework",
    "F6": "safe-but-suspicious code where the false alarm is short and confident",
    "F7": "a correct answer whose verdict/count fields contradict its own text",
    "F8": "the right finding with the severity off by two levels",
    "F9": "decisive evidence where the wrong answer hedges",
    "F10": "a fix that a specific input bypasses",
}


def clip(s: str, n: int = 500) -> str:
    s = s.strip()
    return s if len(s) <= n else s[:n] + " …"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scores")
    ap.add_argument("--data", required=True, help="the data file the scores belong to")
    ap.add_argument("--md")
    a = ap.parse_args(argv)

    data_path = Path(a.data)
    rows = {row_id(r["prompt"], r["chosen"], r["rejected"]): r for _, r in read_jsonl(data_path)}
    meta = meta_for(data_path)
    scores = [s for s in json.loads(Path(a.scores).read_text())
              if s.get("row_id") in rows and Path(s.get("file", a.data)).name == data_path.name]
    wrong = [s for s in scores if s["correct"] < 1.0]
    by = defaultdict(list)
    for s in wrong:
        by[s.get("family") or "?"].append(s)

    out = [f"# Error worksheet: `{a.scores}` on `{a.data}`", "",
           f"{len(wrong)} of {len(scores)} pairs ranked wrong. Write **new** training pairs that target each failure; "
           "never copy these pairs into training.", ""]
    out += ["| family | wrong / total |", "|---|---|"]
    totals = defaultdict(int)
    for s in scores:
        totals[s.get("family") or "?"] += 1
    for fam in sorted(totals, key=lambda f: (len(f), f)):
        out.append(f"| {fam} | {len(by.get(fam, []))} / {totals[fam]} |")
    out.append("")
    for fam in sorted(by, key=lambda f: (len(f), f)):
        out += [f"## {fam}: write {HINTS.get(fam, 'a new case with the same flaw')}", ""]
        for s in sorted(by[fam], key=lambda s: s["chosen"] - s["rejected"]):
            r, m = rows[s["row_id"]], meta.get(s["row_id"], {})
            out += [f"### `{m.get('case', '?')}`: margin {s['chosen'] - s['rejected']:+.3f} (chosen − rejected)", "",
                    f"**Flaw:** {m.get('flaw_note', '?')}", "",
                    "**Prompt:**", "", "```", clip(r["prompt"]), "```", "",
                    "**Chosen (should win):**", "", "```", clip(r["chosen"]), "```", "",
                    "**Rejected (won instead):**", "", "```", clip(r["rejected"]), "```", ""]
    text = "\n".join(out)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(text + "\n")
        print(f"wrote {a.md}: {len(wrong)} errors across {len(by)} families")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
