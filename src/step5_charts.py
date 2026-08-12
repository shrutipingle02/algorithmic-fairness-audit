# Step 5
# Goal: turn the three findings into charts I can put in the README.
#
# Chart 1 - ProPublica's finding: the errors fall differently by race
# Chart 2 - Northpointe's defence: the score is calibrated
# Chart 3 - Chouldechova: the gap survives even a perfectly equal tool

import matplotlib
matplotlib.use("Agg")            # I'm saving files, not opening a window
import matplotlib.pyplot as plt
import pandas as pd

# --- my style settings, kept in one place so all three charts match ---------
BLUE = "#2a78d6"      # African-American
ORANGE = "#eb6834"    # Caucasian
SURFACE = "#fcfcfb"   # background
INK = "#0b0b0b"       # main text
INK_SOFT = "#52514e"  # axis labels, secondary text
GRID = "#e5e4e0"      # very light gridlines

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK_SOFT,
    "text.color": INK,
    "xtick.color": INK_SOFT,
    "ytick.color": INK_SOFT,
    "font.size": 11,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "grid.linestyle": "-",        # solid, never dashed
    "axes.axisbelow": True,       # grid sits behind the bars
})


def tidy(ax):
    """Remove the top and right frame lines so the chart breathes."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.xaxis.grid(False)          # vertical gridlines add nothing here


def header(fig, ax, title):
    """Put the title top-left and the legend in a row underneath it.

    My first attempt put the legend inside the plot and it landed on top of
    the value labels. Keeping it outside the axes means it can never collide
    with the data, no matter what the numbers turn out to be.
    """
    ax.set_title(title, fontsize=13, fontweight="bold", color=INK,
                 pad=34, loc="left")
    ax.legend(frameon=False, ncol=2, loc="lower left",
              bbox_to_anchor=(0, 1.005), fontsize=10.5)


df = pd.read_csv("data/raw/compas-scores-two-years.csv")
df["high_risk"] = (df["score_text"] != "Low").astype(int)
races = ["African-American", "Caucasian"]


def rates(race):
    g = df[df["race"] == race]
    no = g[g["two_year_recid"] == 0]
    yes = g[g["two_year_recid"] == 1]
    fpr = (no["high_risk"] == 1).mean() * 100
    fnr = (yes["high_risk"] == 0).mean() * 100
    return fpr, fnr


# ===========================================================================
# CHART 1 - the error rates
# ===========================================================================
fpr_b, fnr_b = rates("African-American")
fpr_w, fnr_w = rates("Caucasian")

fig, ax = plt.subplots(figsize=(8, 4.8))
positions = [0, 1]
width = 0.26

bars_b = ax.bar([p - width/2 - 0.02 for p in positions], [fpr_b, fnr_b],
                width, label="Black defendants", color=BLUE)
bars_w = ax.bar([p + width/2 + 0.02 for p in positions], [fpr_w, fnr_w],
                width, label="White defendants", color=ORANGE)

# I put the number on top of each bar so nobody has to squint at the axis.
for group in (bars_b, bars_w):
    for bar in group:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
                "{:.1f}%".format(bar.get_height()),
                ha="center", va="bottom", fontsize=10, color=INK)

ax.set_xticks(positions)
ax.set_xticklabels(["Wrongly flagged as high risk\n(did NOT reoffend)",
                    "Wrongly cleared as low risk\n(DID reoffend)"])
ax.set_ylabel("Share of that group (%)")
ax.set_ylim(0, 56)
header(fig, ax, "COMPAS made opposite mistakes for each group")
tidy(ax)
fig.text(0.008, -0.02,
         "Source: ProPublica COMPAS data, 7,214 defendants, Broward County FL.",
         fontsize=8.5, color=INK_SOFT)
fig.tight_layout()
fig.savefig("images/1_error_rates.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("saved images/1_error_rates.png")


# ===========================================================================
# CHART 2 - calibration
# ===========================================================================
two = df[df["race"].isin(races)]
cal = two.groupby(["decile_score", "race"])["two_year_recid"].mean().unstack() * 100
counts = two.groupby(["decile_score", "race"]).size().unstack()

fig, ax = plt.subplots(figsize=(8, 4.8))
ax.plot(cal.index, cal["African-American"], color=BLUE, linewidth=2,
        marker="o", markersize=7, label="Black defendants")
ax.plot(cal.index, cal["Caucasian"], color=ORANGE, linewidth=2,
        marker="o", markersize=7, label="White defendants")

ax.set_xticks(range(1, 11))
ax.set_xlabel("COMPAS risk score (1 = lowest risk, 10 = highest)")
ax.set_ylabel("Actually reoffended within 2 years (%)")
ax.set_ylim(0, 90)
header(fig, ax, "The score means roughly the same thing for both groups")
tidy(ax)

# Being honest about the thin data at the top of the white line.
n8, n9, n10 = (counts.loc[s, "Caucasian"] for s in (8, 9, 10))
fig.text(0.008, -0.02,
         "The white line dips above score 8; only {}, {} and {} white defendants "
         "scored 8, 9 and 10, so that wobble is sampling noise.".format(n8, n9, n10),
         fontsize=8.5, color=INK_SOFT)
fig.tight_layout()
fig.savefig("images/2_calibration.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("saved images/2_calibration.png")


# ===========================================================================
# CHART 3 - the impossibility
# ===========================================================================
def base_rate(race):
    return df[df["race"] == race]["two_year_recid"].mean()


def forced_fpr(p, ppv, fnr):
    """Chouldechova's identity, solved for FPR."""
    return (p / (1 - p)) * ((1 - ppv) / ppv) * (1 - fnr) * 100


# A hypothetical tool that treats both groups identically.
EQUAL_PPV, EQUAL_FNR = 0.61, 0.35
hyp_b = forced_fpr(base_rate("African-American"), EQUAL_PPV, EQUAL_FNR)
hyp_w = forced_fpr(base_rate("Caucasian"), EQUAL_PPV, EQUAL_FNR)

fig, ax = plt.subplots(figsize=(8, 4.8))
positions = [0, 1]
bars_b = ax.bar([p - width/2 - 0.02 for p in positions], [fpr_b, hyp_b],
                width, label="Black defendants", color=BLUE)
bars_w = ax.bar([p + width/2 + 0.02 for p in positions], [fpr_w, hyp_w],
                width, label="White defendants", color=ORANGE)

for group in (bars_b, bars_w):
    for bar in group:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.2,
                "{:.1f}%".format(bar.get_height()),
                ha="center", va="bottom", fontsize=10, color=INK)

# I write the gap above each pair, because the gap IS the point of this chart.
for x, (b, w) in zip(positions, [(fpr_b, fpr_w), (hyp_b, hyp_w)]):
    ax.text(x, 52, "{:.2f}x gap".format(b / w), ha="center",
            fontsize=10.5, fontweight="bold", color=INK)

ax.set_xticks(positions)
ax.set_xticklabels(["COMPAS as it actually scored",
                    "A tool built to treat both groups\nidentically (same PPV, same miss rate)"])
ax.set_ylabel("Wrongly flagged as high risk (%)")
ax.set_ylim(0, 58)
header(fig, ax, "The gap does not come from the algorithm")
tidy(ax)
fig.text(0.008, -0.02,
         "Right-hand pair: base rates 51.4% vs 39.4% are the only difference left. "
         "The forced gap equals the base-rate odds ratio, whatever PPV and miss rate are chosen.",
         fontsize=8.5, color=INK_SOFT)
fig.tight_layout()
fig.savefig("images/3_impossibility.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("saved images/3_impossibility.png")
