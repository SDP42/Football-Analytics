"""
Ingest match results + bookmaker odds from football-data.co.uk.

One CSV per (league, season). URL pattern:
    https://www.football-data.co.uk/mmz4281/<SSSS>/<DIV>.csv
where <SSSS> is the season as 4 digits ("2324" = 2023/24) and <DIV> is the
division code:  E0 Premier League, SP1 La Liga, D1 Bundesliga, I1 Serie A,
F1 Ligue 1.

These files are small (tens to hundreds of KB), static once a season ends, and
the site permits free download for research. Static host -> "bulk" mode.

Run:  python scripts/ingest_football_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data.fetching import CachedFetcher  # noqa: E402

BASE = "https://www.football-data.co.uk/mmz4281"
RAW_DIR = REPO_ROOT / "data" / "raw" / "football_data_couk"

# Division code -> human name (for our own reference / inventory).
DIVISIONS = {"E0": "Premier League", "SP1": "La Liga", "D1": "Bundesliga",
             "I1": "Serie A", "F1": "Ligue 1"}

# Seasons: 2000/01 ... 2025/26. Season code = last2(startYear) + last2(endYear).
START_YEARS = range(2000, 2026)


def season_code(start_year: int) -> str:
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def main() -> None:
    fetcher = CachedFetcher(RAW_DIR, mode="bulk")
    ok = failed = 0
    for start in START_YEARS:
        code = season_code(start)
        for div in DIVISIONS:
            url = f"{BASE}/{code}/{div}.csv"
            rel = f"{div}/{code}.csv"
            try:
                fetcher.get(url, rel)
                ok += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"  miss {div} {start}/{start+1}: {e}")
    print(f"\nDONE. {ok} season files ok, {failed} missing. Raw data in {RAW_DIR}")


if __name__ == "__main__":
    main()
