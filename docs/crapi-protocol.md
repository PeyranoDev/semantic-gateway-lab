# crAPI shop study: specification and protocol

**Status: frozen.** Predictions are committed in `results/crapi/predictions.json`
(sha256 `1753379b75ee9e6ddc063e67c37f176de93281544d506c710e3e3131cf297aa5`, commit
443cd15) before any live crAPI campaign was run. Live campaigns are under way.

## Purpose

Test the exact-reach method on a service that this project did not write. The
specification is written from crAPI's documented intended behavior. Hypothesized
defects are guard-removal mutants of that specification. Each generator's detection
probability is computed exactly on the specification model and frozen. Campaigns
then run against the unmodified crAPI shop.

## System under test

- OWASP crAPI at revision `700f03d12a392d9e408260b4beae72ed02a4a1a4`. Every image is
  pinned by digest in `configs/crapi/compose.pinned.yml`.
- The workshop application files in the image are byte-identical to that source.
- Identity, community and workshop are called directly over TLS on 127.0.0.1. The
  chatbot-dependent web proxy is not started.
- Two fixture users are registered through the public signup API:
  `sglab-alice@example.com` and `sglab-bob@example.com`. Each starts with 100 credit.
- Two products exist, each priced at 10.

## Intended rules and their sources

The rules come from crAPI's documented challenges (`docs/challenges.md` at the pinned
revision), read as statements of what a user must not be able to do. The OpenAPI
descriptions are a second source.

| Rule | Statement | Source |
|---|---|---|
| R1 Order privacy | A user can read and modify only their own orders. | Challenge 17 ("Extract the credentials of another user and check their orders") |
| R2 Refund requires return | Credit is refunded only for items returned through the return process. A user cannot obtain a refund by editing an order. | Challenge 8 ("get refunded for an item that you haven't actually returned") |
| R3 Refund bounded by payment | A refund never exceeds what was paid for the order. | Challenge 9 ("get a bigger refund") |
| R4 Purchase accounting | Buying debits price x quantity. A purchase that exceeds the available credit is rejected. | OpenAPI "Create Order"; product and credit fields |
| R5 Return request | A return can be requested once, only for one's own delivered order. It moves the order to `return pending` and does not change credit. Store processing is outside the API domain. | Challenge 8 narrative ("click the return order button, receive a QR code and show it in a USPS store") |

**Disclosure.** The vulnerable shop view code was read on 2026-11-04 to scope the
study, before this specification was written. The rules above cite documentation
only. They have not had external review.

## Finite domain

- Actors: alice, bob.
- Operations: buy product 1 with quantity 1; read order; set order status to
  `returned` or `delivered`; set order quantity to 2; request a return; list own orders.
- Resources are symbolic: a user's k-th created order (k = 1, 2) and one pre-seeded
  order of another account. The adapter binds them to concrete identifiers at run time.
- Reset between programs restores the fixture users' credit and removes their orders
  and applied coupons, using direct SQL on the disposable local database.

## Campaign semantics

crAPI has several defects at once. An episode therefore stops only at a violation of
the campaign's target property; other violations are recorded and the episode
continues. The exact model is computed per target under the same rule
(`integrations/crapi/reach.py`). With the salon rule (stop at any violation),
`REFUND_EXCEEDS_PAYMENT` would be unreachable, because changing the quantity is
itself a tampering violation.

Under the documented-defect hypothesis, the shortest witnesses are:
- `ORDER_PRIVACY`: 1 call;
- `ORDER_TAMPERING`: 2 calls;
- `REFUND_WITHOUT_RETURN`: 2 calls;
- `REFUND_EXCEEDS_PAYMENT`: 3 calls (buy, change quantity, mark returned).

`RETURN_RULES` has no violating program, so it is a negative control.

## Analysis plan (frozen with the predictions)

The plan mirrors `docs/prospective-protocol.md`:
- generator order on pairs separated by at least 0.1 in probability;
- a per-cell exact binomial test;
- zero detections expected for mutants with no reachable violation.

An actual crAPI behavior that violates a rule counts as a detected defect of that rule
family. A rule that crAPI implements correctly is a negative control.

## Limits

The rules are the authors' reading of public documentation. crAPI is a deliberately
vulnerable training application whose challenges are public, so this is implementation
independence, not discovery of unknown defects.
