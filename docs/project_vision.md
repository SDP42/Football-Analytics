# Project Vision

## A. Problem Definition

### What exact problem are we solving?

Football generates enormous amounts of data (every pass, shot, tackle, position)
but that data is **hard to turn into decisions**. A coach, scout, or analyst
typically wants answers to questions like:

- *How good is this team really, beyond the league table?*
- *Which players are statistically similar to a player we cannot afford?*
- *What does this team do well / badly, and where is it exploitable?*
- *What is the likely outcome of the next match, and how confident should we be?*
- *Is a player's recent form real improvement or noise?*

Our platform ingests public event data (and later tracking/video), turns it into
**interpretable analytics and calibrated predictions**, and presents them so a
non-programmer can act on them.

Concretely, the system answers three families of questions:

1. **Descriptive** — "what happened, and how?" (xG, passing networks, pressing
   intensity, territory maps, player role profiles).
2. **Comparative** — "how does X compare to Y / to the league?" (player
   similarity, clustering into roles, percentile radars, team style fingerprints).
3. **Predictive** — "what is likely to happen next?" (match outcome
   probabilities, expected player output, over/under-performance regression).

### Who would use this system?

See section B. Primary target: **analysts and scouts at small clubs / academies,
and serious independent analysts** who cannot afford Wyscout/StatsBomb IQ
subscriptions but can use open data well.

### What decisions can it help with?

| Decision | How the platform helps |
|---|---|
| Recruitment shortlisting | Player similarity + role clustering + percentile profiles on open data |
| Opposition preparation | Team style fingerprint, passing networks, defensive/attacking patterns |
| Match / tournament forecasting | Calibrated outcome probabilities with uncertainty |
| Player development tracking | Time-series of performance metrics, form vs noise |
| Narrative / content | Journalists and analysts explaining *why*, not just the score |

### Why is football analytics a good ML / Data Science problem?

- **Rich, structured, temporal data.** Events have location, time, actor, and
  outcome — perfect for feature engineering, sequence modelling, and spatial
  analysis.
- **Clear targets.** Match result, goals, xG, player output — no need to invent
  a label.
- **Ground truth arrives fast.** Every weekend produces new labelled outcomes,
  so models can be back-tested honestly.
- **Serious leakage traps.** Predicting a match "before kickoff" forces careful
  temporal splits and feature-timing discipline — excellent for learning to do
  ML *correctly*.
- **Interpretability matters.** Stakeholders will not act on a black box, so we
  are pushed toward explainable ML (SHAP, calibration, sensible baselines).
- **Multi-modal.** Tabular events, sequences, graphs (passing networks), and
  video — one domain that touches most of the ML/DL/CV toolbox.

### What makes our project different from a basic "football prediction" project?

A typical beginner project scrapes `football-data.co.uk`, runs
`train_test_split`, trains a classifier on final-table features, and reports a
misleadingly high accuracy. We differ on:

1. **Event-level data, not just results.** We model *how* teams play, not only
   who won.
2. **Honest evaluation.** Strict temporal splits, calibration curves, comparison
   against bookmaker-implied and naive baselines — not a single accuracy number.
3. **Analytics first, prediction second.** The descriptive/comparative layer
   (scouting, style, passing networks) is the core product; prediction is one
   feature.
4. **Explainability is a requirement, not a nice-to-have.**
5. **Engineering discipline.** Reproducible pipeline, data validation, tests,
   decision log — built like a real system.
6. **A path to Deep Learning and Computer Vision** that is justified per
   component, not bolted on for résumé value.

## B. Possible Users

| User | What they want | Fit for us | Notes |
|---|---|---|---|
| **Club/academy analyst (small budget)** | Opposition reports, recruitment support, on open data | **Primary** | Can use open data well; underserved by paid tools |
| **Independent / freelance analyst** | Reusable analytics, shareable visuals | **Primary** | Public audience; attribution-friendly |
| **Scout** | Player shortlists, similarity, role fit | **Secondary (core feature)** | Limited by open-data player coverage |
| **Coach** | Simple, visual tactical insight | Secondary | Needs very clean UX; later phase |
| **Journalist** | "Why" behind results, credible numbers | Secondary | Good for visibility/portfolio |
| **Fantasy football player** | Player point projections | Tertiary | Different data (FPL API); possible side module |
| **Bettor** | Edge vs bookmaker odds | **Explicitly not a target** | We will *use* odds as a baseline, not serve bettors |
| **Casual fan** | Fun visualisations | Tertiary | Falls out of the dashboard for free |
| **Big club / data vendor** | Proprietary tracking-based analytics | Not a target | They have paid data and in-house teams |

**Primary target user (single sentence):** a football analyst or scout at a
small club, academy, or independent practice who needs professional-grade
descriptive and comparative analytics but only has access to public data.

## C. Core Features

Features are split by phase. **The MVP is deliberately small** so we can build it
correctly and explain every line.

### MVP (Phase 1) — "Understand one competition deeply"

Scope: **StatsBomb Open Data, one or two competitions** (e.g. a World Cup +
La Liga seasons).

1. **Data pipeline**: download → validate → clean → store StatsBomb events.
2. **EDA & data dictionary**: documented understanding of the real schema.
3. **xG model (simple, explainable)**: logistic regression / gradient boosting on
   shot features; calibration curve; compare to StatsBomb's own xG.
4. **Player performance profiles**: per-90 metrics, percentile radars within a
   position group.
5. **Team style summary**: possession, directness, pressing, territory — a small
   fixed set of interpretable metrics.
6. **Passing network** for a single match (nodes = players, edges = pass volume).
7. **Match outcome model (baseline)**: predict Home/Draw/Away from pre-match
   features (team strength, form) with **strict temporal split** and comparison
   to naive baselines. Framed as a lesson in leakage as much as a feature.
8. **Notebook-quality visualisations** (pitch plots, radars, shot maps).

### Phase 2 — "Scouting & comparison"

- Player **similarity** (nearest neighbours in a standardised metric space).
- Player **clustering** into data-driven roles; interpret each cluster.
- **Scouting recommendation**: "players like X, under age A, more minutes than M".
- Multi-competition support + entity resolution across competitions.
- Secondary data (FBref historical basic stats, `football-data.co.uk` results)
  for longer match-prediction history.
- Simple **FastAPI** service exposing the analytics; minimal dashboard.
- Experiment tracking (MLflow or Weights & Biases) once we have >1 model.

### Advanced (Phase 3)

- **Sequence models** for player form / temporal performance (LSTM/GRU) —
  *only if* they beat a well-tuned gradient-boosting baseline (see
  [dl_strategy.md](dl_strategy.md)).
- **Player embeddings** learned from event context.
- Passing-network **graph metrics** and possibly a GNN (justified separately).
- Formation / team-shape estimation from event locations.
- Momentum / in-game win-probability model.
- Model monitoring, drift detection, containerisation, CI.

### Research / Experimental (Phase 4)

- **Computer Vision** on SoccerNet / sample tracking data: player & ball
  detection, tracking, homography to pitch coordinates, heatmaps.
- Tracking-data tactical analysis (pitch control, off-ball runs).
- Transformer over event sequences for possession-value estimation.
- These are learning spikes; each needs its own feasibility check and may be
  dropped.

### What the MVP deliberately excludes

- No live data / no real-time.
- No multi-league coverage.
- No frontend framework (notebooks + static plots only).
- No database yet (Parquet files are enough for one competition).
- No deep learning, no computer vision.
- No deployment.

## Non-goals (whole project)

- Not a betting product.
- Not a replacement for paid tracking data / scouting platforms.
- Not trying to beat the bookmakers' market.
- Not attempting full automated tactical analysis from video (research spike
  only).
