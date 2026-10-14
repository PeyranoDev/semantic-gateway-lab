# Sequence-mutation experiment v0.2

This protocol is committed before executing the v0.2 matrix. It is an exploratory
follow-up to the inspected v0.1 results, not an independently preregistered study.

## Treatments

The three frozen v0.1 engines are rerun at the same budgets/seeds as the new engines.
Their Python files are unchanged. A single-threaded harness injects a reserved
service factory only when evaluating additional implementation variants.

The new mutation engines begin with six legitimate workflow programs: sharing
where a same-department recipient exists; two delete/recreate/delete transactions
with distinct fresh fixture approvals per resource; and list/read/update/export.
They contain no unauthorized terminal call. The generator does not import the
directed regression witnesses, the backend, the oracle or defect labels.

Every bootstrap call is counted. A general mutator changes a field, inserts a call,
duplicates a contiguous segment, deletes a step, swaps steps or splices another
legitimate program. Insertions retain an anchor's principal/resource; argument
mutations preferentially sample observed values. Approvals come from a trusted
test fixture and include fresh and historical tokens, not guessed signatures.

- sequence_uniform selects legitimate programs uniformly without feedback memory.
- sequence_enabled and sequence_enriched use the same mutator, seed programs,
  capacity-64 corpus and inverse-selection-count scheduler. They differ only in
  the observational projection used to identify transition feedback.
- no_recipient and no_approval remove those predicate families from enriched keys.
- enriched_uniform keeps full enriched keys but selects stored programs uniformly.

Corpus entries are complete tested programs rather than v0.1 state-reaching prefixes.
One shortest program is retained per observed abstract transition; oldest entries
are evicted at capacity. This changes the search engine as a whole relative to
v0.1; only comparisons within the new matched engines isolate projection effects.
Multiple keys can point to the same program, so corpus partitioning changes its
effective sampling weight. This is measured rather than assumed beneficial.

## Budget and diagnostics

10 new seeds (200-209), 9 engines, 12 variants, budget 3000, depth 20: 1080 runs.
The call budget includes initialization, repeats, denied calls and unchanged source
prefixes. Shrinking happens afterward and is separately counted.

Common discovery fractions and capped call effort are comparable across engines.
Legacy replay calls are selected-prefix replays; new source-prefix calls measure
the unchanged leading part of a mutation source. Their definitions differ and
must not be pooled as one overhead metric. Additional diagnostics include
bootstrap calls, no-op mutations, corpus evictions and stored-program lengths.

## Reserved variants

list_scope, unauthorized_update and cross_department_share were not in v0.1.
They are three new synthetic designs by the same implementation process, not
independently designed or real-world vulnerabilities. The reference oracle is
unchanged. This tests extension to new cases within the same service, not broad
external generalization. A legitimate bootstrap program may already reveal an
incorrect output; the discovery phase is explicitly recorded.

## Analysis and artifact requirements

Keep all misses right-censored. Record matched seed-level contrasts without
claiming significance or optimality. Validate every minimized witness against
the mutated service and the fixed control. Freeze source/config/seed-program
hashes and preserve compressed raw data, summaries, validation and paired
descriptions in the repository. Successful unit tests do not replace discovery
evidence. No LLM, actual MCP transport or human approval is evaluated here.
