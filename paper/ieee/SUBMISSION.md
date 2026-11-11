# Publishing on IEEE Xplore — logic and checklist

IEEE Xplore is a host, not a venue: a paper reaches it by being accepted at an
IEEE conference or journal. The steps below go from the current draft to a
submission.

## 1. Choose the venue (decides template, length, deadlines)

Papers on Xplore closest to this work, as targets:

| Venue | Type | Fit |
|---|---|---|
| IEEE ICST | Conference | Software testing; direct fit (RESTler/AFLNet appear here). |
| IEEE ISSRE | Conference | Reliability + security testing; the closest antecedent [27] is here. |
| ICSE (SEIP / research) | Conference | Top SE venue; more competitive. |
| IEEE Transactions on Software Engineering (TSE) | Journal | For the expanded, journal-length version. |
| IEEE Access | Journal (OA) | Fast, open access, article-processing charge. |

Recommendation: **ICST or ISSRE** for the conference version (what `main.tex`
currently targets); **TSE** if expanded to journal length.

## 2. Use the venue's exact template

`main.tex` uses the official `IEEEtran` class. Before camera-ready, replace it
with the specific template package the venue distributes (same class, sometimes a
pinned version / conference option). Do not change the class to a non-IEEE one.

## 3. Format compliance

- US Letter, 10 pt, two columns (already set by `IEEEtran [conference]`).
- No page numbers / no headers-footers in the camera-ready (IEEE adds them).
- All fonts embedded (pdfTeX embeds by default; verify with `pdffonts main.pdf`).
- Every listed reference is cited and every citation is listed (already true).
- Figures are vector PDF (already true); keep them legible in grayscale.
- Respect the page limit (conference typically 8–10 + references). The draft is
  ~8 pages; trim or move detail to an appendix/online if the venue is stricter.

## 4. Conference-only steps

- **IEEE PDF eXpress**: run the final PDF through PDF eXpress (venue gives a
  conference ID) to produce an Xplore-compliant PDF.
- **Copyright notice**: add the IEEE copyright line to the first page footer
  (venue supplies the exact string; `\IEEEpubidadjcol` / `\thanks` or the
  conference template macro).
- **eCF (electronic Copyright Form)**: sign at submission acceptance.

## 5. Journal-only steps

- Add author biographies and photos (TSE) or omit (IEEE Access).
- No strict page limit, but an over-length charge may apply.

## 6. Open items before submission (TODO)

- [x] **Author affiliation**: Ignacio Peyrano, Universidad Austral
      (`impeyrano@mail.austral.edu.ar`). Add ORCID before camera-ready.
- [ ] **Blind review**: if the chosen venue is double-blind, anonymize the
      author block, the GitHub URL, and self-citations [1], [2].
- [ ] **Title note / draft date**: remove the working-draft framing for
      camera-ready.
- [ ] **Reference completeness**: fill the unverified fields noted in
      `paper/references.md` ([24] volume/issue; [25] venue; [27] pages/DOI).
- [ ] **Artifact evaluation**: the repository supports an artifact badge; prepare
      an artifact-appendix if the venue runs artifact evaluation.
- [ ] **Scope vs. page limit**: if conference, confirm the content fits; if not,
      move the document-benchmark subsection or appendix online.

## 7. Build the submission PDF

```bash
cd paper/ieee && latexmk -pdf main.tex
```

The result `main.pdf` is the submission candidate (pre PDF eXpress).
