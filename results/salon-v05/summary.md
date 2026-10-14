# TurnoSalon v0.5 — measured second-domain results

Newly authored synthetic backend, isolated deliberate mutants; no independent generalization claim.

| Variant | Property | Engine | Detected | Mean capped calls |
|---|---|---|---:|---:|
| confirm_unpaid | CONFIRM_PAYMENT | random | 0/20 | 120.0 |
| confirm_unpaid | CONFIRM_PAYMENT | sequence_enabled | 13/20 | 86.7 |
| confirm_unpaid | CONFIRM_PAYMENT | sequence_enriched | 11/20 | 92.4 |
| confirm_unpaid | CONFIRM_PAYMENT | sequence_uniform | 13/20 | 87.0 |
| fixed | BOOKING_SCOPE | random | 0/20 | 120.0 |
| fixed | BOOKING_SCOPE | sequence_enabled | 0/20 | 120.0 |
| fixed | BOOKING_SCOPE | sequence_enriched | 0/20 | 120.0 |
| fixed | BOOKING_SCOPE | sequence_uniform | 0/20 | 120.0 |
| fixed | CONFIRM_PAYMENT | random | 0/20 | 120.0 |
| fixed | CONFIRM_PAYMENT | sequence_enabled | 0/20 | 120.0 |
| fixed | CONFIRM_PAYMENT | sequence_enriched | 0/20 | 120.0 |
| fixed | CONFIRM_PAYMENT | sequence_uniform | 0/20 | 120.0 |
| fixed | REFUND_REPLAY | random | 0/20 | 120.0 |
| fixed | REFUND_REPLAY | sequence_enabled | 0/20 | 120.0 |
| fixed | REFUND_REPLAY | sequence_enriched | 0/20 | 120.0 |
| fixed | REFUND_REPLAY | sequence_uniform | 0/20 | 120.0 |
| fixed | SLOT_CAPACITY | random | 0/20 | 120.0 |
| fixed | SLOT_CAPACITY | sequence_enabled | 0/20 | 120.0 |
| fixed | SLOT_CAPACITY | sequence_enriched | 0/20 | 120.0 |
| fixed | SLOT_CAPACITY | sequence_uniform | 0/20 | 120.0 |
| read_scope | BOOKING_SCOPE | random | 19/20 | 29.9 |
| read_scope | BOOKING_SCOPE | sequence_enabled | 8/20 | 102.5 |
| read_scope | BOOKING_SCOPE | sequence_enriched | 8/20 | 103.2 |
| read_scope | BOOKING_SCOPE | sequence_uniform | 6/20 | 102.5 |
| refund_replay | REFUND_REPLAY | random | 0/20 | 120.0 |
| refund_replay | REFUND_REPLAY | sequence_enabled | 6/20 | 106.3 |
| refund_replay | REFUND_REPLAY | sequence_enriched | 6/20 | 110.2 |
| refund_replay | REFUND_REPLAY | sequence_uniform | 9/20 | 88.8 |
| slot_capacity | SLOT_CAPACITY | random | 2/20 | 112.0 |
| slot_capacity | SLOT_CAPACITY | sequence_enabled | 7/20 | 112.8 |
| slot_capacity | SLOT_CAPACITY | sequence_enriched | 10/20 | 99.6 |
| slot_capacity | SLOT_CAPACITY | sequence_uniform | 16/20 | 69.8 |

Misses consume all 120 calls. Bootstrap and replay count in search budget.
Shrinking, explicit controls and fresh witness verification are counted separately.
Only sequence_enabled versus sequence_enriched isolates feedback.
Controls with no violations do not establish general security.
