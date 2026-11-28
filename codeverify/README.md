# codeverify: Qwen alone vs Qwen + Telegraph

Independent verification of code written by Qwen before it reaches production (Telegraph's
Alibaba thread, item 4). The frozen rule is in `RULE.md`, and `FREEZE.json` hashes every frozen
file.

- `tasks.json`: 12 tasks, each with a known way to go wrong.
- `tests/`: visible tests (the customer's acceptance tests) and hidden tests (truth only).
- `reference/`: a correct and a typical unsafe solution per task. The tests are checked against
  them in `bench/out/codeverify/reference_check.txt`.
- `generate.py`: local Qwen generates the changes, reviews them itself (arm A) and makes one fix
  round.

## Isolation

Model-written code is imported and tested by `checks.py` under `unshare -n` (no network),
`setpriv` as the unprivileged `nobody` user (it can't read keys or write outside its temp folder),
and `prlimit` (memory, CPU time, file size, open files). Each result row records the isolation it
ran under (`isolation`).

Changes that declare the same requirements share one root-owned environment, which the code under
test can't modify. Installing requirements runs as root with network access; nothing written by
the model runs at that step.

Runs before 28 Nov 18:30 UTC used a fresh virtual environment without this isolation. Re-running
the checks isolated gave the same outcome on every reference solution; see
`eval/reports/2026-11-28-isolation-errata.md`.
