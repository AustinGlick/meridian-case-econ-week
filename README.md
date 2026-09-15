# Meridian Casualty — Econ Week 2026 case

Team analysis for "Hiring Is Broken — Can You Fix It?". Read `prompt.pdf` first.

## Where things are

| Path | What it is |
|---|---|
| `prompt.pdf` | The case prompt |
| `meridian-case-data/` | Raw data. Read-only: never edit these files |
| `analysis/` | Numbered scripts, run in order; `utils.py` holds shared definitions |
| `outputs/exhibits/` | Figures, `E##_name.png` |
| `outputs/tables/` | Tables, `E##_name.md` and `.csv` |
| `outputs/RESULTS.md` | Every estimate with its exhibit id, sample, spec and verdict |
| `report/REVIEW_2026-09-14.md` | What was checked and fixed, what is left, which graphs to use |
| `report/narrative_outline.md` | The four-page structure with exhibit references |
| `PLAN.md` | Hypotheses H0–H12 and what would falsify each |
| `CLAUDE.md` | Analysis rules (also read by Claude Code) |

The outputs are committed, so you can read the results without running anything.

## Running it yourself

Python 3.11 or newer. From the repo root:

```
pip install pandas numpy statsmodels scipy matplotlib tabulate patsy
python -m analysis.00_load
python -m analysis.02_retention_trend
python -m analysis.03_pool_quality
python -m analysis.04_recruiter_capacity
python -m analysis.05_screen_components
python -m analysis.06_essay_validity
python -m analysis.07_identification
python -m analysis.08_cost_worksheet
```

Script 07 runs a wild-cluster bootstrap and takes about five minutes. Each script overwrites its
own exhibits and its own block in `outputs/RESULTS.md`.

## Building the PDF

`python report/build_report.py` from the repo root (needs `pip install typst pypdf`; no pandoc,
LaTeX or system fonts). It converts the Markdown narrative in `report/draft.md` to Typst, appends
every exhibit from `outputs/` in the order listed under "Appendix order" in
`report/narrative_outline.md`, and writes `report/Meridian_Round1.pdf` (committed) plus the Typst
source in `build/report.typ`. The build fails if the narrative exceeds four pages or if an exhibit
id in the outline list has no PNG or table on disk; it warns about exhibits on disk that the
outline does not list.

## Rules everyone should know

- Numbers in the report come from `outputs/RESULTS.md`, never from memory.
- The AI-era cutoff lives in `analysis/utils.py` only. Change it there and re-run everything.
- Commit changes to scripts, not hand edits to outputs.
