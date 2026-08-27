"""
Gzip-compress every already-downloaded raw file in place.

Why: the first StatsBomb run stored ~4.3 GB of uncompressed JSON and filled the
disk. StatsBomb JSON compresses ~8-10x. This script rewrites each file as
"<name>.gz" and deletes the original, freeing space as it goes, so a re-run of
the ingest scripts (now with compress=True) only needs to fetch what is missing.

Skips: manifest.csv, files already ending in .gz.
Safe to re-run.

Run:  python scripts/compact_raw.py
"""

from __future__ import annotations

import gzip
import os
import shutil
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    targets = [
        p for p in RAW.rglob("*")
        if p.is_file() and p.suffix != ".gz" and p.name != "manifest.csv"
    ]
    print(f"{len(targets)} files to compress")
    freed = 0
    for i, p in enumerate(targets, 1):
        before = p.stat().st_size
        gz = p.with_name(p.name + ".gz")
        with p.open("rb") as fin, gzip.open(gz, "wb", compresslevel=6) as fout:
            shutil.copyfileobj(fin, fout, length=1024 * 1024)
        after = gz.stat().st_size
        os.replace(gz, gz)  # ensure flushed
        p.unlink()
        freed += before - after
        if i % 500 == 0:
            print(f"  {i}/{len(targets)}  freed ~{freed / 1e6:.0f} MB so far")
    print(f"DONE. Freed ~{freed / 1e6:.0f} MB. Raw tree now at "
          f"{sum(f.stat().st_size for f in RAW.rglob('*') if f.is_file()) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
