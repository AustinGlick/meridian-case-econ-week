"""H6 -- core test of deliverable (b): does the essay still predict outcomes?
H7 -- mechanism: is it specifically fast, high-scoring essays that stopped predicting?
H8 -- placebo: did OTHER screen inputs also lose predictive power at the same time?

This is the most important script in the project. Every number here must be defensible: which
comparison, on whom, what has to be true (see PLAN.md H6-H9 and CLAUDE.md analysis rules).

Regimes are the FOUR ATS x era cells. The comparison is the within-cell slope of essay score
on the outcome; "on whom" is (i) permanent hires (selected on the essay -> attenuated) and
(ii) flex placements (not selected on the essay by Meridian).

Produces:
  E12  retention by essay bin x regime (headline exhibit for deliverable b)
  E12b/c/d essay slopes by regime: hires-retention, hires-reopen, flex-reopen
  E12e Spec C: essay slope 12 months before vs after a center's own migration (2023/24 waves)
  E13  essay x time-in-section interaction (mechanism)
  E14  placebo table (other inputs' slopes by regime)

    python -m analysis.06_essay_validity
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.utils import (load_frames, hires_obs, fe_ols, regime_slopes, write_table, save_fig,
                            log_result, event_window, REGIMES4, REGIME4_LABELS, PALETTE,
                            HIRE_CTRL, FLEX_CTRL, ESSAY_BINS, ESSAY_BIN_LABELS, EVENT_WINDOW)


def slopes4(df, y, ctrl, fe):
    res = fe_ols(df, y, ["essay_rubric_score:C(regime4)", "C(regime4)", *ctrl], fe=fe)
    tab = regime_slopes(res, "essay_rubric_score", cat="regime4")
    tab["n_cell"] = [int((df.dropna(subset=[y])["regime4"] == r).sum()) for r in REGIMES4]
    return res, tab


def main() -> None:
    d = load_frames()
    h = hires_obs(d["hires_joined"])
    flex = d["flex_joined"]
    mig = d["ats_migration"]

    # ============================================================================
    # H6 -- Spec A: essay slope on retention and reopen, by regime (hires)
    # ============================================================================
    res_hr, s_hr = slopes4(h, "retained_6mo", HIRE_CTRL, ["center_id", "start_month"])
    write_table("E12b", s_hr.round(5),
               "Essay-score slope on six-month retention, by regime (hires)",
               sample_line=f"n={res_hr.sample_n:,}, {res_hr.n_clusters} center clusters.",
               notes="Outcome: retained_6mo. Controls: resume, license, prior years, referral, "
                     "interview score. FE: center, start_month. Cluster: center. Hires are "
                     "selected on the essay, which attenuates every slope toward zero.",
               source="analysis/06_essay_validity.py")
    res_ho, s_ho = slopes4(h, "reopen_rate_6mo_pct", HIRE_CTRL[:-1], ["center_id", "start_month"])
    write_table("E12c", s_ho.round(5),
               "Essay-score slope on six-month reopen rate, by regime (hires)",
               sample_line=f"n={res_ho.sample_n:,}, {res_ho.n_clusters} center clusters.",
               notes="Outcome: reopen_rate_6mo_pct (percentage points). Negative = higher essay "
                     "score predicts fewer reopens. Same FE/cluster as E12b.",
               source="analysis/06_essay_validity.py")

    # ============================================================================
    # H6 -- Spec B: essay slope on reopen rate (FLEX -- not selected on the essay)
    # ============================================================================
    res_f, s_f = slopes4(flex, "reopen_rate_pct", FLEX_CTRL, ["center_id", "placement_month"])
    res_fw = fe_ols(flex, "reopen_rate_pct", ["essay_rubric_score:C(regime4)", "C(regime4)", *FLEX_CTRL],
                    fe=["center_id", "placement_month"], weights="claims_closed")
    s_fw = regime_slopes(res_fw, "essay_rubric_score", cat="regime4")
    s_f["weighted_estimate"] = s_fw["estimate"].values
    s_f["weighted_se"] = s_fw["se"].values
    write_table("E12d", s_f.round(5),
               "Essay-score slope on reopen rate, by regime (flex placements -- NOT selected "
               "on the essay by Meridian)",
               sample_line=f"n={res_f.sample_n:,} flex placements, {res_f.n_clusters} center clusters.",
               notes="Outcome: reopen_rate_pct. Controls: resume, license, prior years, referral, "
                     "certification level. FE: center, placement_month. Cluster: center. A MORE "
                     "NEGATIVE slope means the essay is more informative. Weighted columns weight "
                     "by claims_closed.",
               source="analysis/06_essay_validity.py")

    # ============================================================================
    # H6 -- Spec C: within-center before/after migration (2023/2024 waves), never-migrated
    # centers over the same calendar window as control
    # ============================================================================
    ev, nv, med = event_window(h, mig)
    spec_c = []
    for label, df in (("2023/24-wave centers, own migration month", ev),
                      (f"never-migrated centers, pseudo-event {med}", nv)):
        r = fe_ols(df, "retained_6mo", ["essay_rubric_score:C(post)", "C(post)", *HIRE_CTRL],
                   fe=["center_id", "start_month"])
        for p in (0, 1):
            k = f"essay_rubric_score:C(post)[{p}]"
            spec_c.append({"group": label, "window": f"{EVENT_WINDOW[1] + 1} months after" if p
                           else f"{-EVENT_WINDOW[0]} months before",
                           "estimate": r.params[k], "se": r.bse[k],
                           "ci_low": r.params[k] - 1.96 * r.bse[k],
                           "ci_high": r.params[k] + 1.96 * r.bse[k], "n": r.sample_n})
    spec_c = pd.DataFrame(spec_c)
    write_table("E12e", spec_c.round(5),
               "Spec C: essay slope on retention in the 12 months before vs after a center's own "
               "ATS migration (2023/24 waves) vs never-migrated centers over the same calendar window",
               sample_line=f"{len(ev):,} hires at 2023/2024-wave centers; {len(nv):,} hires at "
                           f"never-migrated centers.",
               notes="Same controls/FE/cluster as E12b. The never-migrated slope also falls over "
                     "this window (calendar 2022-09 to 2024-08), so the migration itself is not "
                     "the whole story: the AI era degrades the timed section too, more slowly.",
               source="analysis/06_essay_validity.py")

    # ============================================================================
    # H6 -- Spec D: nonlinear -- retention by essay bin x regime (E12, headline)
    # ============================================================================
    h["essay_bin"] = pd.cut(h["essay_rubric_score"], bins=ESSAY_BINS, labels=ESSAY_BIN_LABELS)
    g = h.groupby(["essay_bin", "regime4"], observed=True)["retained_6mo"].agg(
        ["mean", "count", "std"]).reset_index()
    g["se"] = g["std"] / np.sqrt(g["count"])
    fig, axes = plt.subplots(1, 4, figsize=(11, 5.4), sharey=True)
    for ax, regime in zip(axes, REGIMES4):
        sub = g[(g["regime4"] == regime) & (g["count"] >= 100)]
        ax.bar(sub["essay_bin"].astype(str), sub["mean"], yerr=1.96 * sub["se"], capsize=4,
              color=PALETTE[regime], width=0.7)
        ax.set_title(REGIME4_LABELS[regime], fontsize=11)
        ax.set_xlabel("Essay score bin (0-30)")
        ax.set_ylim(0.70, 0.96)
        for i, row in sub.reset_index().iterrows():
            ax.text(i, row["mean"] + 1.96 * row["se"] + 0.004, f"{row['mean']:.3f}\nn={int(row['count']):,}",
                    ha="center", fontsize=8.5)
    axes[0].set_ylabel("Six-month retention rate (share of hires)")
    fig.suptitle("E12. A top-bin essay (24-30) used to predict better retention than an 18-23 essay;\n"
                 "on the new ATS after 2023 it predicts slightly worse retention",
                 fontsize=12.5)
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    save_fig(fig, "E12", "retention_by_essay_bin_regime",
            sample_line=f"{len(h):,} permanent hires with an observed six-month outcome, binned by "
                        f"essay score within four ATS x era cells; bins with under 100 hires not shown. "
                        f"Error bars: 95% CI. Y-axis starts at 0.70.",
            source="analysis/06_essay_validity.py")
    plt.close(fig)

    # ============================================================================
    # H7 -- mechanism: time spent in the essay section (with cell main effects)
    # ============================================================================
    h["fast15"] = h["fast_essay15"]      # definition of record lives in utils.add_regime
    res_mech = fe_ols(h, "retained_6mo",
                      ["essay_rubric_score:C(regime4):C(fast15)", "C(regime4)*C(fast15)"],
                      fe=["center_id", "start_month"])
    mech_rows = []
    for regime in REGIMES4:
        for fast in (0, 1):
            k = f"essay_rubric_score:C(regime4)[{regime}]:C(fast15)[{fast}]"
            est, se = res_mech.params[k], res_mech.bse[k]
            n_cell = int(((h["regime4"] == regime) & (h["fast15"] == fast)).sum())
            mech_rows.append({"regime": regime, "fast_lt_15min": fast, "estimate": est, "se": se,
                             "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se, "n_cell": n_cell})
    mech_df = pd.DataFrame(mech_rows)
    write_table("E13b", mech_df.round(5),
               "Essay-score slope on retention, by regime and by whether the applicant spent "
               "under 15 minutes in the situational section",
               sample_line=f"{len(h):,} hires with an observed outcome.",
               notes="Outcome: retained_6mo. essay x cell x fast15 slopes with cell x fast15 main "
                     "effects, center + start-month FE, cluster center. fast_lt_15min=1 means "
                     "essay_section_minutes < 15.",
               source="analysis/06_essay_validity.py")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    width = 0.36
    x = np.arange(len(REGIMES4))
    for i, (fast, lab, col) in enumerate([(0, "15+ minutes in section", "#0072B2"),
                                          (1, "Under 15 minutes in section", "#E69F00")]):
        sub = mech_df[mech_df["fast_lt_15min"] == fast].set_index("regime").reindex(REGIMES4)
        ax.bar(x + (i - 0.5) * width, sub["estimate"], width * 0.94, yerr=1.96 * sub["se"],
              label=lab, capsize=4, color=col)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([REGIME4_LABELS[r] for r in REGIMES4], fontsize=10.5)
    ax.set_ylabel("Essay-score slope on six-month retention (per point, 95% CI)")
    ax.set_title("E13. Essays written in 15+ minutes still predict retention everywhere;\n"
                 "fast essays predict nothing on the legacy ATS after 2023\n"
                 "and predict WORSE retention on the new ATS after 2023", fontsize=12.5)
    ax.legend(title="Time in situational section")
    save_fig(fig, "E13", "essay_slope_by_speed_regime",
            sample_line=f"{len(h):,} hires with an observed six-month outcome, split by ATS x era "
                        f"cell and by time spent in the situational section.",
            source="analysis/06_essay_validity.py")
    plt.close(fig)

    evm = []
    for regime in REGIMES4:
        sub = d["applications"][d["applications"]["regime4"] == regime]
        r = fe_ols(sub, "essay_rubric_score", ["essay_section_minutes"],
                  fe=["center_id", "application_month"])
        evm.append({"regime": regime, "estimate": r.params["essay_section_minutes"],
                    "se": r.bse["essay_section_minutes"], "n": r.sample_n})
    evm_df = pd.DataFrame(evm).set_index("regime")
    write_table("E13c", evm_df.round(5), "Essay score per minute spent in the section, by regime",
               sample_line="All reviewed applications, by cell.",
               notes="essay_rubric_score ~ essay_section_minutes + center FE + application-month "
                     "FE, cluster center. Positive = longer effort earns a higher score.",
               source="analysis/06_essay_validity.py")

    # ============================================================================
    # H8 -- placebo: do OTHER inputs lose predictive power at the same time?
    # ============================================================================
    placebo_rows = []
    for var in ["resume_score", "has_adjuster_license", "prior_claims_years"]:
        res_p = fe_ols(h, "retained_6mo", [f"{var}:C(regime4)", "C(regime4)"],
                      fe=["center_id", "start_month"])
        sl = regime_slopes(res_p, var, cat="regime4"); sl["variable"] = var
        placebo_rows.append(sl)
    res_int = fe_ols(h[h["interview_score"].notna()], "retained_6mo",
                     ["interview_score:C(regime4)", "C(regime4)"], fe=["center_id", "start_month"])
    sl_int = regime_slopes(res_int, "interview_score", cat="regime4"); sl_int["variable"] = "interview_score"
    placebo_rows.append(sl_int)
    placebo_df = pd.concat(placebo_rows, ignore_index=True)
    write_table("E14", placebo_df.round(5),
               "Placebo test: slope of other screen inputs on six-month retention, by regime",
               sample_line=f"{len(h):,} hires with an observed outcome "
                           f"(interview_score restricted to applicants who were interviewed).",
               notes="Univariate slopes (each input alone) with center + start-month FE, cluster "
                     "center. If these are stable while the essay's slope collapses (E12b), the "
                     "essay result is not an artifact of a center-wide shift in hiring quality or "
                     "measurement. E11b gives the multivariate version.",
               source="analysis/06_essay_validity.py")

    print(s_hr.round(5)); print(s_ho.round(5)); print(s_f.round(5)); print(spec_c.round(5))
    print(mech_df.round(5)); print(evm_df.round(5)); print(placebo_df.round(5))

    hr, ho, fx = s_hr.set_index("regime"), s_ho.set_index("regime"), s_f.set_index("regime")
    ci = lambda t, r: f"[{t.loc[r,'ci_low']:.4f}, {t.loc[r,'ci_high']:.4f}]"  # noqa: E731
    log_result(
        "H6 -- does the essay still predict outcomes", "E12/E12b/E12c/E12d/E12e",
        finding=(f"Comparison: the slope of essay score on the outcome within each ATS x era cell. "
                 f"On whom: (i) permanent hires (selected on the essay, so every slope is "
                 f"attenuated) and (ii) flex placements (not selected on the essay by Meridian). "
                 f"HIRES, retention per essay point (E12b, n={res_hr.sample_n:,}): legacy pre-2023 "
                 f"{hr.loc['legacy_pre','estimate']:.4f} {ci(hr,'legacy_pre')}; legacy post-2023 "
                 f"{hr.loc['legacy_post','estimate']:.4f} {ci(hr,'legacy_post')}; new pre-2023 "
                 f"{hr.loc['new_pre','estimate']:.4f} {ci(hr,'new_pre')}; new post-2023 "
                 f"{hr.loc['new_post','estimate']:.4f} {ci(hr,'new_post')}. HIRES, reopen rate "
                 f"(E12c): legacy pre {ho.loc['legacy_pre','estimate']:.3f} -> legacy post "
                 f"{ho.loc['legacy_post','estimate']:.3f}; new pre {ho.loc['new_pre','estimate']:.3f} "
                 f"-> new post {ho.loc['new_post','estimate']:.3f} (sign flips). FLEX, reopen rate "
                 f"(E12d, n={res_f.sample_n:,}): legacy pre {fx.loc['legacy_pre','estimate']:.3f} "
                 f"{ci(fx,'legacy_pre')}; legacy post {fx.loc['legacy_post','estimate']:.3f} "
                 f"{ci(fx,'legacy_post')}; new pre {fx.loc['new_pre','estimate']:.3f} "
                 f"{ci(fx,'new_pre')}; new post {fx.loc['new_post','estimate']:.3f} "
                 f"{ci(fx,'new_post')}. So: on the new ATS in the AI era the essay carries no "
                 f"usable signal for hires and about a third of its former signal for flex; on the "
                 f"legacy ATS in the AI era it keeps roughly half (hires) to two-thirds (flex). "
                 f"Spec C (E12e) shows the same within centers that migrated in 2023/24 "
                 f"({spec_c.iloc[0]['estimate']:.4f} before -> {spec_c.iloc[1]['estimate']:.4f} "
                 f"after), but never-migrated centers over the same calendar window also fall "
                 f"({spec_c.iloc[2]['estimate']:.4f} -> {spec_c.iloc[3]['estimate']:.4f}, n="
                 f"{int(spec_c.iloc[2]['n']):,}), which is why the four-cell comparison, not "
                 f"migration alone, is the identifying comparison. E12 shows it nonparametrically: "
                 f"the 24-30 bin out-retains the 18-23 bin in every cell except new ATS post-2023, "
                 f"where it under-retains it."),
        spec="Spec A (hires): retained_6mo ~ essay:C(regime4) + C(regime4) + controls + center FE "
             "+ start-month FE, cluster center. Spec B (flex): reopen_rate_pct ~ essay:C(regime4) "
             "+ C(regime4) + controls + certification FE + center FE + placement-month FE, cluster "
             "center (claims-weighted robustness in E12d). Spec C: essay:C(post) within +/-12 "
             "months of migration.",
        sample=f"Spec A: {res_hr.sample_n:,} hires with an observed six-month outcome. Spec B: "
              f"{res_f.sample_n:,} flex placements. Spec C: {len(ev):,} + {len(nv):,} hires.",
        verdict=("supported -- the essay no longer works as a screen on the new ATS in the AI "
                 "era and works at reduced strength on the legacy ATS. What must be true: "
                 "selection into the hire sample on the essay must not have changed in a way that "
                 f"produces a zero slope by itself (the essay SD among hires is "
                 f"{h.groupby('regime4', observed=True)['essay_rubric_score'].std().min():.2f}-"
                 f"{h.groupby('regime4', observed=True)['essay_rubric_score'].std().max():.2f} "
                 f"across cells, E15c), and flex placement must not be selected on the essay "
                 "(stated in the case). Identification threats are in H9.")
    )

    m = mech_df.set_index(["regime", "fast_lt_15min"])
    log_result(
        "H7 -- mechanism: time in the section", "E13/E13b/E13c",
        finding=(f"Among hires who spent 15+ minutes in the section, the essay slope on retention "
                 f"is {m.loc[('legacy_pre',0),'estimate']:.4f} (legacy pre), "
                 f"{m.loc[('legacy_post',0),'estimate']:.4f} (legacy post), "
                 f"{m.loc[('new_pre',0),'estimate']:.4f} (new pre) and "
                 f"{m.loc[('new_post',0),'estimate']:.4f} (new post, 95% CI "
                 f"[{m.loc[('new_post',0),'ci_low']:.4f}, {m.loc[('new_post',0),'ci_high']:.4f}]) "
                 f"-- still positive everywhere. Among hires who spent under 15 minutes it is "
                 f"{m.loc[('legacy_pre',1),'estimate']:.4f} (legacy pre), "
                 f"{m.loc[('legacy_post',1),'estimate']:.4f} (legacy post), "
                 f"{m.loc[('new_pre',1),'estimate']:.4f} (new pre) and "
                 f"{m.loc[('new_post',1),'estimate']:.4f} (new post, 95% CI "
                 f"[{m.loc[('new_post',1),'ci_low']:.4f}, {m.loc[('new_post',1),'ci_high']:.4f}]): "
                 f"a high score produced fast on the new ATS in the AI era predicts WORSE "
                 f"retention. The score-per-minute relationship (E13c) is "
                 f"{evm_df.loc['legacy_pre','estimate']:+.4f} (legacy pre), "
                 f"{evm_df.loc['legacy_post','estimate']:+.4f} (legacy post), "
                 f"{evm_df.loc['new_pre','estimate']:+.4f} (new pre), "
                 f"{evm_df.loc['new_post','estimate']:+.4f} (new post): effort used to earn "
                 f"points; on the new ATS after 2023, less time predicts a higher score, the "
                 f"signature of a prepared answer pasted in."),
        spec="retained_6mo ~ essay:C(regime4):C(fast15) + C(regime4)*C(fast15) + center + "
             "start-month FE, cluster center; essay_rubric_score ~ minutes per cell with center + "
             "application-month FE",
        sample=f"{len(h):,} hires with an observed outcome; all reviewed applications for E13c",
        verdict="supported -- time in section is a free signal Meridian already collects and does "
               "not use; slow essays still work, fast high-scoring ones are now a negative signal."
    )

    pb = placebo_df.set_index(["variable", "regime"])["estimate"]
    log_result(
        "H8 -- placebo: other inputs did not lose power", "E14",
        finding=(f"Univariate slopes on retention, legacy pre-2023 -> new post-2023: resume score "
                 f"{pb['resume_score','legacy_pre']:.4f} -> {pb['resume_score','new_post']:.4f}; "
                 f"license {pb['has_adjuster_license','legacy_pre']:.4f} -> "
                 f"{pb['has_adjuster_license','new_post']:.4f}; prior claims years "
                 f"{pb['prior_claims_years','legacy_pre']:.4f} -> "
                 f"{pb['prior_claims_years','new_post']:.4f}; interview "
                 f"{pb['interview_score','legacy_pre']:.4f} -> {pb['interview_score','new_post']:.4f}. "
                 f"Every placebo input holds or strengthens while the essay's slope on the same "
                 f"outcome goes from {hr.loc['legacy_pre','estimate']:.4f} to "
                 f"{hr.loc['new_post','estimate']:.4f} (E12b). The essay is the only input moving "
                 f"the wrong way."),
        spec="retained_6mo ~ <var>:C(regime4) + C(regime4), center + start-month FE, per variable",
        sample=f"{len(h):,} hires with an observed outcome (interview_score: interviewed only)",
        verdict="supported -- rules out a center-wide quality or measurement shift; the loss is "
               "specific to the essay. Other inputs strengthening is consistent with the essay no "
               "longer filtering, leaving more true-quality variation for the other inputs to explain."
    )


if __name__ == "__main__":
    main()
