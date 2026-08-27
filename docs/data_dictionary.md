# Data Dictionary

> **Status: SKELETON.** Per our working rules we do **not** invent columns.
> The tables below are placeholders describing the *entities* we expect. Every
> field marked `⟨verify⟩` must be confirmed by inspecting a real downloaded file
> before we write code against it. We fill this in during the EDA step (F4).

## How this document works

- One section per **entity** (Match, Player, Team, Event, Shot, Pass, ...).
- For each field: name · type · description · source file · notes / gotchas.
- When we confirm a field against real data, replace `⟨verify⟩` with `✔ (yyyy-mm-dd)`.
- If the real data does **not** contain an expected field, we delete the row and
  note it — we never keep an aspirational column.

## Source: StatsBomb Open Data (primary)

Folder structure of the raw repo (this part is documented and stable):

```
data/
  competitions.json                 -> one row per (competition, season)
  matches/{competition_id}/{season_id}.json   -> matches in that comp-season
  events/{match_id}.json             -> ordered list of events in a match
  lineups/{match_id}.json            -> starting XI + subs per team
  three-sixty/{match_id}.json        -> freeze-frame positions (selected matches)
```

### Entity: Competition / Season  (`competitions.json`)

| Field | Type | Description | Verify |
|---|---|---|---|
| competition_id | int | StatsBomb competition id | ⟨verify⟩ |
| season_id | int | StatsBomb season id | ⟨verify⟩ |
| competition_name | str | e.g. "FIFA World Cup" | ⟨verify⟩ |
| season_name | str | e.g. "2022" or "2020/2021" | ⟨verify⟩ |
| country_name | str | competition country / "International" | ⟨verify⟩ |
| competition_gender | str | "male" / "female" | ⟨verify⟩ |
| match_updated / match_available | datetime | data freshness stamps | ⟨verify⟩ |
| match_available_360 | datetime / null | non-null ⇒ 360 data exists for this comp-season | ⟨verify⟩ |

### Entity: Match  (`matches/{comp}/{season}.json`)

| Field | Type | Description | Verify |
|---|---|---|---|
| match_id | int | unique match id (used to name event/lineup files) | ⟨verify⟩ |
| match_date | date | kickoff date | ⟨verify⟩ |
| kick_off | time | kickoff time | ⟨verify⟩ |
| competition / season | nested | competition + season names/ids | ⟨verify⟩ |
| home_team / away_team | nested | team id, name, (manager, country) | ⟨verify⟩ |
| home_score / away_score | int | full-time goals | ⟨verify⟩ — **post-match; leakage risk for prediction** |
| match_status | str | data completeness flag | ⟨verify⟩ |
| stadium / referee | nested | venue and official | ⟨verify⟩ |
| competition_stage | nested | group / knockout round | ⟨verify⟩ |

### Entity: Team

| Field | Type | Description | Verify |
|---|---|---|---|
| team_id | int | StatsBomb team id | ⟨verify⟩ |
| team_name | str | canonical StatsBomb spelling | ⟨verify⟩ — differs from football-data.co.uk |
| country | str | team country | ⟨verify⟩ |

### Entity: Player  (`lineups/{match_id}.json`)

| Field | Type | Description | Verify |
|---|---|---|---|
| player_id | int | StatsBomb player id | ⟨verify⟩ |
| player_name | str | full name | ⟨verify⟩ |
| player_nickname | str / null | common name | ⟨verify⟩ |
| jersey_number | int | shirt number in that match | ⟨verify⟩ |
| country | str | nationality | ⟨verify⟩ |
| position(s) | nested list | position(s) played + minutes windows | ⟨verify⟩ |

### Entity: Event  (`events/{match_id}.json`) — the core table

Common fields expected on (almost) every event:

| Field | Type | Description | Verify |
|---|---|---|---|
| id | uuid | event id | ⟨verify⟩ |
| index | int | order within the match | ⟨verify⟩ |
| period | int | 1,2 (3,4 ET), 5 (pens) | ⟨verify⟩ |
| timestamp | str "HH:MM:SS.mmm" | time since period start | ⟨verify⟩ |
| minute / second | int | clock | ⟨verify⟩ |
| type | nested {id,name} | event type: Pass, Shot, Carry, Pressure, Duel, ... | ⟨verify⟩ |
| possession | int | possession sequence number | ⟨verify⟩ |
| possession_team | nested | team in possession | ⟨verify⟩ |
| play_pattern | nested | e.g. "From Corner", "Regular Play" | ⟨verify⟩ |
| team | nested | team performing the event | ⟨verify⟩ |
| player | nested | player performing the event | ⟨verify⟩ |
| position | nested | player's position at that moment | ⟨verify⟩ |
| location | [x, y] | pitch coords, pitch is 120 × 80 | ⟨verify⟩ |
| duration | float | event duration (s) | ⟨verify⟩ |
| under_pressure | bool | opponent pressure flag | ⟨verify⟩ |
| out / off_camera | bool | data-collection flags | ⟨verify⟩ |
| related_events | list[uuid] | links to connected events | ⟨verify⟩ |

Type-specific nested objects expected (fields inside `⟨verify⟩` in bulk):

| Sub-entity | Lives under | Key fields we expect |
|---|---|---|
| **Pass** | `event.pass` | end_location [x,y], recipient, length, angle, height, body_part, outcome (null ⇒ complete), type (Corner/Free Kick/Throw-in...), cross, cutback, switch, assisted_shot_id, shot_assist, goal_assist |
| **Shot** | `event.shot` | end_location [x,y,z], **statsbomb_xg**, outcome (Goal/Saved/Off T/...), technique, body_part, type (Open Play/Penalty/FK), first_time, **freeze_frame** (list of {location, player, teammate, position}), key_pass_id |
| **Carry** | `event.carry` | end_location [x,y] |
| **Dribble** | `event.dribble` | outcome, nutmeg, overrun |
| **Duel** | `event.duel` | type, outcome |
| **Pressure** | (event itself) | counterpress |
| **Goalkeeper** | `event.goalkeeper` | type, outcome, position, technique |
| **Foul Won / Foul Committed** | `event.foul_*` | advantage, penalty, card |
| **Substitution** | `event.substitution` | replacement, outcome |
| **50/50, Ball Receipt, Interception, Clearance, Block, Miscontrol** | respective keys | outcome fields |

### Entity: 360 freeze frame  (`three-sixty/{match_id}.json`)

| Field | Type | Description | Verify |
|---|---|---|---|
| event_uuid | uuid | links to an event id | ⟨verify⟩ |
| visible_area | list[float] | polygon of the camera-visible pitch area | ⟨verify⟩ |
| freeze_frame | list | per player: location [x,y], teammate (bool), actor (bool), keeper (bool) | ⟨verify⟩ |

---

## Source: football-data.co.uk (secondary — match results & odds)

One CSV per league-season. Column meanings are documented in the site's
`notes.txt`. Expected core columns (`⟨verify⟩` against a downloaded season):

| Field | Type | Description | Verify |
|---|---|---|---|
| Div | str | division code (E0 = Premier League, SP1 = La Liga, ...) | ⟨verify⟩ |
| Date | date | match date (format varies by era: dd/mm/yy vs dd/mm/yyyy) | ⟨verify⟩ |
| HomeTeam / AwayTeam | str | team names (**own spelling — needs mapping**) | ⟨verify⟩ |
| FTHG / FTAG | int | full-time home / away goals | ⟨verify⟩ — post-match |
| FTR | str | full-time result: H / D / A (**this is our prediction target**) | ⟨verify⟩ |
| HTHG / HTAG / HTR | int/str | half-time score & result | ⟨verify⟩ — post-match |
| HS / AS / HST / AST | int | shots / shots on target | ⟨verify⟩ — post-match |
| HC / AC / HF / AF / HY / AY / HR / AR | int | corners / fouls / yellows / reds | ⟨verify⟩ — post-match |
| Referee | str | referee name | ⟨verify⟩ |
| B365H / B365D / B365A (and many more bookmakers) | float | **pre-match** decimal odds for H/D/A | ⟨verify⟩ — **pre-match, usable as feature/baseline** |
| BbAv* / Avg* / Max* | float | market average / maximum odds | ⟨verify⟩ |

**Leakage note:** for a model that predicts a match *before kickoff*, only the
odds columns (and derived pre-match features from *earlier* matches) are legal
inputs. `FTHG/FTAG/FTR/HS/...` describe the outcome and must never be features
for the same match.

---

## Source: FBref (secondary — basic/historical only, post-2026)

Scraped HTML tables. We will only ingest **basic** columns (see
[dataset_research.md](dataset_research.md#-january-2026-change--opta-advanced-stats-removed)).
Fields to be documented **only after** we actually scrape a page, since layout
and available columns changed in 2026.

| Expected field group | Examples | Verify |
|---|---|---|
| Player identity | player, nationality, position, squad, age, born | ⟨verify⟩ |
| Playing time | MP, Starts, Min, 90s | ⟨verify⟩ |
| Basic performance | Gls, Ast, PK, PKatt, CrdY, CrdR | ⟨verify⟩ |
| Basic shooting | Sh, SoT, SoT%, Sh/90 | ⟨verify⟩ |
| ~~Advanced (xG, npxG, xAG, SCA, GCA, progressive, pressures)~~ | **removed Jan 2026 — do not use** | n/a |

---

## Cross-source key map (for entity resolution)

| Concept | StatsBomb | football-data.co.uk | FBref |
|---|---|---|---|
| Competition | competition_id + name | Div code | comp slug in URL |
| Season | season_id + name ("2020/2021") | encoded in filename | season string |
| Match | match_id | (Date, HomeTeam, AwayTeam) | (Date, teams) |
| Team | team_id + team_name | HomeTeam / AwayTeam string | squad string / id in URL |
| Player | player_id + player_name | — (no players) | player id in URL + name |
| Date | match_date (ISO) | Date (locale format) | date string |

The only reliable cross-source join is **(competition, season, date, home_team,
away_team)** after normalising team names and date formats. There are **no shared
numeric IDs** across sources — this is the central integration problem, addressed
in [architecture.md](architecture.md#entity-resolution).
