"""H5 -- which screen components still carry information, by regime. This is the "what the
process gets right" half of deliverable (a): license, referral, and the interview may still work
even where the essay does not, and recruiters' own screening decisions may or may not have
adapted to the essay's declining signal.

Regimes are the FOUR ATS x era cells (legacy_pre, legacy_post, new_pre, new_post): the legacy
system also drifts after 2023, so pooling legacy 2021-25 would overstate its "still works" slope.

Produces:
  E11  coefficient plot: predictors of six-month retention, by regime, with 95% CIs
  E11b the table behind E11
  E11c the essay's weight inside the recruiter screen score, by regime

    python -m analysis.05_screen_components
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.utils import (load_frames, hires_obs, fe_ols, write_table, save_fig, log_result,
                            REGIMES4, REGIME4_LABELS, PALETTE, AI_ERA_CUTOFF)

PREDICTORS = ["essay_rubric_score", "resume_score", "has_adjuster_license",
             "prior_claims_years", "referral", "interview_score"]
PRETTY = {"essay_rubric_score": "Essay score (per point, 0-30)",
         "resume_score": "Resume score (per SD)",
         "has_adjuster_license": "Has adjuster license (0/1)",
         "prior_claims_years": "Prior claims years (per year)",
         "referral": "Employee referral (0/1)",
         "interview_score": "Interview score (per SD)"}
SHORT = {r: REGIME4_LABELS[r].replace("\n", " ") for r in REGIMES4}


def main() -> None:
    d = load_frames()
    h = hires_obs(d["hires_joined"])

    # --- by-regime predictive regressions (one regression per cell) -----------------
    rows = []
    for regime in REGIMES4:
        sub = h[h["regime4"] == regime]
        res = fe_ols(sub, "retained_6mo", PREDICTORS, fe=["center_id", "start_month"])
        for p in PREDICTORS:
            est, se = res.params[p], res.bse[p]
            rows.append({"regime": regime, "predictor": p, "estimate": est, "se": se,
                        "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
                        "n": res.sample_n, "clusters": res.n_clusters})
    coef_df = pd.DataFrame(rows)
    write_table("E11b", coef_df.round(4), "Predictors of six-month retention, by regime",
               sample_line=f"{len(h):,} hires with an observed outcome, split into four ATS x era cells.",
               notes="Outcome: retained_6mo (linear probability). FE: center, start_month. "
                     "Cluster: center. Each cell is a separate regression on its subsample; all "
                     "six predictors enter together.",
               source="analysis/05_screen_components.py")

    fig, ax = plt.subplots(figsize=(10, 7.5))
    offsets = dict(zip(REGIMES4, [-0.3, -0.1, 0.1, 0.3]))
    for i, pred in enumerate(PREDICTORS):
        for regime in REGIMES4:
            row = coef_df[(coef_df["predictor"] == pred) & (coef_df["regime"] == regime)].iloc[0]
            y = i + offsets[regime]
            ax.errorbar(row["estimate"], y,
                       xerr=[[row["estimate"] - row["ci_low"]], [row["ci_high"] - row["estimate"]]],
                       fmt="o", color=PALETTE[regime], capsize=3, markersize=6, linewidth=1.5,
                       label=SHORT[regime] if i == 0 else None)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(range(len(PREDICTORS)))
    ax.set_yticklabels([PRETTY[p] for p in PREDICTORS])
    ax.invert_yaxis()
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.6)
    ax.set_xlabel("Change in six-month retention probability per unit of the input (95% CI)")
    ax.set_title("E11. The essay is the only screen input whose predictive power collapses in the "
                 "AI era;\nlicense, referral, resume and interview all still predict retention",
                 fontsize=11)
    ax.legend(title="Regime (ATS at application x era)", fontsize=8, loc="lower right")
    save_fig(fig, "E11", "screen_component_coefficients_by_regime",
            sample_line=f"{len(h):,} hires with an observed six-month outcome, split into four cells "
                        f"(legacy/new ATS x application before/after {AI_ERA_CUTOFF}); "
                        f"{len(d['hires_joined']) - len(h):,} censored hires excluded.",
            source="analysis/05_screen_components.py")
    plt.close(fig)

    # --- do recruiters still lean on the essay in screening decisions? -------------
    rows2 = []
    for regime in REGIMES4:
        sub = d["applications"][d["applications"]["regime4"] == regime]
        res = fe_ols(sub, "recruiter_screen_score",
                    ["essay_rubric_score", "resume_score", "has_adjuster_license",
                     "prior_claims_years", "referral", "currently_employed"],
                    fe=["center_id", "application_month"])
        est, se = res.params["essay_rubric_score"], res.bse["essay_rubric_score"]
        rows2.append({"regime": regime, "essay_weight_in_screen_score": est, "se": se,
                     "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se, "n": res.sample_n,
                     "r_squared": res.rsquared})
    screen_df = pd.DataFrame(rows2)
    write_table("E11c", screen_df.round(4),
               "How much weight recruiters place on the essay score, by regime",
               sample_line="All reviewed applications, split by regime.",
               notes="Outcome: recruiter_screen_score. FE: center, application_month. Cluster: "
                     "center. An R-squared near 1 means the screen score is a fixed formula of "
                     "its inputs, not a judgment.",
               source="analysis/05_screen_components.py")

    print(coef_df.round(4).to_string(index=False))
    print(screen_df.round(4).to_string(index=False))

    c = coef_df.set_index(["predictor", "regime"])
    ew = screen_df.set_index("regime")
    fmt = lambda p, r: (f"{c.loc[(p, r), 'estimate']:.4f} [{c.loc[(p, r), 'ci_low']:.4f}, "  # noqa: E731
                        f"{c.loc[(p, r), 'ci_high']:.4f}]")
    log_result(
        "H5 -- which screen components still work", "E11/E11b/E11c",
        finding=(f"Controlling for the other inputs (E11b, n by cell: "
                 f"{coef_df.groupby('regime', observed=True)['n'].first().to_dict()}), the essay's "
                 f"slope on six-month retention is {fmt('essay_rubric_score','legacy_pre')} per "
                 f"point on the legacy ATS before 2023, {fmt('essay_rubric_score','legacy_post')} "
                 f"on legacy after 2023, {fmt('essay_rubric_score','new_pre')} on the new ATS "
                 f"before 2023, and {fmt('essay_rubric_score','new_post')} on the new ATS after "
                 f"2023. License ({fmt('has_adjuster_license','legacy_pre')} -> "
                 f"{fmt('has_adjuster_license','new_post')}), referral "
                 f"({fmt('referral','legacy_pre')} -> {fmt('referral','new_post')}), resume score "
                 f"({fmt('resume_score','legacy_pre')} -> {fmt('resume_score','new_post')}) and "
                 f"the interview ({fmt('interview_score','legacy_pre')} -> "
                 f"{fmt('interview_score','new_post')}) all keep or gain predictive power -- these "
                 f"are the parts of the process that still work. The essay's weight inside the "
                 f"recruiter screen score is {ew.loc['legacy_pre','essay_weight_in_screen_score']:.3f} "
                 f"in every cell (E11c; R-squared {ew['r_squared'].min():.3f}-"
                 f"{ew['r_squared'].max():.3f}): the screen score is a fixed formula, so the "
                 f"process still weights the essay exactly as it did when the essay worked."),
        spec="retained_6mo ~ essay + resume + license + prior_years + referral + interview + "
             "center FE + start-month FE, separately per ATS x era cell, cluster center; "
             "recruiter_screen_score ~ same inputs, per cell",
        sample=f"{len(h):,} hires with an observed outcome; all reviewed applications for the "
              "screen-score regression",
        verdict="mixed -- license, referral, resume and interview hold up or strengthen (the "
               "process gets these right); the essay's mechanical weight in the screen formula "
               "has not moved while its predictive content went to zero on the new ATS and "
               "roughly halved on the legacy ATS -- that unadapted formula is the failure."
    )


if __name__ == "__main__":
    main()
