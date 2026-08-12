# Step 1
# Goal: load the COMPAS file and clean it the same way ProPublica did,
# so that my numbers can be compared to theirs.

import pandas as pd

# I'm reading the raw file I downloaded from ProPublica's GitHub repo.
df = pd.read_csv("data/raw/compas-scores-two-years.csv")
print("Rows in the raw file:", len(df))


# ProPublica threw away some rows before they did any analysis.
# I'm repeating their four rules. If I skip this my numbers will not match
# theirs and I will not know whether I made a mistake or they did.

# Rule 1: the arrest and the COMPAS screening must be within 30 days of
# each other. If they are further apart, the score probably belongs to a
# different arrest, so I cannot trust that row.
df = df[(df["days_b_screening_arrest"] <= 30) &
        (df["days_b_screening_arrest"] >= -30)]

# Rule 2: drop rows where we do not know whether the person reoffended.
# In this file, -1 means the information is missing.
df = df[df["is_recid"] != -1]

# Rule 3: drop ordinary traffic offences. The charge degree "O" means the
# person was never actually jailed, so they do not belong in this analysis.
df = df[df["c_charge_degree"] != "O"]

# Rule 4: drop rows where COMPAS did not produce a risk category.
df = df[df["score_text"] != "N/A"]

print("Rows after filtering:", len(df))
print("ProPublica reported:  6172")


# I only need a few columns, so I'm keeping just those to make the next
# steps easier to read.
#   race            -> the group I am comparing
#   decile_score    -> the COMPAS risk score, 1 to 10
#   score_text      -> COMPAS's own label: Low / Medium / High
#   two_year_recid  -> did they actually reoffend within 2 years? 1 = yes
columns_i_need = ["race", "decile_score", "score_text", "two_year_recid"]
df = df[columns_i_need]


# I'm saving the cleaned table so the later steps can just load this
# instead of repeating the filtering every time.
df.to_csv("data/compas_clean.csv", index=False)
print("\nSaved cleaned data to data/compas_clean.csv")

# A quick look at what I ended up with.
print("\nHow many people of each race:")
print(df["race"].value_counts())

print("\nShare of each race who actually reoffended within 2 years:")
print(df.groupby("race")["two_year_recid"].mean().round(3))
