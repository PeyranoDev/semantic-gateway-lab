# Feature: LaTeX / IEEE Xplore conversion

Objective: convert paper/manuscript.md to an IEEE LaTeX paper, single source with a
conference/journal flag, and document the IEEE Xplore submission logic.
Branch: paper/latex-ieee (from main). Decision (user): one source written to the
conference extension, switch journal later.

## Done
- paper/ieee/main.tex: IEEEtran, flag at top (conference default, journal commented).
  Full faithful conversion: abstract, index terms, 10 sections, 2 appendix tables,
  7 tables (wide ones as table*), 2 figures as figure* (vector PDF), evidence tiers.
- paper/ieee/references.bib: 27 entries (r1..r27 -> [n]); IEEE numbers by citation order.
- Figures regenerated as vector PDF (scripts/plot_reach*.py now also emit pdf).
- Builds clean: latexmk -> 8 pages US Letter, 0 undefined citations, 0 overfull hboxes,
  fonts embedded. 21 references appear (only cited ones, per IEEE).
- paper/ieee/README.md (build) and SUBMISSION.md (Xplore venue/format/compliance checklist).

## Open (in SUBMISSION.md)
- Confirm author affiliation + ORCID (placeholder now).
- Pick venue (ICST/ISSRE conference, or TSE/IEEE Access journal).
- Camera-ready: copyright notice, PDF eXpress, blind-review anonymization if needed.
- Fill unverified ref fields ([24] vol, [25] venue, [27] pages/DOI).
