---
name: regression-table
description: Run the project's standard fixed-effects, center-clustered regression and emit a report-ready table with n, SE type, CI, and exhibit id. Use for every hypothesis in PLAN.md that has a regression spec.
---

# Standard regression procedure

1. Load frames with `analysis.utils.load_frames()`; apply the sample filter named in PLAN.md
   for the hypothesis (`hires_obs`, `flex`, `center_month`, or a within-center window).
2. Build the regime variable with `utils.add_regime(df)` (`legacy`, `new_pre`, `new_post`).
   Never rebuild it by hand.
3. Fit with `utils.fe_ols(df, y, x_terms, fe=["center_id", "<month col>"], cluster="center_id")`.
   For interactions use patsy syntax, e.g. `"essay_rubric_score:C(regime)"`, and report the
   essay slope *per regime* (level plus interaction), not just the interaction terms.
4. Report, for every coefficient of interest: point estimate, cluster-robust SE, 95 % CI, n,
   number of clusters, the FE set, the controls set, and the exhibit id.
5. If the coefficient is a headline (appears in the narrative), also run
   `utils.wild_bootstrap_p()` and report that p-value next to the cluster-robust one.
6. Write the table with `utils.write_table(exhibit_id, df_table, title, sample_line, notes)`,
   which saves `outputs/tables/E##_name.md` and `.csv`.
7. Append to `outputs/RESULTS.md` using `utils.log_result(...)`: hypothesis id, exhibit id, the
   numbers, and a one-line verdict against the falsification criterion in PLAN.md.

## Table layout

| term | estimate | SE (cluster: center) | 95 % CI | n | clusters |
|---|---|---|---|---|---|

Under the table: `Sample: …`, `Fixed effects: …`, `Controls: …`, `Source: analysis/0X_*.py`.

## Rules
- Linear probability model for binary outcomes; say so. Logit only as a robustness check.
- Reopen rates: OLS on the rate; robustness weighted by claims closed.
- Do not drop the level term when adding an interaction.
- Never round a CI to a point. Never report a p-value without the estimate and CI.
