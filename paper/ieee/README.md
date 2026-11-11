# IEEE LaTeX source

IEEE paper built from `paper/manuscript.md`, using the official `IEEEtran` class.

## Build

```bash
cd paper/ieee
latexmk -pdf main.tex        # -> main.pdf
# or: pdflatex main; bibtex main; pdflatex main; pdflatex main
latexmk -C                   # clean aux files
```

Requires a TeX distribution with `IEEEtran.cls` and `IEEEtran.bst` (TeX Live
`texlive-publishers`). No internet needed at build time.

## Target format (single source)

The top of `main.tex` has one switch:

```latex
\documentclass[conference]{IEEEtran}   % conference (default)
% \documentclass[journal]{IEEEtran}    % journal (TSE / IEEE Access)
```

The content is written to the conference extension. Switching to `journal`
compiles the same text in the journal layout; a journal submission would then be
expanded (more method/results detail) to fit that venue's expectations.

## Figures

`figures/*.pdf` are vector figures regenerated from the analysis data:

```bash
python scripts/plot_reach.py        paper/ieee/figures   # reach-calibration.pdf
python scripts/plot_reach_curves.py paper/ieee/figures   # reach-curves.pdf
```

(The plot scripts need `matplotlib`; the figure data lives under `results/`.)

## Files

- `main.tex` — the paper.
- `references.bib` — bibliography (keys `r1`..`r27` map 1:1 to the `[n]` of
  `paper/references.md`; IEEE numbers them in order of first citation at build
  time, so printed numbers differ from the key numbers — this is expected).
- `figures/` — vector PDFs.
- `SUBMISSION.md` — IEEE Xplore submission checklist and open items.
