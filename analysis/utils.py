"""Shared helpers for the Meridian case analysis.

Every numbered script imports from here. Change a definition here, never in a script.

    from analysis.utils import (load_frames, add_regime, hires_obs, fe_ols, did_table,
                                wild_bootstrap_p, write_table, save_fig, log_result,
                                AI_ERA_CUTOFF, REGIMES, REGIMES4, DID_TERMS)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "meridian-case-data"
BUILD = ROOT / "build"
EXHIBITS = ROOT / "outputs" / "exhibits"
TABLES = ROOT / "outputs" / "tables"
RESULTS = ROOT / "outputs" / "RESULTS.md"

sys.path.insert(0, str(DATA))          # so `import starter` works
from starter import load as _starter_load  # noqa: E402

# ---------------------------------------------------------------------------
# Definitions of record (see CLAUDE.md). Change here only.
# ---------------------------------------------------------------------------
AI_ERA_CUTOFF = "2023-01"              # application month at/after which post_ai = 1
REGIMES = ["legacy", "new_pre", "new_post"]            # 3-cell: used for level/DiD plots
REGIMES4 = ["legacy_pre", "legacy_post", "new_pre", "new_post"]  # 4-cell: ATS x era, used for
# every essay-SLOPE comparison. The legacy system also drifts after 2023 (applicants can draft
# elsewhere and type it in), so pooling legacy 2021-25 overstates the "still works" benchmark.
# Fixed categorical palette (Okabe-Ito, colourblind-safe); assigned by entity, never cycled.
PALETTE = {"legacy": "#0072B2", "new": "#D55E00",
           "legacy_pre": "#0072B2", "legacy_post": "#56B4E9",
           "new_pre": "#D55E00", "new_post": "#E69F00",
           "2021 vendor pilot": "#D55E00", "2023 rollout": "#E69F00", "2024 rollout": "#CC79A7",
           "not migrated": "#0072B2", "voluntary": "#009E73", "performance": "#D55E00",
           "attendance": "#CC79A7", "neutral": "#7F7F7F"}
REGIME4_LABELS = {"legacy_pre": "Legacy ATS, 2021-22\n(timed, no paste)",
                  "legacy_post": "Legacy ATS, 2023+\n(timed, no paste, AI era)",
                  "new_pre": "New ATS, 2021-22\n(untimed, paste)",
                  "new_post": "New ATS, 2023+\n(untimed, paste, AI era)"}
FAST_ESSAY_MINUTES = 10                # also report 15 as robustness
CONTROLS = ["resume_score", "has_adjuster_license", "prior_claims_experience",
            "prior_claims_years", "referral", "currently_employed"]
HIRE_CONTROLS = CONTROLS + ["starting_wage", "wage_index", "local_unemployment_rate"]


def load_frames() -> dict[str, pd.DataFrame]:
    """starter.load() plus regime flags on every person-level frame and the
    application-month center_month fields on hires and flex."""
    d = _starter_load(DATA)
    cm = d["center_month"]

    apps = d["applications"].copy()
    apps["ats_at_application"] = apps.merge(
        cm[["center_id", "month", "ats"]], on=["center_id", "month"], how="left")["ats"].values
    apps = apps.rename(columns={"month": "application_month"})
    d["applications"] = add_regime(apps)

    cm_app = cm.drop(columns=["ats"]).rename(columns={"month": "application_month"})
    cm_app = cm_app.rename(columns={c: f"{c}_at_app" for c in cm_app.columns
                                    if c not in ("center_id", "application_month")})
    for k in ("hires_joined", "flex_joined"):
        df = add_regime(d[k])
        df = df.merge(cm_app, on=["center_id", "application_month"], how="left")
        d[k] = df

    # labour-market conditions in the START month for hire outcomes
    cm_start = cm[["center_id", "month", "wage_index", "local_unemployment_rate"]].rename(
        columns={"month": "start_month"})
    d["hires_joined"] = d["hires_joined"].merge(cm_start, on=["center_id", "start_month"], how="left")
    d["center_month"] = add_regime(cm.rename(columns={"month": "application_month"}),
                                   ats_col="ats").rename(columns={"application_month": "month"})
    return d


def add_regime(df: pd.DataFrame, ats_col: str = "ats_at_application") -> pd.DataFrame:
    """Adds post_ai, treated_app, regime (legacy / new_pre / new_post), fast_essay."""
    df = df.copy()
    df["post_ai"] = (df["application_month"] >= AI_ERA_CUTOFF).astype(int)
    df["treated_app"] = (df[ats_col] == "new").astype(int)
    df["regime"] = np.select(
        [df["treated_app"] == 0, df["post_ai"] == 0], ["legacy", "new_pre"], "new_post")
    df["regime"] = pd.Categorical(df["regime"], categories=REGIMES)
    df["regime4"] = np.where(df["treated_app"] == 1, "new", "legacy")
    df["regime4"] = df["regime4"] + np.where(df["post_ai"] == 1, "_post", "_pre")
    df["regime4"] = pd.Categorical(df["regime4"], categories=REGIMES4)
    if "essay_section_minutes" in df:
        df["fast_essay"] = (df["essay_section_minutes"] < FAST_ESSAY_MINUTES).astype(int)
        df["fast_essay15"] = (df["essay_section_minutes"] < 15).astype(int)
    if "migration_month" in df:
        df["wave"] = df["migration_wave"].fillna("not migrated")
    return df


def hires_obs(hires_joined: pd.DataFrame) -> pd.DataFrame:
    """Hires with an observed six-month outcome. Never impute the censored ones."""
    out = hires_joined[hires_joined["retained_6mo"].notna()].copy()
    out["retained_6mo"] = out["retained_6mo"].astype(int)
    return out


# ---------------------------------------------------------------------------
# Regression helper: OLS / LPM with absorbed fixed effects and center clusters
# ---------------------------------------------------------------------------
def fe_ols(df: pd.DataFrame, y: str, x_terms: list[str] | str,
           fe: list[str] = ("center_id",), cluster: str = "center_id",
           weights: str | None = None):
    """statsmodels OLS with fixed effects as C() dummies and cluster-robust SEs.

    x_terms: patsy terms, e.g. ["essay_rubric_score:C(regime)", "C(regime)", *CONTROLS].
    Returns the fitted results object (use .params, .bse, .conf_int(), .nobs).
    """
    if isinstance(x_terms, str):
        x_terms = [x_terms]
    rhs = " + ".join(list(x_terms) + [f"C({f})" for f in fe])
    formula = f"{y} ~ {rhs}"
    cols = {y, cluster, *fe} | set(_vars_in(x_terms))
    if weights:
        cols.add(weights)
    data = df.dropna(subset=[c for c in cols if c in df.columns])
    model = smf.wls(formula, data, weights=data[weights]) if weights else smf.ols(formula, data)
    res = model.fit(cov_type="cluster", cov_kwds={"groups": data[cluster]})
    res.n_clusters = data[cluster].nunique()
    res.sample_n = int(res.nobs)
    return res


def _vars_in(terms) -> list[str]:
    import re
    names = set()
    for t in terms:
        for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", t):
            if tok not in {"C", "np", "log", "I"}:
                names.add(tok)
    return sorted(names)


def coef_table(res, terms: list[str] | None = None) -> pd.DataFrame:
    ci = res.conf_int()
    tab = pd.DataFrame({"estimate": res.params, "se": res.bse,
                        "ci_low": ci[0], "ci_high": ci[1], "p": res.pvalues})
    if terms:
        tab = tab.loc[[t for t in tab.index if any(k in t for k in terms)]]
    tab["n"] = res.sample_n
    tab["clusters"] = res.n_clusters
    return tab


def find_param(res, *fragments: str) -> str:
    """Locate a coefficient name containing all fragments, tolerant of patsy's [1] vs [T.1]
    naming (numeric*categorical interactions use [1]; pure categorical dummies use [T.1]).
    Raises KeyError with the full param list if nothing or more than one match is found."""
    hits = [p for p in res.params.index if all(f in p for f in fragments)]
    if len(hits) != 1:
        raise KeyError(f"expected exactly one match for {fragments}, got {hits} "
                       f"(all params: {list(res.params.index)})")
    return hits[0]


DID_TERMS = ["treated_app", "treated_app:post_ai"]
DID_TERMS_HIRES = ["treated_app", "treated_app:post_ai", "post_ai"]
"""Difference-in-differences parametrisation.
  treated_app           = new-ATS effect in the pre-AI era (identified from within-center switches)
  treated_app:post_ai   = the DiD interaction: extra new-ATS effect once AI writing is available
Post-era gap = sum of the two.
Use DID_TERMS when the time FE is the APPLICATION (or placement) month: post_ai is then a function
of that month and is absorbed, and including it (or the `treated_app:C(post_ai)` form) makes the
design rank-deficient and the cluster covariance numerically unstable (SEs of 74, NaN SEs).
Use DID_TERMS_HIRES when the time FE is the START month: post_ai is defined on application month,
and hires whose application and start straddle the cutoff mean it is NOT absorbed, so it must be
included explicitly."""

ESSAY_BINS = [-1, 11, 17, 23, 30]
ESSAY_BIN_LABELS = ["0-11", "12-17", "18-23", "24-30"]
HIRE_CTRL = ["resume_score", "has_adjuster_license", "prior_claims_years", "referral", "interview_score"]
FLEX_CTRL = ["resume_score", "has_adjuster_license", "prior_claims_years", "referral",
             "C(certification_level)"]
MIGRATION_WAVES_LATE = ["2023 rollout", "2024 rollout"]
EVENT_WINDOW = (-12, 11)


def cutoff_label() -> str:
    """Human-readable AI-era cutoff for figure annotations, derived from AI_ERA_CUTOFF."""
    return AI_ERA_CUTOFF


def cutoff_quarter() -> str:
    return str(pd.Period(AI_ERA_CUTOFF, freq="M").asfreq("Q"))


def era_labels() -> tuple[str, str]:
    """('2021-2022', '2023-2025')-style labels derived from the cutoff and the panel span."""
    y = int(AI_ERA_CUTOFF[:4])
    return f"2021-{y - 1}", f"{y}-2025"


def month_diff(a: str, b: str) -> int:
    return pd.Period(a, freq="M").ordinal - pd.Period(b, freq="M").ordinal


def event_window(h: pd.DataFrame, mig: pd.DataFrame, waves=MIGRATION_WAVES_LATE,
                 window=EVENT_WINDOW) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Hires at `waves` centers in event time around their own migration month, and hires at
    never-migrated centers around the waves' median migration month (pseudo-event). Returns
    (migrating_df, never_df, median_migration_month); both carry event_month, event_bin, post."""
    migr = mig[mig["migration_wave"].isin(waves)][["center_id", "migration_month"]]
    never = mig.loc[mig["migration_wave"] == "not migrated", "center_id"]
    parts = []
    for _, rw in migr.iterrows():
        s = h[h["center_id"] == rw.center_id].copy()
        s["event_month"] = s["application_month"].apply(lambda x: month_diff(x, rw.migration_month))
        parts.append(s)
    ev = pd.concat(parts, ignore_index=True)
    mm = sorted(migr["migration_month"]); med = mm[len(mm) // 2]
    nv = h[h["center_id"].isin(never)].copy()
    nv["event_month"] = nv["application_month"].apply(lambda x: month_diff(x, med))
    out = []
    for df in (ev, nv):
        df = df[df["event_month"].between(*window)].copy()
        df["event_bin"] = (df["event_month"] // 3) * 3
        df["post"] = (df["event_month"] >= 0).astype(int)
        out.append(df)
    return out[0], out[1], med


def did_table(res, label: str = "") -> pd.DataFrame:
    """Rows: pre-era new-ATS effect, DiD interaction, and post-era gap (sum) with SE via the
    covariance matrix. Includes n and cluster count."""
    ci = res.conf_int()
    rows = []
    for k, name in (("treated_app", "new ATS effect, pre-AI era (2021-22)"),
                    ("treated_app:post_ai", "DiD interaction: extra new-ATS effect, AI era")):
        rows.append({"term": name, "estimate": res.params[k], "se": res.bse[k],
                     "ci_low": ci.loc[k, 0], "ci_high": ci.loc[k, 1], "p": res.pvalues[k]})
    cov = res.cov_params()
    v = (cov.loc["treated_app", "treated_app"] + cov.loc["treated_app:post_ai", "treated_app:post_ai"]
         + 2 * cov.loc["treated_app", "treated_app:post_ai"])
    est = res.params["treated_app"] + res.params["treated_app:post_ai"]
    se = float(np.sqrt(v))
    from scipy import stats
    rows.append({"term": "post-era gap, new vs legacy (sum of the two)", "estimate": est, "se": se,
                 "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se,
                 "p": 2 * (1 - stats.norm.cdf(abs(est / se)))})
    out = pd.DataFrame(rows).set_index("term")
    out["n"] = res.sample_n
    out["clusters"] = res.n_clusters
    return out


def regime_slopes(res, var: str, regimes: list[str] | None = None, cat: str = "regime") -> pd.DataFrame:
    """Slope of `var` in each regime from a model with var:C(<cat>) (no separate level term)."""
    if regimes is None:
        regimes = REGIMES4 if cat == "regime4" else REGIMES
    rows = []
    for r in regimes:
        key = f"{var}:C({cat})[{r}]"
        if key not in res.params:
            key = f"{var}:C({cat})[T.{r}]"
        est, se = res.params[key], res.bse[key]
        rows.append({"regime": r, "estimate": est, "se": se,
                     "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se})
    return pd.DataFrame(rows)


def wild_bootstrap_p(df: pd.DataFrame, y: str, x_terms: list[str], term: str,
                     fe=("center_id",), cluster="center_id", reps: int = 499, seed: int = 0,
                     res=None) -> float:
    """Wild cluster bootstrap (Rademacher) p-value for H0: coef[term] = 0.
    `term` must be a plain numeric column (e.g. an explicit interaction dummy) so that the
    restricted model can drop it -- testing a SLOPE DIFFERENCE requires building the
    difference as its own column (see 07_identification.py); testing `essay:C(regime)[new_post]`
    would test whether the new_post slope is zero, which is the wrong hypothesis.
    The design matrix is built once with patsy and reused across replications; pass `res` (the
    unrestricted fit from fe_ols on the same df/terms) to skip refitting it."""
    import patsy
    import statsmodels.api as sm
    rng = np.random.default_rng(seed)
    if res is None:
        res = fe_ols(df, y, x_terms, fe, cluster)
    t_obs = res.tvalues[term]
    data = df.dropna(subset=[c for c in ({y, cluster, *fe} | set(_vars_in(x_terms))) if c in df.columns])
    full_rhs = " + ".join(list(x_terms) + [f"C({f})" for f in fe])
    yv, X = patsy.dmatrices(f"{y} ~ {full_rhs}", data, return_type="dataframe")
    j = list(X.columns).index(term)
    X_r = X.drop(columns=[term])
    res_r = sm.OLS(yv.values.ravel(), X_r.values).fit()
    fitted, resid = res_r.fittedvalues, res_r.resid
    groups = data[cluster].values
    uniq = np.unique(groups)
    idx = np.searchsorted(uniq, groups)
    Xv = X.values
    t_boot = np.empty(reps)
    for b in range(reps):
        signs = rng.choice([-1.0, 1.0], size=len(uniq))[idx]
        rb = sm.OLS(fitted + resid * signs, Xv).fit(cov_type="cluster", cov_kwds={"groups": groups})
        t_boot[b] = rb.tvalues[j]
    return float(np.mean(np.abs(t_boot) >= abs(t_obs)))


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------
def write_table(exhibit_id: str, table: pd.DataFrame, title: str, sample_line: str,
                notes: str = "", source: str = "") -> Path:
    TABLES.mkdir(parents=True, exist_ok=True)
    stem = f"{exhibit_id}_{_slug(title)}"
    table.to_csv(TABLES / f"{stem}.csv")
    md = [f"### {exhibit_id}. {title}", "", table.to_markdown(floatfmt=".3f"), "",
          f"*Sample:* {sample_line}"]
    if notes:
        md.append(f"*Notes:* {notes}")
    if source:
        md.append(f"*Source:* {source}")
    (TABLES / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return TABLES / f"{stem}.md"


def save_fig(fig, exhibit_id: str, title: str, sample_line: str, source: str = "") -> Path:
    """Stamps the sample statement and source note under the axes, then saves."""
    EXHIBITS.mkdir(parents=True, exist_ok=True)
    note = f"Sample: {sample_line}"
    if source:
        note += f"   Source: {source}"
    fig.text(0.01, 0.005, note, fontsize=7.5, ha="left", va="bottom", wrap=True)
    fig.subplots_adjust(bottom=max(fig.subplotpars.bottom, 0.16))
    path = EXHIBITS / f"{exhibit_id}_{_slug(title)}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


def log_result(hypothesis: str, exhibit_id: str, finding: str, spec: str, sample: str,
               verdict: str) -> None:
    """Writes one block per hypothesis. Re-running a script REPLACES its existing block (matched
    on the '## <hypothesis>' header) so RESULTS.md never carries stale duplicates."""
    import re
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    block = (f"\n## {hypothesis}  ({exhibit_id})\n"
             f"- Finding: {finding}\n- Spec: {spec}\n- Sample: {sample}\n- Verdict: {verdict}\n")
    text = RESULTS.read_text(encoding="utf-8") if RESULTS.exists() else ""
    pat = re.compile(r"\n## " + re.escape(hypothesis) + r"  \(.*?\)\n.*?(?=\n## |\Z)", re.S)
    if pat.search(text):
        text = pat.sub(lambda m: block.rstrip("\n") + "\n", text, count=1)
    else:
        text += block
    # keep the log in hypothesis order regardless of which script ran last
    blocks = [b for b in re.split(r"(?=\n## H\d+ )", text) if b.strip()]

    def _key(b):
        m = re.match(r"\n## H(\d+)", b)
        return int(m.group(1)) if m else -1
    RESULTS.write_text("".join(sorted(blocks, key=_key)).rstrip("\n") + "\n", encoding="utf-8")


def _slug(s: str, n: int = 40) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return s[:n].rstrip("_")
