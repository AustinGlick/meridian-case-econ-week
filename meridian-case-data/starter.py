#!/usr/bin/env python3
"""Meridian Casualty — starter script.

Loads the five data files and joins them correctly. That is all it does.

There is no analysis in here on purpose. The joins are fiddly and getting them
wrong costs you an afternoon and can leave you with numbers that look fine and
are not, so we have done that part for you. Everything after loading is the
competition.

    python starter.py                 # load, join, print a summary
    python starter.py --dir ./data    # if the CSVs are somewhere else

Or from your own script or notebook, in the same folder:

    from starter import load
    d = load()
    apps, hires, flex = d["applications"], d["hires"], d["flex_placements"]
    hires_full = d["hires_joined"]        # hires + their application record
    flex_full  = d["flex_joined"]         # placements + their application record

The joined frames carry the application fields, the center's ATS at the time of
application, and the center's attributes. They do NOT carry the rest of
`center_month` -- see the note in `load()` for why, and for the one line that
attaches it.

Requires pandas. Nothing else.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

FILES = ("applications", "hires", "flex_placements", "center_month",
         "ats_migration")

# Columns from the application that are worth carrying onto a hire or a
# placement. Everything else stays in `applications` -- join it yourself if you
# want it.
APP_COLS = [
    "application_id", "month", "essay_rubric_score", "essay_section_minutes",
    "resume_score", "has_adjuster_license", "prior_claims_experience",
    "prior_claims_years", "referral", "currently_employed",
    "recruiter_screen_score", "advanced_to_interview", "interview_score",
]


def load(data_dir: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Read the five files and build two joined frames. Returns a dict.

    Keys: the five file names, plus `hires_joined` and `flex_joined`.
    """
    if data_dir is None:
        here = Path(__file__).resolve().parent
        for cand in (here / "data", here, here.parent / "data"):
            if (cand / "applications.csv").exists():
                data_dir = cand
                break
        else:
            raise FileNotFoundError(
                "Could not find applications.csv. Put the CSVs next to this "
                "script, or in a 'data' folder beside it, or pass --dir.")
    data_dir = Path(data_dir)

    d = {name: pd.read_csv(data_dir / f"{name}.csv") for name in FILES}

    # --- the join that matters -------------------------------------------
    # Hires and placements link to applications by application_id, NOT by
    # center and month. A center-month contains many people and therefore does
    # not identify an individual; for hires, the application and start months
    # can also differ. Joining on center_id + month produces plausible-looking
    # mismatches.
    app = d["applications"][APP_COLS].rename(
        columns={"month": "application_month"})

    d["hires_joined"] = d["hires"].merge(app, on="application_id", how="left",
                                         validate="one_to_one")
    d["flex_joined"] = d["flex_placements"].merge(
        app, on="application_id", how="left", validate="one_to_one")

    # --- which ATS the person applied under -------------------------------
    # Named `ats_at_application` rather than `ats` on purpose. center_month has
    # a row per center per month, so "which ATS applies to this hire" depends
    # on which month you pick -- the month they applied, or the month they
    # started, which can differ. We attach the application month because that
    # is when the situational section was written. If your question is about
    # something else, join it yourself on the month you want; the line is:
    #
    #   df.merge(center_month, left_on=["center_id", "<your month>"],
    #            right_on=["center_id", "month"], how="left")
    #
    # We deliberately do not attach the rest of center_month. It is 20 columns
    # including all the unit costs, and which of them belong on a hire row is
    # your call, not ours.
    ats = d["center_month"][["center_id", "month", "ats"]].rename(
        columns={"ats": "ats_at_application"})
    for k in ("hires_joined", "flex_joined"):
        d[k] = (d[k].merge(ats, left_on=["center_id", "application_month"],
                           right_on=["center_id", "month"], how="left")
                    .drop(columns="month"))

    # --- center attributes (one row per center, so this one is unambiguous) --
    for k in ("hires_joined", "flex_joined"):
        d[k] = d[k].merge(d["ats_migration"], on="center_id", how="left")
    return d


def summarise(d: dict[str, pd.DataFrame]) -> str:
    out = ["Loaded:"]
    for name in FILES:
        df = d[name]
        out.append(f"  {name:<18} {len(df):>8,} rows  x {df.shape[1]:>2} cols")
    out.append("")
    out.append("Joined frames built for you:")
    for name in ("hires_joined", "flex_joined"):
        df = d[name]
        out.append(f"  {name:<18} {len(df):>8,} rows  x {df.shape[1]:>2} cols")

    h = d["hires"]
    cm = d["center_month"]
    out += [
        "",
        "A few facts worth knowing before you start:",
        f"  panel runs {cm['month'].min()} to {cm['month'].max()}, "
        f"{cm['center_id'].nunique()} centers",
        f"  {int(d['ats_migration']['migration_month'].isna().sum())} centers "
        f"never migrated to the new ATS",
        f"  {int(h['retained_6mo'].isna().sum()):,} of {len(h):,} hires have no "
        f"6-month outcome yet (they started too recently)",
        f"  {int(h['coaching_hours_first_90d'].isna().sum()):,} hires have no "
        f"coaching hours recorded",
    ]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=None,
                    help="folder holding the five CSV files")
    args = ap.parse_args()
    print(summarise(load(args.dir)))
    print("\nThat is everything this script does. The analysis is yours.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
