
### round-2

| Target | Node rank | Correct / answerable | Accuracy (95% CI) | Valid verdicts / delivered / calls | Charged: headers / on-chain | Cost per correct (95% CI) | Cost per correct, on-chain | Median ms |
|---|---:|---:|---|---:|---:|---|---:|---:|
| a1-preflight | 7 | 27/36 | 75% (59% to 86%) | 46/46/46 | $0.46 / $0.46 | $0.017 ($0.014 to $0.023) | $0.017 | 402 |
| osv-baseline (free) | n/a | 24/36 | 67% (50% to 80%) | 26/26/46 | $0.00 / $0.00 | $0.000 ($0.000 to $0.000) | $0.000 | n/a |
| telegraph-verity-intelligence | 26 | 8/36 | 22% (12% to 38%) | 16/16/46 | $0.46 / $0.46 | $0.058 ($0.035 to $0.153) | $0.058 | 285 |
| zk-secaudit | 29 | 7/36 | 19% (10% to 35%) | 20/23/46 | $0.46 / $0.46 | $0.066 ($0.038 to $0.153) | $0.066 | 562 |
| auto-routed | n/a | 5/36 | 14% (6% to 29%) | 22/46/46 | $0.46 / $0.46 | $0.092 ($0.051 to $0.460) | $0.092 | 430 |
| zk-ghsapub | unranked | 3/36 | 8% (3% to 22%) | 3/11/46 | $0.14 / $0.46 | $0.047 ($0.022 to $0.150) | $0.153 | 2350 |
| zk-secpub | 5 | 2/36 | 6% (2% to 18%) | 2/11/46 | $0.14 / $0.46 | $0.070 ($0.028 to $0.170) | $0.230 | 2259 |
| codewire-security-review | 2 | 2/36 | 6% (2% to 18%) | 7/14/46 | $0.17 / $0.42 | $0.085 ($0.033 to $0.210) | $0.210 | 5193 |
| zk-pysec | 3 | 1/36 | 3% (0% to 14%) | 1/10/46 | $0.13 / $0.46 | $0.130 ($0.035 to $0.180) | $0.460 | 1461 |
| zk-astsec | 27 | 1/36 | 3% (0% to 14%) | 2/2/46 | $0.46 / $0.46 | $0.460 ($0.115 to $0.460) | $0.460 | 29 |
| zk-friendsec | 28 | 0/36 | 0% (0% to 10%) | 0/0/46 | $0.45 / $0.46 | n/a | n/a | n/a |
| pr-guard-sentinel | 1 | 0/36 | 0% (0% to 10%) | 0/12/46 | $0.12 / $0.12 | n/a | n/a | 10 |
| evidence-security-review | 10 | 0/36 | 0% (0% to 10%) | 0/0/46 | $0.46 / $0.46 | n/a | n/a | n/a |
| zk-code-deps | 28 | 0/36 | 0% (0% to 10%) | 0/0/46 | $0.46 / $0.46 | n/a | n/a | n/a |

Kendall's tau-b, node rank vs accuracy over 11 ranked miners: +0.02
