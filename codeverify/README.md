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
