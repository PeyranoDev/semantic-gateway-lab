# Prospective protocol: specification-derived reach predictions

Status: frozen before any campaign on the mutants below was executed.

## Question

Can per-generator detection probabilities, computed only from a specification
model, predict which generator detects a new implementation defect within a
fixed call budget?

## Mutants

`integrations/salon_prospective/mutants.py` removes, one at a time, each top-level
disjunct of every `if ...: raise` guard in `SalonService.read` and
`SalonService.transition`. This yields 18 sites without hand selection. Four of
them coincide with the existing deliberate variants and informed the design, so they
are excluded. The prospective set is the remaining 14 sites.

The measured service source is not edited. Mutants are compiled in memory and
injected only while a research adapter is constructed.

## Predictions

`integrations/salon_prospective/spec.py` removes the corresponding disjunct from the
specification model `expected()` in `integrations/salon/oracle.py`. Where one
specification guard serves both reads and transitions, the removal is restricted to
the operations that the implementation guard covers (`MAPPING`). The unmutated oracle
judges every response.

Before freezing, the specification model was checked on the fixed service and on the
four excluded variants. In all five cases its state graph and violation sets equal the
recorded implementation tables exactly.

For each mutant, the exact model gives P(detect within 120 calls) for `random`,
`seed_extend` and `sequence_uniform`. These are the v0.6 generators, run with the v0.6
settings: depth 8, the ANY target, the charged valid bootstrap, and 30 fresh seeds
(900-929).

- Frozen file: `results/prospective/predictions.json`
- sha256: `2138cab59dea4f3bbe8d12072922f7598d567e5207fa299a01acdbb633116c2a`

## Analysis (fixed in advance)

1. Per cell (mutant x generator): observed detections out of 30 against the frozen
   probability, with a two-sided exact binomial test. The number of cells with
   p < 0.05 is reported. With no model error, about 5% of cells would fall there by
   chance.
2. Pairwise generator order: count the pairs whose frozen probabilities differ by at
   least 0.1, and report how often the observed counts rank the pair the same way.
   Ties count as disagreement.
3. Mutants predicted to have no reachable violation should produce zero detections.

All cells are reported, including disagreements.

## Limits

The specification and implementation share an author. The mutants are generated
systematically but come from one service and one operator family (guard-disjunct
removal). This tests prediction across the specification/implementation boundary
for new defects in a known system. It is not evidence about independent systems.
