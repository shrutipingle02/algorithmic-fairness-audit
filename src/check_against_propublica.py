# Cross-check
# Goal: prove my numbers match ProPublica's published output, cell by cell.
#
# The target values below are copied from the saved output of their own
# notebook, "Compas Analysis.ipynb" in github.com/propublica/compas-analysis
# (cells 71, 75 and 77). If any assert fails, I have made a mistake.

import pandas as pd

df = pd.read_csv("data/raw/compas-scores-two-years.csv")
df["predicted_high_risk"] = (df["score_text"] != "Low").astype(int)


# What ProPublica printed, per race:
#   tn = survived + labelled Low      fp = survived + labelled High
#   fn = recidivated + labelled Low   tp = recidivated + labelled High
PROPUBLICA = {
    "African-American": {"tn": 990,  "fp": 805, "fn": 532, "tp": 1369,
                         "fpr": 44.85, "fnr": 27.99, "ppv": 0.63, "npv": 0.65,
                         "prevalence": 0.51, "total": 3696},
    "Caucasian":        {"tn": 1139, "fp": 349, "fn": 461, "tp": 505,
                         "fpr": 23.45, "fnr": 47.72, "ppv": 0.59, "npv": 0.71,
                         "prevalence": 0.39, "total": 2454},
}

problems = []


def check(label, mine, theirs, tolerance=0.0):
    """Compare one number and record it. tolerance allows for their rounding."""
    ok = abs(mine - theirs) <= tolerance
    print("  {:14s} mine {:>10} | theirs {:>10}  {}".format(
        label, round(mine, 4), theirs, "OK" if ok else "MISMATCH"))
    if not ok:
        problems.append(label)


print("=" * 66)
print("CHECK 1 - row counts")
print("=" * 66)
check("raw rows", len(df), 7214)

# The filter I used in step 1, for the robustness version.
filtered = df[(df["days_b_screening_arrest"] <= 30) &
              (df["days_b_screening_arrest"] >= -30) &
              (df["is_recid"] != -1) &
              (df["c_charge_degree"] != "O") &
              (df["score_text"] != "N/A")]
check("filtered rows", len(filtered), 6172)


print("\n" + "=" * 66)
print("CHECK 2 - every cell of the 2x2 table, per race")
print("=" * 66)

for race, target in PROPUBLICA.items():
    group = df[df["race"] == race]
    survived = group[group["two_year_recid"] == 0]
    recidivated = group[group["two_year_recid"] == 1]

    tn = int((survived["predicted_high_risk"] == 0).sum())
    fp = int((survived["predicted_high_risk"] == 1).sum())
    fn = int((recidivated["predicted_high_risk"] == 0).sum())
    tp = int((recidivated["predicted_high_risk"] == 1).sum())

    print("\n" + race)
    check("total", len(group), target["total"])
    check("true neg", tn, target["tn"])
    check("false pos", fp, target["fp"])
    check("false neg", fn, target["fn"])
    check("true pos", tp, target["tp"])

    # Now the rates they printed. They rounded to 2 decimal places, so I
    # allow a small tolerance rather than demanding an exact match.
    check("FPR %", fp / (tn + fp) * 100, target["fpr"], tolerance=0.01)
    check("FNR %", fn / (fn + tp) * 100, target["fnr"], tolerance=0.01)
    check("PPV", tp / (tp + fp), target["ppv"], tolerance=0.005)
    check("NPV", tn / (tn + fn), target["npv"], tolerance=0.005)
    check("prevalence", (fn + tp) / len(group), target["prevalence"], tolerance=0.005)


print("\n" + "=" * 66)
print("CHECK 3 - data sanity")
print("=" * 66)

# If any of these are surprising, something is wrong with my assumptions.
print("  decile_score range:", df["decile_score"].min(), "to", df["decile_score"].max())
print("  score_text values:", sorted(df["score_text"].dropna().unique()))
print("  two_year_recid values:", sorted(df["two_year_recid"].unique()))
print("  nulls in columns I use:",
      df[["race", "decile_score", "score_text", "two_year_recid"]].isna().sum().sum())

# I claimed in step 2 that "score_text != Low" is the same as "decile >= 5".
# Better to test that than trust it.
same = ((df["score_text"] != "Low") == (df["decile_score"] >= 5)).all()
print("  'not Low' identical to 'decile >= 5':", same)


print("\n" + "=" * 66)
if problems:
    print("FAILED:", len(problems), "mismatches ->", problems)
else:
    print("ALL CHECKS PASSED - my numbers match ProPublica's published output.")
print("=" * 66)
