"""
Ingest understat shot + xG data for recent Premier League & La Liga seasons.

BOUND BY docs/decisions.md #0016 (responsible-collection contract):
  * "polite" mode  -> single-threaded, >= 3 s between requests, jittered
  * honest User-Agent (set in src/data/fetching.py)
  * robots.txt respected (checked by the fetcher in polite mode)
  * immutable cache + manifest; a URL is fetched at most once
  * no raw redistribution (data/ is git-ignored); attribute understat + Opta

The Kaggle mirror (the contract's preferred source for completed seasons) needs
Kaggle API credentials that are not configured here, so we use the contract's
"mirror-unavailable fallback": ONE index page per (league, season). Each
understat league page embeds JSON (datesData / playersData / teamsData) inside
<script> tags; we save the raw HTML now and parse it later, downstream.

That is ~12 requests, once, cached forever. It is not a crawl. Per-match deep
pages are NOT fetched here - they wait for the Kaggle mirror or explicit approval.

Run:  python scripts/ingest_understat.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data.fetching import CachedFetcher  # noqa: E402

BASE = "https://understat.com/league"
RAW_DIR = REPO_ROOT / "data" / "raw" / "understat"

# understat season = starting year. 2018 == 2018/19 ... 2025 == 2025/26 (live).
LEAGUES = {"EPL": "Premier League", "La_liga": "La Liga"}
SEASONS = list(range(2018, 2026))


def main() -> None:
    fetcher = CachedFetcher(RAW_DIR, mode="polite", min_delay=3.0)
    ok = failed = 0
    for lg in LEAGUES:
        for yr in SEASONS:
            url = f"{BASE}/{lg}/{yr}"
            rel = f"league/{lg}/{yr}.html"
            try:
                res = fetcher.get(url, rel)
                tag = "cache" if res.from_cache else "net"
                print(f"  {lg:8} {yr}  {res.n_bytes:>7} bytes  ({tag})")
                ok += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"  FAIL {lg} {yr}: {e}")
                # #0016 rule 6: stop hammering on repeated failure
                if failed >= 3:
                    print("  aborting: 3 failures")
                    break
    print(f"\nDONE. {ok} understat league-season pages ok, {failed} failed.")
    print(f"Raw HTML in {RAW_DIR} (parse downstream). Attribute: understat / Opta.")


if __name__ == "__main__":
    main()
