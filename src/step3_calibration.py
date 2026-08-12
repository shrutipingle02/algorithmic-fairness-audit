# Step 3
# Goal: test Northpointe's defence of COMPAS.
#
# Their argument was NOT that ProPublica's numbers were wrong. They agreed
# with them. Their argument was that a different question matters:
#
#   "When COMPAS says someone is high risk, is it equally right about that
#    for every race?"
#
# If yes, then the score means the same thing for everybody, and Northpointe
# says that is what fairness means. This property is called CALIBRATION.

import pandas as pd

# Using all 7214 rows, same as step 2's main result.
df = pd.read_csv("data/raw/compas-scores-two-years.csv")
df["predicted_high_risk"] = (df["score_text"] != "Low").astype(int)

races = ["African-American", "Caucasian"]


# ---------------------------------------------------------------------------
# Part 1: of the people COMPAS flagged as high risk, how many really did
# reoffend? This is called PPV (positive predictive value).
# ---------------------------------------------------------------------------
print("=" * 62)
print("PART 1 - when COMPAS says HIGH RISK, how often is it right?")
print("=" * 62)

for race in races:
    group = df[df["race"] == race]

    # I only look at the people who were flagged, because the question is
    # about what the flag is worth.
    flagged = group[group["predicted_high_risk"] == 1]

    # Of those flagged people, what share actually reoffended?
    ppv = flagged["two_year_recid"].mean()

    print("{:18s} flagged {:5d} people, {:.1%} of them reoffended".format(
        race, len(flagged), ppv))

print("\nThese two numbers are close. That is Northpointe's whole case:")
print("a high-risk flag means roughly the same thing for both groups.")


# ---------------------------------------------------------------------------
# Part 2: the fuller picture. For every score from 1 to 10, what share of
# people with that score actually reoffended? If the lines for the two races
# sit on top of each other, the score is calibrated.
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("PART 2 - for each score 1 to 10, what share actually reoffended?")
print("=" * 62)

two_races = df[df["race"].isin(races)]

# I group by score AND race, then take the average of two_year_recid.
# Because that column is 1/0, the average IS the share who reoffended.
calibration = (two_races
               .groupby(["decile_score", "race"])["two_year_recid"]
               .mean()
               .unstack())

print((calibration * 100).round(1).to_string())
print("\n(numbers are percent who actually reoffended)")


# I'm saving this table because step 5 will turn it into a chart.
calibration.to_csv("data/calibration_by_score.csv")
print("\nSaved to data/calibration_by_score.csv")


# ---------------------------------------------------------------------------
# Part 3: the number that causes all the trouble. How many of each group
# reoffended overall? This is the BASE RATE.
# ---------------------------------------------------------------------------
print("\n" + "=" * 62)
print("PART 3 - the base rates (remember these for step 4)")
print("=" * 62)

for race in races:
    base_rate = df[df["race"] == race]["two_year_recid"].mean()
    print("{:18s} {:.1%} reoffended within 2 years".format(race, base_rate))
