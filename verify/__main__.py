"""Check answers from the command line.

    echo '<result JSON>' | python -m verify --target pkg:npm/minimist@1.2.5 [--strict-count]
    python -m verify --jsonl      # one {"id", "target", "result"} per input line, one answer per output line

Prints the Verdict as JSON (label, checks, osv_ids). Exit code 0 whatever the label; the caller
decides what to do with it. --jsonl keeps one process and one cache for a whole run (the
connector uses it); a request that can't be read gets {"id", "error"} instead of a verdict.
"""
import argparse
import json
import sys

from .core import verify
from .sources import LiveSources


def _result(raw):
    return raw if isinstance(raw, dict) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target")
    ap.add_argument("--strict-count", action="store_true")
    ap.add_argument("--jsonl", action="store_true")
    a = ap.parse_args()
    if a.jsonl:
        src = LiveSources(max_age=3600, max_entries=20_000)
        for line in sys.stdin:
            if not line.strip():
                continue
            req = None
            try:
                req = json.loads(line)
                out = {"id": req.get("id"), **verify(str(req["target"]), _result(req.get("result")), src,
                                                     strict_count=bool(req.get("strict_count"))).to_dict()}
            except Exception as e:  # report, keep serving
                out = {"id": req.get("id") if isinstance(req, dict) else None, "error": f"{type(e).__name__}: {e}"}
            print(json.dumps(out), flush=True)
        return
    if not a.target:
        ap.error("--target is required (or use --jsonl)")
    raw = sys.stdin.read().strip()
    try:
        result = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        result = None
    v = verify(a.target, _result(result), LiveSources(), strict_count=a.strict_count)
    print(json.dumps(v.to_dict()))


if __name__ == "__main__":
    main()
