"""
Ingest Fantasy Premier League data (recent Premier League player-form module).

Two parts:

1. Live official API (current season only), no auth:
     /api/bootstrap-static/   -> players, teams, gameweeks, positions
     /api/fixtures/           -> all fixtures + basic match stats
     /api/element-summary/{id}/ -> per-player per-gameweek history (one per player)

2. Historical community archive (vaastav/Fantasy-Premier-League on GitHub, an
   openly shared cleaned dataset). We grab, per season 2016-17 .. 2024-25:
     players_raw.csv   (season player master)
     gws/merged_gw.csv (every player's every gameweek that season)

The official API is public and widely used -> "bulk" mode with a small pool.

Run:  python scripts/ingest_fpl.py
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data.fetching import CachedFetcher  # noqa: E402

API = "https://fantasy.premierleague.com/api"
ARCHIVE = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data"
RAW_DIR = REPO_ROOT / "data" / "raw" / "fpl"
ARCHIVE_SEASONS = [f"20{y}-{y+1:02d}" for y in range(16, 25)]  # 2016-17 .. 2024-25


def main() -> None:
    fetcher = CachedFetcher(RAW_DIR, mode="bulk")

    # 1) current-season core
    boot = fetcher.get(f"{API}/bootstrap-static/", "current/bootstrap_static.json")
    fetcher.get(f"{API}/fixtures/", "current/fixtures.json")
    players = json.loads(boot.path.read_bytes())["elements"]
    print(f"current season: {len(players)} players")

    # 2) per-player history (current season) - parallel, keep going on errors
    tasks = [(f"{API}/element-summary/{p['id']}/", f"current/element_summary/{p['id']}.json")
             for p in players]
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(fetcher.get, u, r): r for u, r in tasks}
        for f in as_completed(futs):
            try:
                f.result(); ok += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"  FAIL {futs[f]}: {e}")
    print(f"per-player history: {ok} ok, {failed} failed")

    # 3) historical archive
    arch_ok = arch_miss = 0
    for season in ARCHIVE_SEASONS:
        for rel_src in ["players_raw.csv", "gws/merged_gw.csv"]:
            url = f"{ARCHIVE}/{season}/{rel_src}"
            rel = f"archive/{season}/{rel_src.replace('/', '_')}"
            try:
                fetcher.get(url, rel); arch_ok += 1
            except Exception as e:  # noqa: BLE001
                arch_miss += 1
                print(f"  archive miss {season}/{rel_src}: {e}")
    print(f"archive: {arch_ok} files ok, {arch_miss} missing")
    print(f"\nDONE. Raw data in {RAW_DIR}")


if __name__ == "__main__":
    main()
