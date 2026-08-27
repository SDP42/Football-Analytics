# Requirements & Feature Roadmap

This file is the single source of truth for **scope**. If something is not here,
we are not building it yet. Moving an item between phases is a decision and must
be recorded in [decisions.md](decisions.md).

## Guiding constraints (from the project owner)

1. Every important line of code must be explainable in a viva / interview.
2. Simple and readable before optimised.
3. No library, model, DB, or metric without a written justification.
4. Complexity must be justified by a real requirement.
5. Explain the concept → explain the design → small implementation → line-by-line
   → then production version → explain the diff.

## Functional requirements by phase

### MVP (Phase 1)

| ID | Requirement | Acceptance criteria |
|----|-------------|---------------------|
| F1 | Download StatsBomb Open Data for the agreed competition set (La Liga 2004/05–2020/21 spine + Indian Super League 2021/22 + Premier League 2015/16 + one season each of Bundesliga / Ligue 1 / Serie A — see [decisions.md #0013](decisions.md)) | Script is idempotent; re-running does not re-download; raw files land in `data/raw/statsbomb/` |
| F2 | Validate raw data | Schema + row-count + null checks; failures are loud, not silent |
| F3 | Parse events into tidy tables (matches, players, events, shots, passes) | Stored as Parquet in `data/processed/`; documented in `data_dictionary.md` |
| F4 | EDA notebook | Distributions, missingness, sanity checks (e.g. shots inside the pitch) |
| F5 | xG model | Trained on shot features; calibration curve plotted; Brier score + log-loss reported; compared to StatsBomb xG |
| F6 | Player per-90 profiles + percentile radar | For a chosen position group; reproducible from a function |
| F7 | Team style metrics | Fixed, documented set (~6–10 metrics) with definitions |
| F8 | Passing network for one match | Node = player avg position, edge weight = completed passes; plotted on a pitch |
| F9 | Match outcome baseline model | Home/Draw/Away; **temporal split**; beats "always predict home win" and "class prior" baselines on log-loss |
| F10 | Reproducibility | Fixed random seeds; `scripts/` entry points; a documented run order |

### Phase 2

| ID | Requirement |
|----|-------------|
| F11 | Player similarity (k-NN in standardised metric space, within position group) |
| F12 | Player role clustering (k-means / GMM) + written interpretation of each cluster |
| F13 | Scouting query interface (filter + rank) |
| F14 | Multi-competition ingestion |
| F15 | Cross-source entity resolution (team & player name/ID matching) |
| F16 | Secondary datasets integrated (`football-data.co.uk` results, FBref historical basic stats) |
| F17 | FastAPI service exposing analytics endpoints |
| F18 | Minimal dashboard (Streamlit or plain HTML) |
| F19 | Experiment tracking |

### Advanced (Phase 3)

| ID | Requirement |
|----|-------------|
| F20 | Temporal player-form model; DL only if it beats GBM baseline |
| F21 | Player embeddings |
| F22 | Passing-network graph metrics (centrality, clustering) |
| F23 | Formation / team-shape estimation |
| F24 | In-game win-probability / momentum model |
| F25 | Containerisation + CI + model monitoring |

### Research / Experimental (Phase 4)

| ID | Requirement |
|----|-------------|
| F26 | CV: player + ball detection on SoccerNet clips |
| F27 | CV: multi-object tracking |
| F28 | CV: pitch homography → pitch coordinates → heatmaps |
| F29 | Tracking-data tactical metrics (pitch control) |
| F30 | Transformer over event sequences for possession value |

## Non-functional requirements

| Area | Requirement | When it applies |
|------|-------------|-----------------|
| Reproducibility | Same inputs + seed → same outputs | From MVP |
| Explainability | Every model ships with a "how to read this" note + a baseline comparison | From MVP |
| Data lineage | Every processed file traceable to a raw source + transform | From MVP |
| Testing | `src/` logic covered by pytest; data-shape assertions | From MVP (light), stricter in Phase 2 |
| Licensing | Only licensed data; attribution rendered wherever outputs are shown | Always |
| Performance | Only optimise a measured bottleneck | Phase 3+ |
| Scalability | Design so leagues/seasons are a parameter, not a rewrite | Design from MVP, implement in Phase 2+ |
| Security | No secrets in Git; `.env` for any keys | Always |

## Out of scope (entire project)

- Real-time / live match ingestion.
- Betting-market products or odds-beating claims.
- Paid data sources (Wyscout, StatsBomb IQ, Opta feeds).
- Scraping sites in violation of their terms (see `dataset_research.md`).
- Mobile app.
- User accounts / auth / multi-tenant SaaS.

## Definition of "done" for Phase 0 (this phase)

- [x] Folder structure created
- [x] Vision, requirements, dataset research, comparison, architecture drafted
- [x] `.gitignore` and decision log in place
- [ ] Dataset stack confirmed with the project owner
- [ ] Git repository initialised and first commit made
- [ ] `data_dictionary.md` filled with **real** fields after downloading a
      sample match
