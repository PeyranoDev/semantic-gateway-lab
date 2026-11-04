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
| T2 | S3, S5 | inline | done | 1fb92f1, cb16400: tables replay 2,740 campaigns exactly; fidelity 8,750/8,750; 48/48 cells consistent |
| T3 | S4, S5 | inline | done | 7d60d4f paired tests; 508a90e surrogate n=1000/cell; c9fdaa0 corpus at 480 |
| T4 | S6 | inline | partial | refs 19-26 at metadata/abstract level; full texts pending |
| T5 | S7 | inline | done | 44ea0ab frozen; edb845c 26/26; c9fdaa0 + equivalents diagnosed |
| T6 | S8 | inline | done | 7021ee5 rewrite; wording corrections after advisor review |

## Log

- L1 (2026-11-04, user): "revisa el estado actual del paper y las pruebas, que cambiarias o mejorarias para hacer mejor el paper?"
- L2 (2026-11-04, user): "arranca con lo que te parezca, hay que hacer un paper solido y novedoso"
- L3: Minimal witness length is constant per defect. Salon: read 1, capacity 2, unpaid 2, refund 5. Aoristo: read 1, invitation 1, cancel 2. Documents: depth 1 random >= mutation; depth >= 3 mutation 10/10 vs random 0-2/10; depth 2 mixed (wrong_recipient random 8/10 vs sequence_uniform 4/10). Depth alone is insufficient, so add edit distance (S3).
- L4: `datetime.utcnow` in the Aoristo adapters is left unchanged because the adapters are hash-pinned measured source.
- L5: Closest prior work found: Sahin, Zhang, Arcuri, arXiv 2604.00702 (EvoMaster access-policy oracles, multi-call sequences, 52 APIs). The paper must position against it. Bug-depth antecedent: PCT (ASPLOS 2010).
- L6: Design: exact transition tables recorded from the real backend; the table must reproduce every recorded v0.5/v0.6/v0.8 campaign field-for-field (replay) before any prediction is trusted. Predictions are exploratory and post hoc; the prospective test is T5.
- L7: Advisor correction: 48/48 agreement validates the pipeline (exact model over a verified replica), it is not independent predictive evidence. A failed Holm test at n=30 is low power, not absence of a feedback effect; the surrogate with 1000 seeds per cell settles effect sizes.
- L8: Document benchmark (Monte Carlo, 10,000 episodes per defect): per-episode reach probability orders the observed random-vs-mutation winner for all 11 defects, including wrong_recipient (depth 2; p_random 0.0083 > p_mutation 0.0017). Thesis: the winner follows each generator's reach probability for the shortest witnesses; depth is only a proxy.
- L9: T5 redesign (advisor option A): derive predictions from the specification (oracle `expected()` with the same guard removed), commit their hash, then run campaigns on new guard-removal implementation mutants.
- L10: Prospective scoring: the depth rule gets 15/15 orderable random-vs-mutation pairs. Reach also orders 11 seed_extend pairs correctly (26/26 total). The one depth/reach disagreement (transition:66:0, gap below 0.1) went against reach (29 vs 27). Claim: reach is quantitative across generators; depth is a categorical proxy that fails post hoc (wrong_recipient). Corrected the earlier "11/11 document defects" statement: only the large-gap cases are confirmable at n=10.
- L11: The surrogate shows the corpus engines (80% selection from a 64-entry FIFO corpus, rare-key scheduler) lose 12-33 points to uniform seed mutation on history defects at 120 calls; the 480-call check is pending before any title wording. Enriched vs coarse: +20.7 +- 3.6 points on slot_capacity only.
- L12: Equivalent mutants verified on implementation tables: 64:0 is covered by the other disjunct, 64:1 by the scope check, 69:0 is unreachable under the fixture's credit (min balance 2,000). Novelty sentence restated positively, without characterizing [21, 22] before reading them.
- L13: Open: full texts of [19]-[26]; independent service (crAPI); comparison with EvoMaster access-policy oracles [19]; venue selection.
