# Step 4
# Goal: show WHY ProPublica and Northpointe were both right.
#
# Chouldechova (2017) points out that these four numbers are locked together:
#
#     FPR = ( p / (1-p) ) * ( (1-PPV) / PPV ) * ( 1 - FNR )
#
#   p    = base rate, the share who actually reoffended
#   PPV  = when the tool says high risk, how often it is correct
#   FNR  = share of real reoffenders the tool missed
#   FPR  = share of non-reoffenders the tool wrongly flagged
#
# Once three of them are set, the fourth is forced. Nobody chooses it.

import pandas as pd

df = pd.read_csv("data/raw/compas-scores-two-years.csv")
df["predicted_high_risk"] = (df["score_text"] != "Low").astype(int)

races = ["African-American", "Caucasian"]


def get_numbers(race):
    """Pull the four quantities out of the real data for one race."""
    group = df[df["race"] == race]
    survived = group[group["two_year_recid"] == 0]
    recidivated = group[group["two_year_recid"] == 1]

    tn = (survived["predicted_high_risk"] == 0).sum()
    fp = (survived["predicted_high_risk"] == 1).sum()
    fn = (recidivated["predicted_high_risk"] == 0).sum()
    tp = (recidivated["predicted_high_risk"] == 1).sum()

    p = (tp + fn) / len(group)      # base rate
    ppv = tp / (tp + fp)            # a high-risk flag is right this often
    fnr = fn / (fn + tp)            # real reoffenders that were missed
    fpr = fp / (fp + tn)            # non-reoffenders wrongly flagged
    return p, ppv, fnr, fpr


def formula(p, ppv, fnr):
    """Chouldechova's identity: work out FPR from the other three."""
    return (p / (1 - p)) * ((1 - ppv) / ppv) * (1 - fnr)


# ---------------------------------------------------------------------------
# Part 1: does the formula actually reproduce the real FPR?
# If it does not, I have misunderstood the formula.
# ---------------------------------------------------------------------------
print("=" * 66)
print("PART 1 - check the formula against the real data")
print("=" * 66)

for race in races:
    p, ppv, fnr, real_fpr = get_numbers(race)
    predicted_fpr = formula(p, ppv, fnr)
    print("\n" + race)
    print("  base rate p : {:.4f}".format(p))
    print("  PPV         : {:.4f}".format(ppv))
    print("  FNR         : {:.4f}".format(fnr))
    print("  FPR measured: {:.4f}".format(real_fpr))
    print("  FPR formula : {:.4f}".format(predicted_fpr))
    print("  difference  : {:.10f}".format(abs(real_fpr - predicted_fpr)))


# ---------------------------------------------------------------------------
# Part 2: the actual point.
#
# Suppose I build a PERFECT tool that treats both groups identically:
# the same PPV and the same FNR for everybody. Northpointe's fairness AND
# equal miss rates, both satisfied at once.
#
# What false positive rate does each group end up with?
# ---------------------------------------------------------------------------
print("\n" + "=" * 66)
print("PART 2 - force the tool to behave IDENTICALLY for both groups")
print("=" * 66)

# I pick one PPV and one FNR and apply them to both races.
# The values are roughly what COMPAS actually achieves.
same_ppv = 0.61
same_fnr = 0.35

print("\nI am now pretending the tool has, for BOTH races:")
print("  PPV = {}   (equally trustworthy when it says high risk)".format(same_ppv))
print("  FNR = {}   (misses real reoffenders equally often)".format(same_fnr))
print("\nThe ONLY thing still different between the groups is the base rate.\n")

results = {}
for race in races:
    p, _, _, _ = get_numbers(race)
    forced_fpr = formula(p, same_ppv, same_fnr)
    results[race] = forced_fpr
    print("  {:18s} base rate {:.3f}  ->  FPR is forced to {:.1%}".format(
        race, p, forced_fpr))

gap = results["African-American"] / results["Caucasian"]
print("\n  Even with an identical tool, the FPR gap is {:.1f}x.".format(gap))
print("  Nothing about the model caused this. Only the base rates differ.")


# ---------------------------------------------------------------------------
# Part 3: what would it take to make the false positive rates equal?
# ---------------------------------------------------------------------------
print("\n" + "=" * 66)
print("PART 3 - the only ways out")
print("=" * 66)

p_black, _, _, _ = get_numbers("African-American")
p_white, _, _, _ = get_numbers("Caucasian")

# Option A: keep FNR equal, and solve for the PPV that white defendants would
# need in order to match the black FPR. If it differs from same_ppv, then
# calibration has been broken on purpose.
target_fpr = results["African-American"]
# rearranging the formula for PPV:
#   FPR = (p/(1-p)) * ((1-PPV)/PPV) * (1-FNR)
#   -> PPV = 1 / ( 1 + FPR*(1-p) / (p*(1-FNR)) )
odds_white = p_white / (1 - p_white)
needed_ppv_white = 1 / (1 + target_fpr / (odds_white * (1 - same_fnr)))

print("\nTo give white defendants the same FPR as black defendants,")
print("their PPV would have to move from {:.2f} to {:.2f}.".format(
    same_ppv, needed_ppv_white))
print("That means deliberately making the score MEAN something different")
print("depending on race. That is exactly what calibration forbids.")

print("\nSo the choice is:")
print("  - equal PPV  (the score means the same thing for everyone), or")
print("  - equal FPR  (innocent people are flagged at the same rate),")
print("  - but not both, unless the base rates are equal.")
print("\nBase rates here: {:.3f} vs {:.3f}. Not equal.".format(p_black, p_white))
