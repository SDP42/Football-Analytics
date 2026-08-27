# AI-Powered Football Intelligence & Tactical Analytics Platform

> **Status:** Phase 0 — Research & Architecture. No models trained yet. No app yet.
> This repository currently contains **analysis and design documents only**.

## What this project is

An end-to-end football (soccer) analytics system built for **learning by building**.
It combines Data Science, classical Machine Learning, Deep Learning, and (later)
Computer Vision on top of **publicly available, properly-licensed** football data.

The immediate goal is not code volume. It is to build something we can fully
explain: *what each part does, why it exists, what alternatives we rejected, and
what would break if we changed it.*

## Read the docs in this order

| # | File | What it answers |
|---|------|-----------------|
| 1 | [docs/project_vision.md](docs/project_vision.md) | The problem, the users, the "why" |
| 2 | [docs/requirements.md](docs/requirements.md) | Feature roadmap: MVP → Phase 2 → Advanced → Research |
| 3 | [docs/dataset_research.md](docs/dataset_research.md) | Every candidate dataset, license, coverage, limits |
| 4 | [docs/dataset_comparison.md](docs/dataset_comparison.md) | Side-by-side comparison + recommended dataset stack |
| 5 | [docs/data_dictionary.md](docs/data_dictionary.md) | Confirmed fields/entities (filled in after inspecting data) |
| 6 | [docs/architecture.md](docs/architecture.md) | Data pipeline, storage decisions, folder layout |
| 7 | [docs/ml_strategy.md](docs/ml_strategy.md) | ML problem formulations, models, leakage, splits |
| 8 | [docs/dl_strategy.md](docs/dl_strategy.md) | Where Deep Learning actually earns its place |
| 9 | [docs/cv_strategy.md](docs/cv_strategy.md) | Computer Vision plan (later phase) |
| 10 | [docs/evaluation_strategy.md](docs/evaluation_strategy.md) | Metrics and why each matters for football |
| 11 | [docs/decisions.md](docs/decisions.md) | Decision log (ADR style) — every important choice |

## Repository layout

See [docs/architecture.md](docs/architecture.md#project-folder-structure) for the
full explanation of every folder. Short version:

```
docs/        design & research documents (this phase)
data/        raw / interim / processed / external  (git-ignored contents)
notebooks/   exploration; throwaway thinking, not the source of truth
src/         importable library code (data, features, analytics, models, ...)
tests/       pytest tests for src/
configs/     YAML configs (no secrets)
scripts/     thin entry points that call into src/
```

## Data & licensing note

We only use datasets whose licenses permit our use. StatsBomb Open Data is our
planned primary source and requires attribution: **"Data provided by StatsBomb"**.
Full details and the current state of every source (including the **January 2026
removal of Opta advanced stats from FBref**) are in
[docs/dataset_research.md](docs/dataset_research.md).

## Setup

Not yet defined — no dependencies are installed at this stage on purpose. The
environment (`requirements.txt` / `pyproject.toml`) will be created when we write
the first real code, and every library added will be justified in
[docs/decisions.md](docs/decisions.md).
