# Deep Learning Strategy

**Default position: we do NOT use deep learning unless it clearly beats a
well-tuned classical baseline on a real metric.** Football's tabular problems are
mostly won by gradient boosting. DL is justified only where the data is
sequential, relational, high-dimensional, or raw (video) — and where we have
enough of it.

Every candidate below is stated as a hypothesis to test, with the honest answer
to *"why not XGBoost?"*.

---

## Decision gate for any DL component

A DL model enters the project only if **all** of these hold:

1. There is a classical baseline (GBM / linear / hierarchical) tuned honestly.
2. The DL model beats it on the primary metric **on a temporal test set**, by a
   margin larger than run-to-run noise.
3. We can explain what the architecture does and why it fits the data structure.
4. Training cost (time, GPU) is acceptable for the value gained.
5. The result is reproducible (seed, config logged).

If any fails → we keep the classical model and record the negative result in
[decisions.md](decisions.md). A negative result is a valid deliverable.

---

## Candidate 1 — Sequence model for player form (LSTM / GRU / small Transformer)

| | |
|---|---|
| **Data structure** | Per player, an ordered sequence of match-level performance vectors |
| **Hypothesis** | Recurrent/attention models capture form momentum, streaks, and recovery patterns that trailing averages miss |
| **Why maybe DL** | Genuine sequential dependence; variable-length histories; the relationship between past and future performance may be nonlinear and order-dependent |
| **Why maybe NOT** | Sequences are **short** (tens of matches), signal-to-noise is low, and a GBM on engineered lag/rolling/EWMA features usually captures most of it. Small data + flexible model = overfitting |
| **Baseline to beat** | Empirical-Bayes shrinkage + GBM on lag features (Problem 2 in [ml_strategy.md](ml_strategy.md)) |
| **Verdict** | **Phase 3 experiment.** Likely loses. Worth doing once as a lesson in when RNNs don't help. |

## Candidate 2 — Player embeddings

| | |
|---|---|
| **Data structure** | Players appear in many event contexts; we want a dense vector per player capturing style/quality |
| **Approaches** | (a) Autoencoder on the per-90 metric matrix; (b) "player2vec": predict player from surrounding-event context; (c) factorise a player × action-type matrix |
| **Why maybe DL** | Learns interactions we didn't hand-design; embeddings are reusable across similarity, clustering, and as features for other models |
| **Why maybe NOT** | PCA/whitening on curated metrics already gives a usable low-dim representation and is interpretable. Embeddings are opaque and need a lot of data to be stable |
| **Baseline to beat** | PCA components + GMM soft assignments as the "embedding" |
| **Verdict** | **Phase 3.** Try an autoencoder; adopt only if it clearly improves similarity precision@k or downstream model performance. |

## Candidate 3 — Sequence model over event streams (possession → value)

| | |
|---|---|
| **Data structure** | A possession = an ordered sequence of events (type, location, player, outcome). Rich, plentiful (millions of events) |
| **Hypothesis** | A Transformer/RNN over event sequences can estimate the **value of an action** (how much it changes goal probability) better than frame-independent models — related to VAEP / "expected threat" |
| **Why maybe DL** | Large data; real sequential/spatial structure; context matters (a pass is valuable depending on what came before and the positions around it); 360 freeze frames add a set-of-points input that suits attention/DeepSets |
| **Why maybe NOT** | **VAEP with gradient boosting** (the `socceraction` approach) is a strong, published, interpretable baseline. Expected Threat (xT) is just a Markov grid — trivially simple and surprisingly good |
| **Baseline to beat** | xT grid model, then VAEP-with-GBM |
| **Verdict** | **Phase 3–4, highest-potential DL use case.** This is where sequence models plausibly win because the data volume and structure finally justify them. |

## Candidate 4 — Graph neural network on passing networks

| | |
|---|---|
| **Data structure** | Passing network = graph (nodes = players/positions, edges = pass volume/quality) |
| **Hypothesis** | A GNN summarises team structure for style classification or match-outcome features better than hand-computed centrality metrics |
| **Why maybe DL** | Relational data is literally a graph; GNNs are the natural fit |
| **Why maybe NOT** | Classical graph metrics (degree/betweenness/eigenvector centrality, clustering coefficient, network centralisation) are interpretable and often sufficient. A GNN needs many labelled graphs to train and is hard to explain |
| **Baseline to beat** | Hand-computed network metrics fed to a GBM |
| **Verdict** | **Phase 4, low priority.** Interesting, but hard to justify over classical graph features for our data volume. |

## Candidate 5 — Computer vision models

Covered in [cv_strategy.md](cv_strategy.md). CV is the **one place DL is not
optional** — detection, tracking, pose, and homography have no viable classical
alternative at usable accuracy. But it is Phase 4 and uses pretrained models.

## Candidate 6 — Match outcome via neural net

| | |
|---|---|
| **Verdict** | **Rejected for now.** ~20 tabular features, a few thousand matches, class imbalance, needs calibrated probabilities. This is textbook GBM / logistic territory. A neural net would need heavy regularisation just to match them and would be less calibratable. Revisit only if we add high-cardinality/sequence inputs. |

---

## Summary table

| Component | DL justified? | When | Baseline it must beat |
|---|---|---|---|
| Match outcome | No | — | GBM / Poisson-goals |
| Player form (sequence) | Probably not | Phase 3 (one experiment) | Shrinkage + GBM on lags |
| Player embeddings | Maybe | Phase 3 | PCA + GMM |
| Action value from event sequences | **Most likely yes** | Phase 3–4 | xT grid, VAEP-GBM |
| GNN on passing networks | Unlikely worth it | Phase 4 | Classical graph metrics + GBM |
| Computer vision | **Yes, unavoidable** | Phase 4 | (no classical alternative) |

**Guiding sentence for the viva:** *"We used deep learning only for computer
vision and for action-value estimation over event sequences, because those are
the cases where the data is raw or genuinely sequential and abundant; everywhere
else a tuned gradient-boosting model matched or beat it and was easier to
explain and calibrate."*
