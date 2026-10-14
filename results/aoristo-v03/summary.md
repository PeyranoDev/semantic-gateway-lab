# AoristoTech v0.3 exploratory results

Runs: 120; campaign calls: 8268; verified witness replays: 150.

Known defects and reviewed specification; no held-out discovery or significance claim.

| Property | Engine | Detected | Mean capped calls |
|---|---|---:|---:|
| CANCEL_REPLAY | random | 0/10 | 120.0 |
| CANCEL_REPLAY | sequence_enabled | 9/10 | 48.8 |
| CANCEL_REPLAY | sequence_enriched | 9/10 | 50.2 |
| CANCEL_REPLAY | sequence_uniform | 10/10 | 34.9 |
| INVITATION_SCOPE | random | 10/10 | 11.2 |
| INVITATION_SCOPE | sequence_enabled | 6/10 | 83.9 |
| INVITATION_SCOPE | sequence_enriched | 5/10 | 82.1 |
| INVITATION_SCOPE | sequence_uniform | 6/10 | 85.8 |
| READ_TENANT | random | 9/10 | 31.8 |
| READ_TENANT | sequence_enabled | 4/10 | 88.0 |
| READ_TENANT | sequence_enriched | 4/10 | 85.0 |
| READ_TENANT | sequence_uniform | 3/10 | 105.1 |

Misses use the full call budget. Shrinking, regression and validation calls are counted separately.
The only feedback-only comparison is sequence_enabled vs sequence_enriched.
Original and minimized traces are reexecuted through the original HTTP authorization path.
This study does not demonstrate that richer feedback always improves search.
