# Public real-backend case and mitigation validation

The owner's requested public extraction now makes the selected AoristoTech case
executable without private GitHub access. It contains 81 Python files: 62 copied
verbatim, 19 adaptations for bootstrap/configuration, exports and the ORM registry.
The same patch changes 11 real application modules and was tested on both the
public subset and the full private application. All adaptations are identified;
the subset is not claimed to be identical to the complete enterprise application.

## Evidence

| Execution | Checks | Campaigns | Campaign calls | Total HTTP calls |
|---|---:|---:|---:|---:|
| Public original subset | 19 | Historical witness replay | 0 | 288 |
| Public fixed subset | 21 | 120 | 14,400 | 14,438 |
| Full fixed AoristoTech application | 21 | 120 | 14,400 | 14,438 |

The original subset reproduces all **150 historical original/minimized witness
traces** exactly at the recorded semantic boundary. This is bounded equivalence
over those observations, not a proof of equivalence for every operation or input.
The corrected counterparts produce **no target or other oracle discrepancy** in
the finite campaign. The seven reviewed regressions now give these results:

| Case | Original | Corrected |
|---|---|---|
| Cancel sale twice | 200/200, stock 7 → 10 → 13 | 200/400, stock stays 10 |
| Read another store's sale | 200 | 404 |
| Cancel another store's sale | 200 with stock effect | 404 without effect |
| Revoke another unit's invitation | 200 with deletion | 403 without effect |
| Create another unit's invitation | 404 after row creation | 403 without effect |
| Create own-unit invitation | 404 after row creation | 201 with correct response fields |
| List own-unit invitations | 500 | 200 |

Additional checks verify purchase read/update isolation, staff access within its
building, unknown-role rejection, nonpending-sale rejection, missing-record 404,
and successful creation plus single-use consumption of an invitation.

Cancellation is corrected at the SQL transaction boundary. A forced failure after
inventory restoration rolls back the stock and sale status. Two synchronized HTTP
cancellations use independent SQL sessions and converge to **200/400**, with
stock restored once. These tests were run on both corrected counterparts, outside
the serial savepoint isolation used by the campaigns.

Public validation: https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38610191671.
Full-application validation: https://github.com/PeyranoDev/AoristoTech/actions/runs/38609721094.
Application correction: https://github.com/PeyranoDev/AoristoTech/pull/45.

## Interpretation and limits

This is mitigation of reviewed natural discrepancies in the same author's code,
not independent or held-out vulnerability discovery. The source subset preserves
the chosen routes, use cases and repositories, while adapting its bootstrap and
model registry. Tests use PostgreSQL 16.15, Python 3.12.15 and synthetic fixtures;
the schema comes from ORM metadata rather than live Alembic migrations. Concurrent
cancellation and rollback are directly tested, but broader concurrency, QR races,
payments, deployment configuration, MCP and LLM behavior remain outside this study.

The v0.3 baseline data and measured engine are frozen. Public fixed results use
the same action domain, seeds, modes and per-call budget; no failures in 14,400
campaign calls establish only bounded observed agreement with the adopted contract.

## Reproduce

See case_studies/aoristo/README.md. Public data validation requires no DB:

```bash
python -m scripts.analyze_aoristo_case
```
