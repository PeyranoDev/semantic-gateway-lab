# Sequence-mutation follow-up: measured results v0.2

1080 runs; 1,147,407 executed backend calls; 829 original/minimized witnesses replayed by the separate analysis step.
65 automated tests passed on Python 3.11, 3.12 and 3.13 before the matrix.
The 90 fixed-control campaigns produced zero observed violations (270,000 calls).

All results are from a synthetic service. Ten seeds per condition yield substantial uncertainty; full Wilson intervals and matched descriptions are stored with the raw data.
First-failure stopping and censored misses remain part of the analysis.

## Detection fractions

| Variant | Legacy enabled | Seed mutation, no corpus | Seed mutation, coarse | Seed mutation, enriched |
|---|---:|---:|---:|---:|
| fixed | 0/10 | 0/10 | 0/10 | 0/10 |
| cross_department_read | 10/10 | 10/10 | 10/10 | 10/10 |
| wrong_recipient | 10/10 | 4/10 | 6/10 | 6/10 |
| sharing_overwrite | 1/10 | 10/10 | 10/10 | 10/10 |
| unauthorized_revoke | 10/10 | 10/10 | 10/10 | 10/10 |
| approval_scope | 7/10 | 6/10 | 5/10 | 6/10 |
| approval_replay | 0/10 | 10/10 | 10/10 | 10/10 |
| missing_approval | 9/10 | 10/10 | 10/10 | 10/10 |
| deny_audit | 10/10 | 10/10 | 10/10 | 10/10 |
| list_scope | 10/10 | 10/10 | 10/10 | 10/10 |
| unauthorized_update | 10/10 | 6/10 | 7/10 | 8/10 |
| cross_department_share | 10/10 | 10/10 | 10/10 | 10/10 |

## Mean capped call effort

Misses contribute the full 3000-call budget. Bootstrap and repeated calls count. This is a descriptive capped-effort metric, not an uncensored estimate.

| Variant | Legacy enabled | Seed mutation, no corpus | Seed mutation, coarse | Seed mutation, enriched |
|---|---:|---:|---:|---:|
| approval_replay | 3000.0 | 218.4 | 595.4 | 198.2 |
| sharing_overwrite | 2935.7 | 168.8 | 228.4 | 540.8 |
| wrong_recipient | 662.7 | 2185.8 | 1976.4 | 1674.5 |

## Paired contrasts and ablations

The CSV includes all nine engines; paired.json retains same-seed discordant detections and capped-effort differences. A positive right-minus-left difference means more calls for the right-hand treatment. No significance or optimality claim is made.

| Variant | Contrast | Left-only hits | Right-only hits | Mean right-minus-left calls |
|---|---|---:|---:|---:|
| approval_replay | abstraction | 0 | 0 | -397.2 |
| approval_replay | corpus_guidance | 0 | 0 | 377.0 |
| approval_replay | recipient_ablation | 0 | 0 | 0.0 |
| approval_replay | approval_ablation | 0 | 0 | 102.1 |
| approval_replay | scheduler_ablation | 0 | 0 | 22.9 |
| sharing_overwrite | abstraction | 0 | 0 | 312.4 |
| sharing_overwrite | corpus_guidance | 0 | 0 | 59.6 |
| sharing_overwrite | recipient_ablation | 0 | 0 | -163.7 |
| sharing_overwrite | approval_ablation | 0 | 0 | -405.5 |
| sharing_overwrite | scheduler_ablation | 0 | 0 | -218.0 |
| wrong_recipient | abstraction | 2 | 2 | -301.9 |
| wrong_recipient | corpus_guidance | 2 | 4 | -209.4 |
| wrong_recipient | recipient_ablation | 1 | 1 | 201.6 |
| wrong_recipient | approval_ablation | 4 | 2 | 425.7 |
| wrong_recipient | scheduler_ablation | 2 | 2 | 412.6 |

## Corpus diagnostics at equal full budget

Only fixed-control runs are used, so all treatments execute the full budget. Legacy selected-prefix replay and new unchanged-source-prefix calls differ and are not pooled.

| Sequence engine | Mean stored keys | Mean evictions | Mean program length | Source-prefix calls | No-op mutations |
|---|---:|---:|---:|---:|---:|
| sequence_uniform | 0.0 | 0.0 | 0.0 | 45.6% | 14.7% |
| sequence_enabled | 64.0 | 145.6 | 7.0 | 45.7% | 12.4% |
| sequence_enriched | 64.0 | 683.3 | 10.4 | 47.5% | 12.8% |
| sequence_no_recipient | 64.0 | 698.4 | 10.4 | 47.4% | 12.9% |
| sequence_no_approval | 64.0 | 560.5 | 11.6 | 47.0% | 12.1% |
| sequence_enriched_uniform | 64.0 | 712.2 | 10.6 | 48.1% | 13.2% |

## Interpretation

Workflow-seeded mutation makes approval reuse discoverable in this benchmark. That comparison changes both initial workflow knowledge and mutation, so it does not isolate a mutation-only benefit against v0.1. The matched new corpus engines share both.

Enrichment is property-dependent: it lowers observed approval-replay call effort relative to the coarse key, while coarse guidance is faster for sharing overwrite. Removing approval history changes those costs in opposite directions. The no-corpus seed mutator is competitive, showing that much of the gain can come from seeds and mutations without richer feedback.

Wrong-recipient discovery regresses relative to legacy guidance. The new engine is not a universal replacement. Stored-program sampling and argument-distribution effects require further controlled ablations before causal mechanisms are asserted.

Approval replay here relies on deleting and recreating the same identifier. The fixture does not model generation/version binding. This is a narrow test of consumed-grant history, not evidence of the same vulnerability in systems with non-reused identifiers.

Reserved variants were authored in the same project and backend. They support within-project extension, not independent external generalization. No LLM or actual MCP transport is evaluated.

## Reproduce

Source experiment commit: ab4b6c3388b54d1efb021fc7ee9afecf59309805.
Experiment run: https://github.com/PeyranoDev/semantic-gateway-lab/actions/runs/38593192649

```bash
python scripts/unpack_sequence_results.py
python -m fuzzlab.sequence run --config configs/sequence-pilot.json --out results/local-sequence
python -m scripts.analyze_sequence
```

Fresh output reproduces the configured matrix; timings vary by machine. The analysis command regenerates tables from the committed historical dataset.
