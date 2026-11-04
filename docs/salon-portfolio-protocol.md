# v0.8: budget-balanced portfolio, frozen before execution

## Motivation and scope

The reviewed v0.5–v0.7 observations suggest a tradeoff: random generation readily
exposes scope errors while valid-workflow mutation reaches history-sensitive faults.
We test a fixed portfolio, inspired by established ensemble fuzzing [15], without
claiming a new ensemble algorithm or implementing EnFuzz. EcoFuzz [16] motivates
careful resource accounting; our scheduler is deliberately non-adaptive and uses
neither coverage rewards nor a bandit. Evaluation cautions in Klees et al. [17]
motivate repeated seeds, complete reporting, and explicit experimental units.

This follow-up is informed by observed defects. Seeds 800–829 are fresh, but the
four defects and authored backend are NOT held out. No defect, oracle, legitimate
seed, mutation operator or response handler changes from v0.6. It remains an
exploratory development study. RESTler is not a treatment in this phase.

## Frozen design

- 3 modes: random, sequence_uniform, portfolio_balanced.
- 5 assemblies: fixed, read_scope, slot_capacity, confirm_unpaid, refund_replay.
- 30 seeds: 800–829; two total request budgets: 120 and 480; depth 8.
- 900 campaigns. Both budgets are reported, never pooled as independent trials.
- ANY-property stop for every assembly. Same SQL oracle and reset isolation.
- Same FastAPI TestClient ASGI HTTP adapter and real SQLite database for all modes;
  no claim of a TCP performance benchmark. Wall time is incidental, not an endpoint.

At an episode boundary the portfolio selects the component with fewer dispatched
business requests; ties choose random. Each complete program runs against a fresh
fixture. Separate Random(seed) streams reproduce each component's standalone
program sequence. Each component gets approximately half the requests, with at
most one depth-8 episode imbalance. Initialization costs are charged to the workflow
component; all eight legitimate programs (24 calls) precede its mutations. Global
budget exhaustion truncates the current episode. The scheduler consumes only call
counts. It cannot read the variant, oracle result, target property or SQL state.

The baselines have the entire shared budget; the portfolio does not get two budgets.
Early discovery, minimization, authentication, controls and exact validation are
accounted separately. There is no ratio sweep, tuning on seeds 800–829, best-seed
selection or replacement of failed observations. Implementation tests use seeds
91201–91204; the full matrix starts only after source publication.

## Outcomes and decision rule

Primary: detected campaigns / 30 for each defect at budget 120. Budget 480 is the
prespecified sensitivity condition. Secondary: mean min(T, budget), counting misses
at the bound. This censored cost is not the unconditional mean time to discovery.
Report both portfolio-minus-random and portfolio-minus-uniform for every defect
at both budgets: 16 contrasts, 5000 paired bootstrap resamples each. Intervals are
descriptive, unadjusted and conditional on these four fixed defects. No significance
claims across systems. Pairing aligns component streams, not independent systems.

A broad improvement requires no observed detection loss against either constituent
on any defect at the primary budget and a gain on at least one. Otherwise report
the tradeoff. A macro-average across these four chosen defects may be shown only
as a secondary descriptive summary with equal weights and full per-defect results.
A new seed is not a new defect; multiple campaigns reproducing one mutant are not
multiple vulnerabilities. Budget variants reuse streams and are dependent.

## Reproduction and integrity

```
python -m unittest discover -s tests -v
python -m integrations.salon_portfolio.run --out results/salon-v08
python -m scripts.verify_salon_portfolio results/salon-v08 --replay
```

The runner refuses to overwrite results, records every completed row immediately,
hashes source/config before and after execution, records all 60 positive/negative
controls, and repeats original and minimized witnesses. A failed run stays separate.
The verifier checks the full Cartesian matrix, hashes, SQL oracle and continuity,
all costs, each scheduler decision, and regenerated summaries/intervals. Optional
live replay executes every archived witness against a fresh adapter. The artifact
stores detected traces and scheduling ledgers, not all successful SQL snapshots;
a complete independent rerun remains needed to audit every negative observation.

References [15]–[17] are in paper/references.md. Next independent work still needed:
stronger RESTler workflow reachability, independent policy/oracle review, and a
service or defect set not used to design the treatment.
