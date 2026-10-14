# Beyond Tool Enabledness: Reproducible Stateful Authorization Testing for Agent Tool Runtimes

Ignacio Peyrano

**Working draft, 14 October 2026. Not submission-ready.**
This draft describes a synthetic executable benchmark. It does not claim that a
deployed agent system has been formally verified or that the proposed abstraction
outperforms alternatives in general. Measured results are in `results.md`.

## Abstract

Agents that invoke enterprise tools must obey authorization rules involving
principals, objects and execution history. A state abstraction that retains only
the names of lifecycle-enabled tools can omit distinctions that determine whether
a particular invocation is authorized. We present a reproducible laboratory for
studying this information loss and its implications for stateful fuzzing. The
artifact executes a document service with ten tools, eight isolated implementation
mutants and a fixed control. An independent specification oracle checks decisions,
observable outputs, state changes and audit completeness after every call. We
compare uniform random testing with two corpus-guided strategies that use coarse
enabledness and relationally enriched state keys. Budgets include prefix replay,
and undetected defects remain censored observations. A bounded recipient-sharing
submodel supplies an executable counterexample to action distinguishability under
the coarse projection. The experiments evaluate whether added information improves
discovery rather than assuming that it does. The resulting artifact separates
counterexample evidence, finite testing and formal guarantees, providing a basis
for a subsequent study with independent backends and language-model agents.

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
de Caso et al. [3], with subsequent work on behavior validation [4]. This artifact's
coarse projection is inspired by that research; it is not presented as a sound
implementation of all assumptions or guarantees of those techniques.

AgentGuard [5] studies runtime verification using learned probabilistic models of
agent behavior. MCPSHIELD [6] presents a formal security framework for MCP-based
agents using transition systems and trust boundaries. HCP [7] evaluates explicit
execution-control invariants in MCP-style runtimes. These works require a precise
positioning of any claim about agent verification or runtime mediation. The present
experiment concerns offline exploration and abstraction-induced information loss
in a small deterministic execution service. It does not replace those frameworks
or empirically compare their complete implementations.

MCP's HTTP authorization specification [8] already defines an OAuth-based flow.
The benchmark therefore does not compare a supposedly secure protocol with an
inherently insecure REST protocol. Transport and backend authorization are distinct
concerns, and this version does not implement an MCP transport.

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

Eight isolated implementation mutants remove or weaken checks. The oracle and
generator do not receive mutant annotations. These are seeded defects, not claimed
discoveries in external implementations.

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

## 5. Testing methodology

The fuzzer calls the service rather than a precomputed transition graph. Before
and after every invocation, the harness records snapshots and the visible response.
A separate specification oracle derives authorization, expected effects and output,
and checks audit completeness. It imports neither implementation checks nor
abstraction logic. Shared data conventions and fixture constants remain potential
sources of correlated mistakes, motivating independent review.

Uniform random testing samples tool names and arguments and resets between bounded
episodes. Two guided methods use the same 80% lifecycle-enabled selection rule,
argument generator and corpus scheduler. They retain one shortest safe prefix per
abstract key. Their only treatment difference is the coarse versus enriched key.
The random baseline differs in both selection and lack of prefix reuse, so it
evaluates the guided mechanism as a whole rather than abstraction alone.

Every replayed call consumes the runtime-call budget. Campaigns terminate on the
first violation or budget exhaustion. Afterward, deletion-based minimization finds
a 1-minimal witness under action removal; its cost is reported separately. The
generator uses no directed regression witness as an initial seed.

## 6. Experimental setup

The final pilot evaluates seeds 0-9, three strategies and nine variants with a
1500-call budget and depth 12, totaling 270 runs. An additional matrix uses seeds
100-129, budget 10000 and depth 20, totaling 810 runs. This second matrix was
configured after inspecting the first pilot; it is not independently preregistered.
No exploration algorithm was changed between matrices. Budget/depth changes mean
cross-matrix differences cannot be attributed solely to held-out seeds.

Primary outcomes are defect detection fraction and call index to first violation.
Misses are right-censored at the budget. Mean capped discovery effort includes
misses at their budget rather than discarding them. Wilson intervals describe
variation over seeds in this synthetic benchmark, not a real-world breach rate.
Results are descriptive; no statistical superiority claim is made.

Common concrete state and edge counts provide auxiliary diagnostics. Their values
are affected by early stopping and do not constitute exhaustive coverage. Abstract
state counts are not directly comparable coverage percentages. Timing observations
come from a local, potentially contended host and do not support production latency
claims. Source hashes, fixture configuration and host metadata accompany raw data.

## 7. Results

See `results.md` and the committed raw JSONL, CSV summaries and manifests. Report
the results by defect and strategy, including misses and fixed-control outcomes.
Do not substitute directed regression success for stochastic discovery rates.

The abstraction counterexample establishes a concrete limit of tool-name projection.
It does not establish that a finer abstraction improves the current scheduler's
discovery efficiency. That question must be answered from the measured matrices.

## 8. Threats to validity

**Construct validity:** lifecycle availability is a deliberately coarse projection;
results do not establish limitations of every sound enabledness-preserving method.
The abstract keys contain hand-selected predicates and no general sufficiency proof.

**Internal validity:** implementation and independent oracle can share mistaken
business assumptions. Corpus fragmentation, replay overhead and uniform argument
generation can limit guided testing. Campaigns stop at first failure, affecting
observed coverage. The pilot informed the later matrix design.

**External validity:** one synthetic in-memory backend, seeded single defects,
four principals and a finite argument domain do not represent enterprise deployments.
No language model, transport MCP implementation, OPA process, concurrency or human
operator was evaluated. Real attacks may be distributed differently from mutants.

**Conclusion validity:** seed variation is not variation across independent systems.
Conditional medians are subject to detection selection; capped effort and censoring
must accompany them. No-failure runs support only bounded observational claims.

## 9. Discussion and next study

Preserving authorization-relevant distinctions and efficiently exploring the resulting
state partition are different problems. A method can satisfy the first while
performing poorly on the second. A subsequent version should separately ablate
predicate families, corpus scheduling and argument/sequence mutation, preserving
matched generators for abstraction comparisons. It should include independent
backends and held-out defect families before adding a real-agent evaluation.

## 10. Conclusion

This artifact makes a narrow question executable: whether tool-name enabledness
retains sufficient information for particular stateful authorization decisions,
and what happens when additional predicates guide exploration. It supplies a
counterexample and measured, reproducible tests without identifying finite fuzzing
with a universal safety proof. Further evidence is required for broader claims.

## Artifact availability

The repository at https://github.com/PeyranoDev/semantic-gateway-lab includes source,
unit/regression tests, configurations, raw experiments, replayable witnesses,
summaries and this draft. Campaign manifests identify the exact measured source.

## References

See `references.md`. The bibliography must be reviewed and expanded before submission.
