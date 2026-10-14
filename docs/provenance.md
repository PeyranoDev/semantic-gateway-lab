# Provenance and changes from the preprint

Author: Ignacio Peyrano. Research artifact prepared 2026-10-14.

## Reference sources

- Uploaded preprint: `2604.25555v1.pdf`, arXiv:2604.25555v1, April 2026.
  SHA-256: `a830518826ed5059203255047ee99e148f62e94eb358edced0d6e529748a8d00`.
  The PDF is not redistributed in this repository; retain the uploaded source.
- Existing PoC: https://github.com/PeyranoDev/semantic-gateway-poc
  Reviewed default branch: `master`.
  Reviewed commit: `1efca4bf0a9e541577ba050e5f4e57ce367bdb68`.
  Inspected README, `gateway/epa.py`, `gateway/policy.py` and
  `fuzzer/semantic_fuzzer.py` using the connected GitHub account.

## What was retained

The document-sharing scenario, the separation of proposed actions and authority,
the accept-sharing overwrite example, seeded stochastic testing, and enabled-tool
abstractions as a research direction.

## What was rewritten

All delivered Python implementation and tests are newly authored. No original
source files are copied. The existing fuzzer calls `EPAGraph.next_state` on a
handwritten graph; a constructor flag inserts a known defective edge. The new
fuzzer calls `Gateway.execute`, checks concrete effects and builds observed
coverage from snapshots. Mutants change implementation checks, not graph labels.

The new artifact does not carry over the preprint's 500,000-sequence, 200-tool,
99.4% filter, 84.2% code-reduction, universal discovery or proof-of-safety claims.
Each result included here comes from the delivered campaign configuration.

The original repository README refers to a `tools/documents.py` path that could
not be fetched at the reviewed revision. A root `LICENSE` was also unavailable
through the connector. Neither file is relied on or copied. The delivered MIT
license applies to this new code; no upstream license is inferred.

## Bibliographic repair

The preprint's reference [5] gives incorrect authors/year for *Validation of
Contracts using Enabledness Preserving Finite State Abstractions*. The correct
authors are Guido de Caso, Víctor Braberman, Diego Garbervetsky and Sebastián
Uchitel, ICSE 2009. Verify against the research group's primary page:
https://lafhis.dc.uba.ar/contractor/contractor.net-web/

## Publication status

The manuscript is a working draft. Novelty, completeness of related work and
external validity are not established. Local artifact validation used Python
3.12. GitHub Actions supplies an additional Python version matrix; its current
status is recorded by the repository's Actions runs rather than inferred from
the local tests. Historical campaign-validation metadata records the local
checks that preceded publication.

Hosted repository: https://github.com/PeyranoDev/semantic-gateway-lab
The repository was created by the author and populated through the connected
GitHub account. The earlier ZIP is a separate snapshot of the initial artifact.
