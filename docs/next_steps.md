# Next investigation after sequence mutation

The v0.2 engine, matched comparison, predicate/scheduler ablations and three new
synthetic variants are implemented. See paper/sequence-results.md for measurements,
docs/sequence-protocol.md for the design and results/sequence-v02 for raw evidence.

## Before adding an LLM

1. Audit both the original specification and the new seeded programs independently.
2. Separate state-coverage measurement at full budget from first-failure stopping.
3. Test another document-service implementation and independently authored defect
   families; the current reserved variants are still written within this project.
4. Expand approval semantics to resource generations/versions and policy revocation.
   The current replay witness depends on recreating the same identifier after deletion.
5. Confirm important contrasts with new seeds and a frozen, separately reviewed
   protocol. Current ten-seed contrasts are exploratory, not broad superiority claims.

The recipient/approval predicate and scheduler ablations are measured in v0.2.
An owner-only ablation is implemented/tested but not included in that matrix.
Department and task-scoped delegation ablations remain future work.

## Agent evaluation as a separate phase

Expose the service through a versioned MCP adapter and keep server-side authority
outside model outputs. Evaluate successful legitimate tasks, adversarial tasks,
token/call costs and denied effects independently of offline fuzzing coverage.
Model API costs, credentials and task datasets need explicit configuration before
running that phase; no LLM evaluations are represented by the current artifact.

Record observable actions, arguments, sources, identities, policy decisions and
effects. Do not require private internal reasoning to establish execution authority.
Review the full primary papers in the bibliography before asserting novelty.
