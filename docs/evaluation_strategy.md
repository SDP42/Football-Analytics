# Evaluation Strategy

Decide **how we judge models before we build them**, so we cannot fool ourselves
later. Beginner football projects fail here: one accuracy number, random split,
no baseline.

## Principles

1. **Always have a baseline.** A model is only "good" relative to something dumb
   (class prior, "predict the mean", bookmaker odds, "next = last").
2. **Probabilities are judged by proper scoring rules** (log-loss, Brier), not
   just accuracy. If we claim to output probabilities, they must be *calibrated*.
3. **Evaluate on the future.** Temporal test set, touched once.
4. **One primary metric per problem**, chosen up front. Secondary metrics for
   diagnosis only.
5. **Report uncertainty.** Run-to-run variation, confidence intervals via
   bootstrap where feasible.

## Classification (match outcome, xG, "will player start", etc.)

| Metric | What it tells us | Why it matters for football |
|---|---|---|
| **Log-loss** | Penalises confident wrong probabilities | We sell probabilities; a 90%-confident wrong call should hurt |
| **Brier score** | Mean squared probability error; decomposes into calibration + refinement | Directly measures "are the % believable" |
| **Calibration curve / ECE** | Do 30%-predicted events happen ~30% of the time? | A miscalibrated xG makes every downstream metric wrong |
| **ROC-AUC** | Ranking ability, threshold-free | "Are better chances ranked above worse ones" |
| **PR-AUC** | Ranking under class imbalance | Goals are rare (~10% of shots); draws are the minority class |
| **Accuracy** | Fraction correct at a threshold | Intuitive but misleading with imbalance; **secondary only** |
| **Confusion matrix** | Where errors concentrate | E.g. model never predicts draws → known football failure mode |
| **Ranked Probability Score (RPS)** | Ordinal-aware Brier (H > D > A) | Predicting Away when Home wins is worse than predicting Draw |
| **vs bookmaker odds** | Are we better than the de-margined market? | The honest bar for match prediction (we likely won't clear it) |

**Match outcome primary metric:** log-loss (with RPS and calibration as required
companions).
**xG primary metric:** log-loss + calibration curve + Σ xG vs Σ goals by bucket.

## Regression (player performance, goals rate, minutes)

| Metric | What it tells us | Football note |
|---|---|---|
| **MAE** | Typical error in the metric's own units | "We're off by ~0.15 goals/90 on average" — interpretable |
| **RMSE** | Penalises large misses | Big projection errors are costly in recruitment |
| **R²** | Variance explained vs predicting the mean | Sanity check; will be *low* — performance is noisy, that's real |
| **Prediction-interval coverage** | Do 80% intervals contain the truth 80% of the time? | A projection without honest uncertainty is dangerous for decisions |
| **vs shrinkage baseline** | Are we beating "regress last season to the positional mean"? | This baseline is strong; beating it is the whole job |

**Primary:** MAE vs the shrinkage baseline, plus interval coverage.

## Clustering (player roles)

| Metric | What it tells us | Limits |
|---|---|---|
| **Silhouette score** | Cohesion vs separation | Rewards round, equal clusters; football roles aren't |
| **Davies–Bouldin / Calinski–Harabasz** | Alternative separation measures | Same caveats |
| **Gap statistic / elbow** | Choosing *k* | Guidance, not gospel |
| **Cluster stability** | Do clusters persist across seasons / bootstraps? | **The real test of a useful typology** |
| **Interpretability audit** | Can we name each cluster? Do known players land correctly? | The decisive check — a cluster we can't explain is useless |

**Primary:** interpretability + stability. Silhouette only picks the *shortlist*
of *k* values.

## Recommendation / retrieval (similarity, scouting shortlist)

| Metric | What it tells us |
|---|---|
| **Precision@k** | Of the top *k* suggestions, how many are genuinely relevant (expert-labelled) |
| **Recall@k** | Of all known-relevant players, how many made the top *k* |
| **Ranking stability** | Small feature perturbation → small ranking change |
| **Face validity** | Do obvious analogues surface (e.g. query a metronome DM → get other metronome DMs) |
| **List diversity** | Not 10 players from the same team/league |

**Primary:** Precision@k against a small hand-labelled evaluation set + face
validity review. No ground-truth dataset exists, so human review is mandatory.

## Cross-cutting checks (every model)

- **Baseline comparison** in every report — no exceptions.
- **Temporal split** — documented, no leakage (see
  [ml_strategy.md](ml_strategy.md#data-leakage--splitting--the-rules-for-this-project)).
- **Error slicing** — by competition, position, team strength, home/away, score
  state. A model good on average but broken for defenders is not shipped.
- **Calibration** for any probability output.
- **Stability** — rerun with different seeds; report the spread.
- **A "how to read this" note** shipped with every model output.

## What a model report must contain (template)

```text
Problem:                 (link to ml_strategy.md section)
Data slice + split:      train/val/test seasons, row counts
Baseline(s):             metric values
Model:                   type, key hyperparameters, why chosen
Primary metric:          value (± spread) vs baseline
Secondary metrics:       ...
Calibration:             curve / ECE (if probabilistic)
Error slices:            worst-performing segments
Leakage review:          what was checked
Known limitations:       ...
How to read the output:  1-paragraph plain-English guide
Interview one-liner:     how I'd summarise this in 20 seconds
```
