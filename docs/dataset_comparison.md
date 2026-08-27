# Dataset Comparison & Recommended Stack

Companion to [dataset_research.md](dataset_research.md). This file is the
**decision-support summary**: what each dataset can do, side by side, then the
recommended stack and the reasoning.

## Capability matrix

Legend: ●● strong · ● usable · ○ weak / indirect · — not supported

| Dataset | Match prediction | Player analytics | Scouting / similarity | Tactical (passing, shape) | Computer Vision | Time-series form | Data quality | License friction |
|---|---|---|---|---|---|---|---|---|
| **StatsBomb Open Data** | ● (tournament-scale only) | ●● | ●● (within covered comps) | ●● | — | ○ (coverage gaps) | ●● | Non-commercial + attribution |
| **Wyscout public (CC-BY)** | ● | ●● | ●● | ● (no freeze frames) | — | ○ | ● | **Low (CC-BY)** |
| **football-data.co.uk** | ●● (long history + odds) | — | — | — | — | ● (team form) | ● | Informal / low |
| **FBref (post-2026)** | ● (basic results) | ● (basic only) | ● (basic only) | — | — | ● (season basic) | ● | Scrape, rate-limited, no advanced |
| **understat (scrape)** | ● | ● (shots/xG) | ○ | ○ | — | ● (shot history) | ● | No license (scrape) |
| **SoccerNet** | — | — | — | ○ (from CV output) | ●● | — | ●● | NDA, non-commercial, large |
| **Metrica / SkillCorner / IDSSE** | — | ○ | ○ | ●● (tracking) | ○ | — | ●● | Research; very few matches |
| **Kaggle European Soccer DB** | ● (2008–2016) | ○ | ○ | — | — | ● | ○–● | Open but stale |
| **FPL API** | ○ | ● (PL only, fantasy pts) | ○ | — | — | ●● (weekly) | ● | Public |

### Reasoning behind the matrix

**StatsBomb** — the only *free* source with true event-level detail (locations,
outcomes, qualifiers, shot freeze-frames, and its own xG for benchmarking). This
makes it unbeatable for **xG, passing networks, player profiles, and team style**.
Its weakness is that coverage is a set of competitions, not a continuous league
history, so it is a **poor large training set for match prediction** and only
**okay for time-series** (a given player rarely appears across many consecutive
covered seasons).

**Wyscout public dataset** — almost as good as StatsBomb for aggregate player and
team analytics, covers the **2017/18 top-5 leagues + Euro 2016 + WC 2018** in one
consistent drop, and is **CC-BY (commercial use allowed)**. It lacks shot
freeze-frames and 360-style context. We hold it as the **commercial-safe fallback
core** and as an extra source of leagues.

**football-data.co.uk** — no player or event data at all, but it is the
**cleanest long history of match results plus pre-match bookmaker odds**. For
match prediction this is the right training set, and the odds give us the
**baseline every honest match-prediction project must beat**.

**FBref** — after the January 2026 Opta removal it only reliably provides
**basic** season stats and deep history. Useful for context, squad/minutes data,
and older seasons; **not** for advanced metrics. We will prefer computing our own
aggregates from StatsBomb events where competitions overlap.

**understat** — fills StatsBomb's biggest gap (continuous shot-level xG for the
top-5 leagues since 2014) but has **no license** and is a scrape. Optional,
cache-only, never redistributed. Only adopt if a feature genuinely needs
continuous shot history.

**SoccerNet** — the serious CV dataset, but **NDA-gated, non-commercial, and
hundreds of GB**. Strictly a Phase 4 research spike. Not aligned with our
StatsBomb competitions, so CV output and event analytics stay in separate worlds
for now.

**Metrica / SkillCorner / IDSSE** — 3–10 matches each of synced tracking+events.
Too small to model on, but the **best way to learn tracking-data methods**
(pitch control, off-ball runs) before committing to SoccerNet.

**Kaggle European Soccer DB / FIFA ratings** — convenient, but stale (2016) or
attribute-only. Low priority; possible extra match-prediction data or
similarity sanity check.

**FPL API** — clean, live, free, but Premier-League-only and fantasy-scoped.
Perfect for an optional standalone module, not the core.

## Recommended dataset stack

```text
PRIMARY:     StatsBomb Open Data
             - core of the analytics layer
             - powers: xG, passing networks, player profiles, team style,
               player similarity/clustering, tactical analysis
             - start with 1-2 competitions (e.g. FIFA World Cup 2022  +  a
               stack of La Liga seasons), expand later

SECONDARY:   football-data.co.uk        (match results + bookmaker odds history)
             - powers: match outcome prediction with a long temporal history
             - provides the odds-implied baseline for honest evaluation

             FBref (basic/historical only)
             - powers: historical context, squad minutes, older seasons
             - DO NOT depend on advanced (Opta) columns - removed Jan 2026

             understat (shot + xG, recent PL & La Liga)   [ADOPTED - decisions.md #0016]
             - powers: recent-season xG models, shot maps, finishing profiles
             - SHOTS ONLY - no passes/carries/pressures
             - collected under a binding responsible-collection contract:
               Kaggle mirror for completed seasons, direct fetch only for the
               live season, >=3s/request, immutable cache + manifest, honest UA

ADD (free, clean licence - see decisions.md #0015):
             StatsBomb recent seasons        - Bundesliga 2023/24 (+360),
                                               Ligue 1 2021/22 & 2022/23 (+360)
             ClubElo                         - team-strength feature for match
                                               prediction (official endpoint)
             openfootball / football.db      - CC0 results/fixtures backup
             FPL API                         - recent Premier League player-form
                                               module (only clean current PL data)
             Kaggle "Club Football Match
             Data 2000-2025"                 - pre-joined football-data + ClubElo

OPTIONAL:    Wyscout public dataset (CC-BY)  - commercial-safe event fallback,
                                               extra leagues (2017/18)
             transfermarkt mirror (Kaggle)   - market value / age / injuries for
                                               scouting metadata (Phase 2)
             Kaggle European Soccer DB       - extra 2008-2016 match-prediction data

DECLINED:    WhoScored scraping              - only free route to recent FULL
                                               event data, but ToS forbid it and
                                               data is Opta-licensed (#0015)

CV (Phase 4): SoccerNet          - detection, tracking, calibration, action spotting
             Metrica sample data - learn tracking analytics on 3 clean matches
             SkillCorner opendata - broadcast-tracking prototyping (~10 matches)
```

### Why this stack (short form)

- **One rich primary** keeps the analytics layer coherent and deeply
  understandable, instead of spreading thin across many half-integrated sources.
- **football-data.co.uk** is added *only* because StatsBomb cannot give a long
  match-prediction history — a real requirement gap, not novelty.
- **FBref** is kept minimal and clearly bounded because its advanced data is gone.
- Everything else is **optional and gated behind a specific need**, satisfying the
  "no dataset without justification" rule.
- CV data is quarantined to Phase 4 so we do not sink weeks into GPU work before
  the core exists.

### What we will NOT do

- Not download SoccerNet now.
- Not scrape FBref until a feature demands it. understat **is** adopted (#0016)
  but only via the responsible-collection contract (mirror-first, cache-first,
  ≥3s/request).
- Not scrape WhoScored at all (#0015 — ToS forbids it).
- Not merge StatsBomb and football-data.co.uk into one table blindly — they join
  only at the (competition, season, date, home, away) level and need entity
  resolution (see [architecture.md](architecture.md#entity-resolution) and
  [data_dictionary.md](data_dictionary.md)).

## Resolved with the project owner (2026-08-27)

1. **Non-commercial** — confirmed. StatsBomb stays primary.
2. **Men's football only** — confirmed.
3. **Competitions** — owner requested Premier League + Indian Super League +
   La Liga + European big leagues. Final plan after reality-check + follow-ups
   ([decisions.md #0013, #0015, #0016, #0017](decisions.md)):

   | League | StatsBomb event data | Recent-season data | Plan |
   |---|---|---|---|
   | La Liga | **2004/05–2020/21** (deep) + 360 for 2020/21 | understat shots 2021→now; ClubElo; football-data.co.uk | **Spine of player analytics** |
   | Premier League | only **2015/16** | FPL API (player form); understat shots; ClubElo; football-data.co.uk | 2015/16 event deep-dive + recent via understat/FPL |
   | Bundesliga | 2015/16 **and 2023/24 (+360)** | football-data.co.uk; ClubElo | ingest both seasons |
   | Ligue 1 | **2021/22 & 2022/23 (+360)** | football-data.co.uk; ClubElo | ingest both |
   | Serie A | 2015/16 | football-data.co.uk; ClubElo | optional single-season |
   | **Indian Super League** | 2021/22 only | none (football-data.co.uk excludes India) | **DROPPED for now (#0017)** |

   Match prediction across PL / La Liga / Bundesliga / Serie A / Ligue 1 →
   football-data.co.uk + ClubElo, full continuous history.
