# Decision Log (ADR)

Every important architectural / methodological decision is recorded here, newest
last. Format:

```text
### NNNN — Title
Date:
Status:      proposed | accepted | superseded by NNNN | rejected
Decision:
Why:
Alternatives considered:
Why alternatives were rejected:
Consequences:
```

Nothing in this log is "just an opinion" — if we revisit it, we add a new entry
that supersedes the old one. We never silently edit a past decision.

---

### 0001 — Build in phases; keep the MVP tiny
Date: 2026-08-27
Status: accepted
Decision: Ship an MVP limited to StatsBomb + 1–2 competitions + a small fixed set
of analytics and one honest match-prediction model. Everything else is Phase 2+.
Why: The owner is learning and must be able to explain every line. A large
surface area now = shallow understanding and unexplainable code.
Alternatives: (a) Build the full platform from the roadmap. (b) Start with match
prediction only, like most beginner projects.
Why rejected: (a) unmanageable, unexplainable, high abandonment risk. (b) misses
the point — the descriptive/scouting layer is the actual product and the better
learning.
Consequences: Slower visible progress; much stronger understanding; roadmap items
must earn their way in via requirements.md.

---

### 0002 — StatsBomb Open Data is the primary dataset
Date: 2026-08-27
Status: accepted
Decision: Core analytics built on StatsBomb Open Data.
Why: Only free source with true event-level detail (locations, outcomes,
qualifiers, shot freeze-frames, own xG for benchmarking). Enables xG, passing
networks, player profiles, style, similarity, clustering.
Alternatives: Wyscout public dataset (CC-BY); understat scrape; FBref; paid data.
Why rejected: Wyscout is less rich (no freeze frames) — kept as commercial-safe
fallback (0004). understat has no license and is a scrape. FBref lost advanced
data in Jan 2026 (0005). Paid data is out of budget/scope.
Consequences: Project is **non-commercial** (StatsBomb license). Attribution
"Data provided by StatsBomb" required on all outputs. Coverage is
competition-by-competition, so match prediction needs a secondary source (0003).

---

### 0003 — football-data.co.uk as secondary source for match prediction
Date: 2026-08-27
Status: accepted
Decision: Use football-data.co.uk CSVs for long-history match results + pre-match
bookmaker odds.
Why: StatsBomb has no continuous league history; match prediction needs many
seasons of results, and the odds give us the baseline every honest match model
must be compared against.
Alternatives: Kaggle European Soccer DB (ends 2016); scraping results; football
APIs (rate-limited free tiers).
Why rejected: Kaggle set is stale; scraping/APIs add fragility for data that
football-data.co.uk already packages cleanly.
Consequences: Need entity resolution between StatsBomb and football-data.co.uk
team names (0006). Odds columns are the evaluation baseline. Must guard against
using football-data's post-match stat columns as pre-match features.

---

### 0004 — Keep Wyscout public dataset as a documented fallback, do not ingest now
Date: 2026-08-27
Status: accepted
Decision: Record the Wyscout CC-BY event dataset as the path to a commercial
version of the project; do not download or integrate it in the MVP.
Why: CC-BY allows commercial use; if the project ever needs that, the event core
swaps to Wyscout. But integrating a second event schema now adds cost with no
MVP benefit.
Alternatives: Start on Wyscout instead of StatsBomb.
Why rejected: StatsBomb is richer and better documented for learning; commercial
use is not a current requirement.
Consequences: If a commercial pivot happens, expect rework in src/data parsing
and the data dictionary.

---

### 0005 — Treat FBref as basic/historical only (post-Jan-2026 Opta removal)
Date: 2026-08-27
Status: accepted
Decision: Do not build any feature that depends on FBref advanced metrics. Use
FBref only for basic season stats, squad minutes, and historical context, via
polite rate-limited scraping.
Why: In January 2026, StatsPerform/Opta terminated Sports Reference's data feed;
advanced stats (xG, progressive actions, pressures, SCA/GCA) were removed from
FBref/Stathead and are no longer updated. Basic historical data remains.
Alternatives: Depend on FBref advanced data (as many tutorials do); use another
scraped aggregate source.
Why rejected: The advanced data is gone/frozen — building on it is building on
sand. We compute our own advanced aggregates from StatsBomb events where
competitions overlap.
Consequences: Some "player comparison" richness must come from our own
StatsBomb-derived metrics, limited to covered competitions.

---

### 0006 — Entity resolution via a reviewed YAML registry, not pure fuzzy matching
Date: 2026-08-27
Status: accepted
Decision: Cross-source joins use a human-reviewed alias registry
(configs/entities/*.yaml); deterministic normalised matching first, rapidfuzz
only to *propose* new aliases for human confirmation.
Why: No shared IDs across sources; football names are genuinely ambiguous
(reserve teams, multiple "Arsenal", nationalities). A reviewed registry is
auditable, stable, reproducible.
Alternatives: Pure fuzzy string matching at join time; ML entity-matching model.
Why rejected: Fuzzy-at-join-time silently mislabels and changes run to run; an ML
matcher is overkill for a few hundred teams.
Consequences: Small manual curation step when adding a competition/source.
Unmatched rows are reported, never force-merged.

---

### 0007 — Files (Parquet) for storage in the MVP; DuckDB later; Postgres only if a live API needs it
Date: 2026-08-27
Status: accepted
Decision: Store interim/processed data as partitioned Parquet. Introduce DuckDB
(embedded SQL over Parquet) in Phase 2 if cross-competition querying gets
painful. PostgreSQL only when there is a live API with concurrent users/writes.
Why: MVP scale (1–2 competitions) fits in memory / on a laptop. A DB server now =
ops overhead, no benefit.
Alternatives: Start with Postgres/SQLite; use CSV.
Why rejected: Postgres premature; CSV loses types and is slow; SQLite has no
columnar advantage for analytics.
Consequences: Need a documented run order for the file pipeline. Migration to
DuckDB/Postgres is a later decision with its own entry.

---

### 0008 — Strict temporal splits; no random shuffling for any time-dependent model
Date: 2026-08-27
Status: accepted
Decision: Match prediction and player-performance models use time-ordered
train/validation/test by season; time-series CV within training; all
scalers/encoders fit on training folds only.
Why: Football is a time series. Random splits leak the future and inflate every
metric, producing models that fail at the only task that matters.
Alternatives: `train_test_split(shuffle=True)`, k-fold CV.
Why rejected: They produce dishonest, non-reproducible-in-practice results.
Consequences: Reported numbers will be lower and honest. Pipeline code must carry
a "prediction time" concept for every feature.

---

### 0009 — Deep learning is opt-in, gated behind beating a classical baseline
Date: 2026-08-27
Status: accepted
Decision: No DL component ships unless it beats a tuned classical baseline on a
temporal test set by more than noise, and we can explain the architecture. CV is
the sole exception (no classical alternative). See dl_strategy.md.
Why: Football's tabular problems are won by gradient boosting; DL on small,
noisy data overfits and is hard to calibrate/explain.
Alternatives: Use DL broadly (common in portfolio projects).
Why rejected: Complexity without justified benefit violates the project's core
principle.
Consequences: Some roadmap DL items may end as documented negative results —
which we treat as valid deliverables.

---

### 0010 — Computer vision is Phase 4, pretrained-only, scoped to a few clips
Date: 2026-08-27
Status: accepted
Decision: No CV work until the event-analytics core exists. When it starts: use
pretrained detection/tracking models, prototype tactical metrics on Metrica
sample tracking data first, use SoccerNet only for a small CV demo. No
from-scratch training, no real-time.
Why: CV is expensive (GPU, storage, time) and disconnected from our event data
(different matches). High learning value but low priority vs the core product.
Alternatives: Make CV a headline feature; train custom models.
Why rejected: Would consume the schedule before the core exists; SoccerNet is
NDA-gated and hundreds of GB.
Consequences: CV results will be standalone demos, not fused with event
analytics.

---

### 0011 — Added docs/evaluation_strategy.md to the doc set
Date: 2026-08-27
Status: accepted
Decision: Split evaluation philosophy into its own document rather than a section
of ml_strategy.md.
Why: Evaluation is where beginner football-ML projects most often go wrong; it
deserves prominence and applies across ML, DL, and analytics.
Alternatives: Keep it inside ml_strategy.md.
Why rejected: It would be under-weighted and harder to find.
Consequences: One more file to keep in sync; cross-linked from ml_strategy.md.

---

### 0012 — Owner scope choices (2026-08-27)
Date: 2026-08-27
Status: accepted
Decision: Non-commercial project (→ 0002 stands, StatsBomb primary). Men's
football only. Commit notebook outputs to git.
Consequences: `.gitignore` keeps notebook outputs (already does). Entity
resolution stays single-gender. StatsBomb license attribution required on
outputs.

---

### 0013 — Competition selection vs StatsBomb reality
Date: 2026-08-27
Status: accepted
Decision: Owner asked for Premier League + Indian Super League + La Liga + "some
European big leagues". Adjusted to what the data actually supports:
- **Event-analytics core (StatsBomb):** La Liga 2004/05–2020/21 (deep, primary
  for player analytics; 360 for 2020/21) + Indian Super League 2021/22 + Premier
  League 2015/16 + one season each of 1. Bundesliga / Ligue 1 / Serie A.
- **Match-prediction training (football-data.co.uk):** Premier League, La Liga,
  Bundesliga, Serie A, Ligue 1 — full continuous history (1990s→now).
Why: StatsBomb Open Data's **Premier League coverage is only 2015/16 and
2003/04**, and ISL is only 2021/22 — there is no continuous multi-season PL/ISL
event data available for free. La Liga is the only deeply-covered league.
Alternatives: Insist on multi-season PL event data (would require paid data or
scraping understat/Opta — rejected: cost/license); drop PL/ISL entirely.
Why rejected: Owner wants those leagues represented; single-season snapshots + a
deep La Liga spine + football-data.co.uk history covers the realistic use cases.
Consequences:
- Player time-series / form models are viable mainly for **La Liga** (only league
  with many consecutive covered seasons).
- Cross-league player comparison mixes different seasons → needs era/League
  strength adjustment before similarity/clustering.
- **ISL is not in football-data.co.uk** → ISL match prediction would need a
  separate results source (deferred; flagged in requirements F16).
- Regenerate exact season/match lists from real `competitions.json` during EDA.

---

### 0014 — Why "last 5 seasons" is possible for match data but not for event data
Date: 2026-08-27
Status: accepted
Question from owner: "Why can't we take the last 5 Premier League seasons (and
the other leagues) instead of 2 fixed seasons?"

Decision: We split coverage by **data layer**, because the free/legal supply is
completely different for each:

| Layer | Powers | Free + legal supply | Last-5 PL seasons available free? |
|---|---|---|---|
| **Event data** (passes, carries, pressures, shot freeze-frames, locations) | passing networks, deep player style, tactical analysis, freeze-frame xG | StatsBomb Open Data — a **fixed, curated donation**, not a feed | **No.** PL = 2015/16 + 2003/04 only |
| **Shot data** (shot location + xG, no other events) | xG models, shot maps, finishing profiles | understat (scrape, **no licence**), top-5 leagues 2014/15→now | Yes, but licence-grey and shots only |
| **Match data** (result, goals, basic counts, pre-match odds) | match prediction, team form, odds baseline | football-data.co.uk — full history | **Yes**, 1993→now |
| **Season aggregates** (basic) | career/season context, squad minutes | FBref — 100+ comps, deep history (basic only post-Jan-2026) | Yes (basic only) |

**Why StatsBomb doesn't give recent PL events for free:** that exact data is
their commercial product (StatsBomb IQ). The open-data repo is a one-off goodwill
release — mostly La Liga (the Messi years), World Cups, women's football, and a
handful of single league-seasons. It is not a rolling feed and will not grow to
cover recent PL. We cannot change that.

**What we can do for "last 5 seasons" of PL / La Liga / Bundesliga / Serie A /
Ligue 1:**
- Match prediction + team form + odds baseline → football-data.co.uk, all five
  leagues, last 5+ seasons. **Yes, do this** (already SECONDARY in the stack).
- Recent xG / shot analysis / finishing profiles → understat scrape. **Optional,
  owner must accept the licence grey area** (cache only, never redistribute,
  polite rate limit). Tracked as P7 below.
- Full event-level tactical analysis for recent PL → only via **paid data**
  (StatsBomb IQ / Opta / Wyscout, thousands of £/yr). **Out of scope** (0002).

Alternatives considered:
- Pay for a data licence — rejected: cost, and non-commercial project.
- Scrape WhoScored / Opta-backed sites for full events — rejected: direct ToS
  violation and redistribution risk; brittle.
- Drop the deep-analytics ambition and do match prediction only — rejected:
  that's the generic beginner project we explicitly aren't building (see
  project_vision.md §C).

Consequences:
- **La Liga stays the event-analytics spine** — it is the only league where free
  event data covers many consecutive recent-ish seasons (2004/05–2020/21).
- Premier League / Bundesliga / Serie A / Ligue 1 get: 1 StatsBomb event-season
  each (a "deep dive" sample) **plus** full football-data.co.uk history for
  prediction/form. That is the realistic meaning of "include these leagues".
- If owner approves understat (P7), recent PL/other-league xG and shot maps
  become possible; passing networks and pressing metrics still will not.

---

### 0015 — Additional free sources for recent seasons (research follow-up)
Date: 2026-08-27
Status: accepted
Trigger: owner asked to search for other free sources covering seasons StatsBomb
Open Data lacks. Full findings in
[dataset_research.md §6](dataset_research.md#6-options-for-recent-season-data--closing-the-pl--la-liga-2021-gap).

Decision — add to the stack:
- **StatsBomb Open Data recent men's league-seasons** we had under-counted:
  **1. Bundesliga 2023/24 (+360)** and **Ligue 1 2021/22 & 2022/23 (+360)**.
  Ingest these — they give recent European big-league event + tracking data for
  free with a clean licence. (Updates 0013's competition list.)
- **ClubElo** — official CSV/HTTP endpoint, free non-commercial + attribution.
  Use as the team-strength feature for match prediction instead of hand-rolling
  Elo.
- **openfootball / football.db** — CC0 (public domain). Results/fixtures backup.
- **Fantasy Premier League API** — free, no auth. Adopt for a **PL-specific
  player-form module** (rich per-gameweek per-player data; the only clean, current
  Premier League player dataset).
- **Kaggle "Club Football Match Data (2000–2025)"** — pre-joined
  football-data.co.uk + ClubElo, 42 leagues, refreshed monthly. Use as a
  convenience input for the match-prediction dataset (verify freshness per use).

Decision — do NOT adopt:
- **WhoScored scraping** — it is the only free route to recent *full* event data
  (passes, carries, etc. via Opta), but its ToS explicitly forbid scraping and
  the data is Opta-licensed. Too risky for a public portfolio project. Recorded
  as a known option we are deliberately declining.
- **Sofascore / FBref match-log scraping** — optional, low priority; not core.

Consequences:
- "Recent European big-league" event analytics is now partly covered free & clean
  (Germany, France via StatsBomb 360).
- Recent **Premier League** deep analytics still limited to: FPL form data +
  results/Elo, or understat shots (P7, grey). Recent **La Liga** deep analytics:
  understat shots (P7) or wait.
- New optional dependency surface: `soccerdata` (for ClubElo/understat),
  the FPL JSON API. Each justified when first used.

---

### 0016 — Adopt understat (shot + xG data) with a responsible-collection contract
Date: 2026-08-27
Status: accepted
Decision: understat shot-level data (x/y, xG, situation, body part, minute) +
per-match xG/PPDA + player/team aggregates is adopted as a **secondary source**
for recent-season shot analysis (Premier League and La Liga first; other Big-5
optional). It fills the gap that StatsBomb Open Data leaves for recent PL / La
Liga. It provides **shots only** — no passes, carries, or pressures.

Why now: owner approved (was pending decision P7). It is the only realistic way
to get recent Premier League / La Liga event-type data without a paid licence or
the WhoScored ToS violation we declined in 0015.

**Responsible-collection contract (binding — the scraper MUST follow all of
these):**

1. **History from the mirror, not the site.** Backfill seasons 2014/15 →
   last-completed season from the **Kaggle understat mirror**
   (`codytipton/understat-data` or equivalent). Only hit understat.com directly
   for the **current, still-changing season**. Completed seasons are immutable —
   fetch once, ever.
2. **One request at a time.** No concurrency, no thread pools. Minimum **3
   seconds** between requests (`time.sleep`), jittered.
3. **Cache-first, immutable raw store.** Every response written verbatim to
   `data/raw/understat/` (git-ignored) with a manifest row `(url, utc_timestamp,
   http_status, sha256)`. Re-runs read cache; a URL is fetched **at most once**
   unless it is the live season.
4. **Honest identification.** Real `User-Agent` naming the project + a contact
   URL/email. No rotating fake browser strings, no proxies to evade blocks.
5. **Fetch only the agreed scope.** A config list of `(league, season)` pairs.
   Never crawl the whole site or follow arbitrary links.
6. **Back off and stop.** Exponential backoff on 429/5xx; after 3 consecutive
   failures, abort the run and log — do not hammer.
7. **robots.txt respected.** Check it in code; if it disallows a path, we do not
   fetch that path.
8. **Off-peak bulk runs.** Any large backfill scheduled for low-traffic hours.
9. **No redistribution of raw data.** `.gitignore` already blocks it. We publish
   only derived models / aggregated figures, and only where compatible.
10. **Attribution.** "Shot data via understat" (and Opta as the ultimate source)
    on any output that uses it.

Prefer implementing via the `soccerdata` library's `Understat` reader (it already
caches locally and is maintained) over a hand-rolled scraper, unless it proves
inflexible. Decide at implementation time; either way the contract above holds.

Alternatives considered: hand-rolled `requests` + BeautifulSoup (more control,
more ways to be a bad citizen); `understatapi` package (thin, less caching);
WhoScored (richer but ToS-forbidden, 0015); do nothing (leave recent PL/La Liga
uncovered).

Consequences:
- Recent PL / La Liga get: xG models, shot maps, finishing/over-performance
  profiles, chance-quality team metrics. **Not** passing networks or pressing.
- New optional dependency: `soccerdata` (and/or `beautifulsoup4`), justified when
  first imported.
- A small `data/raw/understat/manifest.csv` becomes part of data lineage.
- If understat blocks us despite the contract, we stop and fall back to the
  Kaggle mirror only.

---

### 0017 — Defer Indian Super League
Date: 2026-08-27
Status: accepted
Decision: Drop ISL from the active scope. The StatsBomb ISL 2021/22 event season
is **not** ingested for now; no ISL match-prediction source is pursued.
Why: owner decision. ISL is a single isolated event-season with no continuous
results/odds source (football-data.co.uk excludes India), so it adds
integration + entity-resolution work for little analytical payoff at this stage.
Supersedes the ISL parts of 0013; removes pending decision P6.
Consequences: competition set is now La Liga (spine) + Premier League 2015/16 +
Bundesliga (2015/16 and/or 2023/24) + Ligue 1 2021/22 & 2022/23, plus
football-data.co.uk / ClubElo / FPL for recent seasons, plus understat shots
(0016). ISL can be revisited later as a self-contained mini-study.

---

## Pending decisions (to resolve with the owner)

- **P3 (partly open)** — Exact La Liga season range to ingest first (all
  2004/05–2020/21, or a recent subset e.g. 2015/16–2020/21 to start smaller?).
- **P5** — Experiment tracking tool when the time comes: MLflow (local, simple)
  vs Weights & Biases (hosted, nicer UI, account needed).

Resolved: **P6** deferred → 0017 (ISL dropped for now). **P7** approved → 0016
(understat adopted with a responsible-collection contract).
