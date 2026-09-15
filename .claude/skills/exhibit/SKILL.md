---
name: exhibit
description: Produce one appendix exhibit (figure or table) with the required naming, labelling, sample statement, source note, and RESULTS.md log entry. Use every time an E## exhibit from PLAN.md is created.
---

# Before writing chart code
Load the `dataviz` skill first. It governs colour, chart form, and legibility.

# Naming
- Figures: `outputs/exhibits/E##_short_name.png` (e.g. `E06_essay_score_by_ats_monthly.png`).
- Tables: `outputs/tables/E##_short_name.md` and `.csv` with the same stem.
- Exhibit ids come from the register in PLAN.md. Do not renumber; add `E##b` for a variant.

# Every figure must have
1. A title that states the finding, not the variable ("Essay scores rise on the new ATS after
   2023; legacy centers are flat"), plus the exhibit id in the title.
2. Axis labels with units ("Six-month retention rate (share of hires)", "Application month").
3. A one-line sample statement under the plot: what rows, how many, which months, what was
   excluded ("Sample: 41,677 permanent hires with an observed six-month outcome, start months
   2021-01 to 2025-06; 4,589 censored hires excluded").
4. A source note: the script that made it.
5. Vertical reference lines for the AI-era cutoff and migration waves where time is on the x-axis.
6. Confidence bands or error bars when the y-value is an estimate.
7. Legend labels in plain English (`Legacy ATS (timed, no paste)`, `New ATS (untimed, paste)`).

# Every table must have
Title with exhibit id; column headers with units; sample statement; notes on FE, controls, SE
type; source script. Use `utils.write_table()`.

# After saving
Append to `outputs/RESULTS.md` via `utils.log_result()`:
```
## H# — <hypothesis title>  (E##)
- Finding: <one sentence with the number and its range>
- Spec: <outcome ~ terms; FE; cluster>
- Sample: <n, window, exclusions>
- Verdict: supported | not supported | mixed — <why, against the falsification line in PLAN.md>
```
