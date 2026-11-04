# Feature: history-depth paper strengthening

Objective: turn the property-dependent tradeoffs into a measurable, falsifiable explanation (witness history depth + edit distance from the valid bank), with sound statistics and an honest exploratory/prospective split.
Branch: `paper/history-depth-analysis`. Delivery: ask-on-risk. Test runner: `python -m unittest discover -s tests` (salon lockfile installed for HTTP tests).

## Specs

- S1. "hay que hacer un paper solido y novedoso" (L2): changes must strengthen soundness and novelty, without overstating evidence.
- S2. CI must run the HTTP/SQL tests that currently skip (32 skipped without `backends/salon/requirements.lock`).
- S3. Engine-independent explanatory variables per defect: exact shortest-witness depth from the fixture initial state (BFS over the finite action domain, using the specification oracle), and edit distance from the nearest valid-bank program. Compare with minimized-witness lengths.
- S4. Survival analysis from existing first-failure data (Kaplan-Meier, right-censored) and paired statistics (exact McNemar, Vargha-Delaney A12, Holm adjustment), labeled exploratory/post hoc.
- S5. Analytic detection model for uniform random and single-mutation generation; predicted vs observed detection per defect and budget.
- S6. Literature check of antecedents for "bug depth" (e.g., PCT) and missing REST baselines (EvoMaster, Schemathesis) plus statistics guidance (Arcuri & Briand); cite, do not claim the concept as new.
- S7. Prospective confirmation protocol: systematic guard-removal mutants in TurnoSalon, predictions committed before execution.
- S8. Manuscript reorganized around the explanation, historical phases moved to an appendix, caveats consolidated in threats to validity; numbers produced by scripts.

Assumption: frozen measured source files (hash-pinned in `results/*/manifest.json`, e.g. adapters) are not edited.

## Tasks

| ID | Specs | Route | Status | Evidence |
|---|---|---|---|---|
| T1 | S2 | inline | done | 139 tests, 0 skipped with lockfile (local 3.12) |
| T2 | S3 | inline | pending | |
| T3 | S4, S5 | inline | pending | |
| T4 | S6 | inline | pending | |
| T5 | S7 | inline | pending | |
| T6 | S8 | inline | pending | |

## Log

- L1 (2026-11-04, user): "revisa el estado actual del paper y las pruebas, que cambiarias o mejorarias para hacer mejor el paper?"
- L2 (2026-11-04, user): "arranca con lo que te parezca, hay que hacer un paper solido y novedoso"
- L3: Minimal witness length is constant per defect. Salon: read 1, capacity 2, unpaid 2, refund 5. Aoristo: read 1, invitation 1, cancel 2. Documents: depth 1 random >= mutation; depth >= 3 mutation 10/10 vs random 0-2/10; depth 2 mixed (wrong_recipient random 8/10 vs sequence_uniform 4/10). Depth alone is insufficient, so add edit distance (S3).
- L4: `datetime.utcnow` in the Aoristo adapters is left unchanged because the adapters are hash-pinned measured source.
