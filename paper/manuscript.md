# Beyond Tool Enabledness: Workflow-Seeded Authorization Fuzzing for Agent Tool Runtimes

Ignacio Peyrano

**Working draft, 14 October 2026. Not submission-ready.**
This draft describes a synthetic executable benchmark and an exploratory
HTTP/PostgreSQL case study and a newly authored HTTP/SQLite salon backend,
all implemented within the same project. It does not claim that a
deployed agent system has been formally verified or that the proposed abstraction
outperforms alternatives in general. Measured results are in `results.md`.

## Abstract

Authorization in agent tool runtimes depends on principals, resources and execution
history, not only which tool names are currently enabled. We present a reproducible
synthetic laboratory that separates abstraction information loss from exploration
efficiency. An executable sharing counterexample shows that a coarse enabled-tool
projection can merge states requiring different decisions for the same invocation.
An independent specification oracle checks actual service effects, decisions,
outputs and audit records. Following a baseline evaluation, we introduce mutation
of legitimate workflow programs, matched coarse and relational corpus feedback,
and predicate/scheduler ablations. A new matrix comprises 1080 runs over nine
engines and twelve variants, with all initialization and repeated calls counted.
The three original engines fail to discover approval replay within 3000 calls
in all ten-seed conditions; every sequence-mutation engine detects it in 10/10.
However, wrong-recipient discovery is lower for the new guided engines than for
legacy guidance. Enrichment improves observed replay effort but worsens overwrite
effort, and a no-corpus seed mutator is competitive. These findings support a
property-dependent exploration tradeoff rather than universal superiority.
All 829 detected witnesses are replayed and checked against the fixed control.
The synthetic study remains limited to authored mutants and ten seeds per
treatment. A second, exploratory case study exercises an unmodified FastAPI
backend with PostgreSQL: 120 campaigns target reviewed natural discrepancies.
Seed mutation detects repeated cancellation in 10/10 runs versus 0/10 for random
programs, while random programs more often detect store/unit scope violations.
Matched coarse and enriched feedback shows no clear overall enrichment advantage.
A further authored salon service transfers the frozen search algorithm to
transactional HTTP/SQLite appointment, payment and refund workflows. Across
640 campaigns, workflow mutation detects unpaid confirmation in 13/20 and
repeated refund in 9/20 runs versus 0/20 for random programs; random programs
more often detect cross-scope reads. All 134 detected campaigns have original
and minimized witnesses reverified. Fixed controls show no observed discrepancy
in 38,400 search calls. These authored evaluations do not supply independent
held-out evidence, language models or real MCP transport.

## 1. Introduction

Tool connectivity does not determine whether a specific execution is authorized.
An operation may be callable in principle while a particular principal lacks
authority over its resource, recipient or approval token. Stateful testing must
exercise these relations across sequences of calls, not only inspect a tool name.

Our earlier preprint [1] proposed a Semantic Gateway with enabled-tool abstractions
and semantic fuzzing. Its companion proof of concept [2] demonstrated a sharing
overwrite scenario by walking a graph containing a deliberately inserted defective
edge. That illustration does not itself establish discovery against executable
implementation behavior or the absence of other violations. This study changes
the unit of evaluation to actual tool execution and independently checked effects.

The research questions are:

1. Can coarse lifecycle enabledness merge concrete states requiring different
   authorization decisions for an identical invocation?
2. How does relational enrichment of corpus keys affect discovery under equal
   runtime-call budgets and identical argument generation?
3. Which defects remain difficult to discover despite directed regression witnesses?

The intended contributions are an explicit abstraction counterexample, an executable
benchmark with an independent oracle, and a descriptive evaluation that retains
negative outcomes. Their novelty relative to prior formal abstraction, model-based
testing and agent security work remains to be established through full review.

## 2. Related work and positioning

Enabledness-preserving abstractions were developed for contract validation by
de Caso et al. [3], with subsequent behavior-validation work [4]. Our lifecycle
projection is inspired by that research, not a claim to implement every assumption
or guarantee of a sound EPA. The action-distinguishability counterexample below is
a limitation of this particular projection, not a refutation of those methods.

Stateful request generation and preservation of dependencies are established
testing techniques. RESTler [9] uses dependencies inferred from API specifications
and execution feedback to generate request sequences. AFLNet [10] mutates protocol
message sequences and guides exploration using state feedback. Our hand-authored
workflow seeds and generic mutations are not presented as inventions of either
sequence mutation or dependency-aware testing. We specialize an executable
experiment to principal/resource/approval-history relationships and compare
observational feedback under explicit call budgets and an independent oracle.
A full empirical comparison with RESTler or AFLNet has not been performed.

AgentGuard [5] studies runtime verification with probabilistic behavior models.
MCPSHIELD [6] provides a security framework for MCP-based agents with transition
systems and trust boundaries. HCP [7] evaluates execution-control invariants in
MCP-style runtimes. This study concerns offline testing at a deterministic tool
execution boundary, rather than a replacement for those frameworks. Novelty
relative to their complete methods and broader testing literature remains open.

MCP's HTTP authorization specification [8] already defines an OAuth-based flow.
Transport and object/operation authorization are distinct concerns. Neither this
benchmark nor its results establish protocol superiority over REST.

## 3. System and threat model

The system under test is a deterministic document service reached through structured
tool invocations. An untrusted proposer selects a tool and arguments. The harness
supplies an authenticated principal from a finite fixture; it does not permit role
claims in generated tool arguments to create authority. Server state determines
ownership, departments, ACL membership and workflow phase.

The four principals, candidate resources and ten tools are specified in the artifact.
Sharing requires an owner-manager to initiate a request for a same-department
recipient. Only that pending recipient may accept. An owner-manager may revoke
sharing. Deletion requires a draft resource, a deletion request and an unexpired,
single-use approval scoped to actor, resource and operation. Read/export operations
require same-department ownership or granted ACL membership. Denied calls may not
change business state and must leave an audit record.

A trusted fixture issues HMAC-authenticated test approvals. This simulates an
external approval authority, not a production human approval mechanism. The test
clock is fixed; approval expiry boundaries and reuse are tested against that clock.
Approvals are not generation-bound. Concurrent actions, server compromise, changing
policies, arbitrary binary tools and real model prompt injection are out of scope.

Eight original implementation mutants remove or weaken checks. Three additional
synthetic variants disclose object identifiers in list responses, permit non-owner
updates or permit cross-department sharing. The generator does not receive defect
labels. All eleven defects were authored within this project and the same backend;
the new variants are not independently sourced held-out vulnerabilities.

The replay witness recreates the same resource identifier after deletion. The
fixture tests consumed-grant history without generation/version binding; no claim
is made that production systems with non-reused identifiers exhibit this defect.

## 4. Abstraction and action distinguishability

Let S be the service's concrete state space and a be a fully specified invocation
including principal, resource, tool and parameters. Let Allow(s,a) be the reference
authorization decision. Define alpha_E(s) as the set of tool names enabled by
existential lifecycle conditions over fixture objects. This projection does not
encode authorization for each parameterized invocation.

**Proposition.** If states s1 and s2 satisfy alpha_E(s1) = alpha_E(s2), but
Allow(s1,a) differs from Allow(s2,a) for an identical invocation a, there is no
decision function f(alpha_E(s),a) that exactly reproduces Allow on both states.

**Proof.** The inputs to f are identical for both states, so its output must be
identical. The required decisions differ, yielding a contradiction.

This elementary argument concerns information loss in the projection. It is not a
novel formal-verification theorem or proof of gateway security. The executable
counterexample supplies two sharing prefixes: one designates Bob, the other
Mallory. Both enable the same tools, but Bob's identical acceptance call has
different authorization outcomes. A bounded explorer enumerates states reached
with a five-action subalphabet to depth three and records the witness.

The enriched projection alpha_R augments alpha_E with object phase, deletion-request
status, principal-resource relations and consumed approval nonces. It separates
the recipient witness. No general property-preservation or minimality result is
claimed for this projection. A finer projection may also fragment the exploration
corpus and consume more replay budget.

The proposition concerns exact authorization reconstruction from the projection.
Our projections are used for feedback selection only. The runtime and oracle
continue to inspect full concrete state. Thus a projection can lose distinctions
while still being useful for testing; a coarser search key does not itself weaken
the service's authorization boundary. This distinction motivates measuring
discovery rather than inferring it directly from representational fidelity.

## 5. Testing methodology

The harness executes the service and captures before/after snapshots and visible
responses. A separate oracle derives authorization, effects and expected output,
and checks denied-call atomicity and audit completeness. It imports neither
implementation check helpers nor abstraction logic. Shared fixture assumptions
remain a possible source of correlated mistakes and require independent review.

The three v0.1 engines remain byte-for-byte unchanged. They use uniform arguments,
with two variants preferring lifecycle-enabled tool names and reusing state-reaching
prefixes indexed by coarse or enriched projections. They are rerun at the same
v0.2 budgets and seeds as the new engines. For new synthetic variants only, the
single-threaded harness substitutes the service constructor without editing their
generation, selection or oracle code. A regression test verifies unchanged
behavior on an original variant.

The new engine initializes six legitimate workflow programs. Sharing programs
include initiation, acceptance, read and revocation. Deletion programs include
two authorized lifecycle transactions using distinct fresh fixture approvals.
A final program covers list/read/update/export. None contains an unauthorized
terminal operation or imports known failing regression traces.

Generic operators change a field, insert a call, duplicate a contiguous segment,
delete a step, swap calls or splice a fragment from another legitimate program.
Insertions retain the anchor principal/resource; field mutations preferentially
sample values already observed in the program. Approvals are test-fixture outputs,
not guessed cryptographic signatures.

A no-corpus engine selects these seeds uniformly. Two matched corpus engines use
the identical mutator, seeds, capacity of 64 and inverse-selection-count scheduler.
They differ only in coarse versus enriched feedback keys. Each key identifies an
observed abstract transition and retains one shortest complete tested program.
FIFO eviction bounds memory. Multiple keys may select the same program, so
partitioning changes effective sampling weights as well as information retained.

Two ablations remove recipient or consumed-approval predicates. Another retains
full enrichment but selects stored programs uniformly. An owner-only ablation is
implemented and tested, but not included in the measured matrix.

All bootstrap, repeated, denied and mutation-source-prefix calls consume budget.
Legacy selected-prefix replay and new unchanged-source-prefix counts differ and
are not pooled as one overhead metric. Campaigns stop at their first oracle
violation or budget exhaustion. Deletion-based shrinking occurs afterward and
has a separate call count. Every detected original and minimized trace is replayed
in a separate analysis process; minimized traces are also checked on the fixed service.

## 6. Experimental setup

The v0.1 artifact contains a 270-run pilot (seeds 0-9, budget 1500, depth 12)
and an 810-run larger-budget matrix (seeds 100-129, budget 10000, depth 20).
Their 3,233,104 executed calls are preserved as historical evidence. The second
matrix was configured after inspecting the pilot and is not independently preregistered.

The v0.2 protocol was committed before execution. It is nevertheless an exploratory
follow-up designed after inspecting v0.1, not an independent confirmatory study.
Ten new seeds (200-209), nine engines and twelve variants yield 1080 runs, each
with budget 3000 and depth 20. There are three legacy engines, six sequence engines,
eight original defects, three new synthetic defects and a fixed control.

Source/config/seed-program hashes identify the measured implementation. The original
source hashes remain valid. All 65 automated tests pass on Python 3.11, 3.12 and 3.13.
GitHub Actions executes the matrix and the separate witness-validation analysis.
The matrix consumes 1,147,407 actual service calls before its stop conditions.

Primary measures are detection fraction and first-failure call index. Undetected
runs remain right-censored, contributing the full budget to mean capped effort.
Wilson intervals summarize seed variation within this benchmark, not real-world
breach probability. Same-seed descriptions record detection discordance and
right-minus-left capped-effort differences; no significance claim is made.

Auxiliary corpus diagnostics use fixed-control runs only, so all methods complete
the full budget and avoid early-stopping coverage differences. Per-call timings
describe instrumented in-process execution, not network, model or deployment latency.

## 7. Results

Detailed tables, paired descriptions and full-budget diagnostics are in
sequence-results.md; raw evidence and manifests are in results/sequence-v02.
The historical matrices remain documented in results.md.

### 7.1 Sequence-dependent discovery

For approval replay, each legacy engine discovers zero failures in ten runs.
All six sequence-mutation engines discover the defect in 10/10 at the same
3000-call budget. The no-corpus seed mutator has mean capped effort 218.4 calls,
coarse guidance 595.4 and full enriched guidance 198.2.

This comparison changes both initial workflow knowledge and mutation operators
relative to v0.1. It supports the combined workflow-seeded system in this fixture,
not an isolated mutation-only or abstraction-only benefit.

Sharing overwrite is found by legacy coarse guidance in 1/10 runs and by the
three principal seed-mutation variants in 10/10. Capped effort is 168.8 calls for
no-corpus mutation, 228.4 for coarse guidance and 540.8 for full enrichment.

### 7.2 Negative results and property dependence

Wrong-recipient discovery is 10/10 for each legacy guided engine but 6/10 for both
new guided engines, with four censored misses. The no-corpus seed mutator finds
4/10. Approval-scope and unauthorized-update results are also mixed. Therefore
the new engine is not a universal replacement, and a single overall detection
percentage would conceal relevant per-property tradeoffs.

Removing approval history raises observed replay effort from 198.2 to 300.3 calls,
but lowers overwrite effort from 540.8 to 135.3. Uniform selection with enriched
keys produces 221.1 replay calls and 322.8 overwrite calls. These descriptive
contrasts motivate property-sensitive feedback and scheduling rather than the
claim that every additional predicate improves exploration.

### 7.3 Exploration cost and validation

At equal full budget, coarse sequence guidance has mean 145.6 corpus evictions and
mean stored-program length 7.0; full enrichment has 683.3 evictions and length 10.4.
Unchanged source prefixes consume 45.7% versus 47.5% of calls respectively.
These diagnostics establish higher observed turnover and longer stored programs
for enrichment in this configuration. They do not independently prove why one
method wins on a particular defect.

All 829 recorded failures have their original and minimized witnesses replayed.
Each minimized witness produces no oracle disagreement on the fixed service.
The 90 fixed-control campaigns produce zero observed violations in 270,000 calls.
These are bounded validation results, not a proof of universal safety.

## 7.1 AoristoTech HTTP/PostgreSQL case study

The optional v0.3 integration exercises the original FastAPI ASGI HTTP pipeline,
authentication/service guards and SQL repositories of the pinned AoristoTech
backend against PostgreSQL 16.15. Only the database dependency is overridden for
serial program isolation. ORM metadata supplies the schema, and source commits
release savepoints inside an outer rollback transaction. Production migrations,
independent network transactions and concurrent races are not represented.

Eleven positive/denial controls pass and seven reviewed regressions reproduce,
including foreign-store reading/cancellation, foreign-unit invitation effects
and repeated cancellation that increases stock from 7 to 10 to 13. Invitation
creation can store a row before returning a response-validation error mapped to
404; a failed HTTP response therefore does not establish absence of an effect.

The matrix comprises 120 runs, four engines, three target properties and ten
seeds, with 120 calls per campaign. Seed mutation without corpus detects repeated
cancellation in 10/10 runs versus 0/10 for random programs. Conversely, random
programs detect foreign-store reading in 9/10 versus 3/10 for that seed mutator,
and invitation scope in 10/10 versus 6/10. The matched coarse/enriched engines
both detect cancellation replay in 9/10 and foreign-store reading in 4/10;
invitation scope is 6/10 versus 5/10. These small mixed contrasts establish no
general enrichment advantage.

All 75 detected campaigns have original and minimized witnesses reexecuted.
The matrix consumes 8,268 campaign calls; all recorded stages total 8,831 HTTP
executions. Full results, cost categories, censoring and provenance are in
aoristo-results.md and results/aoristo-v03.

The source is another implementation by the same author. Policies and reviewed
defects are not independent or held out, and reproduction currently requires
access to its private source. This adds bounded evidence from another domain,
not an independently validated enterprise deployment.

## 7.2 Public real-source extraction and mitigation

An owner-authorized source subset now makes the selected case executable without
private-repository access. It includes 81 Python files, 62 copied verbatim and 19
documented adaptations for bootstrap, configuration, module exports and the ORM
registry. The original subset reproduces all 150 historical original/minimized
witness traces at the observed HTTP/business-state boundary. This is finite
observational agreement, not an equivalence theorem for the complete application.

The same 11-module patch is tested on the public subset and the full application.
It adds store-scoped queries, trusted resident/staff unit/building scope, correct
invitation response mapping and transactional pending-sale cancellation. Each
corrected assembly passes 21 checks and 120 campaign conditions with no oracle
disagreement in 14,400 calls. Synchronized concurrent HTTP cancellation returns
200/400 and restores stock once; an injected post-stock failure rolls back both
stock and sale status using the actual SQL repositories.

These results demonstrate mitigation of reviewed discrepancies in the selected
domain. They do not establish independent generalization, production-migration
compatibility or broader application security. The public source, patch, evidence
and reproduction commands are documented in mitigation-results.md and
case_studies/aoristo/README.md.

## 7.3 Newly authored appointment/payment backend

TurnoSalon adds a different business contract and persistence mechanism:
two salon branches, customers and staff, capacity-limited slots, reservations,
synthetic-credit payments, confirmation, cancellation and refunds. The service
uses FastAPI, database-resolved identities from signed sessions and file-backed
SQLite WAL transactions with independent connections and committed writes.
It was created for the experiment rather than taken from a production system.

The v0.3 mutator is copied byte for byte and the campaign implementation changes
only its module description. Domain declarations, eight legitimate seed programs,
observations, feedback projections and the separate specification oracle are new.
The call budget (120), maximum depth (8), corpus capacity (64), operators and
80% guided-selection rule are retained. The protocol and configuration were
committed before the first full matrix, with no later tuning of search parameters.

Four isolated deliberate mutants omit reading scope, slot-capacity enforcement,
payment before staff confirmation, or the already-refunded check. Each mutant
has one target; the fixed control runs all four targets. Twenty seeds per
engine/target produce 320 mutant campaigns and 320 controls. As before, only
the enabled/enriched pair isolates feedback; comparisons to random or uniform
mutation include other treatment differences.

Uniform workflow mutation detects overbooking in 16/20, unpaid confirmation in
13/20 and repeated refund in 9/20, versus 2/20, 0/20 and 0/20 for random programs.
Random detects cross-scope reads in 19/20 versus 6/20 for uniform mutation.
The matched enriched/coarse pair detects overbooking in 10/20 versus 7/20, unpaid
confirmation in 11/20 versus 13/20, and ties on read scope and refund at 8/20 and
6/20. These mixed descriptive differences do not establish general superiority.

All 134 detected campaigns have original and deletion-minimized witnesses
reexecuted, giving 268 exact response/state revalidations. The fixed control
executes 38,400 search calls without any observed oracle discrepancy. Total
HTTP executions across authentication, controls, search, shrinking and witness
verification are 71,674; contract tests and the TCP smoke are accounted separately.
Fixed targets reuse seed/mode streams and are not independent replications.

Nineteen additional tests cover HTTP/SQL business rules, identity forgery,
resource creation, refund rollback and synchronized concurrent requests using
independent SQL connections. Both last-slot contention and double-refund checks
return 200/409 with one effect. A separate smoke completes the business lifecycle
over loopback TCP; the campaign itself uses in-process ASGI HTTP. Another test
exhibits equal globally enabled-tool sets with different correct decisions for
confirming the same booking.

This transfers execution and search to a new authored contract. It does not
provide independent production generalization or held-out discovery. Credits
are simulated; the finite campaign uses four provisioned bookings and tests
creation separately. SQLite BEGIN IMMEDIATE serializes writers and is not a
substitute for PostgreSQL race evaluation. Detailed results and reproduction
commands are in salon-results.md and case_studies/salon/README.md.

## 8. Threats to validity

**Construct validity:** lifecycle availability is a deliberately coarse projection;
results do not establish limitations of every sound enabledness-preserving method.
The abstract keys contain hand-selected predicates and no general sufficiency proof.

**Internal validity:** implementation and independent oracle can share mistaken
business assumptions. Corpus fragmentation, replay overhead and uniform argument
generation can limit guided testing. Campaigns stop at first failure, affecting
observed coverage. The pilot informed the later matrix design, and both v0.1 evaluations informed v0.2.
Workflow seeds encode domain knowledge; they are a substantive treatment difference.
Corpus capacity and hand-selected predicates constrain the observed tradeoffs.

**External validity:** the synthetic in-memory benchmark and AoristoTech case
study both use small finite fixtures and are authored within this project.
They do not represent enterprise deployments. AoristoTech's ORM-schema and
savepoint isolation further limit transfer to live production behavior.
No language model, transport MCP implementation, OPA process or human
operator was evaluated. Discovery campaigns are serial; selected mitigation and
business contract tests separately exercise synchronized concurrent requests. Real attacks may be distributed differently from mutants.

**Conclusion validity:** seed variation is not variation across independent systems.
Conditional medians are subject to detection selection; capped effort and censoring
must accompany them. No-failure runs support only bounded observational claims.

## 9. Discussion and next study

Preserving authorization distinctions and efficiently searching their partition
are separate objectives. The matched sequence engines demonstrate opposite
enrichment effects for replay and overwrite, while a seed mutator without corpus
feedback is competitive. A stronger next study should isolate workflow seeding
from sequence mutation, vary corpus capacity and retention, and evaluate
full-budget state exploration separately from first-failure discovery.

New variants in the same authored service are not independent generalization.
The AoristoTech case study adds another implementation and domain, but independently
designed defect families, reviewed policies and generation-bound approvals are
still required before deployment claims. An agent/MCP phase
must separately evaluate legitimate tasks, adversarial model inputs, call/token
costs and actual execution effects. None is represented by this offline benchmark.

## 10. Conclusion

The artifact supplies a concrete enabled-tool information-loss witness and
executable authorization testing with a separate oracle. Workflow-seeded sequence
mutation makes a previously missed history-dependent defect discoverable in this
synthetic service. Its negative results and ablations show that richer feedback
and corpus guidance have property-dependent costs. The evidence supports a
bounded experimental contribution and a direction for further study, without
identifying finite fuzzing or seeded-defect detection with general security verification.

## Artifact availability

The repository at https://github.com/PeyranoDev/semantic-gateway-lab includes source,
unit/regression tests, configurations, raw experiments, replayable witnesses,
summaries and this draft. Campaign manifests identify the exact measured source.
The AoristoTech integration publishes synthetic observations and source hashes;
the selected public source subset and patch are bundled separately, while the
complete private backend implementation is not. The newly authored salon backend,
frozen protocol, raw observations and replay commands are public.

## References

See `references.md`. The bibliography must be reviewed and expanded before submission.
