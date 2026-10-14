# Public real-backend case: AoristoTech

This is an owner-authorized extraction of the AoristoTech sales, purchases and
invitation backend, not a newly written toy implementation. Of 81 Python files,
62 are copied verbatim. The remaining files provide research-only settings,
bootstrap/package exports and a reduced ORM registry; unrelated model relationships
are omitted. Each file's status and hashes are in export-manifest.json. Original
business use cases, HTTP routes, authorization dependencies and SQL repositories
remain intact. The extraction's bounded equivalence is checked by replaying all
150 historical original/minimized HTTP witnesses from the full private application.

The source is by Ignacio Peyrano / PeyranoDev. See the repository license. No .env,
deployment configuration, production credentials, live data, external services or
vendored dependencies are included. The settings contain a clearly public fixture
key and a loopback disposable database default.

## Original and fixed versions

- original/backend/app contains the vulnerable real-source subset.
- fix.patch changes exactly 11 original modules and applies to the full backend too.
- export-manifest.json distinguishes copied source, adaptations and patched hashes.

The fixes enforce store-scoped sale/purchase lookup, a mandatory pending-sale
transition, one transaction for cancellation/stock restoration, unit/building
invitation scope, fail-closed unknown roles and PascalCase API responses mapped
from the actual snake_case invitation entities. Cancellation locks the sale row
and uses SQL increments for stock; failures roll back both effects.

## Run without private GitHub access

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r integrations/aoristo/requirements.lock
python -m scripts.materialize_aoristo --variant fixed --out /tmp/aoristo-fixed
docker run --rm -d --name sglab-case -p 127.0.0.1:55432:5432 \
  -e POSTGRES_DB=sglab_case -e POSTGRES_USER=lab -e POSTGRES_PASSWORD=lab \
  postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d
# Wait for pg_isready before the next command.
.venv/bin/python -m integrations.aoristo_case.run --variant fixed \
  --source /tmp/aoristo-fixed \
  --database-url postgresql://lab:lab@127.0.0.1:55432/sglab_case \
  --out results/local-aoristo-case
docker stop sglab-case
```

Use a new empty disposable database for every run. To reproduce the original
cases, use --variant original and --source case_studies/aoristo/original.
The fixed run includes the same 120 campaign conditions, historical regressions,
valid tasks, staff/resident scope, purchases, rollback injection and synchronized
concurrent HTTP cancellation with independent SQL sessions.

This subset and its tests do not establish general security of the application.
The historical v0.3 full-backend experiment remains unchanged. Public extraction,
known-regression mitigation and future held-out discovery are distinct claims.
