# Official RESTler execution: completed setup pilot (v0.7)

The official RESTler compiler, .NET driver and Python engine were built from
unmodified commit `6d984deedbc54aad957fa3da0c7e9e5df23a2aee`. The frozen lab
source commit is `8061df5a24e21eb8ca044bde39e5d0bcdabe6169`. The dedicated
[workflow](https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38632820433)
completed successfully on 14 October 2026. This replaces the earlier status
"external tool not executed" with an executed, explicitly limited setup pilot.
It does not complete a definitive comparison of RESTler's capabilities.

## Design and measured costs

See [the frozen protocol](../docs/restler-pilot-protocol.md). Five assemblies,
four generation treatments and three fresh seed labels 700–702 produce **60
campaigns**. All use TCP, the same real backend, identities/resources, sequence
reset fixture and common HTTP/SQL business oracle. The dispatched search budget
is 1,200 calls and depth is 8. The stopping rule is the first discrepancy of any
oracle property, rather than the target-specific stopping rule of v0.5/v0.6.
Native RESTler checkers are disabled; these are generation-plus-common-observer
results, not reports from RESTler's native security rules.

- **44,808** dispatched search calls.
- **31** discovered campaign witnesses, each exactly revalidated in the runner.
- **45,351** normalized HTTP transitions checked again from archived SQL states.
- **0** infrastructure errors, outside-domain search calls, premature tool exits
  or wall-time cutoffs. Every campaign stops at the oracle or request bound.
- Four identity logins per assembly: **20** authentication calls.
- Eight valid tasks and four known-defect controls per assembly: **60 controls**,
  **170** business calls. The controls are excluded from search.
- Official RESTler test-mode smoke: **103** dispatched business calls, also
  excluded from search. Thus smoke plus controls is **273** calls.
- **270** post-search business calls include internal-generator minimization and
  runner witness revalidation. They are excluded from search and separately
  preserved in the journals; they are not additional discovered campaigns.
- **4,479** loopback HTTP control calls, **5** readiness calls and **28** rejected
  post-bound requests. Total HTTP requests reaching the wrapper: **49,883**.
  The **13,897** implicit sequence resets are SQL harness operations, not
  additional HTTP requests. They are separately recorded.

The portable/HTTP test suite has **132 tests** after adding ten integration
checks. All tests passed in the execution workflow. An additional local TCP
replay on Python 3.12.14 reproduces **all 31 witnesses** with **84 business calls**
and **16 fixture logins**. This is replication of the same finite observations,
not validation by an independent author or on another service.

## Detection observations

Cells below are detected seed labels / three, followed by mean calls capped at
the budget. No significance tests or uncertainty intervals are attached to this
setup pilot. In particular, all three seed labels yield **identical complete
search streams** for each of the ten RESTler variant/strategy groups, checked by
hashing normalized actions, responses, SQL states and discrepancies. They are
repeated deterministic executions, not three independent stochastic samples.

| Treatment | Cross-scope read | Overbooking | Unpaid confirmation | Repeated refund |
|---|---:|---:|---:|---:|
| Official RESTler BFS | 3/3 (12.0) | 3/3 (1190.0) | 0/3 (1200.0) | 0/3 (1200.0) |
| Official RESTler BFS-cheap | 0/3 (1200.0) | 3/3 (131.0) | 3/3 (752.0) | 0/3 (1200.0) |
| Internal random | 3/3 (19.3) | 2/3 (673.3) | 2/3 (639.7) | 0/3 (1200.0) |
| Internal valid-workflow mutation | 3/3 (341.3) | 3/3 (96.7) | 3/3 (46.7) | 3/3 (234.0) |

Each treatment also ran three fixed controls at all 1,200 calls, with no observed
discrepancy: **12 campaigns and 14,400 search calls**. These bounded observations
do not establish general absence of defects.

The witnessed business errors match the omitted guards. A native generator can
produce a business-rule violation that our observer detects even when RESTler's
own checker/reporting configuration is disabled. Do not describe the table as
31 native RESTler security reports or conflate HTTP failures with oracle findings.

## Reachability findings and limitations

RESTler's initial test-mode smoke succeeds for list, read and reserve, but does
not execute pay, confirm, cancel or refund successfully. Requests to those routes
are present and denied; route presence is not business-state reachability.
Under the fixed assembly during measured search:

| Treatment | Successful business operations |
|---|---|
| RESTler BFS | list, read, reserve |
| RESTler BFS-cheap | list, read, reserve, pay |
| Internal random | list, read, reserve, pay, cancel |
| Valid-workflow mutation | all seven, including confirm and refund |

No tested RESTler strategy reaches refund successfully under the supplied
unannotated dictionary and 1,200-call bound. Its zero refund finding therefore
does not establish an intrinsic inability to detect replayed refunds. The task
library gives our seeded generator business-history knowledge that this RESTler
input lacks. No response-id dependency is inferred in this existing-resource
domain and no manual business ordering annotation is supplied. This is a
substantive treatment difference, not a hidden implementation benefit.

BFS also catches cross-scope reading at 12 calls, well before this seeded
mutator's mean of 341.3; BFS-cheap misses that defect in this bound while finding
capacity and confirmation faults. These counter-results reinforce the need to
publish per-property behavior and exploration strategy rather than one winner.

The pilot does not test RESTler's default BFS-fast, random-walk, native active
checkers, larger budgets, a resource-creating grammar or any independent backend.
With native checkers enabled, reset-on-header would be unsuitable: some checker
requests create fresh trace IDs while relying on earlier effects. A future
checker experiment must establish its isolation separately.

## Evidence and next measured step

The [complete Actions artifact](https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38632820433/artifacts/11927202027)
preserves the **exact** measured output bytes,
SHA-256 `97e6ff731a4f15869af17f247e06fef82669ba7daa7ab16e598fc3f1f0df3dee`.
It contains 357 files: original compiler outputs/grammar, generated dictionaries,
settings, invocation/exit records, native logs, raw compressed HTTP/SQL journals,
controls, campaign observations and source/output hashes. Native text session
values are replaced with fixture labels; reproduce executable credentials by
public fixture login. Force-stopped fuzz invocations do not have a finalized
native testing summary; invocation records and the observation journal are the
complete source of budget/finding counts. The completed native test-mode report
and all native logs produced before termination remain archived.

The exact ZIP is now also committed as `results/restler-v07/archive.zip` on the
v0.8 research branch. Preservation run 38753068080 checked its SHA-256 and all
archived observations before committing it. Verification works directly after
checkout; no expiring Actions download or separate root controls.json is needed.
The original measured source and artifact hash are unchanged.

```bash
python -m scripts.analyze_restler_pilot
python -m scripts.replay_restler_pilot
```

The next scientific step is to validate a stronger RESTler configuration using
ordinary valid workflow dependencies and additional documented strategies, with
all supplied knowledge disclosed. Require successful fixed-service reachability
of the legitimate lifecycle before freezing a larger new comparison. Do not
optimize annotations on mutant outcomes, pool this pilot with that follow-up, or
use three deterministic labels to claim a statistical RESTler defeat. External
policy review and a separately authored service remain outstanding.
