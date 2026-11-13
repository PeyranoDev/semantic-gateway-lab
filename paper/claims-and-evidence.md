# Claims and the evidence the paper needs

Evidence levels: **validation** (the pipeline reproduces what was recorded),
**exploratory** (defects and designs that informed the method) and **prospective**
(predictions frozen before execution).

| Scoped claim | Level | Evidence | Limit |
|---|---|---|---|
| The transition tables reproduce the measured backend | Validation | 2,740 v0.5/v0.6/v0.8 campaigns identical in 19 fields; negative control 19/20; 8,750 transitions along real paths | Assumes dependence on observable state only; 50 sampled states |
| Mutation enumeration is exact | Validation | Test that walks every choice path of the real `Mutator` | TurnoSalon mutator only |
| The corrected service does not violate the oracle in programs of up to 8 actions | Validation | Full table of 723 states and 126,525 transitions with no violation | 175-action domain, no resource creation, oracle properties only |
| Valid tasks vs. random bank, same mutator: +43 to +76 points on history defects, −45 on the read | Exploratory | Surrogate with 1,000 seeds; planned contrasts with exact McNemar and Holm; A12 on capped calls 0.15 (read), 0.84 (overbooking), 0.77 (unpaid confirmation), 0.67 (repeated refund) | One service; reviewed defects |
| Corpus guidance underperforms uniform mutation on history defects | Exploratory | −12 to −33 points at 120 calls; persists at 480 | The contrast changes selection, eviction and scheduler at once |
| The enriched key helps only on overbooking | Exploratory | +20.7 ± 3.6 points; the other three include zero | One service |
| Depth is a proxy; per-episode reach explains `wrong_recipient` | Exploratory | Monte Carlo over 10,000 episodes per defect on the document benchmark | n = 10 does not confirm the budget direction |
| Specification-derived predictions order generators on new defects | Prospective | 26/26 pairs (gap ≥ 0.1); 3 equivalent mutants with 0/270 detections | The depth rule is also right on 15/15; reach adds 11 pairs involving prefix extension |
| Per-cell calibration is compatible with sampling (salon) | Prospective + diagnosis | Frozen metric: 4/42 cells with p < 0.05 (~2 expected by chance); none after Holm (min adjusted p = 0.22); pooled per generator: random 176 vs 176.0, extension 160 vs 160.2, mutation 200 vs 193.2; 3/20 in the non-degenerate subset (secondary); impl/spec graphs identical on the deviating cells; 3,000–12,000 seeds reproduce the frozen values | The spec→impl mapping is hand-written; graphs identical for 13/14 mutants; for `transition:81:0` only beyond the first violation (violation-free subgraph identical) |
| Specification-derived predictions order generators on a service by another author (crAPI) | Prospective + independence | 9/9 orderings (gap ≥ 0.1); 1/15 cells at uncorrected p < 0.05, none after Holm (min adjusted p = 0.44); Return rules unreachable 0/30 in all three generators; 450 live campaigns, 30 seeds per cell (the executor stops only at the target, like the model); predictions frozen, sha256 1753379b | crAPI is a training app with public defects; we wrote its specification |
| Valid-bank mutation on crAPI is under-predicted | Prospective + diagnosis | Pooled 20 observed vs 12.4 expected (exact Poisson-binomial P(X ≥ 20) = 0.019; 0.058 after Holm over three generators); random 50 vs 45.9 and extension 55 vs 52.9 are calibrated; the campaign code on the specification model (2,000 seeds per cell) reproduces the frozen values within 0.02, so the DP is correct and the gap is specification vs. live implementation | Localizing it needs the same mutated programs run live; ordering unaffected |
| The generator fingerprint differs between services and the model predicts it | Independence | On crAPI random/extension win (depth 1–2 defects); on the salon mutation wins (history) | Two services; finite domains |
| Reach orders pairs the depth rule cannot | Independence | On crAPI the depth rule orders 4/6 random-vs-workflow pairs and has no criterion for the 3 extension-vs-mutation pairs; reach orders 9/9 | One service |
| HTTP errors can accompany business writes | Exploratory | Invitation witnesses in Aoristo and a rollback patch | Case fact |
| An official external generator was run | Exploratory | v0.7: RESTler, 60 campaigns, 31 traces revalidated | Native checkers disabled; refund not reached |

## Experimental unit

Seeds vary the search within one system. The systematic mutants are new defects of the
same service, not independent systems. Surrogate cells use fresh seeds and the unchanged
campaign code on validated tables; they measure search variation, not variation across
systems, and they are measurements, not predictions.

## Claims the current evidence does not support

- General superiority over RESTler, EvoMaster or other fuzzers not compared.
- Novelty of generating sequences, mutating them, or checking authorization with an oracle.
- That reach beats depth prospectively on the random/mutation comparison on the salon:
  both got the same pairs right (on crAPI reach orders pairs depth cannot).
- That probability is calibrated on every service: crAPI mutation is under-predicted.
- That corpus guidance is inferior in general: only in this configuration and service.
- Generalization to non-finite domains (the exact method requires a finite domain and
  tractable states; crAPI is by another author but still finite-domain).
- Formal safety outside the bounded domain and depth.
- That crAPI behavior is independent of concrete order ids: not verified directly.

## Before submission

Done: full texts of [19]–[27] read; independent service (crAPI) measured; reference
metadata completed. Future work: run the mutated programs on live crAPI to localize the
mutation gap; compare with EvoMaster's access-policy oracles [19, 27] and RESTler; select
venue and format.
