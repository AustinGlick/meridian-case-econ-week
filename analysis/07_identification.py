"""H9 -- identification threats, bounds, and the defended range for deliverable (b).

Migration was NOT random (pilot centers = large, strong IT). This script checks the threats
directly: pre-trends around migration, whether the essay was equally valid in pilot vs legacy
centers BEFORE the AI era, whether labor-market conditions explain the pattern, whether
selection into the hire sample changed, and the small-cluster inference on the headline slope
DIFFERENCE (legacy pre-2023 vs new post-2023) via a wild cluster bootstrap. It also produces
the range for signal loss (hires-sample vs flex-sample estimates).

Produces:
  E15  event study: retention around migration month, 2023/24 waves vs never-migrated
  E15b the means behind E15
  E15c selection check: essay mean/SD among applicants vs hires, and hire rate by essay bin
  E15d wild-cluster bootstrap p-values on the headline slope differences
  E15e share of the legacy pre-2023 essay signal retained, hires vs flex
  E15f size-and-region matched comparison of the seven legacy centers (option-b proxy), 2024-25
  E15g pre-2023 essay slope, pilot vs never-migrated centers (migration did not select on validity)
  E16  labor-market controls (unemployment, wage index) by ATS

    python -m analysis.07_identification
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from analysis.utils import (load_frames, hires_obs, fe_ols, regime_slopes, write_table, save_fig, TABLES,
                            log_result, wild_bootstrap_p, event_window, did_table, REGIMES4, PALETTE,
                            HIRE_CTRL, FLEX_CTRL, ESSAY_BINS, ESSAY_BIN_LABELS, AI_ERA_CUTOFF,
                            EVENT_WINDOW, HIRE_CONTROLS, DID_TERMS_HIRES, matched_legacy_gaps,
                            option_b_cohorts, legacy_match_weights, MATCH_APPROACHES, MATCH_LABELS,
                            MATCH_OUTCOMES, MATCH_HEADLINE, OPTION_B_WINDOW)


def add_slope_dummies(df: pd.DataFrame) -> pd.DataFrame:
    """Explicit numeric columns so a slope DIFFERENCE is a single coefficient (needed for the
    wild bootstrap's restricted model). Base cell = legacy_pre."""
    df = df.copy()
    e = df["essay_rubric_score"]
    df["e_base"] = e
    for r in REGIMES4[1:]:
        df[f"e_{r}"] = e * (df["regime4"] == r)
        df[f"d_{r}"] = (df["regime4"] == r).astype(int)
    return df


def main() -> None:
    d = load_frames()
    h = hires_obs(d["hires_joined"])
    flex = d["flex_joined"]
    apps = d["applications"]
    mig = d["ats_migration"]

    # ============================================================================
    # Check 1: pre-period essay validity, pilot vs never-migrated centers
    # ============================================================================
    pilot_centers = mig.loc[mig["migration_wave"] == "2021 vendor pilot", "center_id"]
    never_centers = mig.loc[mig["migration_wave"] == "not migrated", "center_id"]
    pre = h[h["post_ai"] == 0]
    r_pilot = fe_ols(pre[pre["center_id"].isin(pilot_centers)], "retained_6mo",
                     ["essay_rubric_score", *HIRE_CTRL], fe=["center_id", "start_month"])
    r_never = fe_ols(pre[pre["center_id"].isin(never_centers)], "retained_6mo",
                     ["essay_rubric_score", *HIRE_CTRL], fe=["center_id", "start_month"])
    pilot_pre = (r_pilot.params["essay_rubric_score"], r_pilot.bse["essay_rubric_score"], r_pilot.sample_n)
    never_pre = (r_never.params["essay_rubric_score"], r_never.bse["essay_rubric_score"], r_never.sample_n)
    parity = pd.DataFrame([
        {"centers": "2021 vendor pilot (migrated 2021)", "essay_slope_on_retention": pilot_pre[0],
         "se_cluster_center": pilot_pre[1], "ci_low": pilot_pre[0] - 1.96 * pilot_pre[1],
         "ci_high": pilot_pre[0] + 1.96 * pilot_pre[1], "n_hires": pilot_pre[2],
         "clusters": int(pre[pre["center_id"].isin(pilot_centers)]["center_id"].nunique())},
        {"centers": "Never migrated (legacy throughout)", "essay_slope_on_retention": never_pre[0],
         "se_cluster_center": never_pre[1], "ci_low": never_pre[0] - 1.96 * never_pre[1],
         "ci_high": never_pre[0] + 1.96 * never_pre[1], "n_hires": never_pre[2],
         "clusters": int(pre[pre["center_id"].isin(never_centers)]["center_id"].nunique())},
    ]).set_index("centers")
    write_table("E15g", parity.round(4),
                "Pre-2023 essay slope on retention: pilot centers vs never-migrated centers",
                sample_line=(f"Hires applying before {AI_ERA_CUTOFF} with an observed six-month outcome: "
                             f"{pilot_pre[2]:,} at pilot centers, {never_pre[2]:,} at never-migrated centers."),
                notes=("retained_6mo ~ essay_rubric_score + controls, center FE + start-month FE, SEs "
                       "clustered by center. If migration had selected centers where the essay was "
                       "more or less valid, these slopes would differ."),
                source="analysis/07_identification.py")

    # ============================================================================
    # Check 2: event study around migration month (retention level)
    # ============================================================================
    event_df, never_hjo, median_mm = event_window(h, mig)

    g_event = event_df.groupby("event_bin")["retained_6mo"].agg(["mean", "count", "std"]).reset_index()
    g_event["se"] = g_event["std"] / np.sqrt(g_event["count"])
    g_never = never_hjo.groupby("event_bin")["retained_6mo"].agg(["mean", "count", "std"]).reset_index()
    g_never["se"] = g_never["std"] / np.sqrt(g_never["count"])

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.errorbar(g_event["event_bin"] + 1.5, g_event["mean"], yerr=1.96 * g_event["se"], marker="o",
               capsize=3, color=PALETTE["new"], linewidth=2,
               label="2023/2024-wave centers (event time = months since their own migration)")
    ax.errorbar(g_never["event_bin"] + 1.5, g_never["mean"], yerr=1.96 * g_never["se"], marker="s",
               capsize=3, color=PALETTE["legacy"], linewidth=2,
               label=f"Never-migrated centers (same calendar window around {median_mm})")
    ax.axvline(0, color="grey", linestyle="--", linewidth=1)
    ax.text(0.2, ax.get_ylim()[1], "ATS migration", fontsize=9.5, va="top")
    ax.set_xlabel("Months relative to ATS migration (application month, quarterly bins)")
    ax.set_ylabel("Six-month retention rate (share of hires)")
    ax.set_title("E15. Migrating and never-migrated centers track each other before migration;\n"
                 "the gap opens after the switch", fontsize=12.5)
    ax.legend(fontsize=9.5, loc="lower left")
    save_fig(fig, "E15", "migration_event_study",
            sample_line=f"{len(event_df):,} hires at 2023/2024-migration-wave centers ({EVENT_WINDOW[0]} to "
                        f"+{EVENT_WINDOW[1]} months around each center's migration) and {len(never_hjo):,} hires at "
                        f"never-migrated centers (same window around the waves' median migration "
                        f"month). Error bars: 95% CI.",
            source="analysis/07_identification.py")
    plt.close(fig)

    pre_mig = event_df[event_df["event_bin"] < 0]["retained_6mo"].mean()
    pre_nev = never_hjo[never_hjo["event_bin"] < 0]["retained_6mo"].mean()
    post_mig = event_df[event_df["event_bin"] >= 0]["retained_6mo"].mean()
    post_nev = never_hjo[never_hjo["event_bin"] >= 0]["retained_6mo"].mean()
    write_table("E15b", pd.DataFrame([
        {"period": "12 months before", "migrating_centers": pre_mig, "never_migrated": pre_nev,
         "gap_never_minus_migrating": pre_nev - pre_mig},
        {"period": "12 months after", "migrating_centers": post_mig, "never_migrated": post_nev,
         "gap_never_minus_migrating": post_nev - post_mig},
    ]).round(4), "Event-study means: retention before/after migration vs never-migrated",
        sample_line=f"{len(event_df):,} + {len(never_hjo):,} hires, event window +/-12 months.",
        source="analysis/07_identification.py")

    # ============================================================================
    # Check 3: labor-market conditions by ATS (rules out "it's the economy")
    # ============================================================================
    cm = d["center_month"].copy()
    cm["year"] = cm["month"].str[:4]
    lm = cm.groupby(["year", "ats"])[["local_unemployment_rate", "wage_index"]].mean().reset_index()
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, col, label in zip(axes, ["local_unemployment_rate", "wage_index"],
                              ["Local unemployment rate (%)", "Wage index (2021 = 1.00)"]):
        for ats in ["legacy", "new"]:
            sub = lm[lm["ats"] == ats].sort_values("year")
            ax.plot(sub["year"], sub[col], marker="o", label=f"{ats.capitalize()} ATS", color=PALETTE[ats], linewidth=2)
        ax.set_xlabel("Calendar year"); ax.set_ylabel(label)
        ax.axvline(int(AI_ERA_CUTOFF[:4]) - 2021, color="grey", linestyle="--", linewidth=1)
    axes[1].text(int(AI_ERA_CUTOFF[:4]) - 2021, axes[1].get_ylim()[1], f" AI-era cutoff\n ({AI_ERA_CUTOFF})",
                 fontsize=9.5, va="top")
    axes[0].legend()
    fig.suptitle("E16. Local labor-market conditions move together regardless of ATS;\n"
                 "they do not explain the new-vs-legacy divergence", fontsize=12.5)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save_fig(fig, "E16", "labor_market_by_ats",
            sample_line="2,400 center-months, 40 centers, yearly means by ATS in that center-month; "
                        "dashed line = 2023 AI-era cutoff.",
            source="analysis/07_identification.py")
    plt.close(fig)
    write_table("E16b", lm.round(3), "Labor-market conditions by year and ATS",
               sample_line="2,400 center-months.", source="analysis/07_identification.py")

    # ============================================================================
    # Check 4: selection into the hire sample on the essay, by cell
    # ============================================================================
    apps = apps.copy()
    apps["hired"] = apps["outcome"].isin(["hired", "hired_pending_start"]).astype(int)
    apps["essay_bin"] = pd.cut(apps["essay_rubric_score"], ESSAY_BINS, labels=ESSAY_BIN_LABELS)
    sel = pd.DataFrame({
        "applicant_essay_mean": apps.groupby("regime4", observed=True)["essay_rubric_score"].mean(),
        "applicant_essay_sd": apps.groupby("regime4", observed=True)["essay_rubric_score"].std(),
        "hire_essay_mean": h.groupby("regime4", observed=True)["essay_rubric_score"].mean(),
        "hire_essay_sd": h.groupby("regime4", observed=True)["essay_rubric_score"].std(),
        "hire_rate_bin_18_23": apps[apps["essay_bin"] == "18-23"].groupby("regime4", observed=True)["hired"].mean(),
        "hire_rate_bin_24_30": apps[apps["essay_bin"] == "24-30"].groupby("regime4", observed=True)["hired"].mean(),
        "share_applicants_24_30": apps.groupby("regime4", observed=True).apply(lambda s: (s["essay_bin"] == "24-30").mean()),
    })
    write_table("E15c", sel.round(3), "Selection on the essay into the hire sample, by regime",
               sample_line="All reviewed applications and all hires with an observed outcome.",
               notes="If the hire-sample essay SD were much smaller in one cell, a zero slope there "
                     "could be a range-restriction artifact. It is not: the SD is similar in every "
                     "cell. What changed is the share of applicants scoring 24-30 and the hire "
                     "rate within that bin.",
               source="analysis/07_identification.py")

    # ============================================================================
    # Check 5: small-cluster inference -- wild cluster bootstrap on the slope DIFFERENCES
    # ============================================================================
    hd = add_slope_dummies(h)
    terms_h = ["e_base", *[f"e_{r}" for r in REGIMES4[1:]], *[f"d_{r}" for r in REGIMES4[1:]], *HIRE_CTRL]
    res_hd = fe_ols(hd, "retained_6mo", terms_h, fe=["center_id", "start_month"])
    fd = add_slope_dummies(flex)
    terms_f = ["e_base", *[f"e_{r}" for r in REGIMES4[1:]], *[f"d_{r}" for r in REGIMES4[1:]], *FLEX_CTRL]
    res_fd = fe_ols(fd, "reopen_rate_pct", terms_f, fe=["center_id", "placement_month"])
    wb_rows = []
    for label, df, y, terms, res, fe in (
            ("hires: retention slope, new_post minus legacy_pre", hd, "retained_6mo", terms_h, res_hd, ["center_id", "start_month"]),
            ("hires: retention slope, legacy_post minus legacy_pre", hd, "retained_6mo", terms_h, res_hd, ["center_id", "start_month"]),
            ("flex: reopen slope, new_post minus legacy_pre", fd, "reopen_rate_pct", terms_f, res_fd, ["center_id", "placement_month"]),
            ("flex: reopen slope, legacy_post minus legacy_pre", fd, "reopen_rate_pct", terms_f, res_fd, ["center_id", "placement_month"])):
        term = "e_new_post" if "new_post" in label else "e_legacy_post"
        p_wb = wild_bootstrap_p(df, y, terms, term=term, fe=fe, reps=299, res=res)
        wb_rows.append({"test": label, "difference": res.params[term], "cluster_se": res.bse[term],
                        "cluster_p": res.pvalues[term], "wild_bootstrap_p_299": p_wb, "n": res.sample_n,
                        "clusters": res.n_clusters})
        print(wb_rows[-1])
    wb = pd.DataFrame(wb_rows).set_index("test")
    write_table("E15d", wb.round(5), "Small-cluster inference: wild-cluster bootstrap on the headline "
                "essay-slope differences",
               sample_line="Hires with an observed outcome (retention) and flex placements (reopen).",
               notes="H0: the essay slope in the named cell equals the legacy pre-2023 slope. "
                     "Rademacher wild cluster bootstrap, 299 draws, 40 center clusters, restricted "
                     "model imposes H0. A p below 0.05 means the difference survives small-cluster "
                     "inference.",
               source="analysis/07_identification.py")

    # ============================================================================
    # Range: share of legacy pre-2023 predictive power lost, hires vs flex, by cell
    # ============================================================================
    s_h = regime_slopes(fe_ols(h, "retained_6mo", ["essay_rubric_score:C(regime4)", "C(regime4)", *HIRE_CTRL],
                               fe=["center_id", "start_month"]), "essay_rubric_score", cat="regime4").set_index("regime")
    s_f = regime_slopes(fe_ols(flex, "reopen_rate_pct", ["essay_rubric_score:C(regime4)", "C(regime4)", *FLEX_CTRL],
                               fe=["center_id", "placement_month"]), "essay_rubric_score", cat="regime4").set_index("regime")
    loss = pd.DataFrame({
        "hires_share_of_legacy_pre_slope_retained": (s_h["estimate"] / s_h.loc["legacy_pre", "estimate"]).clip(lower=0),
        "flex_share_of_legacy_pre_slope_retained": (s_f["estimate"] / s_f.loc["legacy_pre", "estimate"]).clip(lower=0),
    })
    loss["range_retained"] = loss.apply(lambda r: f"[{min(r.iloc[0], r.iloc[1]):.0%}, {max(r.iloc[0], r.iloc[1]):.0%}]", axis=1)
    write_table("E15e", loss.round(3), "Share of the legacy pre-2023 essay signal retained, by cell: "
                "hires sample vs flex sample",
               sample_line="Slopes from E12b (hires) and E12d (flex). Negative hire slopes are "
                           "clipped at 0% retained.",
               notes="The two samples bracket the truth: hires are selected on the essay "
                     "(attenuated, lower bound on retained signal); flex are not.",
               source="analysis/07_identification.py")

    # ============================================================================
    # Check 6 (E15f): does the legacy centers' 2024-25 advantage survive matching on size and
    # region? The seven never-migrated centers are the option-(b) proxy in E17/E19. They are
    # small and southern / mid-Atlantic, so compare them with new-ATS centers restricted or
    # reweighted to the same region and size band. Power is thin (7 legacy centers), so this is
    # a BOUND, not a clean estimate.
    # ============================================================================
    cm_full = d["center_month"]
    co = option_b_cohorts(h, cm_full, mig)
    gaps = matched_legacy_gaps(h, cm_full, mig)
    # the H1 DiD bound (E01b), recomputed here exactly as 08 does, for the verdict
    res_did = fe_ols(h, "retained_6mo", [*DID_TERMS_HIRES, *HIRE_CONTROLS], fe=["center_id", "start_month"])
    did_gain = -did_table(res_did).iloc[1]["estimate"]
    # wild-cluster bootstrap on the headline retention gap for the unweighted (band) approach:
    # wild_bootstrap_p fits OLS, so only the restriction-based approach fits it cleanly
    new_centers = sorted(co["status_quo"]["center_id"].unique())
    w_band = legacy_match_weights(mig, "band", new_centers)
    band_df = pd.concat([co["legacy_never"].assign(legacy=1),
                         co["status_quo"][co["status_quo"]["center_id"].isin(w_band.index)].assign(legacy=0)])
    res_band = fe_ols(band_df, "retained_6mo", ["legacy"], fe=["start_month"])
    p_wb_band = wild_bootstrap_p(band_df, "retained_6mo", ["legacy"], term="legacy", fe=["start_month"],
                                 reps=299, res=res_band)
    gaps["wild_bootstrap_p_299"] = np.where((gaps["approach"] == "band") & (gaps["outcome"] == "retained_6mo"),
                                            p_wb_band, np.nan)
    leg_desc = mig[mig["migration_wave"] == "not migrated"]
    band_lo, band_hi = leg_desc["size_index"].min(), leg_desc["size_index"].max()
    regions = ", ".join(sorted(leg_desc["region"].unique()))
    # printed table: one row per approach x outcome, flat index, the columns a reader needs;
    # the full frame (unmatched CIs, legacy n, matched center lists) goes to the CSV next to it
    tab = gaps.set_index("approach")[
        ["outcome", "unmatched_gap", "matched_gap", "matched_ci_low", "matched_ci_high",
         "wild_bootstrap_p_299", "n_comparison_centers_matched", "n_comparison_rows_matched"]]
    tab = tab.rename(columns={"wild_bootstrap_p_299": "wild_boot_p",
                              "n_comparison_centers_matched": "matched_centers",
                              "n_comparison_rows_matched": "matched_rows"})
    gaps.to_csv(TABLES / "E15f_matched_comparison_full.csv", index=False)
    matched_lists = "; ".join(f"{a}: {c}" for a, c in
                              gaps[gaps["outcome"] == "retained_6mo"][["approach", "comparison_centers"]].values)
    write_table("E15f", tab.round(4),
                "Matched comparison: legacy-minus-new-ATS gaps in 2024-25, unmatched vs matched on size and region",
                sample_line=(f"Legacy = {int(gaps['n_legacy_centers'].iloc[0])} never-migrated centers, "
                             f"{int(gaps['n_legacy_rows'].iloc[0]):,} hires starting {OPTION_B_WINDOW} or later "
                             f"with an observed six-month outcome ({int(gaps.loc[gaps['outcome']=='days_to_fill','n_legacy_rows'].iloc[0])} "
                             f"center-months for days to fill). Comparison = new-ATS-at-application hires "
                             f"starting {OPTION_B_WINDOW} or later (unmatched: 33 centers, "
                             f"{int(gaps['n_comparison_rows_unmatched'].iloc[0]):,} hires; matched: see n columns)."),
                notes=(f"Gap = coefficient on a legacy dummy in outcome ~ legacy + start-month (or month) FE, "
                       f"linear probability model for retention, SEs clustered by center; center FE are not "
                       f"identified for a between-center contrast. Approaches: band = comparison centers in the "
                       f"legacy regions ({regions}) with size_index in [{band_lo:.3f}, {band_hi:.3f}] (the legacy "
                       f"centers' min..max, no margin), unweighted; nn1/nn2 = each legacy center matched with "
                       f"replacement to its 1 or 2 nearest new-ATS centers on size_index within the same region, "
                       f"comparison centers weighted by times matched, spread evenly over their hires; ps = logit "
                       f"P(legacy | size_index, region) on the centers in legacy regions, comparison weight "
                       f"p/(1-p). Matched comparison centers, as center(weight): {matched_lists}. Unmatched 95% CIs, "
                       f"legacy n and per-approach detail are in E15f_matched_comparison_full.csv. With 12-26 clusters the cluster-robust "
                       f"CIs are unreliable; the wild-cluster bootstrap p (299 Rademacher draws) is reported for "
                       f"the unweighted band retention gap only. The H1 DiD bound (E01b) is {did_gain:.4f}. "
                       f"The '(b, matched)' row in E19 uses the {MATCH_HEADLINE} retention and reopen gaps."),
                source="analysis/07_identification.py")

    # figure: dot-and-CI, one panel per outcome, unmatched row plus one row per approach
    fig, axes = plt.subplots(1, 3, figsize=(11, 5))
    row_labels = ["Unmatched\n(all 33 new-ATS centers)"] + [
        {"band": "Region + size band", "nn1": "Nearest neighbour k=1", "nn2": "Nearest neighbour k=2",
         "ps": "Propensity reweighted"}[a] for a in MATCH_APPROACHES]
    ypos = np.arange(len(row_labels))[::-1]
    for ax, (y, lab) in zip(axes, MATCH_OUTCOMES.items()):
        g = gaps[gaps["outcome"] == y].set_index("approach")
        u = g.iloc[0]
        ests = [u["unmatched_gap"]] + [g.loc[a, "matched_gap"] for a in MATCH_APPROACHES]
        los = [u["unmatched_ci_low"]] + [g.loc[a, "matched_ci_low"] for a in MATCH_APPROACHES]
        his = [u["unmatched_ci_high"]] + [g.loc[a, "matched_ci_high"] for a in MATCH_APPROACHES]
        cols = [PALETTE["neutral"]] + [PALETTE["legacy"]] * len(MATCH_APPROACHES)
        for yp, e, lo, hi, c in zip(ypos, ests, los, his, cols):
            ax.plot([lo, hi], [yp, yp], color=c, linewidth=2)
            ax.plot(e, yp, "o", color=c, markersize=8, markeredgecolor="white", markeredgewidth=1.5)
        ax.axvline(0, color="#BBBBBB", linewidth=1)
        if y == "retained_6mo":
            ax.axvline(did_gain, color=PALETTE["new"], linestyle="--", linewidth=1.2)
            ax.text(did_gain, ypos[0] + 0.55, f" H1 DiD bound {did_gain:.3f} (E01b)", fontsize=9,
                    color=PALETTE["new"], va="bottom", ha="left")
        ax.set_yticks(ypos); ax.set_yticklabels(row_labels if ax is axes[0] else [""] * len(row_labels), fontsize=10)
        ax.set_xlabel({"retained_6mo": "Six-month retention gap (share of hires)",
                       "reopen_rate_6mo_pct": "Reopen-rate gap (percentage points)",
                       "days_to_fill": "Days-to-fill gap\n(days, center-month panel)"}[y], fontsize=10)
        ax.set_ylim(-0.7, len(row_labels) - 0.3 + 0.6)
        ax.grid(axis="x", color="#EEEEEE"); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    hl = gaps[(gaps["approach"] == MATCH_HEADLINE) & (gaps["outcome"] == "retained_6mo")].iloc[0]
    u_ret = hl["unmatched_gap"]
    fig.suptitle(f"E15f. The legacy centers' retention advantage does not shrink once matched on size and region\n"
                 f"(unmatched {u_ret:.3f}, matched {hl['matched_gap']:.3f} [{hl['matched_ci_low']:.3f}, "
                 f"{hl['matched_ci_high']:.3f}] with k=2 nearest neighbours), but 7 vs 5-19 centers is thin.\n"
                 f"All gaps are legacy minus new-ATS, 2024-25.",
                 fontsize=11.5)
    fig.subplots_adjust(top=0.80, bottom=0.17, left=0.17, right=0.98, wspace=0.22)
    save_fig(fig, "E15f", "matched_legacy_comparison",
             sample_line=(f"{int(gaps['n_legacy_rows'].iloc[0]):,} hires at 7 never-migrated centers vs "
                          f"{int(gaps['n_comparison_rows_unmatched'].iloc[0]):,} new-ATS hires at 33 centers, starting "
                          f"{OPTION_B_WINDOW} or later, observed six-month outcome; days to fill from "
                          f"{int(gaps.loc[gaps['outcome']=='days_to_fill','n_legacy_rows'].iloc[0])} + "
                          f"{int(gaps.loc[gaps['outcome']=='days_to_fill','n_comparison_rows_unmatched'].iloc[0])} "
                          f"center-months. Bars: 95% CI, SEs clustered by center (12-40 clusters; unreliable)."),
             source="analysis/07_identification.py")
    plt.close(fig)
    g_ret = gaps[gaps["outcome"] == "retained_6mo"].set_index("approach")
    g_reo = gaps[gaps["outcome"] == "reopen_rate_6mo_pct"].set_index("approach")
    g_dtf = gaps[gaps["outcome"] == "days_to_fill"].set_index("approach")
    print(tab.round(4).to_string())
    print(f"wild bootstrap p, band retention gap: {p_wb_band:.3f}; DiD bound {did_gain:.4f}")

    print(f"Pre-2023 essay slope, pilot: {pilot_pre[0]:.5f} (se {pilot_pre[1]:.5f}, n={pilot_pre[2]})")
    print(f"Pre-2023 essay slope, never-migrated: {never_pre[0]:.5f} (se {never_pre[1]:.5f}, n={never_pre[2]})")
    print(sel.round(3)); print(loss)

    pre_gap, post_gap = pre_nev - pre_mig, post_nev - post_mig
    w = wb["wild_bootstrap_p_299"]
    log_result(
        "H9 -- identification, bounds, and the defended range", "E15/E15b/E15c/E15d/E15e/E15f/E15g/E16",
        finding=(f"(1) Pre-2023 the essay slope is the same in pilot centers ({pilot_pre[0]:.4f}, se "
                 f"{pilot_pre[1]:.4f}, n={pilot_pre[2]:,}) and never-migrated centers ({never_pre[0]:.4f}, "
                 f"se {never_pre[1]:.4f}, n={never_pre[2]:,}): pilot centers were not different "
                 f"before the AI era. (2) Event study (E15/E15b): the never-minus-migrating retention "
                 f"gap is {pre_gap:.3f} in the 12 months before migration and {post_gap:.3f} after; "
                 f"the widening ({post_gap - pre_gap:.3f}) matches the H1 DiD (E01b) from a "
                 f"different design. (3) Unemployment and wages move together by ATS (E16). "
                 f"(4) Selection (E15c): the essay SD among hires is "
                 f"{sel['hire_essay_sd'].min():.2f}-{sel['hire_essay_sd'].max():.2f} in every cell, "
                 f"so the zero slope in new_post is not range restriction; what changed is that "
                 f"{sel.loc['new_post','share_applicants_24_30']:.0%} of new-ATS AI-era applicants "
                 f"score 24-30 versus {sel.loc['legacy_pre','share_applicants_24_30']:.0%} of legacy "
                 f"pre-2023 applicants. (5) Small clusters (E15d): the wild-cluster bootstrap p on "
                 f"the new_post-minus-legacy_pre slope difference is {w.iloc[0]:.3f} (hires) and "
                 f"{w.iloc[2]:.3f} (flex); on the legacy_post-minus-legacy_pre difference it is "
                 f"{w.iloc[1]:.3f} (hires) and {w.iloc[3]:.3f} (flex). Defended range (E15e): the "
                 f"new ATS in the AI era retains {loss.loc['new_post','range_retained']} of the "
                 f"essay's pre-2023 predictive power; the legacy ATS in the AI era retains "
                 f"{loss.loc['legacy_post','range_retained']}. It is a range because hires are "
                 f"selected on the essay (attenuated) and flex placements are not; the truth sits "
                 f"between them. (6) Matched comparison of the legacy centers (E15f), the option-(b) "
                 f"proxy: in the 2024-25 window the seven never-migrated centers' six-month retention "
                 f"gap over new-ATS hires is {u_ret:.3f} [{hl['unmatched_ci_low']:.3f}, "
                 f"{hl['unmatched_ci_high']:.3f}] unmatched (33 comparison centers, "
                 f"{int(hl['n_comparison_rows_unmatched']):,} hires vs {int(hl['n_legacy_rows']):,} legacy hires); "
                 f"restricted to the same regions and size band it is {g_ret.loc['band','matched_gap']:.3f} "
                 f"[{g_ret.loc['band','matched_ci_low']:.3f}, {g_ret.loc['band','matched_ci_high']:.3f}] "
                 f"(9 centers, {int(g_ret.loc['band','n_comparison_rows_matched']):,} hires; wild-cluster "
                 f"bootstrap p {p_wb_band:.3f} with 16 clusters); nearest-neighbour k=1 "
                 f"{g_ret.loc['nn1','matched_gap']:.3f} [{g_ret.loc['nn1','matched_ci_low']:.3f}, "
                 f"{g_ret.loc['nn1','matched_ci_high']:.3f}] (5 centers); k=2 "
                 f"{g_ret.loc['nn2','matched_gap']:.3f} [{g_ret.loc['nn2','matched_ci_low']:.3f}, "
                 f"{g_ret.loc['nn2','matched_ci_high']:.3f}] (7 centers); propensity-reweighted "
                 f"{g_ret.loc['ps','matched_gap']:.3f} [{g_ret.loc['ps','matched_ci_low']:.3f}, "
                 f"{g_ret.loc['ps','matched_ci_high']:.3f}] (19 centers). Reopen gap (points): "
                 f"{g_reo.iloc[0]['unmatched_gap']:.2f} unmatched, {g_reo['matched_gap'].min():.2f} to "
                 f"{g_reo['matched_gap'].max():.2f} matched; days-to-fill gap: {g_dtf.iloc[0]['unmatched_gap']:.2f} "
                 f"days unmatched, {g_dtf['matched_gap'].min():.2f} to {g_dtf['matched_gap'].max():.2f} matched "
                 f"(legacy centers still fill faster). The matched retention gaps ({g_ret['matched_gap'].min():.3f} "
                 f"to {g_ret['matched_gap'].max():.3f}) all sit at or above the H1 DiD bound of {did_gain:.3f} "
                 f"(E01b), so matching does not move the legacy advantage toward the DiD bound; but with "
                 f"7 legacy centers against 5-19 comparison centers the CIs span roughly 0 to 0.1 and "
                 f"this is a bound, not a clean estimate."),
        spec="Pre-period subsample regressions; event-study means; yearly labor-market means; "
             "selection table; wild-cluster bootstrap (Rademacher, 299 reps) on explicit "
             "slope-difference columns with the restricted model imposing H0; E15f: outcome ~ legacy "
             "+ start-month (or month) FE on the 2024-25 window, comparison centers restricted "
             "(region + size band) or reweighted (nearest-neighbour k=1/2 within region on "
             "size_index; propensity p/(1-p)), cluster center, 12-26 clusters",
        sample="Pre-2023 hires in pilot vs never-migrated centers; hires +/-12 months around "
              "migration; 2,400 center-months; all applications; hires and flex for the bootstrap; "
              f"E15f: {int(hl['n_legacy_rows']):,} legacy and {int(hl['n_comparison_rows_unmatched']):,} "
              f"new-ATS hires starting {OPTION_B_WINDOW} or later, plus 2024-25 center-months",
        verdict=("supported -- direction, timing, placebo and both samples agree, and the "
                 "headline slope differences survive small-cluster inference. Named holes: we "
                 "cannot observe AI use; we cannot see the ~94% of applications never reviewed; "
                 "migration waves were chosen on size and IT readiness, so something unobserved "
                 "that changed at large centers around 2023 could still contribute; the legacy "
                 "ATS is itself eroding, so the 7 legacy centers are an imperfect proxy for a "
                 "timed section; 2025 cohorts are partly censored. E15f verdict: matching the "
                 "legacy centers to new-ATS centers on size and region does NOT shrink their "
                 f"2024-25 retention advantage toward the H1 DiD bound ({did_gain:.3f}) -- the matched "
                 f"gap is {g_ret['matched_gap'].min():.3f} to {g_ret['matched_gap'].max():.3f} against "
                 f"{u_ret:.3f} unmatched, all at or above the bound -- so the (b) range in E19 keeps the "
                 "DiD bound as its low end and the legacy-observed gap as its high end; with 7 legacy "
                 "centers this is a bound on the proxy's bias, not a clean estimate, and the "
                 "Round 2 trigger (advantage disappears once matched) has not fired on this data.")
    )


if __name__ == "__main__":
    main()
