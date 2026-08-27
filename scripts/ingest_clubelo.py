"""
Ingest team-strength ratings from ClubElo (http://clubelo.com/API).

Two endpoint types:
  http://api.clubelo.com/<YYYY-MM-DD>  -> CSV snapshot of ALL clubs on that date
  http://api.clubelo.com/<ClubName>    -> full rating history for one club

The ClubElo API computes each response on the fly and is SLOW (~30-40 s per
request even for a tiny client). A full monthly history back to 2010 would take
hours, so for now we take a monthly snapshot from START (below) to today. That
covers the recent seasons we will model first; deeper history can be backfilled
later (or taken from the Kaggle "Club Football Match Data" merge).

Stitching the monthly snapshots gives a per-club rating time series across all
our leagues without needing ClubElo's club-name list.

"polite" mode, 1 s nominal delay (the 30-40 s response time is the real limiter).
Free for non-commercial use with attribution.

Run:  python scripts/ingest_clubelo.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data.fetching import CachedFetcher  # noqa: E402

BASE = "http://api.clubelo.com"
RAW_DIR = REPO_ROOT / "data" / "raw" / "clubelo"
START = date(2022, 7, 1)  # start of 2022/23 season; extend backwards later if needed


def month_firsts(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while date(y, m, 1) <= end:
        out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main() -> None:
    fetcher = CachedFetcher(RAW_DIR, mode="polite", min_delay=1.0)
    today = date.today()
    snapshots = month_firsts(START, today) + [today]

    ok = failed = 0
    for d in snapshots:
        iso = d.isoformat()
        try:
            fetcher.get(f"{BASE}/{iso}", f"snapshots/{iso}.csv")
            ok += 1
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  miss {iso}: {e}")
    print(f"\nDONE. {ok} ClubElo snapshots ok, {failed} failed. Raw data in {RAW_DIR}")


if __name__ == "__main__":
    main()
