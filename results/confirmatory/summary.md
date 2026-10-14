# Descriptive campaign results

Synthetic implementation mutants; finite fixture; first violation per run.
Misses are right-censored at the call budget. Replays count toward that budget.
Wilson intervals describe variation over seeds in this benchmark, not real-world breach probability.
Conditional medians omit misses; use capped effort and detection rate together.

| Variant | Strategy | Hits / seeds | 95% Wilson interval | Mean capped calls | Mean concrete states |
|---|---|---:|---:|---:|---:|
| approval_replay | enabled | 0/30 | 0.00-0.11 | 10000.0 | 200.7 |
| approval_replay | enriched | 0/30 | 0.00-0.11 | 10000.0 | 194.6 |
| approval_replay | random | 0/30 | 0.00-0.11 | 10000.0 | 123.1 |
| approval_scope | enabled | 30/30 | 0.89-1.00 | 1454.6 | 44.0 |
| approval_scope | enriched | 30/30 | 0.89-1.00 | 1920.2 | 51.2 |
| approval_scope | random | 26/30 | 0.70-0.95 | 3700.5 | 62.0 |
| cross_department_read | enabled | 30/30 | 0.89-1.00 | 7.4 | 1.4 |
| cross_department_read | enriched | 30/30 | 0.89-1.00 | 7.4 | 1.4 |
| cross_department_read | random | 30/30 | 0.89-1.00 | 10.4 | 1.3 |
| deny_audit | enabled | 30/30 | 0.89-1.00 | 1.1 | 1.1 |
| deny_audit | enriched | 30/30 | 0.89-1.00 | 1.1 | 1.1 |
| deny_audit | random | 30/30 | 0.89-1.00 | 1.3 | 1.1 |
| fixed | enabled | 0/30 | 0.00-0.11 | 10000.0 | 200.7 |
| fixed | enriched | 0/30 | 0.00-0.11 | 10000.0 | 194.6 |
| fixed | random | 0/30 | 0.00-0.11 | 10000.0 | 123.1 |
| missing_approval | enabled | 30/30 | 0.89-1.00 | 770.6 | 27.6 |
| missing_approval | enriched | 30/30 | 0.89-1.00 | 892.1 | 29.2 |
| missing_approval | random | 29/30 | 0.83-0.99 | 1877.8 | 40.0 |
| sharing_overwrite | enabled | 28/30 | 0.79-0.98 | 4582.7 | 105.0 |
| sharing_overwrite | enriched | 13/30 | 0.27-0.61 | 8263.8 | 164.8 |
| sharing_overwrite | random | 2/30 | 0.02-0.21 | 9513.7 | 118.0 |
| unauthorized_revoke | enabled | 30/30 | 0.89-1.00 | 597.2 | 22.3 |
| unauthorized_revoke | enriched | 30/30 | 0.89-1.00 | 838.9 | 25.8 |
| unauthorized_revoke | random | 30/30 | 0.89-1.00 | 1095.8 | 27.1 |
| wrong_recipient | enabled | 30/30 | 0.89-1.00 | 517.6 | 22.5 |
| wrong_recipient | enriched | 30/30 | 0.89-1.00 | 1088.7 | 33.1 |
| wrong_recipient | random | 28/30 | 0.79-0.98 | 2527.6 | 47.7 |

Abstraction sizes are diagnostics, not comparable coverage percentages.
Fixed-control hits would indicate a defect in the implementation or specification.
