# AoristoTech v0.3 case-study protocol

## Scope and provenance

Source: private `PeyranoDev/AoristoTech`, app snapshot at
`f9420647c6fad86294032126a77b5d4880a11f21`. The public integration contains
synthetic fixtures, a specification, generator and adapter; it does not contain
the application's private implementation. All 216 app Python files are checked
against `integrations/aoristo/source-lock.json` before execution. Dependency
versions are frozen in `requirements.lock`. Access to the private source is
currently required to reproduce the full study.

This is another implementation/domain by the same author, not independently
authored external validation. The defects were identified during review before
the protocol and generator were written. All observations are exploratory and
known-defect evaluation; none is a held-out discovery claim.

## Execution boundary

Requests traverse the original full FastAPI application using an in-process ASGI
HTTP client. Headers, bearer authentication, service guards, routes, schemas,
use cases and SQLAlchemy repositories are original. Only `get_db` is overridden
to connect each request to an isolated program transaction. The source's JWT
issuer creates fixture credentials for existing synthetic DB users; login and
password security are not under test. No MCP transport or LLM agent is present.

PostgreSQL runs as a disposable GitHub Actions service. URLs must point to
loopback and a database named `sglab_*`. The adapter refuses a database containing
tables. The schema is created from the original ORM metadata, not migrated using
Alembic; production-schema behavior remains untested. Each serial program runs
in an outer rollback transaction, with source commits implemented as savepoint
releases. This retains observable effects between calls while resetting fixture
data between programs. It does not reproduce independent network transactions,
concurrent requests, durability failures or production transaction isolation.

## Fixture and adopted contract

Two stores, two buildings, one unit per building, four users and an unauthenticated
actor. Alice and Bob are admins in different stores; Ruth and Nina are residents
in different units/buildings. Each store initially has a pending three-unit sale
and stock 7; each unit has an invitation with one permitted use. Invitation tokens
are public test capabilities, never production credentials.

The specification requires:

- Individual sale reads/cancellations are within the authenticated store.
- A pending sale can be cancelled once; cancellation restores three units once.
- Creating, listing or revoking invitations is limited to the resident's own unit.
- Possession of an invitation capability is sufficient for the explicitly public
  consumption endpoint; at most one successful consumption is allowed here.
- Unauthorized actions must preserve observed business state; valid operations
  have exact expected effects. HTTP errors after writes are recorded separately.

These are explicit research policies. Confirm intended product policies with
the author before treating every discrepancy as a production vulnerability.
Snapshots cover Sales, InventoryItems and Invitations, not every table or field.
Activities/audit records and timestamps are intentionally outside the oracle.

Seven operations vary actor and fixture resource. Missing IDs are included.
Sale/invitation IDs are fixture-known; guessing IDs and obtaining capabilities
are not measured. Generated UUIDs, JWTs and capability tokens are omitted from
published observations. New invitation rows are normalized to stable names.
Pydantic validation details embedding randomly generated fixture UUIDs/times are
normalized to the schema name and validation-error count. HTTP status and all
observed business-state effects remain exact. In the pinned service, creation
can persist a row then translate response validation into HTTP 404; listing
existing invitations can return HTTP 500. These are separate behaviors.

## Controls and known regressions

Six seed programs must succeed under the specification before campaigns start:
own sale read/cancel for each store, own invitation revocation for each resident,
and public invitation consumption for each unit. Additional controls exercise
own-store lists, unauthenticated rejection, cross-product rejection, exhausted
invitations and revoked invitations. Regression witnesses are in a separate
module and never imported by the generator/campaign.

The reviewed regressions test repeated cancellation, foreign-store reading and
cancellation, foreign-unit invitation revocation/creation, and invitation
creation/list response serialization. A 500 response does not itself establish
a disclosure: actual response and persisted effects must be inspected.

## Exploratory search

Config `configs/aoristo-pilot.json`: ten fresh seeds 300–309; four engines;
three target properties; 120 HTTP calls per campaign; depth 8; corpus capacity 64.
This yields 120 runs. The unmodified backend contains multiple simultaneous
defects, so campaigns target one property at a time. Other specification failures
end that episode and are reported, but search continues until the target is
found or the budget is exhausted. Feedback only retains violation-free prefixes.

`random` draws operations/actors/resources uniformly and random program lengths.
The sequence engines bootstrap the same six valid tasks and use the same generic
field/insert/duplicate/delete/swap/splice mutation operators. `sequence_uniform`
samples seed programs without a feedback corpus. The two feedback engines use
the same FIFO bounded corpus and inverse-selection-count scheduler, with 80%
corpus sampling; only their projection differs.

`sequence_enabled` projects an existential union of lifecycle-enabled operations.
`sequence_enriched` also preserves named resource scope, sale lifecycle, stock
and invitation usage state. The latter is a rich full observable-state baseline,
not a proven minimal abstraction. These projections guide search only.

All execution calls, including seed bootstrap and repeated prefixes, consume the
campaign budget. Shrinking, regression and witness validation calls are reported
separately. Deletion minimization produces a 1-minimal witness for the target.
Every original and minimal detected witness is reexecuted from a clean fixture.

Detection rates, Wilson intervals over seeds and mean capped calls are descriptive.
Misses cost the entire budget. The paired enabled/enriched comparison isolates
the selected feedback representation within these matched engines. Random vs
seeded engines changes initialization and generation jointly. Small-sample
results cannot justify universal superiority, security guarantees or statistical
significance. Observed states are diagnostics, not coverage percentages.

## Reproduction

```bash
git clone https://github.com/PeyranoDev/semantic-gateway-lab.git
git clone https://github.com/PeyranoDev/AoristoTech.git ../AoristoTech
git -C ../AoristoTech checkout f9420647c6fad86294032126a77b5d4880a11f21
python3.12 -m venv .venv
.venv/bin/pip install -r integrations/aoristo/requirements.lock
docker run --rm -d --name sglab-postgres -p 127.0.0.1:55432:5432 \
  -e POSTGRES_DB=sglab_aoristo -e POSTGRES_USER=lab -e POSTGRES_PASSWORD=lab postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d
# Wait for pg_isready inside the disposable container before continuing.
.venv/bin/python -m integrations.aoristo.run --source ../AoristoTech \
  --database-url postgresql://lab:lab@127.0.0.1:55432/sglab_aoristo \
  --out results/local-aoristo
docker stop sglab-postgres
```

Use a fresh disposable container/database for every complete run. The source
checkout is required; public unit tests do not constitute HTTP/PostgreSQL evidence.
The private research workflow performs the same experiment without using Azure,
MercadoPago, email, or an existing application database. Future concurrency,
Alembic, MCP, LLM and independent held-out evaluations are separate phases.
