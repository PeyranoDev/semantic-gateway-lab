# Official RESTler integration — v0.7 setup pilot

This is an execution/setup pilot, not a preregistered definitive superiority
comparison. Its configuration is committed before CI execution. Historical
v0.5/v0.6 data are not pooled with it. No backend, generator or oracle from
those studies is modified.

## Immutable upstream and scope

- Official repository: https://github.com/microsoft/restler-fuzzer
- Commit: `6d984deedbc54aad957fa3da0c7e9e5df23a2aee`.
- Build the unmodified compiler, .NET driver and Python engine using upstream
  `build-restler.py`; .NET 8 and Python 3.12. Disable telemetry.
- Existing-resource domain: GET list/read and POST reserve/pay/confirm/cancel/
  refund. Login, create and health are outside generation, as in v0.5/v0.6.
- OpenAPI 3.0.3 documents that finite subset of the actual API. A contract test
  checks its route set. No response-id dependencies, examples, annotation,
  failing program or target label is supplied to RESTler. Resources are already
  provisioned, and no operation creates resources in the measured domain.
- Dictionary: five existing-resource labels and four signed identities plus an
  empty Authorization value for anonymous access. All come from the public
  synthetic fixture, never from production data. Inputs are shared by variants.
- The generated Python grammar is archived. No hand-authored RESTler engine or
  replacement grammar is used. Our internal `seed_extend` is unrelated to it.

## Controls before search

Run all eight valid tasks and four known-defect controls for every assembly over
TCP using the same wrapper and SQL snapshots. These controls validate the
measurement; they are outside the measured generators and dictionary. After
compilation, execute official RESTler `test` mode and archive reachability and
native diagnostics. A route that is only denied is not successfully covered.
Lack of business-state dependencies may make some valid tasks unreachable in
test mode; publish that setup limitation rather than claiming a tool defect.

## Pilot settings, fixed before execution

`configs/restler-pilot.json` defines:

- Five assemblies: fixed plus the four historical single-guard omissions.
- Three fresh seed labels 700–702; a label does not equate random streams across
  implementations, and seeds may not change deterministic BFS behavior.
- Official RESTler BFS and BFS-cheap; internal random and workflow-seeded uniform
  mutation. 5 × 4 × 3 = 60 campaigns.
- 1,200 dispatched search calls, depth 8, 25 RESTler parameter combinations,
  corpus capacity 64 for the internal generator. A wall ceiling of 90 seconds
  per RESTler invocation is an infrastructure guard, not a request-cost metric.
- Stop at the first discrepancy of the common business oracle, the hard call
  budget, tool completion, or wall ceiling. Any violation is the stopping event;
  this differs from v0.5/v0.6's mutant-specific target campaigns.
- Disable all native checkers. The estimand is external **generation** under a
  common observer. This pilot does not evaluate RESTler's security-checker suite
  or imply its oracle alone would report every business-rule discrepancy.
- BFS/cheap are only two of RESTler's strategies. In particular, random-walk and
  default BFS-fast are not tested here; no claim about all RESTler modes follows.

## Isolation and costs

The disposable Uvicorn wrapper binds only to 127.0.0.1. No endpoint is added to
the reusable business backend. Both generators use TCP, real signed sessions,
the same fixture, SQLite commits and the same separately specified oracle.
The wrapper serializes each observed HTTP request and brackets it with SQL
snapshots. It resets the fixture when a new sequence arrives. RESTler supplies
`x-restler-sequence-id`; the internal adapter supplies `x-lab-sequence` and an
explicit loopback reset control before its own SQL snapshot. Resets have the
same state effect; internal control HTTP calls are recorded separately.

RESTler's cached-prefix option is set to an empty `create_prefix_once` list so
the prefix is re-executed even for reads. Requests without a sequence ID or
noncontiguous reuse are infrastructure errors. No resource deletion/GC request
exists in this finite grammar. The server rejects any additional search request
after the budget/first failure **before** invoking the backend. Those guard
responses are archived separately and are not backend bugs or dispatched calls.
The controller terminates the process group and retains the stop reason and
exit code. A deliberate SIGTERM at a reached bound is not a tool crash.

Login, readiness, reset, smoke, validation and independent replay costs are
recorded outside search. Every dispatched generated request, including a denial
or outside-domain request, consumes the budget. Outside-domain actions remain
in the journal with snapshots and are never silently counted as negatives under
an oracle that cannot represent them. A generator's discovered trace must match
an independent TCP replay exactly: action, response, SQL states and violations.

## Preservation, exclusions and interpretation

Keep the partial output of every infrastructure failure and every repair as a
distinct attempt. Never overwrite an attempt or pool repair reruns as new
independent observations. Infrastructure failure, missing ID, process failure,
zero measured HTTP calls, outside-domain traffic or premature time exhaustion
are setup findings and prevent a definitive efficacy interpretation. Natural
completion below budget is reported as such, not padded to the budget.

Archive source/configuration hashes, raw request observations, successful
operation coverage, response codes, witnesses/replays, exact invocation, grammar
and native RESTler reports. Suppress session strings in HTTP journals and replace
them in native text artifacts with `<fixture-session:actor>` after execution.
These text artifacts are documentation; reproduce executable dictionaries by
running the public fixture login and `write_inputs`, not by reusing expired or
redacted credentials. No authorization value or password is stored in a journal.

Do not tune generation after observing detection and call the pilot a confirmatory
test. Inspect setup/coverage, specify any annotated or checker-enabled follow-up
as a different treatment, then freeze a larger matrix with new seeds. Enabled
checkers require another isolation strategy: upstream `checker_base.py` can start
new sequence traces for individual checker requests, so sequence-header resets
would destroy checker preconditions. Retain native findings separately from the
branch/role business oracle in that future study.

An independently authored service or independent policy review remains necessary
for external validity; this pilot still uses our authored salon fixture.

## Reproduce

```bash
python -m pip install -r backends/salon/requirements.lock applicationinsights==0.11.10
git clone https://github.com/microsoft/restler-fuzzer.git /tmp/restler-upstream
git -C /tmp/restler-upstream checkout 6d984deedbc54aad957fa3da0c7e9e5df23a2aee
python /tmp/restler-upstream/build-restler.py --dest_dir /tmp/restler-bin
RESTLER_TELEMETRY_OPTOUT=1 python -m integrations.restler.run \
  --restler /tmp/restler-bin/restler/Restler --upstream /tmp/restler-upstream \
  --out /tmp/restler-pilot
```

The dedicated GitHub Actions workflow installs .NET because the local authoring
environment lacks it. The workflow artifacts, not prepared source alone, establish
whether the official tool actually built and ran successfully.
