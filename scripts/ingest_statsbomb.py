"""
Ingest StatsBomb Open Data for the competitions listed in
configs/statsbomb_targets.yaml.

StatsBomb Open Data is a Git repo of JSON files served from GitHub's raw CDN.
Layout we mirror into data/raw/statsbomb/:

    competitions.json
    matches/{competition_id}/{season_id}.json
    events/{match_id}.json
    lineups/{match_id}.json
    three-sixty/{match_id}.json      (only for configured comp-seasons)

Why direct file fetch instead of `git clone`:
  The full repo is several GB (all competitions, men's + women's, all World Cups).
  We only want a men's-league subset, so we fetch exactly those files.

Why threaded + "bulk" mode:
  The data is on GitHub's CDN and StatsBomb explicitly publish it for bulk use.
  Politeness rate-limiting is reserved for small sites (see understat script).

Licence: StatsBomb Open Data User Agreement - non-commercial, attribution
"Data provided by StatsBomb". Raw data is NOT redistributed (data/ is git-ignored).

Run:  python scripts/ingest_statsbomb.py
Re-running is cheap: files already downloaded are skipped.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
from src.data.fetching import CachedFetcher  # noqa: E402

BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
RAW_DIR = REPO_ROOT / "data" / "raw" / "statsbomb"
CONFIG = REPO_ROOT / "configs" / "statsbomb_targets.yaml"
N_WORKERS = 12


def load_targets() -> dict:
    return yaml.safe_load(CONFIG.read_text())["statsbomb"]


def resolve_comp_seasons(fetcher: CachedFetcher, targets: dict) -> list[dict]:
    """Turn the config into a concrete list of {competition_id, season_id, ...}."""
    comps = json.loads(fetcher.get(f"{BASE}/competitions.json", "competitions.json").path.read_bytes())
    wanted = []
    for entry in targets["competitions"]:
        cid = entry["competition_id"]
        rows = [c for c in comps if c["competition_id"] == cid and c["competition_gender"] == "male"]
        if not entry.get("all_seasons"):
            rows = [c for c in rows if c["season_name"] in entry["seasons"]]
        wanted.extend(rows)
    return wanted


def want_360(targets: dict, comp_season: dict) -> bool:
    for rule in targets.get("fetch_360_for", []):
        if (rule["competition_id"] == comp_season["competition_id"]
                and rule["season_name"] == comp_season["season_name"]):
            return True
    return False


def main() -> None:
    targets = load_targets()
    fetcher = CachedFetcher(RAW_DIR, mode="bulk")

    comp_seasons = resolve_comp_seasons(fetcher, targets)
    print(f"{len(comp_seasons)} competition-seasons selected")

    # 1) match-list files (one per comp-season) and collect all match_ids
    jobs_360: set[int] = set()
    match_ids: list[int] = []
    for cs in comp_seasons:
        cid, sid = cs["competition_id"], cs["season_id"]
        mfile = fetcher.get(f"{BASE}/matches/{cid}/{sid}.json", f"matches/{cid}/{sid}.json")
        matches = json.loads(mfile.path.read_bytes())
        ids = [m["match_id"] for m in matches]
        match_ids.extend(ids)
        if want_360(targets, cs):
            jobs_360.update(ids)
        print(f"  {cs['competition_name']:16} {cs['season_name']:10} {len(ids):4d} matches"
              f"{'  (+360)' if want_360(targets, cs) else ''}")

    match_ids = sorted(set(match_ids))
    print(f"\n{len(match_ids)} unique matches -> events + lineups"
          f"  |  {len(jobs_360)} matches -> 360 frames")

    # 2) events + lineups (+ 360) for every match, in parallel
    tasks: list[tuple[str, str]] = []
    for mid in match_ids:
        tasks.append((f"{BASE}/events/{mid}.json", f"events/{mid}.json"))
        tasks.append((f"{BASE}/lineups/{mid}.json", f"lineups/{mid}.json"))
    for mid in sorted(jobs_360):
        tasks.append((f"{BASE}/three-sixty/{mid}.json", f"three-sixty/{mid}.json"))

    done = failed = 0
    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(fetcher.get, url, rel): (url, rel) for url, rel in tasks}
        for fut in as_completed(futures):
            url, rel = futures[fut]
            try:
                fut.result()
                done += 1
            except Exception as e:  # noqa: BLE001 - we want to keep going, log the rest
                failed += 1
                print(f"  FAIL {rel}: {e}")
            if done % 200 == 0:
                print(f"  ... {done}/{len(tasks)} files")

    print(f"\nDONE. {done} files ok, {failed} failed. Raw data in {RAW_DIR}")


if __name__ == "__main__":
    main()
