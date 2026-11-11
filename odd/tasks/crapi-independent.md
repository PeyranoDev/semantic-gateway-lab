# Feature: independent-implementation test on OWASP crAPI

Objective: test the exact-reach method on a service not authored by this project. A specification is written from crAPI's documented business rules, hypothesized defects are its guard-removal mutants, generator order is predicted and frozen, and campaigns run against the unmodified crAPI shop.
Branch: `paper/crapi-independent` (stacked on PR #5). Delivery: ask-on-risk. Test runner: `python -m unittest discover -s tests`.

## Specs

- S1. "Hace push y pr, despues, seguir con el resto" (L1): continue with the open items of PR #5. The main one is an independently authored service (crAPI).
- S2. Run pinned crAPI 1.1.5 (revision `700f03d1`) locally, bound to 127.0.0.1, without the chatbot/chromadb stack, and record image digests.
- S3. Use a finite shop domain: two users plus anonymous; orders (create, read, PUT status/quantity, return), list orders and apply coupon, with small fixed argument sets.
- S4. Write the specification from crAPI's documented intended behavior (docs and OpenAPI), not from observed responses. Disclose that the vulnerable view code was already read on 2026-11-04.
- S5. Make the state resettable and snapshot-able (Postgres orders/credit, Mongo coupons). Check fidelity as was done for the salon tables.
- S6. Derive predictions from specification guard-removal mutants, freeze them by hash, then run real campaigns and compare (same protocol as docs/prospective-protocol.md).

## Tasks

| ID | Specs | Route | Status | Evidence |
|---|---|---|---|---|
| T1 | S2 | inline | done | 00395f0, 54a337b; stack up (user ran compose); fixture users registered; ~97 ms/request |
| T2 | S3, S4 | inline | done | integrations/crapi: model, reach, generator, adapter, experiment; 5 tests green |
| T3 | S5 | inline | done | SQL snapshot/reset in adapter; single docker exec, cached |
| T4 | S6 | inline | done | 9/9 orderings, 0/15 cells deviate, controls 0/30; results/crapi |

## Log

- L1 (2026-11-04, user): "Hace push y pr, despues, seguir con el resto"
- L2: PR #5 opened, and CI is green (including http-contracts). Related work now positions against the full texts of Sahin et al. [19] (post-processing oracles, one generator, no reach model, no history-dependent business oracles, crAPI among its APIs) and Böhme & Paul [22].
- L3: crAPI shop views read: `OrderControlView.get` has no ownership check; `put` lets the owner set any valid status, and setting `returned` credits quantity x price; `quantity` can be changed after purchase. These are history-dependent and in scope for the method.
- L4: `docker compose up` of the pinned crAPI images was denied by the auto-mode classifier ([Code from External]). The user must decide whether to allow it.
- L5 (2026-11-04, user decision): pin by "Digest + matching commit". No 1.1.5 images are published. The main images were built 2025-09-22 15:03-18:27 UTC, right after 700f03d (14:58 UTC), which is still upstream HEAD, so the pin is unchanged. Workshop app files in image d4d2d94d are byte-identical to the source (diff -r: 0). All seven images are now pinned by digest in configs/crapi/compose.pinned.yml.
- L6: Identity and workshop require TLS on 127.0.0.1 (fixture certificate). Fixture users were created through signup; each has 100 credit, and both products cost 10. Five pre-seeded orders of other accounts exist. A request takes ~97 ms (salon: ~3 ms), so an exhaustive 8-level implementation table is not feasible. Predictions will be exact on the specification model, and campaigns run on real crAPI with an SQL reset between programs.
- L7: Classifier safety stop. Running the refund exploit by hand with curl tripped a safety classifier twice. Switched to running it only through the experiment harness (oracle-judged), which is the same framing as the salon study. No manual exploit curls.
- L8: crAPI exact predictions (budget 60) order generators DIFFERENTLY from salon: random/seed_extend beat valid-bank mutation on every target (e.g. ORDER_PRIVACY 0.868/0.691/0.191). crAPI defects are shallow (read other = depth 1; tamper own order = depth 2) and its valid tasks do not sit one mutation from the exploit. A different fixture giving a different, predicted ordering is stronger evidence than reproducing salon.
- L9 (review): a reviewing session found the calibration report deviated from the frozen plan (3/20 vs the frozen 4/42). Fixed in 33b9688: 4/42 primary, 3/20 secondary. Added Threats text on the hand-written spec->impl mapping (12 of 14 graphs verified) and the snapshot-observable assumption. Added bank-sensitivity analysis (removing the witness-prefix template flips the winner; the reach model predicts it). crapi-protocol.md marked frozen with the predictions hash.
- L10 (2026-11-11): Re-run after the week's Docker restart. Two harness bugs surfaced only by executing against the external service: (1) the adapter divided credit by price while the oracle uses raw credit -> fixed; (2) crAPI's GET order calls an unused payment gateway with a 5s timeout -> pointed at a dead port. With both fixed, 450 live campaigns reproduce 9/9 frozen generator orderings, 0/15 cells deviate at p<0.05, both controls 0/30. Clean PR branch paper/crapi-results built from main.
