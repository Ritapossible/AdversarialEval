# Errata: what "sandbox" meant in the 25 and 28 Nov reports, and the isolation added since (2026-11-28)

The reports below are signed and anchored on Solana, so they are not edited. This note corrects
one word in them.

- `2026-11-25-qwen-agent-predeploy.md` says every finding came from "installing and running the app
  in a fresh sandbox".
- `2026-11-28-qwen-code-verification.md` and `codeverify/RULE.md` speak of "the sandbox".

**What it was at the time:** a fresh Python virtual environment per candidate or change. It gave a
clean, reproducible install, but **no isolation**: the code under test (Qwen-Agent's package, and
the code Qwen wrote) ran as root with network access on the test machine.

**What changed (28 Nov, after an internal audit):**
- **Code written by a model** (`codeverify/checks.py`) is imported and tested with no network, as
  the unprivileged `nobody` user, under memory, CPU-time, file-size and open-file limits.
- **The app under test in a pre-deployment check** (`deploycheck/core.py`) is imported and served
  as `nobody` under resource limits. Network stays on because the smoke test serves the app on
  localhost.
- **Each result records the isolation it ran under** (`isolation` field).
- **Test:** `tests/test_codeverify.py` (`Isolation`) runs an escape attempt and checks it can't use
  the network, read root's files or write outside its folder.

**Results are unchanged.** Under isolation:
- all 24 reference solutions gave the same truth and the same decision as before;
- all 6 Qwen-Agent candidates gave the same decision, imports, advisory counts and smoke-test
  result (12 components served for fixes 1, 2 and 5).

The re-runs reused the saved Telegraph answers, so nothing was paid. Two setup problems were found
and fixed on the way:
- the app needed a readable copy of the host's CA bundle;
- the app needed its own temp folder, because a root-owned `/tmp/gradio` was left over from earlier
  runs.
