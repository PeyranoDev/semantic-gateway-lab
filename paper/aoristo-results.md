# AoristoTech: HTTP/PostgreSQL case study

## What was executed

The unmodified AoristoTech app snapshot identified by its aggregate fingerprint
was exercised through its original
FastAPI ASGI HTTP pipeline and SQLAlchemy repositories, using PostgreSQL 16.15
and Python 3.12.15. The measured public harness commit is
`835e35ee55cc907aa4dd2e0b905ba840dd4e1288`.

The successful research run is
https://github.com/PeyranoDev/AoristoTech/actions/runs/38601878137.
Full commit provenance, individual backend-file metadata and installed-package
inventory remain in the private research branch. Only synthetic observations and
public harness code are included here. The backend implementation remains private.

All 216 app Python files match the source lock. Dependencies are pinned, and the
PostgreSQL image digest is recorded in the reproduction protocol. The ORM schema
was created from metadata, not production migrations. Original commit calls
release savepoints in an outer serial rollback transaction. Authentication and
authorization were not replaced; login, independent network transactions,
concurrency, MCP and LLM agents were not evaluated.

## Controls and reviewed regressions

Eleven controls passed, including all six legitimate seed programs, cross-product
and unauthenticated rejection, invitation exhaustion and revocation. Seven known
regressions were reproduced:

| Case | Observed response and effect |
|---|---|
| Cancel the same pending sale twice | Both calls return 200; stock goes 7 → 10 → 13. |
| Read a sale in another store | 200 returns the other store's sale. |
| Cancel a sale in another store | 200 cancels that sale and increases its store's stock. |
| Revoke an invitation in another unit/building | 200 deletes the other unit's invitation. |
| Create an invitation in another unit/building | 404 is returned after the new invitation row is stored. |
| Create an invitation in the resident's own unit | 404 is returned after storage because response-schema validation fails. |
| List existing invitations in the resident's own unit | 500 from response-schema validation. |

The last row does not establish token disclosure. The scope violation in the
foreign-unit creation case is established by the observed row, despite its 404.
Volatile fixture UUIDs/times embedded in Pydantic error details are normalized to
schema name and error count; response status and business-state effects remain
exact. The policy is the explicitly adopted store/unit isolation contract, not
an independently reviewed product requirements document.

## Exploratory search results

Three target properties × four engines × ten seeds (300–309) = **120 campaigns**.
Each run permits 120 HTTP calls, depth 8 and corpus capacity 64. All seed bootstrap
and repeated-prefix calls consume that budget. Other property failures end the
episode and are counted; search continues for the designated target.

Each cell shows **detections / 10; mean capped HTTP calls**. Misses cost 120 calls.

| Property | Random programs | Seed mutation without corpus | Enabled-tool feedback | Enriched state feedback |
|---|---:|---:|---:|---:|
| Repeated cancellation | 0/10; 120.0 | 10/10; 34.9 | 9/10; 48.8 | 9/10; 50.2 |
| Foreign-store sale reading | 9/10; 31.8 | 3/10; 105.1 | 4/10; 88.0 | 4/10; 85.0 |
| Invitation scope | 10/10; 11.2 | 6/10; 85.8 | 6/10; 83.9 | 5/10; 82.1 |

The matrix consumes **8,268 campaign calls**. Shrinking adds 175 calls, regression
controls/witnesses 24 calls, and fresh original/minimal witness verification 261
calls. Building the minimized traces adds another 103 calls, derived from their
recorded lengths: **8,831 HTTP executions** across all stages. The original
manifest lists the first four categories; offline validation reports the
additional post-shrink trace calls explicitly. There are **75
detected campaigns**; all 150 original/minimal witness replays match their recorded
semantic observations. Offline validation additionally checks raw hashes,
source/config/harness identity, matrix completeness, state continuity, oracle
outcomes, summaries and cost totals.

Raw SHA-256:
`7a450d5636ea94ddc856b8c66d7d4e10216685953e4ca3c3fbcb530bbb53af07`.

Wilson intervals and complete per-seed observations are in
`results/aoristo-v03/summary.json` and `raw.jsonl.gz`. For example, 0/10 still has
a Wilson upper bound about 0.278, and 10/10 a lower bound about 0.722.

## Interpretation

Legitimate workflow seeds plus generic mutation make the history-dependent
cancellation defect easier to reach under this small budget. This comparison
changes seeding and generation jointly; it does not isolate mutation alone.
Conversely, uniformly generated programs find the single-step scope defects
more often and with lower capped effort. The seeded engines are therefore not
a general replacement for random exploration in this domain.

The only feedback-only comparison is the matched enabled/enriched pair. Both
detect replay in 9/10 runs, and enrichment increases mean capped replay effort
by 1.4 calls. Reading detection is 4/10 for each, with one exclusive detection on
each side. Invitation scope loses one detection under enrichment, while mean
capped effort decreases by 1.8 calls. These small, mixed differences do not
establish an enrichment advantage or statistical significance. Enrichment here
preserves full observed resource/stock/usage state and can fragment the corpus;
its causal contribution has not been isolated through capacity/retention trials.

These are reviewed natural discrepancies in another implementation by the same
author. Neither the policies nor defect selection are independent or held out.
The fixture covers two stores, two buildings, four users and seven operations;
the observer covers selected business tables. A fixed-backend counterpart,
fresh-seed replication, independent policy review and additional domains are
needed before stronger generalization or deployment claims.

## Reproduce and inspect

See `docs/aoristo-protocol.md` for private-source execution. Public artifact
validation needs no private repository or database:

```bash
python -m scripts.analyze_aoristo
python -m unittest discover -s tests -v
```
