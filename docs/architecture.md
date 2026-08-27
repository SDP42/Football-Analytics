# Architecture

Covers: the data pipeline, what is stored where and why, entity resolution, the
folder structure, and scalability posture. **No technology is adopted here
without a reason.** Adoptions are also logged in [decisions.md](decisions.md).

## 1. Data pipeline (conceptual)

```text
        ┌─────────────┐
        │  SOURCES    │  StatsBomb repo · football-data.co.uk CSVs · FBref pages
        └──────┬──────┘
               │  scripts/ingest_*.py   (idempotent download, polite rate limits)
        ┌──────▼──────┐
        │  data/raw/  │  EXACT bytes as downloaded. Never edited. Not in Git.
        └──────┬──────┘
               │  src/data/validate.py   (schema, row counts, null rules, ranges)
        ┌──────▼──────────┐
        │  validation     │  fails LOUD. A bad download must not flow downstream.
        └──────┬──────────┘
               │  src/data/parse_*.py   (JSON/CSV -> tidy tables, typed, 1 row = 1 thing)
        ┌──────▼──────────┐
        │ data/interim/   │  tidy but not yet feature-engineered. Reproducible.
        └──────┬──────────┘
               │  src/features/*.py   (per-90 rates, rolling form, xG features, ...)
        ┌──────▼──────────┐
        │ data/processed/ │  model-ready / analytics-ready tables (Parquet).
        └──────┬──────────┘
               │
     ┌─────────┼─────────────┬──────────────┐
     ▼         ▼             ▼              ▼
 analytics   ML models   DL models    visualization
 (src/analytics) (src/models)         (src/visualization)
```

### Stage responsibilities

| Stage | Input | Output | Rule |
|---|---|---|---|
| **Ingest** | remote | `data/raw/` | Never transforms. Records source URL + fetch time in a small manifest. Re-runnable without re-downloading. |
| **Validate** | `data/raw/` | pass/fail + report | Cheap, strict, first line of defence against silent corruption. |
| **Parse** | `data/raw/` | `data/interim/` | Flatten nested JSON, fix types, one tidy row per event / match / player-match. No business logic, no aggregation. |
| **Feature engineering** | `data/interim/` | `data/processed/` | All derived quantities. Must be **time-aware** (no future info). Documented. |
| **Analytics / models / viz** | `data/processed/` | figures, tables, model artefacts | Consume processed data only; never reach back to raw. |

## 2. What is stored where, and why

### Raw — keep as files, immutable, git-ignored

- StatsBomb JSON, football-data CSVs, FBref HTML/CSV.
- **Why files, not a DB:** raw data is write-once/read-rarely, the vendor format
  *is* the schema, and re-downloading is the recovery path. A database here would
  add work with no benefit.

### Interim — Parquet files

- Tidy `events`, `matches`, `players`, `lineups`, `three_sixty`.
- **Why Parquet:** columnar, typed, compressed, fast partial reads, native to
  pandas/polars/duckdb. CSV would lose types and be slow; JSON would stay nested.
- Partitioned by `competition_id / season_id` so we can load one slice.

### Processed — Parquet files (+ DuckDB view layer later)

- `shot_features`, `player_match_stats`, `player_season_profiles`,
  `team_match_form`, `match_prediction_dataset`, etc.
- **Why still files for the MVP:** one or two competitions is millions of event
  rows at most — Parquet + pandas/polars handles this on a laptop. A server DB
  would be premature.
- **When a database earns its place (Phase 2+):** when we have many
  competitions, need ad-hoc cross-table queries, or serve an API.
  - First choice: **DuckDB** — an embedded analytical DB that queries Parquet
    files directly, no server, SQL. Gets us indexing and joins with near-zero
    ops cost.
  - **PostgreSQL** only if/when we have a live API with concurrent writes,
    users, or need it as a service. Logged as a future decision, not now.

### Features / model artefacts

- Model files (`.pkl`, `.pt`) → `models/`, git-ignored, later a registry.
- Metrics/params → experiment tracker (MLflow local dir) from Phase 2.
- **Why not commit models:** large binaries, and they are reproducible from
  code + data + config + seed.

### Caching

- Only introduced when a *measured* recompute is painful (e.g. re-deriving all
  passing networks for a dashboard request). Likely a simple on-disk cache
  (`joblib.Memory` or parquet snapshots) before anything like Redis.

## 3. Entity resolution

The integration problem (from [data_dictionary.md](data_dictionary.md#cross-source-key-map-for-entity-resolution)):
**no shared IDs across sources.** Team "Manchester United" may appear as
`Man United`, `Manchester Utd`, `Man Utd`.

### Approach (build in Phase 2, when a second source arrives)

1. **Canonical registry.** One table per entity type
   (`configs/entities/teams.yaml`, `players.yaml`) mapping a canonical id/name to
   every known alias per source:
   ```yaml
   - canonical_id: t_man_utd
     canonical_name: Manchester United
     aliases:
       statsbomb: ["Manchester United"]
       football_data: ["Man United"]
       fbref: ["Manchester Utd"]
   ```
2. **Deterministic first.** Exact match on normalised strings (lowercase, strip
   accents, remove `FC`/`CF`/`AFC`, collapse whitespace).
3. **Fuzzy assist.** For the remainder, `rapidfuzz` token-set ratio proposes
   matches; a human confirms and the alias is written back to the YAML.
4. **Match-level join key:** `(competition, season, date, home_canonical,
   away_canonical)`. Allow date ±1 day for timezone differences.
5. **Never silently merge.** Unmatched rows go to a `unresolved/` report, not
   into the joined dataset.

**Why YAML + human confirmation, not pure fuzzy matching:** football has real
ambiguity (multiple "Arsenal", parent vs reserve teams, national vs club). A
reviewed registry is auditable and stable; pure fuzzy matching silently
mislabels and is unreproducible.

## 4. Project folder structure

```text
football-ai/
├── README.md
├── .gitignore
├── docs/                     design & research (this phase). Prose, not code.
│   ├── project_vision.md
│   ├── requirements.md
│   ├── dataset_research.md
│   ├── dataset_comparison.md
│   ├── data_dictionary.md
│   ├── architecture.md
│   ├── ml_strategy.md
│   ├── dl_strategy.md
│   ├── cv_strategy.md
│   ├── evaluation_strategy.md
│   └── decisions.md
│
├── data/                     DATA, never code. Contents git-ignored.
│   ├── raw/        immutable downloads (+ a manifest of source/date)
│   ├── interim/    tidy, typed, not yet feature-engineered
│   ├── processed/  analytics-ready / model-ready Parquet
│   └── external/   third-party reference tables (entity maps, lookups) that ARE
│                   small and MAY be committed if licensing allows
│
├── notebooks/                exploration & explanation. Named NN_topic.ipynb.
│                             Throwaway thinking; NOT imported by src/.
│
├── src/                      importable library code. Pure functions where possible.
│   ├── data/        ingest, validate, parse   (sources -> interim)
│   ├── features/    feature engineering        (interim -> processed)
│   ├── analytics/   descriptive/comparative: xG, passing nets, style, similarity
│   ├── models/      ML/DL: training, inference, model classes
│   ├── evaluation/  metrics, calibration, backtesting, split logic
│   └── visualization/  pitch plots, radars, shot maps, network plots
│
├── tests/                    pytest. Mirrors src/. Data-shape + logic tests.
│
├── configs/                  YAML. Run configs, model hyperparams, entity maps.
│                             NO secrets (those go in .env, git-ignored).
│
└── scripts/                  thin CLI entry points. Parse args, call into src/.
                              e.g. scripts/ingest_statsbomb.py, scripts/build_features.py
```

### What belongs where — and what does NOT

| Folder | Belongs | Does NOT belong |
|---|---|---|
| `docs/` | Markdown design/research/decisions | code, data, images that are outputs |
| `data/` | data files only | scripts, notebooks, code |
| `notebooks/` | exploration, narrative, one-off analysis | reusable functions (promote those to `src/`), pipeline steps |
| `src/` | tested, importable, reusable logic | argument parsing / file paths hardcoded, print-driven scripts, notebook cruft |
| `tests/` | pytest tests | fixtures larger than a few KB (generate them) |
| `configs/` | YAML config, hyperparameters, entity maps | secrets, API keys, large data |
| `scripts/` | thin entry points (`argparse` → `src`) | business logic (belongs in `src/`) |

**The `src/` ↔ `notebooks/` rule:** if a piece of code is used twice or is part
of the pipeline, it moves to `src/` with a test. Notebooks import from `src/`,
never the reverse.

### Deviations from the owner's proposed structure

- Added `docs/evaluation_strategy.md` (evaluation philosophy deserves its own
  file — it is where beginner projects go wrong).
- `data/external/` clarified as "small committable reference tables", distinct
  from `raw/` third-party *bulk* data.
- Kept everything else as proposed. `src/` split matches the pipeline stages so a
  reader can map a folder to a diagram box.

## 5. Scalability posture

Current scale (MVP): 1–2 competitions ≈ up to ~10 million event rows ≈ hundreds
of MB of Parquet. **A laptop handles this.** So:

| Technique | Adopt now? | Trigger to adopt |
|---|---|---|
| Partitioned Parquet by comp/season | **Yes** (costs nothing, helps immediately) | — |
| DuckDB SQL layer over Parquet | Phase 2 | many competitions / ad-hoc cross-comp queries |
| Postgres | Later | live API with concurrent users/writes |
| Batch/parallel processing (`joblib`, `multiprocessing`) | When a step exceeds ~a few minutes | measured slow step |
| Incremental / delta ingestion | Phase 2 | re-downloading everything gets slow |
| Caching layer | When a repeated recompute is measurably painful | dashboard latency |
| Async API | When endpoints do slow I/O and get concurrent traffic | real usage |
| Docker | Phase 3 (before any deployment) | need reproducible deploy env |
| Horizontal scaling / queues / Kubernetes | Not planned | genuine production load (unlikely for this project) |

**Principle:** design so that *"add a league"* is changing a config entry and
re-running a pipeline, not a rewrite. Implement heavy machinery only against a
measured bottleneck.
