# Experimental protocol v0.1

## Research questions

- RQ1: Can lifecycle enabledness merge states with different authorization outcomes
  for the same principal, object and action?
- RQ2: Under equal runtime-call budgets, how does predicate-enriched corpus
  indexing change discovery and exploration compared with coarse indexing?
- RQ3: Which synthetic defects remain hard to discover despite known executable
  regression witnesses?

H1 predicts an action-distinguishability counterexample for the coarse abstraction.
H2 is an open directional hypothesis about discovery, not a promised improvement.
Retaining more information can fragment the corpus and increase replay overhead.

## Trusted boundary and attacker

The authenticated fixture identifies principals. Actor identifiers represent
different authenticated test sessions, not an agent choosing arbitrary identities
inside one real session. The attacker/proposer controls structured tool selection,
document identifiers, recipient parameters, text payloads and approval-token reuse.
Identity mapping, the external approval fixture, the oracle and reset mechanism
are trusted. Principals and permissions are loaded from authoritative service state.

Four principals and five candidate identifiers are used. Three documents initially
exist. Each document carries owner, department, content, phase, pending recipient,
ACL and deletion-request flag. Approvals bind actor, resource, operation, nonce and
expiry; consumed nonces survive deletion/recreation. The time is fixed at 1000.
Approvals do not bind a document generation/version; concurrency, distributed
revocation and policy updates are outside this benchmark. Identifier deletion/recreation
is exercised by the replay witness, but separate resource-generation semantics are not modeled.

Approval signing is a trusted fixture operation and is not exposed as a tool.
The public HMAC key is deliberately test-only. There is no human study or
production cryptographic credential mechanism in this artifact.

## Independent oracle

Every executed call yields before/after snapshots and an observable response.
The oracle independently computes specification authorization and expected effects.
It also checks denial atomicity, output correctness, identity immutability and
exactly one audit entry per call. The oracle never imports the backend, its mutant
flags, its check helpers, the fuzzer, or the abstraction implementation.

The oracle shares data types, serialization conventions and fixture constants.
Independence of code does not eliminate correlated specification mistakes. Manual
review of both semantics and extension to independently sourced test cases remain
necessary. Regression witnesses exercise all mutants against their fixed controls
and include accepted legitimate workflows, avoiding a deny-everything solution.

## Treatments

`random` samples tools uniformly and starts each episode from the initial fixture.
`enabled` and `enriched` both select from lifecycle-enabled tools with probability
0.8; otherwise they sample all ten tools uniformly. Their argument distributions
are identical: principals, candidate identifiers, recipients and six token options
are sampled uniformly. There is no access to an authorization oracle for generation.

For guided methods, one shortest safe prefix is retained per abstract key. Episodes
choose an eligible corpus key with probability 0.8 and inverse selection-count
weighting; otherwise they start empty. Replays execute the backend normally.
Both methods differ only in the abstraction key used for corpus indexing.

Coarse enabledness is existential lifecycle availability over fixture objects,
without parameter-specific role or ownership checks. It is an observational
baseline inspired by the preprint, not a proven implementation of a sound EPA.
The enriched key adds each candidate object's phase, deletion-request status and
relations to authenticated principals: same department, owner, pending recipient
and ACL membership; it also retains consumed nonce identities. These predicates
are sufficient for the explicit small recipient counterexample, not established
as sufficient for all security properties or all enterprise states.

## Execution and budgets

Each variant contains one enabled implementation mutant. The fuzzer receives no
mutant label in its generation or feedback; the runner uses it to instantiate the
system under test. The oracle and abstractions are identical across variants.
Campaigns stop at their first violation or the exact backend-call budget. Every
replayed call consumes budget and contributes observations. Reset is not a call.
Snapshot/oracle/abstraction computation time is included in overall wall time.
Trace shrinking occurs afterward, has a separate reported call count, and does
not alter first-discovery metrics. Minimization is deletion-based and 1-minimal.

Pilot: seeds 0-9, budget 1500, depth 12, 270 runs. Additional matrix: seeds
100-129, budget 10000, depth 20, 810 runs. Same budgets apply to every strategy
within each matrix. Comparisons across matrices also change depth/budget, so they
are not a pure seed replication. The additional matrix was configured after the
first pilot was inspected, with no algorithm changes; it is not independently
preregistered. Its directory name `confirmatory` denotes the reserved-seed matrix,
not a claim of preregistration or definitive hypothesis confirmation.

The first pilot ran before adding the separate bounded-analysis command and its
test. The final pilot repeats the same algorithms and seeds with the delivered
source manifest. An intermediate pilot is excluded from the release. Final pilot
and additional matrix ran concurrently on the local host. Timings are descriptive
and cannot support comparative latency or throughput claims under that contention.

## Outcomes and analysis

Primary outcomes: detection fraction by defect and strategy; first violation call
index (including replay); and mean min(discovery call, budget). Unfound defects are
right-censored, never dropped or described as absent. Conditional detected-only
medians are provided for inspection but must not be used alone for comparisons.
The fixed control's expected count is zero *observed* violations, not proven safety.

Wilson 95% intervals summarize detection variation over seeds in this finite
benchmark. They do not estimate real-world attack probabilities. Seeds share the
same implementation and defect; a large seed count does not create independent
real-world systems. The artifact reports descriptive results, not significance
claims. The reserved matrices permit future paired analysis and correction for
multiple per-defect comparisons; any inferential analysis must state its estimand.

Common concrete-state keys omit audit but retain documents and consumed nonces.
Common edges encode source state, tool, allow/deny outcome and destination state.
Different arguments that yield the same edge can collapse; this is not complete
parameter coverage. States/edges observed before first failure also depend on how
early a run stops. Abstract-state counts are diagnostic only and cannot be compared
as universal coverage percentages. Per-call latency measures local Gateway.execute
only, including audit append, without a network or LLM.

## Artifact outputs and reproducibility

Raw JSONL rows preserve all runs, response witnesses, minimal traces, budgets and
metrics. Manifests identify source hashes, Python, host and exact config. Sorted
collections and local PRNGs prevent hash-seed-driven ordering differences. Tests
compare deterministic campaign fields across PYTHONHASHSEED values; timing fields
are excluded. Results must never be silently overwritten. Source hashes are checked
against the release before packaging.

## Limits and criteria for a stronger paper

No real MCP deployment, OPA engine, LLM, prompt-injection dataset, multi-agent
delegation or concurrent backend is evaluated. All defects are deliberately seeded.
The study must be expanded with independent implementations and held-out defect
families before claiming generalization. A finite graph is not an exhaustive
verification result. A deployment guarantee would require property-preserving
abstraction arguments and complete mediation assumptions in addition to fuzzing.
