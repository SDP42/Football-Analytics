# Dataset Research

> Last researched: **2026-08-27**. Licensing and availability change — re-verify
> before relying on anything here. Where a fact came from the web it is cited at
> the bottom.

## How to read this document

For each source we record: what it is, how to get it, the license (and whether
**commercial use** and **attribution** apply), format, coverage, granularity,
quality, and **what it can realistically support**. We then choose a small stack
in [dataset_comparison.md](dataset_comparison.md).

A dataset existing is **not** a reason to use it. We only adopt a source if it
powers a feature in [requirements.md](requirements.md) and we can legally and
practically use it.

---

## 1. StatsBomb Open Data  ★ planned PRIMARY

| Field | Value |
|---|---|
| Name | StatsBomb Open Data |
| Source | StatsBomb (now part of Hudl) |
| URL | https://github.com/statsbomb/open-data |
| Python access | `statsbombpy` library, or read the JSON directly, or via `kloppy` / `socceraction` |
| License | Custom "StatsBomb Open Data User Agreement" (`LICENSE.pdf` in the repo). Free for **public, non-commercial** research and education. **Attribution required**: "Data provided by StatsBomb" / "Powered by StatsBomb" + link, and use of their logo when publishing. Redistribution of the raw data is restricted — link to the repo instead. |
| Commercial use | **No** (not without a separate agreement) |
| Attribution | **Yes, mandatory** |
| Format | JSON files in a fixed folder structure: `competitions.json`, `matches/{comp}/{season}.json`, `events/{match}.json`, `lineups/{match}.json`, `three-sixty/{match}.json` |
| Size | Low-single-digit GB total (events are the bulk) |
| Matches | Hundreds of matches across the competitions below (exact count changes as they add data) |
| Seasons | Mix of modern and historic |
| Players / teams | Full lineups per match; player IDs are StatsBomb-internal |
| Event granularity | **Very high** — every on-ball event with `x,y` location (pitch is 120×80), timestamp, outcome, plus rich qualifiers (pass height, body part, shot technique, freeze-frame of players for shots, pressure, carry, etc.) |
| StatsBomb 360 | Broadcast-tracking-derived freeze frames (positions of all visible players at each event) for **selected competitions** — see below |
| Historical coverage | Deep for a few competitions (e.g. La Liga incl. many Messi seasons), shallow/one-off for others |
| Missing data | Older matches have fewer qualifiers; not all competitions have 360; some historic matches lack full detail |
| Data quality | High and consistent; this is a professional collection product |
| Update frequency | Irregular — StatsBomb adds competitions periodically (often around tournaments) |
| API availability | No REST API for open data; it's a Git repo. `statsbombpy` wraps file access. |
| Download method | `git clone` the repo (large), sparse-checkout a subset, or fetch individual raw JSON files over HTTPS |

### Competitions available (as of 2026-08-27)

**With StatsBomb 360 data:** FIFA World Cup 2022, UEFA Euro 2024 & 2020, UEFA
Women's Euro 2025 & 2022, Women's World Cup 2023, 1. Bundesliga 2023/24, La Liga
2020/21, Ligue 1 2022/23 & 2021/22, MLS 2023, Africa Cup of Nations 2023.

**Events only (no 360):** La Liga many seasons back to 2004/05 (plus 1973/74),
Premier League 2015/16 & 2003/04, Serie A 2015/16 & 1986/87, 1. Bundesliga
2015/16, Champions League many seasons (incl. several finals), FA Women's Super
League multiple seasons, NWSL, Liga F, Frauen/Serie A Women 2023/24, Copa America
2024, Copa del Rey (historic), Indian Super League 2021/22, Liga Profesional
(Argentina, historic), FIFA U20 World Cup 1979, plus the men's World Cups
2018 & 1958-era additions.

> **Action item:** after we clone, regenerate this list from the real
> `competitions.json` and put exact match counts in `data_dictionary.md`.

### What StatsBomb can support

| Task | Supported? | Why |
|---|---|---|
| Passing analysis / passing networks | **Yes, excellent** | Every pass has origin, destination, outcome, height, recipient |
| Shot analysis / xG | **Yes, excellent** | Shots include location, body part, technique, shot freeze-frame, and StatsBomb's own xG for comparison |
| Player performance profiles | **Yes** | Full event coverage → per-90 metrics for the covered competitions |
| Team performance / style | **Yes** | Possession, pressing, territory all derivable |
| Formations | **Partial** | Starting formation is in lineups; live shape only via 360 freeze frames / event positions |
| Player positioning / tactical analysis | **Partial → good with 360** | Event `x,y` gives on-ball position; 360 adds off-ball |
| Match outcome prediction | **Limited by volume** | Not a continuous league history; good for tournaments, weaker as a large training set |
| Time-series player form | **Limited** | Coverage is not continuous season-over-season for most players |
| Computer vision | **No** | No video; 360 is derived coordinates, not frames |

### Limitations

- Non-commercial license.
- Not a continuous historical feed → match-prediction training data is thin
  compared to a results-only dataset.
- Player/team IDs are StatsBomb-specific → cross-source joins need entity
  resolution.
- Coverage is competition-by-competition, not "all of league X forever".

---

## 2. FBref (Sports Reference)  — SECONDARY, but with a major 2026 caveat

| Field | Value |
|---|---|
| Name | FBref |
| Source | Sports Reference LLC |
| URL | https://fbref.com |
| License | No open-data license. Site terms + a **published bot policy**: hard limit of **≤ 10 requests per minute**; heavier traffic gets your IP blocked for up to a day. They **cannot offer bulk downloads** because most data was licensed from a third party. |
| Commercial use | Not granted; treat as "personal research, respect rate limits" |
| Attribution | Expected if you publish |
| Format | HTML tables (scrape); community wrappers: `soccerdata`, `worldfootballR` (R), `ScraperFC` |
| Coverage | Historically huge — 100+ competitions, deep history, **including women's football** and lower divisions |
| Granularity | **Season / match aggregate stats per player and team** (not event-level). Standard + (previously) advanced Opta metrics (xG, progressive passes, SCA/GCA, pressures, etc.) |

### ⚠️ January 2026 change — Opta advanced stats removed

In **January 2026**, StatsPerform/Opta **terminated Sports Reference's access**
to its data feeds (citing a terms violation) and required deletion of that data.
Result:

- **Advanced metrics** (xG, xAG, progressive carries/passes, SCA/GCA, pressures,
  possession-adjusted defensive stats, etc.) were **removed** from FBref and
  Stathead and are **no longer updated**.
- **Basic historical data remains** — Sports Reference says it will keep
  presenting deep historic basic stats for 100+ competitions (goals, assists,
  appearances, minutes, cards, basic shooting, standard team/league tables).
- This particularly hurt **women's football** data availability, which had few
  alternatives.

**Implication for us:** FBref is now useful for **basic** season/career stats and
historical context, **not** for current advanced analytics. We should not build a
feature that depends on FBref's advanced columns. For advanced season aggregates
we can compute our own from StatsBomb events (for covered competitions) rather
than rely on a scraped source.

### What FBref can support (post-2026)

| Task | Supported? |
|---|---|
| Season/career basic stats, player comparison (basic) | Yes |
| Long historical context, squad lists, minutes | Yes |
| Advanced metrics (xG, progressive, pressures) | **No longer** (frozen/removed) |
| Event-level anything | No (never did) |
| Match outcome features (team form from results) | Partial (basic results) |

### Limitations

- Scraping only, strict rate limit, fragile to layout changes.
- No license for redistribution — we store derived aggregates, not raw scrapes,
  and cache politely.
- Advanced data now unreliable/absent.

---

## 3. football-data.co.uk  — SECONDARY (match results & odds history)

| Field | Value |
|---|---|
| Name | Football-Data.co.uk historical results |
| URL | https://www.football-data.co.uk/data.php |
| License | Free to download and use; the site requests a link back if you republish. No explicit commercial restriction, but no formal open license either — treat as "free for research, attribute". |
| Commercial use | Not formally addressed; low-risk for research/portfolio use |
| Attribution | Requested (link back) |
| Format | CSV per league per season |
| Coverage | ~22 European leagues, **continuous since the 1990s** for the big ones (E0 = Premier League from 1993/94) |
| Granularity | **Match level**: date, teams, full-time & half-time score, result, shots, shots on target, corners, fouls, cards, referee, **and pre-match bookmaker odds** from many bookmakers |
| Quality | Good and widely used; occasional missing columns in older seasons; team-name spellings differ from other sources |

### What it can support

| Task | Supported? |
|---|---|
| Match outcome prediction (long training history) | **Yes — this is its main value** |
| Bookmaker-implied probabilities as a **baseline** to beat | **Yes** (important for honest evaluation) |
| Team form / rolling features | Yes |
| Player-level anything | **No** |
| Tactical / event analysis | No |

### Limitations

- No player data, no locations, no event detail.
- Team-name normalisation needed ("Man United" vs "Manchester United").
- Match "stats" columns (shots, corners) are basic and post-match — usable as
  *history* features, not as pre-match inputs for the same match (leakage).

---

## 4. SoccerNet  — EXPERIMENTAL / CV phase only

| Field | Value |
|---|---|
| Name | SoccerNet (v2 / v3 / SoccerNet-Tracking / -GSR / -Depth / others) |
| Source | Academic consortium (Silvio Giancola et al.) |
| URL | https://www.soccer-net.org , https://github.com/SoccerNet |
| License | **Research/non-commercial**. Access requires filling an **NDA / access form** to get the password for the download script (video rights are the constraint). |
| Commercial use | **No** |
| Attribution | Cite the papers |
| Format | Broadcast video clips + JSON annotations; download via their `SoccerNet` pip package + password |
| Coverage | ~**550 complete broadcast games** from major European leagues (2014–2017 era) + 12 single-camera games; many derived task sets |
| Granularity by task | Action spotting (timestamps of events), **ball action spotting** (12 classes), **tracking** (bounding boxes + IDs + jersey numbers on short clips), pitch localisation / camera calibration, player re-identification, game-state reconstruction, dense video captioning, monocular depth |
| Size | **Large** — hundreds of GB for full video; task subsets smaller |
| Quality | High, well-benchmarked, annual challenge |

### What SoccerNet can support

| Task | Supported? |
|---|---|
| Player detection / ball detection | Yes (tracking + v3 subsets) |
| Multi-object tracking | Yes (SoccerNet-Tracking) |
| Jersey number / team assignment | Yes (annotations included) |
| Pitch detection / camera calibration / homography | Yes (calibration subset) |
| Action spotting from video | Yes |
| Pose estimation | Not directly (would add a pose model on top) |
| Event/tabular analytics, xG, passing networks | No (different modality) |

### Limitations

- Access form / NDA required; **cannot be committed or redistributed**.
- Large storage + GPU needed for training.
- Broadcast (moving, zoomed) camera → homography is non-trivial.
- Older matches; not aligned to our StatsBomb competitions.

---

## 5. Other sources considered (and current verdict)

| Source | URL | License / access | Verdict |
|---|---|---|---|
| **Wyscout Match Event Dataset** (public research release) | figshare / PappalardoEtAl 2019 | CC-BY 4.0 (**commercial OK, attribution required**) | **Strong backup / secondary event source.** Events for 2017/18 top-5 leagues + World Cup 2018 + Euro 2016. Less rich than StatsBomb (no shot freeze-frames) but **big and permissively licensed.** Good if we ever need commercial-safe data or more leagues. |
| **Metrica Sports sample data** | github.com/metrica-sports/sample-data | Custom permissive (research) | 3 anonymised matches with **synced tracking + events**. Tiny but the cleanest way to *learn* tracking-data methods (pitch control, off-ball). Good Phase 3 teaching set. |
| **SkillCorner Open Data** | github.com/SkillCorner/opendata | CC-BY-NC (non-commercial) | ~10 broadcast-tracking matches (A-League 2024/25). Small; useful to prototype tracking analytics without SoccerNet's size. |
| **IDSSE-data / DFL** | github.com/spoho-datascience/idsse-data | Research license | 7 Bundesliga matches, synced TRACAB tracking + DFL events. Another small tracking teaching set. |
| **Impect Open Data** | via `kloppy` | Vendor sample terms | Bundesliga 2023/24 sample with packing / possession-value metrics. Niche. |
| **Kaggle "European Soccer Database"** | kaggle.com/hugomathien/soccer | Open (Kaggle) | SQLite, ~25k matches 2008–2016, 11 countries, some FIFA player attributes + betting odds. Convenient but **stale (ends 2016)** and quality is mixed. Usable as an extra match-prediction set, low priority. |
| **Kaggle FIFA / EA Sports player ratings** | multiple | Open | Player attribute ratings. Useful as *features* for player modelling / as a similarity sanity check, not as ground truth. Optional. |
| **Fantasy Premier League API** | fantasy.premierleague.com/api/ | Public JSON, no key | Live PL player points, prices, ownership, fixtures. Great for a **fantasy side-module**; not core. |
| **Football-Data.org API** | football-data.org | Free tier (rate-limited, needs key) | Fixtures, results, standings, some lineups for major comps. Handy for keeping results current; free tier is limited. |
| **API-Football (RapidAPI)** | api-sports.io | Freemium (key, quota) | Broad coverage incl. lineups, events, stats. Free tier small; ToS restrict redistribution. Possible later. |
| **understat** | understat.com (scrape via `understatapi`) | No open license; scrape | Shot-level data + xG for top-5 leagues since 2014. **Fills StatsBomb's biggest gap (continuous shot history)** but is a scrape with no license — use cautiously, cache, don't redistribute. |
| **Opta / StatsBomb IQ / Wyscout (paid)** | — | Commercial subscription | Out of scope (cost + license). |
| **transfermarkt** | transfermarkt scrape / Kaggle mirrors | Scrape; ToS restrict | Market values, transfers, injuries, ages. Useful metadata for scouting; use a Kaggle mirror and attribute. Optional Phase 2. |

---

## Summary of legal posture

| Source | Commercial use | Attribution | Redistribute raw? | Our use |
|---|---|---|---|---|
| StatsBomb Open Data | No | **Yes** | No (link to repo) | Primary — non-commercial portfolio/research |
| Wyscout public dataset | **Yes** (CC-BY) | Yes | Yes (with attribution) | Backup event source / commercial-safe path |
| football-data.co.uk | Grey (informal) | Requested | Avoid | Match results + odds baseline |
| FBref | No | Expected | No | Basic historical context only |
| SoccerNet | No | Cite papers | **No (NDA)** | CV research spike only |
| Metrica / SkillCorner / IDSSE | Research / NC | Cite | Mostly yes | Teaching sets for tracking methods |
| understat | None (scrape) | Courtesy | No | Optional gap-fill, cache only |

**Because our project is a non-commercial student/portfolio project, StatsBomb's
license is acceptable.** If the project ever needs to be commercial, the path is:
switch the event core to the **CC-BY Wyscout** dataset (and/or license data).

---

## Sources

- [statsbomb/open-data (GitHub)](https://github.com/statsbomb/open-data)
- [StatsBomb open-data issue #47 — license clarification for publications](https://github.com/statsbomb/open-data/issues/47)
- [socceraction docs — loading StatsBomb data](https://socceraction.readthedocs.io/en/latest/documentation/data/statsbomb.html)
- [Sports-Reference bot / scraping policy](https://www.sports-reference.com/bot-traffic.html)
- [Sports-Reference blog — FBref & Stathead data update, Jan 2026](https://www.sports-reference.com/blog/2026/01/fbref-stathead-data-update/)
- [Awful Announcing — Sports Reference pulls advanced soccer data](https://awfulannouncing.com/soccer/sports-reference-pulls-advanced-data-agreement-violation-dispute.html)
- [The IX — loss of FBref advanced stats and women's soccer data](https://www.theixsports.com/the-ix-soccer/fbrefs-loss-advanced-stats-womens-soccer-data-accessibility/)
- [SoccerNet — tasks / action spotting](https://www.soccer-net.org/tasks/action-spotting)
- [SoccerNet 2024 Challenges Results (arXiv)](https://arxiv.org/pdf/2409.10587)
- [Jan Van Haaren — football analytics resources list](https://www.janvanhaaren.be/resources.html)
- [withqwerty/open-football — curated map of open football data](https://github.com/withqwerty/open-football)
- [Liam Henshaw — where to find football data in 2026](https://www.liamhenshaw.com/writing/where-to-find-football-data)
- [Pappalardo et al. — public soccer event dataset (Wyscout), figshare/Nature Scientific Data](https://www.nature.com/articles/s41597-019-0247-7)
