# Descriptive campaign results

Synthetic implementation mutants; finite fixture; first violation per run.
Misses are right-censored at the call budget. Replays count toward that budget.
Wilson intervals describe variation over seeds in this benchmark, not real-world breach probability.
Conditional medians omit misses; use capped effort and detection rate together.

| Variant | Strategy | Hits / seeds | 95% Wilson interval | Mean capped calls | Mean concrete states |
|---|---|---:|---:|---:|---:|
| approval_replay | enabled | 0/10 | 0.00-0.28 | 1500.0 | 40.7 |
| approval_replay | enriched | 0/10 | 0.00-0.28 | 1500.0 | 39.8 |
| approval_replay | random | 0/10 | 0.00-0.28 | 1500.0 | 29.0 |
| approval_scope | enabled | 5/10 | 0.24-0.76 | 1138.5 | 34.2 |
| approval_scope | enriched | 7/10 | 0.40-0.89 | 1171.0 | 33.7 |
| approval_scope | random | 5/10 | 0.24-0.76 | 1130.2 | 24.5 |
| cross_department_read | enabled | 10/10 | 0.72-1.00 | 13.6 | 2.1 |
| cross_department_read | enriched | 10/10 | 0.72-1.00 | 13.6 | 2.1 |
| cross_department_read | random | 10/10 | 0.72-1.00 | 11.1 | 1.3 |
| deny_audit | enabled | 10/10 | 0.72-1.00 | 1.6 | 1.3 |
| deny_audit | enriched | 10/10 | 0.72-1.00 | 1.6 | 1.3 |
| deny_audit | random | 10/10 | 0.72-1.00 | 1.1 | 1.0 |
| fixed | enabled | 0/10 | 0.00-0.28 | 1500.0 | 40.7 |
| fixed | enriched | 0/10 | 0.00-0.28 | 1500.0 | 39.8 |
| fixed | random | 0/10 | 0.00-0.28 | 1500.0 | 29.0 |
| missing_approval | enabled | 9/10 | 0.60-0.98 | 699.1 | 25.4 |
| missing_approval | enriched | 9/10 | 0.60-0.98 | 925.9 | 29.1 |
| missing_approval | random | 5/10 | 0.24-0.76 | 1130.2 | 24.5 |
| sharing_overwrite | enabled | 2/10 | 0.06-0.51 | 1426.1 | 39.4 |
| sharing_overwrite | enriched | 0/10 | 0.00-0.28 | 1500.0 | 39.8 |
| sharing_overwrite | random | 0/10 | 0.00-0.28 | 1500.0 | 29.0 |
| unauthorized_revoke | enabled | 10/10 | 0.72-1.00 | 432.0 | 16.4 |
| unauthorized_revoke | enriched | 10/10 | 0.72-1.00 | 631.6 | 19.4 |
| unauthorized_revoke | random | 5/10 | 0.24-0.76 | 1172.3 | 25.5 |
| wrong_recipient | enabled | 10/10 | 0.72-1.00 | 420.7 | 15.1 |
| wrong_recipient | enriched | 5/10 | 0.24-0.76 | 839.7 | 24.2 |
| wrong_recipient | random | 4/10 | 0.17-0.69 | 1138.8 | 23.6 |

Abstraction sizes are diagnostics, not comparable coverage percentages.
Fixed-control hits would indicate a defect in the implementation or specification.
