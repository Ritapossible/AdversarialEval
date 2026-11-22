"""Check one answer from the command line.

    echo '<result JSON>' | python -m verify --target pkg:npm/minimist@1.2.5 [--strict-count]

Prints the Verdict as JSON (label, checks, osv_ids). Exit code 0 whatever the label; the caller
decides what to do with it.
"""
import argparse
import json
import sys

from .core import verify
from .sources import LiveSources


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    ap.add_argument("--strict-count", action="store_true")
    a = ap.parse_args()
    raw = sys.stdin.read().strip()
    try:
        result = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        result = None
    v = verify(a.target, result if isinstance(result, dict) else None, LiveSources(), strict_count=a.strict_count)
    print(json.dumps(v.to_dict()))


if __name__ == "__main__":
    main()
