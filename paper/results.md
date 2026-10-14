# Measured results and interpretation

Research artifact v0.1; synthetic finite-domain evaluation. No general security
guarantee or statistical superiority claim follows from these measurements.

## Directed regression validation

All 44 automated tests pass locally on Python 3.12. Eight directed witnesses
produce their expected independent-oracle violations in their corresponding
implementation mutants. The same action sequences are handled without violations
in the fixed service, with their final unauthorized action denied. An accepted
legitimate workflow exercises all ten tools and checks actual observable effects.

The suite includes cross-process hash-seed reproducibility, capped-budget accounting,
censoring-aware summaries, minimal-trace replay, output-directory protection,
denial atomicity and an abstraction counterexample. This is validation of the
artifact, not evidence that the stochastic generator finds every seeded defect.
Only Python 3.12 was executed locally; the CI matrix is prepared but not run remotely.

## Bounded abstraction counterexample

`python -m fuzzlab analyze` observes five reachable business states with five
sharing actions and maximum depth three. Two prefixes issue a sharing request
for Bob or Mallory. Their coarse tool-enabledness labels are equal. The identical
subsequent `accept_share(actor=bob, document=d1)` is authorized in the first state
and denied in the second. The enriched key separates them. No further collision
was found for the enriched projection in this tiny explored submodel; that is
not a general soundness result.

## Final pilot

270 runs, ten seeds per defect/strategy, 1500-call budget and depth twelve.
242,987 backend calls were actually executed before stop conditions. The fixed
control had zero observed violations in 30 campaigns (45,000 calls).

| Implementation variant | Random hits | Enabled hits | Enriched hits |
|---|---:|---:|---:|
| cross_department_read | 10/10 | 10/10 | 10/10 |
| wrong_recipient | 4/10 | 10/10 | 5/10 |
| sharing_overwrite | 0/10 | 2/10 | 0/10 |
| unauthorized_revoke | 5/10 | 10/10 | 10/10 |
| approval_scope | 5/10 | 5/10 | 7/10 |
| approval_replay | 0/10 | 0/10 | 0/10 |
| missing_approval | 5/10 | 9/10 | 9/10 |
| deny_audit | 10/10 | 10/10 | 10/10 |
| fixed control | 0/10 | 0/10 | 0/10 |

The pilot does not show a uniform benefit from predicate enrichment. For wrong
recipient acceptance the simpler guided corpus has a higher observed detection
fraction; for approval scope the enriched corpus has a higher fraction. Ten
seeds yield broad uncertainty intervals, supplied in the CSV. These contrasts
must not be described as established significant differences.

The approval-replay mutant remains undiscovered by all stochastic strategies
at this budget, despite its five-call directed witness. The method needs a
valid request, scoped deletion, recreation, another request and reuse of the
same consumed token in the relevant episode. A known reachable counterexample
does not imply high discovery probability under the current uniform arguments.

Preserving relational information resolves the explicit counterexample but does
not by itself improve the scheduler. Corpus fragmentation and replay overhead are
candidate explanations to test with ablations, not causal conclusions from this pilot.

## Additional matrix

810 runs, thirty seeds per variant/strategy, a 10,000-call budget and depth twenty. 2,990,117 backend calls were executed. The fixed control had zero observed violations in 90 campaigns (900,000 calls). This is a larger-budget reserved-seed evaluation, not a pure seed-only replication or independently preregistered experiment.

| Implementation variant | Random hits | Enabled hits | Enriched hits |
|---|---:|---:|---:|
| cross_department_read | 30/30 | 30/30 | 30/30 |
| wrong_recipient | 28/30 | 30/30 | 30/30 |
| sharing_overwrite | 2/30 | 28/30 | 13/30 |
| unauthorized_revoke | 30/30 | 30/30 | 30/30 |
| approval_scope | 26/30 | 30/30 | 30/30 |
| approval_replay | 0/30 | 0/30 | 0/30 |
| missing_approval | 29/30 | 30/30 | 30/30 |
| deny_audit | 30/30 | 30/30 | 30/30 |
| fixed | 0/30 | 0/30 | 0/30 |

The coarse guided method finds the overwrite defect in 28/30 runs, versus 13/30 for the enriched method and 2/30 for random testing. Both guided methods detect wrong-recipient and approval-scope mutants in every observed reserved-seed run, but coarse guidance has lower mean capped call effort on those variants. No stochastic strategy detects approval replay at this budget. These are descriptive benchmark findings; they do not establish a general ranking or an optimal abstraction.

Across both matrices, 722 detected runs have had their original and minimized witnesses replayed successfully, and the minimized witnesses yield no oracle violation on the fixed service. Source hashes match the delivered implementation.

## Interpretation boundaries

Unit-test success, seeded-mutant detection, observed graph coverage and a universal
proof of security are different forms of evidence. Timings come from concurrently
executed local campaigns and are not a comparative performance benchmark. The next
study should use independent defect families and implementations and separately
evaluate finer predicates, corpus scheduling and relation-preserving mutation.
