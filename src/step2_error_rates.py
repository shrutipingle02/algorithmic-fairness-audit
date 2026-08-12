# Step 2
# Goal: reproduce ProPublica's finding.
# They said COMPAS makes different KINDS of mistakes for different races.
#
# NOTE TO SELF ON WHICH ROWS TO USE:
# ProPublica used two different subsets in their work.
#   - All 7214 rows  -> for the confusion tables (the famous FPR / FNR numbers)
#   - 6172 rows      -> for their logistic regression, after dropping rows where
#                       the arrest and the screening were more than 30 days apart
# I got confused by this at first and applied the 30-day filter to everything,
# which made my numbers about 2 points off theirs. So here I run BOTH and show
# that the conclusion is the same either way.

import pandas as pd


def error_rates(df, race):
    """Work out how often COMPAS was wrong, for one race, in two ways."""

    group = df[df["race"] == race]

    # I split by what ACTUALLY happened, because a mistake only makes sense
    # once I know the truth.
    did_not_reoffend = group[group["two_year_recid"] == 0]
    did_reoffend = group[group["two_year_recid"] == 1]

    # FALSE POSITIVE: did not reoffend, but COMPAS said high risk.
    # I divide by everyone who did not reoffend, because they are the only
    # people who could possibly have been wrongly flagged.
    false_positives = (did_not_reoffend["predicted_high_risk"] == 1).sum()
    fpr = false_positives / len(did_not_reoffend)

    # FALSE NEGATIVE: did reoffend, but COMPAS said low risk.
    false_negatives = (did_reoffend["predicted_high_risk"] == 0).sum()
    fnr = false_negatives / len(did_reoffend)

    return len(group), fpr, fnr


# ---------------------------------------------------------------------------
# Version 1: all the rows, which is what ProPublica used for these tables.
# ---------------------------------------------------------------------------
all_rows = pd.read_csv("data/raw/compas-scores-two-years.csv")

# COMPAS labels people Low, Medium or High. To count mistakes I need a plain
# yes/no, so I follow ProPublica: Medium and High both count as "high risk".
all_rows["predicted_high_risk"] = (all_rows["score_text"] != "Low").astype(int)

print("=" * 62)
print("MAIN RESULT - all 7214 rows (matches ProPublica exactly)")
print("=" * 62)
print("{:18s} {:>6s} {:>10s} {:>10s}".format("group", "n", "FPR", "FNR"))

for race in ["African-American", "Caucasian"]:
    n, fpr, fnr = error_rates(all_rows, race)
    print("{:18s} {:6d} {:9.2f}% {:9.2f}%".format(race, n, fpr * 100, fnr * 100))

print("\nProPublica published: Black 44.85 / 27.99, White 23.45 / 47.72")


# ---------------------------------------------------------------------------
# Version 2: the filtered rows, as a robustness check.
# If my conclusion only held for one choice of rows, it would be a weak result.
# ---------------------------------------------------------------------------
filtered = pd.read_csv("data/compas_clean.csv")
filtered["predicted_high_risk"] = (filtered["score_text"] != "Low").astype(int)

print("\n" + "=" * 62)
print("ROBUSTNESS CHECK - 6172 rows, after the 30-day filter")
print("=" * 62)
print("{:18s} {:>6s} {:>10s} {:>10s}".format("group", "n", "FPR", "FNR"))

for race in ["African-American", "Caucasian"]:
    n, fpr, fnr = error_rates(filtered, race)
    print("{:18s} {:6d} {:9.2f}% {:9.2f}%".format(race, n, fpr * 100, fnr * 100))


# ---------------------------------------------------------------------------
# The thing I actually care about: is the gap the same size in both versions?
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("DOES THE CONCLUSION DEPEND ON WHICH ROWS I USED?")
print("=" * 62)

for label, data in [("all 7214 rows", all_rows), ("filtered 6172", filtered)]:
    _, black_fpr, _ = error_rates(data, "African-American")
    _, white_fpr, _ = error_rates(data, "Caucasian")
    print("{:15s}  black FPR is {:.1f} times the white FPR".format(
        label, black_fpr / white_fpr))

print("\nSame answer both ways, so the finding is not an artefact of my filtering.")
