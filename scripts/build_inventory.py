"""
Walk data/raw/ and write docs/data_inventory.md — a human-readable summary of
exactly what has been collected: sources, file counts, sizes, and per-source
detail (StatsBomb competitions/matches, football-data leagues/seasons/rows, etc.).

Pure standard library + pandas (for the CSV row counts). Read-only over data/raw.

Run:  python scripts/build_inventory.py
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW = REPO_ROOT / "data" / "raw"
OUT = REPO_ROOT / "docs" / "data_inventory.md"


def human(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def tree_stats(root: Path) -> tuple[int, int]:
    files = [p for p in root.rglob("*") if p.is_file()]
    return len(files), sum(p.stat().st_size for p in files)


def statsbomb_detail() -> list[str]:
    d = RAW / "statsbomb"
    if not d.exists():
        return ["_not collected_"]
    comps = {c["competition_id"]: c for c in
             json.loads((d / "competitions.json").read_bytes())}
    lines = ["| Competition | Season | Matches | Events files | 360 files |",
             "|---|---|--:|--:|--:|"]
    event_ids = {p.stem for p in (d / "events").glob("*.json")} if (d / "events").exists() else set()
    threesixty_ids = {p.stem for p in (d / "three-sixty").glob("*.json")} if (d / "three-sixty").exists() else set()
    total_m = total_e = total_3 = 0
    for mfile in sorted((d / "matches").rglob("*.json")):
        cid = int(mfile.parent.name)
        matches = json.loads(mfile.read_bytes())
        ids = [str(m["match_id"]) for m in matches]
        n_e = sum(i in event_ids for i in ids)
        n_3 = sum(i in threesixty_ids for i in ids)
        c = comps.get(cid, {})
        season = matches[0]["season"]["season_name"] if matches else "?"
        lines.append(f"| {c.get('competition_name', cid)} | {season} | {len(ids)} | {n_e} | {n_3 or '-'} |")
        total_m += len(ids); total_e += n_e; total_3 += n_3
    lines.append(f"| **TOTAL** | | **{total_m}** | **{total_e}** | **{total_3}** |")
    return lines


def football_data_detail() -> list[str]:
    d = RAW / "football_data_couk"
    if not d.exists():
        return ["_not collected_"]
    names = {"E0": "Premier League", "SP1": "La Liga", "D1": "Bundesliga",
             "I1": "Serie A", "F1": "Ligue 1"}
    lines = ["| Division | Seasons | Total matches (rows) |", "|---|--:|--:|"]
    for div in sorted(names):
        csvs = sorted((d / div).glob("*.csv"))
        rows = 0
        for c in csvs:
            try:
                rows += len(pd.read_csv(c, encoding="latin-1", on_bad_lines="skip"))
            except Exception:
                pass
        lines.append(f"| {names[div]} ({div}) | {len(csvs)} | {rows} |")
    return lines


def clubelo_detail() -> list[str]:
    d = RAW / "clubelo" / "snapshots"
    if not d.exists():
        return ["_not collected_"]
    snaps = sorted(d.glob("*.csv"))
    if not snaps:
        return ["_no snapshots_"]
    sample = pd.read_csv(snaps[-1])
    return [f"- {len(snaps)} monthly snapshots, {snaps[0].stem} → {snaps[-1].stem}",
            f"- latest snapshot lists {len(sample)} clubs, columns: {', '.join(sample.columns)}"]


def fpl_detail() -> list[str]:
    d = RAW / "fpl"
    if not d.exists():
        return ["_not collected_"]
    lines = []
    boot = d / "current" / "bootstrap_static.json"
    if boot.exists():
        b = json.loads(boot.read_bytes())
        lines.append(f"- current season: {len(b['elements'])} players, "
                     f"{len(b['teams'])} teams, {len(b['events'])} gameweeks")
    es = list((d / "current" / "element_summary").glob("*.json")) if (d / "current" / "element_summary").exists() else []
    lines.append(f"- per-player history files: {len(es)}")
    arch = sorted((d / "archive").glob("*")) if (d / "archive").exists() else []
    lines.append(f"- historical archive seasons: {len(arch)} ({', '.join(p.name for p in arch)})")
    return lines


def understat_detail() -> list[str]:
    d = RAW / "understat"
    pages = list((d / "league").rglob("*.html")) if (d / "league").exists() else []
    if pages:
        return [f"- {len(pages)} league-season pages collected"]
    return ["- **BLOCKED**: understat robots.txt is `Disallow: /` — not scraped "
            "(see docs/decisions.md #0016). Recent PL/La Liga shot data is a known gap."]


def main() -> None:
    sources = {
        "statsbomb": ("StatsBomb Open Data (events, lineups, 360)", statsbomb_detail),
        "football_data_couk": ("football-data.co.uk (results + bookmaker odds)", football_data_detail),
        "clubelo": ("ClubElo (team strength ratings)", clubelo_detail),
        "fpl": ("Fantasy Premier League (recent PL player form)", fpl_detail),
        "understat": ("understat (recent shot/xG)", understat_detail),
    }

    out = [f"# Data Inventory\n",
           f"_Generated by `scripts/build_inventory.py` on {date.today().isoformat()}._\n",
           "Raw data lives in `data/raw/` and is **git-ignored** — this file is the "
           "committed record of what exists locally.\n",
           "## Totals\n",
           "| Source | Files | Size on disk |", "|---|--:|--:|"]
    grand_f = grand_b = 0
    for key, (label, _) in sources.items():
        p = RAW / key
        if p.exists():
            nf, nb = tree_stats(p)
        else:
            nf = nb = 0
        grand_f += nf; grand_b += nb
        out.append(f"| {label} | {nf} | {human(nb)} |")
    out.append(f"| **TOTAL** | **{grand_f}** | **{human(grand_b)}** |")

    for key, (label, fn) in sources.items():
        out += [f"\n## {label}\n", *fn()]

    out += ["\n## Attribution required on any published output\n",
            "- StatsBomb: *\"Data provided by StatsBomb\"* + logo",
            "- ClubElo: link to clubelo.com (non-commercial use)",
            "- football-data.co.uk: link back if republished",
            "- FPL: unofficial API; community archive `vaastav/Fantasy-Premier-League`"]

    OUT.write_text("\n".join(out) + "\n")
    print(f"wrote {OUT}")
    print("\n".join(out[:20]))


if __name__ == "__main__":
    main()
