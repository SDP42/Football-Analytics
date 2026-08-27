# ML Strategy

Defines the candidate ML problems **before** we pick models. For each: input,
target, features, problem type, candidate models (with why), metrics, leakage
risks, difficulty, and football value. Model choice is justified, never "because
it's popular".

Metrics rationale lives in [evaluation_strategy.md](evaluation_strategy.md).
Leakage and splitting are expanded in the final section here.

---

## Dataset → feature mapping (overview)

```text
StatsBomb events ─┬─ shots ───────────► shot features ──► xG model
                  ├─ passes ──────────► passing network + progression metrics
                  ├─ all on-ball events► player per-90 profiles ──► similarity / clustering
                  └─ possessions ─────► team style metrics ──► team strength

football-data.co.uk ─ results + odds ─► rolling team form ──► match outcome model
                                       └ odds-implied probs ──► evaluation baseline

FBref (basic) ─ season minutes/goals ─► career context features (scouting filter)
```

---

## Problem 1 — Match outcome prediction (Home / Draw / Away)

| Aspect | Detail |
|---|---|
| **Input** | Pre-kickoff state only: each team's recent form, rolling goals for/against, rest days, home/away, (optional) squad availability, bookmaker odds |
| **Target** | `FTR ∈ {H, D, A}` (from football-data.co.uk) |
| **Features** | Rolling window (last k matches) points, goals, xG-for/against if available, shot rates; Elo / SPI-style team rating updated match-by-match; home indicator; days since last match; head-to-head; odds-implied probabilities (de-margined) |
| **Problem type** | Multiclass classification (3 classes), **imbalanced** (draws ~25%), **temporal** |
| **Candidate models** | 1. **Baselines:** class prior, "always home", bookmaker-implied probabilities. 2. **Multinomial logistic regression** — transparent, calibrated-ish, great teaching baseline. 3. **Gradient boosting (XGBoost / LightGBM)** — handles nonlinear feature interactions, robust to scale, strong tabular performance. 4. (Later) **Ordered/Poisson goals model** (predict home & away goal rates, derive result probabilities) — often beats direct classification and is interpretable. |
| **Why these** | LR for a readable, calibratable reference; GBM because tabular football features have interactions and it is the honest strong baseline; Poisson-goals because it matches the data-generating process and gives score distributions, not just result. No neural net — see [dl_strategy.md](dl_strategy.md). |
| **Metrics** | **Log-loss** (primary — proper scoring rule, matches "probabilities" goal), **Brier score**, calibration curve, accuracy (secondary), **ranked probability score** (respects H>D>A ordering), comparison vs odds baseline |
| **Leakage risks** | Using post-match stats (FTHG/HS/HST) as features; using future matches in rolling windows; computing team ratings with lookahead; scaling/imputing using full-data statistics; league-table position that already encodes the result |
| **Difficulty** | Medium. Getting a *correct* pipeline is the hard part; beating the bookmaker is essentially not expected. |
| **Football value** | Forecasting, expectation-setting, "was this result surprising?" Also the flagship lesson in doing ML honestly. |

---

## Problem 2 — Player performance prediction

| Aspect | Detail |
|---|---|
| **Input** | A player's historical per-90 metrics + context (age, position, minutes, team strength, competition) up to time *t* |
| **Target** | A future performance quantity: next-period goals+assists per 90, or npxG+xA per 90, or a composite output score |
| **Features** | Trailing per-90 rates, minutes trend, age curve, role, team attacking volume, home/away split; regression-to-mean priors |
| **Problem type** | Regression (optionally quantile regression for intervals); **temporal**, **panel data** |
| **Candidate models** | 1. **Baseline:** "next = last" and "next = trailing mean" and **shrinkage estimate** (empirical-Bayes toward positional mean). 2. **Ridge / ElasticNet** regression. 3. **Gradient boosting** (with monotonic constraints where sensible, e.g. age). 4. **Mixed-effects / hierarchical model** (player random effect) — principled for panel data. 5. (Phase 3) sequence model — only if it beats GBM. |
| **Why these** | Shrinkage baseline because small samples of minutes are noisy and regression to the mean is the dominant effect; hierarchical model because players are repeated units; GBM for nonlinear age/role/volume interactions. |
| **Metrics** | MAE, RMSE, R², and **calibration of prediction intervals** (coverage). Compare to shrinkage baseline. |
| **Leakage risks** | Trailing windows crossing into the target period; using season-total minutes (known only after the season); target metric appearing (transformed) among features; player appearing in both train and test at the same time slice |
| **Difficulty** | Medium–hard. Signal is weak; honest baselines are strong. |
| **Football value** | Recruitment (projecting output after transfer), contract decisions, identifying likely regression candidates. |

---

## Problem 3 — Player clustering (data-driven roles)

| Aspect | Detail |
|---|---|
| **Input** | Standardised per-90 style metrics per player-season (within a minutes threshold), position group fixed or included |
| **Target** | None (unsupervised) |
| **Features** | Style ratios not volume: pass length mix, progressive actions, pressures, touches by pitch third, dribble rate, aerials, shot location profile, defensive action height |
| **Problem type** | Clustering + dimensionality reduction |
| **Candidate models** | 1. **PCA** first (understand variance, denoise). 2. **K-means** (simple, fast, needs *k* and assumes round clusters). 3. **Gaussian Mixture** (soft assignment — a player can be 70% "deep playmaker", 30% "shuttler"). 4. **Hierarchical / Ward** for a dendrogram narrative. 5. **UMAP / t-SNE** for visualisation only (not for defining clusters). |
| **Why these** | Start with the simplest (k-means) and a visual (PCA); GMM because football roles are fuzzy; avoid density methods (HDBSCAN) unless k-means clearly fails, to keep it explainable. |
| **Metrics** | **Silhouette**, Davies–Bouldin, gap statistic for *k*; **but the real test is interpretability** — can we name each cluster and do known players land where expected (e.g. Rodri → deep controller)? Stability across seasons. |
| **Leakage risks** | Minimal (unsupervised) but: standardising across the whole dataset then "evaluating" on a subset; mixing positions so clusters just re-discover position; using volume metrics so clusters just re-discover minutes/team. |
| **Difficulty** | Easy–medium technically; medium to make *useful and stable*. |
| **Football value** | A shared vocabulary of roles; finding role-alike replacements; spotting mis-used players. |

---

## Problem 4 — Player similarity

| Aspect | Detail |
|---|---|
| **Input** | Query player-season vector (standardised style + output metrics) |
| **Target** | None — a ranking task |
| **Features** | Same feature space as Problem 3, possibly weighted by what the user cares about |
| **Problem type** | Nearest-neighbour retrieval in a metric space |
| **Candidate models** | 1. **Standardise → weighted Euclidean / cosine → k-NN.** 2. **PCA/whiten then distance** (decorrelate before measuring). 3. (Phase 3) **learned embeddings** (Problem-3 GMM responsibilities, or a trained autoencoder / player2vec) then distance. |
| **Why these** | k-NN on a sensible feature space is transparent and debuggable — you can show *which metrics* drive a match. Learned embeddings only if the simple version demonstrably misses obvious similarities. |
| **Metrics** | No ground truth → **face validity** (known similar players rank high), **precision@k** against a hand-labelled small eval set, robustness (small feature change → small ranking change), positional sanity. |
| **Leakage risks** | Comparing across incompatible competitions/eras without adjustment; letting team context dominate (a metric inflated by teammates); different minutes making noisy vectors look "unique". |
| **Difficulty** | Easy to build, medium to make trustworthy. |
| **Football value** | "Find me a cheaper/younger version of X" — the core scouting use case. |

---

## Problem 5 — Player scouting recommendation

| Aspect | Detail |
|---|---|
| **Input** | A target profile (either a reference player, or explicit metric targets) + hard filters (age, position, minutes, competition, contract/value if available) |
| **Target** | A ranked shortlist |
| **Features** | Similarity score (Problem 4) + projected performance (Problem 2) + filters + optional "upside" (age-adjusted trajectory) |
| **Problem type** | Filtering + multi-criteria ranking (not a classic recommender — no user-item interaction history) |
| **Candidate models** | 1. **Rule + score composite:** filter, then rank by a weighted blend of similarity, projected output, and age value. 2. **Pareto front** across objectives (don't collapse to one number — show trade-offs). 3. (Much later, if interaction data existed) learning-to-rank. |
| **Why these** | Scouting is a decision-support tool; a transparent, tunable score that a scout can interrogate beats a black-box recommender they won't trust. No collaborative filtering — we have no "users who liked X" data. |
| **Metrics** | **Precision@k / Recall@k** against expert-labelled shortlists; diversity of the list; "would a scout act on this?" qualitative review. |
| **Leakage risks** | Ranking on metrics measured *after* a breakout the club already knows about; survivorship (only players with lots of minutes are visible); target-league metrics not comparable to source-league. |
| **Difficulty** | Medium — mostly a data-quality and comparability problem. |
| **Football value** | Direct: shortlisting under budget and squad constraints. |

---

## Supporting model — Expected Goals (xG)  *(MVP, feeds Problems 1–5)*

| Aspect | Detail |
|---|---|
| **Input** | One shot: location (→ distance, angle to goal), body part, shot type (open play / set piece / penalty), assist type, under pressure, (later) defender positions from the shot freeze-frame, goalkeeper position |
| **Target** | `goal ∈ {0,1}` |
| **Problem type** | Binary classification, **probability** output (calibration is the point) |
| **Candidate models** | 1. **Logistic regression** on distance, angle, dummies — the classic, fully explainable xG. 2. **GBM** for interactions (angle × pressure, header × distance). 3. Compare both to **StatsBomb's own xG** as an external reference. |
| **Why** | xG is a *calibrated probability* product; logistic regression is the honest baseline and interpretable ("each extra metre of distance multiplies odds by ..."). GBM shows the ceiling. Freeze-frame features are what separate a toy xG from a real one. |
| **Metrics** | **Log-loss, Brier, calibration curve, ROC-AUC / PR-AUC**; sum(xG) vs actual goals by bucket. |
| **Leakage risks** | Using shot outcome fields (e.g. "shot ended in goal location") as features; penalties dominating if not separated; including post-shot info (post-shot xG is a *different* model). |
| **Difficulty** | Easy baseline, medium with freeze frames. Great first model. |
| **Football value** | Foundation metric for finishing skill, chance creation, team quality, and match simulation. |

---

## Data leakage & splitting — the rules for this project

### Golden rule

> A feature is only legal if its value was **knowable at prediction time**.

### Match prediction — temporal split, no shuffling

```text
train:      seasons  ... up to  S-2
validation: season   S-1          (model selection, hyperparameters, calibration)
test:       season   S            (touched once, at the end)
```

- Within training, use **time-series / expanding-window CV**, never random
  k-fold.
- Rolling features use only matches with `date < current match date`.
- Team ratings (Elo/SPI) updated strictly forward in time.
- Fit scalers/imputers/encoders **on the training fold only**, then apply.
- Report against the **bookmaker-odds baseline** and naive baselines on the same
  test season.

### Player analytics — split by time and/or by player

- Performance prediction: **time-based** (predict season S from ≤ S-1). If also
  generalising to unseen players, additionally hold out players.
- Similarity/clustering: fit the standardisation and PCA on a reference set;
  evaluate stability on a later season.

### xG — split by match, ideally by competition/season

- Never let shots from the same match be split across train/test (weak leakage
  via match conditions). Prefer holding out whole seasons/competitions to test
  transfer.

### Things that look fine but are leakage

| Looks harmless | Why it leaks |
|---|---|
| `StandardScaler().fit(X_all)` | test distribution info bleeds into training |
| League position as a feature | already contains the results you're predicting |
| "Average xG this season" for a mid-season match | includes future matches |
| Imputing missing odds with the column mean | mean computed over the test set |
| Player's season-total minutes | only known after the season ends |
| Randomly splitting a player's seasons | near-duplicate rows across train/test |

### Why not just `train_test_split(shuffle=True)`?

Football is a time series. Random splitting lets the model "see the future"
(train on May, test on March of the same season), inflating every metric and
producing a model that fails in the only setting that matters: predicting
matches that **haven't happened yet**. We accept lower, honest numbers.
