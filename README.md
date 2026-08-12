# Algorithmic Fairness Audit

A famous public argument about a criminal risk score where **both sides were right**.
Reproduced from the raw data, then explained.

COMPAS scores US defendants 1 to 10 on how likely they are to reoffend. Judges use those
scores for bail and sentencing. In 2016 ProPublica reported it was biased against Black
defendants. Northpointe, the vendor, replied that it was fair. Both had evidence.

---

## 1. ProPublica was right

![Error rates by race](images/1_error_rates.png)

Among defendants who did **not** reoffend, Black defendants were flagged high risk almost
twice as often. The figures are 44.8% against 23.5%. The mistake reverses for the other
error. Among those who **did** reoffend, white defendants were cleared as low risk twice
as often.

## 2. Northpointe was also right

![Calibration by score](images/2_calibration.png)

A score means the same thing whoever holds it. A 5 is roughly a coin flip for both groups.
A 10 is roughly 70 to 80 percent for both. When COMPAS says high risk it is correct 63% of
the time for Black defendants and 59% for white defendants. The score is **calibrated**.

## 3. Both, because of arithmetic

![The forced gap](images/3_impossibility.png)

These four quantities are locked together:

```
FPR = ( p / (1 - p) ) x ( (1 - PPV) / PPV ) x ( 1 - FNR )
```

Here `p` is the base rate, `PPV` is how often a high risk flag is correct, `FNR` is how
often real reoffenders are missed, and `FPR` is how often innocent people are flagged. Fix
any three and the fourth is decided.

Base rates differ here. They are 51.4% and 39.4%. So a tool built to treat both groups
*identically* still produces a 1.63x gap in wrongly flagged people. Taking the ratio, the
PPV and FNR terms cancel and what remains is **exactly the base rate odds ratio**. No model
can move it. Verified across 800 combinations of PPV and FNR, where the gap never budges.

**"Fair" is not one thing.** Equal PPV or equal FPR. You may have either but not both,
unless the base rates match. That is a choice about values and it cannot be delegated to an
engineer.

---

## Running it

```bash
pip install pandas matplotlib
python src/step1_load_data.py         # filter, matching ProPublica's rules
python src/step2_error_rates.py       # their finding
python src/step3_calibration.py       # Northpointe's defence
python src/step4_impossibility.py     # the identity
python src/step5_charts.py            # the three figures
python src/check_against_propublica.py   # verify against their published output
```

The raw CSV is not committed. `src/step1_load_data.py` expects it at
`data/raw/compas-scores-two-years.csv`. Download it from the repo linked below.

## Which rows

ProPublica used two subsets. All **7,214** rows for the confusion tables, which produced the
widely quoted FPR and FNR figures, and **6,172** rows after dropping cases where arrest and
screening were more than 30 days apart, which they used for their regression. This repo
reports the 7,214 figures as primary and the 6,172 version as a robustness check. **The
disparity is 1.9x either way.**

`check_against_propublica.py` verifies every cell of both contingency tables against their
published notebook output and fails loudly on any drift.

## Scope

This reproduces ProPublica's contingency table analysis. Their full study also included a
logistic regression on score disparity and a Cox proportional hazards model on predictive
accuracy. Neither is replicated here.

## Limitations

- **The label is re-arrest, not crime.** Arrest depends on where police patrol and who gets
  stopped. The base rate gap is itself partly a product of unequal enforcement, so
  "calibrated" means calibrated to arrests.
- **Calibration is not strictly monotonic for white defendants above decile 8.** Only 114, 98
  and 64 of them scored 8, 9 and 10. The 95% intervals overlap heavily, so the reversal is
  sampling noise rather than a defect.
- **One county, one period.** Broward County, Florida, 2013 to 2014. Nothing here generalises
  automatically.

---

## Acknowledgments

**Data and the original investigation.** [ProPublica](https://github.com/propublica/compas-analysis)
obtained the records, published the dataset, and released their full analysis. This
repository reproduces part of their work. It does not discover it.

- Julia Angwin, Jeff Larson, Surya Mattu, Lauren Kirchner. *Machine Bias.* ProPublica,
  23 May 2016.
  [Article](https://www.propublica.org/article/machine-bias-risk-assessments-in-criminal-sentencing)
- Jeff Larson, Surya Mattu, Lauren Kirchner, Julia Angwin. *How We Analyzed the COMPAS
  Recidivism Algorithm.* ProPublica, 23 May 2016.
  [Methodology](https://www.propublica.org/article/how-we-analyzed-the-compas-recidivism-algorithm)
- Dataset and notebook at
  [github.com/propublica/compas-analysis](https://github.com/propublica/compas-analysis)

**The result being reproduced.**

- Alexandra Chouldechova. *Fair prediction with disparate impact: A study of bias in
  recidivism prediction instruments.* 28 February 2017.
  [arXiv:1703.00056](https://arxiv.org/abs/1703.00056)
- Jon Kleinberg, Sendhil Mullainathan, Manish Raghavan. *Inherent Trade-Offs in the Fair
  Determination of Risk Scores.* ITCS 2017.
  [arXiv:1609.05807](https://arxiv.org/abs/1609.05807). This proves a closely related
  impossibility independently.

**The other side of the argument.** Northpointe, now Equivant, published a rebuttal arguing
COMPAS satisfies predictive parity. Their case is the one reproduced in section 2 and it
deserves to be read directly rather than through its critics.

**Tools.** pandas, matplotlib, and their maintainers.

## Licence

MIT for the code. The COMPAS data belongs to ProPublica under their own terms.
