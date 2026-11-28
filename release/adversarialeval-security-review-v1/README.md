---
license: mit
language:
- en
pretty_name: AdversarialEval SECURITY_REVIEW preference pairs
size_categories:
- n<1K
task_categories:
- text-classification
tags:
- security
- preference
- reward-model
- dpo
- vulnerability
- telegraph
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train.jsonl
  - split: validation
    path: data/validation.jsonl
  - split: test
    path: data/test.jsonl
---

# AdversarialEval: security review preference pairs (v1.0)

Pairs of answers to software security questions in which the worse answer is **plausible but wrong
in one decisive, verifiable way**: a real advisory id for the wrong package, a patched version
called vulnerable, a confident "Secure" on vulnerable code, a fix that doesn't fix. A judge that
rewards length, fluency or security keywords picks the wrong answer. A judge that checks the facts
picks the right one.

Built for the `SECURITY_REVIEW` intent on [Telegraph](https://telegraphprotocol.com), Season II.
Project: https://github.com/Ritapossible/AdversarialEval

## Splits

| Split | Pairs | Who wrote them | Review |
|---|---:|---|---|
| train | 264 | generated from OSV records (`generator:osv-v1`) and drafted with an AI assistant (`claude-draft`) | every advisory fact machine-checked against OSV; not individually human-reviewed |
| validation | 87 | the same, in a second voice (`claude-draft-voice2`) | as train |
| test | 40 | two independent outside authors, Fexx (drafted with GPT-6) and Lino (drafted with Grok) | each author read and revised every pair |

The splits are disjoint (near-duplicate check across all of them), and none of them overlaps
the private material uploaded to Telegraph's evaluation pool, which is not part of this release.

## Fields

| Field | Meaning |
|---|---|
| `id` | SHA-256 row id over prompt, chosen and rejected |
| `prompt` | the question (often with code or a dependency pin) |
| `chosen` | the better answer |
| `rejected` | the worse answer: plausible, wrong in one decisive way |
| `family` | the failure family of the rejected answer (table below) |
| `flaw_note` | what exactly is wrong with the rejected answer |
| `source_url` | the public source that settles it (GitHub advisory, NVD, CWE or vendor docs) |
| `verdict_chosen`, `verdict_rejected` | the verdict each answer gives (Secure, Insecure, Needs changes, ...) |
| `case`, `format`, `author`, `reviewed`, `label_kind`, `provenance` | provenance details |

Rendered for a reward model as `### Task:\n{prompt}\n\n### Answer:\n{answer}`. Every row fits in 512
tokens, with the decisive flaw early.

## Failure families

| Family | Meaning | Train | Validation | Test |
|---|---|---:|---:|---:|
| F0 | not labelled (independent test pairs) | 0 | 0 | 40 |
| F1 | wrong advisory id | 28 | 6 | 0 |
| F2 | version-range error | 100 | 33 | 0 |
| F3 | missed critical issue | 11 | 3 | 0 |
| F4 | context reversal | 20 | 6 | 0 |
| F5 | overconfident "Secure" | 15 | 5 | 0 |
| F6 | false alarm | 26 | 5 | 0 |
| F7 | inconsistent fields | 28 | 11 | 0 |
| F8 | wrong severity or class | 20 | 11 | 0 |
| F9 | needless hedging | 6 | 3 | 0 |
| F10 | ineffective fix | 10 | 4 | 0 |

## Baselines

- **Shortcut judges** (longer answer, shorter answer, more advisory ids, security keywords): at
  most 58% on validation and 60% on test.
- **An adapter trained on the train split** with Telegraph's official kit: 72 to 75% on
  validation and **77.5%** (31/40, 95% CI 62.5 to 87.7%) on the independent test. Details are in
  the project's reports.

## Intended use

Training and evaluating reward models, judges and evaluators for security answers, and checking
that a judge isn't rewarding length or keywords. It is not a vulnerability database: check facts
against the cited source before relying on them.

## Limitations

- **Small:** 391 pairs.
- **One author style:** train and validation share it, so validation overstates accuracy on other
  authors' material.
- **Mostly machine-checked:** the train and validation pairs are drafted with an AI assistant or
  generated, then checked against OSV by script, not read row by row by a person. The test pairs
  are AI-assisted drafts revised by their human authors.
- **Coverage:** advisory facts are as of November 2026; later advisories can change what is
  vulnerable.

## Licence and attribution

The pairs are released under the MIT licence. The advisory facts they state come from the
**GitHub Advisory Database** (CC BY 4.0, © GitHub, Inc. and contributors,
https://github.com/github/advisory-database) and the PyPA Advisory Database (CC BY 4.0), through
[OSV](https://osv.dev). Keep that attribution when you reuse them. Thanks to Fexx and Lino for
the independent test pairs.

## Citation

```
@misc{adversarialeval2026,
  title  = {AdversarialEval: security review preference pairs},
  author = {Rita (Ritapossible)},
  year   = {2026},
  url    = {https://github.com/Ritapossible/AdversarialEval}
}
```
