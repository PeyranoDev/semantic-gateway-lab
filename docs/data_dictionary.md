# Data dictionary

`raw.jsonl` has one JSON object per seed/strategy/variant. Values are measured
or deterministic metadata; no line is removed because no defect was found.
Historical datasets are stored losslessly as `raw.jsonl.gz` in Git. Run
`python scripts/unpack_results.py` to restore original bytes and derive each
individual trace file. Raw SHA-256 values are checked against release validation.

| Field | Meaning |
|---|---|
| `strategy`, `mutant`, `seed` | Treatment, implementation variant and local PRNG seed |
| `budget`, `max_depth` | Runtime call limit and maximum episode length including replay |
| `calls`, `replay_calls` | Actual calls executed and subset replaying corpus prefixes |
| `episodes` | Number of fixture resets started |
| `allowed`, `denied` | Observable decision counts; their sum equals calls |
| `detected`, `violations` | Whether the independent oracle found a disagreement and its codes |
| `first_failure_call` | Global executed-call index of first violation; null for misses |
| `right_censored` | True when stopped at budget without a violation |
| `elapsed_s` | Complete campaign time before minimization, including instrumentation |
| `gateway_p95_us` | Nearest-rank 95th percentile of local execute latency; no network/LLM |
| `concrete_states`, `concrete_edges` | Counts observed in common business-state projection before stopping |
| `abstract_states`, `abstract_edges` | Corpus partition/transition diagnostics; zero for the random strategy |
| `trace`, `minimal_trace` | Original first-failure episode and deletion-minimized replayable episode |
| `witness` | Before/after concrete snapshots and response of first failure |
| `shrink_calls` | Extra backend calls used to minimize after the campaign |
| `coverage_digest` | SHA-256 of sorted common observed edges, for deterministic comparison |

Coverage keys collapse irrelevant audit history. Edge keys omit parameters and
therefore do not measure parameter coverage. Only failure episodes are retained
as full action lists; other explored transitions can be regenerated from config,
seed and matching source hashes. Snapshots contain no production credentials.

## Oracle codes

`READ_SCOPE`, `SHARE_RECIPIENT`, `SHARE_PHASE`, `REVOKE_OWNER`, `DELETE_APPROVAL`,
`APPROVAL_SCOPE` and `APPROVAL_REPLAY` identify relevant authorization failures.
`AUTHORIZATION` covers other unpermitted successful actions.
`LEGITIMATE_TASK_BLOCKED` identifies an overrestrictive decision.
`UNEXPECTED_EFFECT`, `DENY_MUTATED_STATE`, `OUTPUT_MISMATCH`, `AUDIT_COMPLETENESS`
and `IDENTITY_MUTATION` identify disagreements in effects, responses or audit.
One bad call can produce multiple codes. A campaign stops at the first call with
any code; the first code is the minimizer's preservation target.

## Summary fields

Detection rates and Wilson bounds are grouped by variant/strategy. `mean_capped_calls`
averages first-failure call indices for hits and budget for misses.
`median_calls_detected_only` omits misses and is intentionally named that way.
Use both detection and capped effort, never this median alone. Fixed-control
violation rates describe implementation/oracle agreement in executed samples.
