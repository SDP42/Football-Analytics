"""
Shared HTTP fetching for all ingestion scripts.

Design goals (see docs/architecture.md "Ingest" stage and docs/decisions.md #0016):
- **Idempotent**: a URL is downloaded at most once. Re-running a script is cheap
  and does not re-hit the network for files we already have.
- **Immutable raw store**: responses are written verbatim under data/raw/<source>/.
  We never edit them; parsing happens later, downstream.
- **Auditable**: every fetch appends a row to a per-source manifest.csv
  (url, path, utc timestamp, http status, bytes, sha256).
- **Two politeness modes**:
    * "bulk"   -> GitHub / static CDNs that are built for heavy traffic and
                  whose data is explicitly published for bulk download.
    * "polite" -> small third-party sites (e.g. understat). Single-threaded,
                  min delay between requests, honest User-Agent, backoff.

Only the Python standard library + `requests` (already in the base env) is used.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import time
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser

import requests

# A truthful User-Agent. We identify the project and give a contact point instead
# of pretending to be a browser (docs/decisions.md #0016, rule 4).
USER_AGENT = (
    "football-analytics-student-project/0.1 "
    "(+https://github.com/SDP42/Football-Analytics; non-commercial research)"
)


@dataclass
class FetchResult:
    url: str
    path: Path
    status: int
    n_bytes: int
    sha256: str
    from_cache: bool


class CachedFetcher:
    """Download files once, cache them on disk, and log every fetch.

    Parameters
    ----------
    source_dir : Path
        Root folder for this source, e.g. data/raw/statsbomb. The manifest lives
        at <source_dir>/manifest.csv and cached files are placed relative to it.
    mode : {"bulk", "polite"}
        "polite" enforces `min_delay` seconds between network requests and
        respects robots.txt. "bulk" does neither (use only for CDNs that invite
        bulk access).
    min_delay : float
        Minimum seconds between two *network* requests in polite mode
        (cache hits do not count). #0016 rule 2 requires >= 3.0 for understat.
    """

    def __init__(self, source_dir: Path, mode: str = "bulk", min_delay: float = 3.0,
                 compress: bool = False):
        assert mode in {"bulk", "polite"}
        self.source_dir = Path(source_dir)
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode
        self.min_delay = min_delay
        # When True, text responses are stored gzip-compressed at "<rel_path>.gz".
        # StatsBomb/understat JSON/HTML shrink ~8-10x. Downstream readers must use
        # gzip.open() for ".gz" files (helper: src.data.fetching.read_maybe_gz).
        self.compress = compress
        self.manifest_path = self.source_dir / "manifest.csv"
        self._last_request_ts = 0.0
        self._robots: dict[str, robotparser.RobotFileParser] = {}
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT
        if not self.manifest_path.exists():
            with self.manifest_path.open("w", newline="") as fh:
                csv.writer(fh).writerow(
                    ["utc_time", "url", "rel_path", "http_status", "n_bytes", "sha256", "from_cache"]
                )

    # -- robots.txt (polite mode only) -----------------------------------------
    def _allowed_by_robots(self, url: str) -> bool:
        if self.mode != "polite":
            return True
        from urllib.parse import urlparse

        parts = urlparse(url)
        root = f"{parts.scheme}://{parts.netloc}"
        rp = self._robots.get(root)
        if rp is None:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{root}/robots.txt")
            try:
                rp.read()
            except Exception:
                # If robots.txt is unreachable we treat it as "no rules stated".
                pass
            self._robots[root] = rp
        return rp.can_fetch(USER_AGENT, url)

    # -- rate limiting --------------------------------------------------------
    def _throttle(self) -> None:
        if self.mode != "polite":
            return
        elapsed = time.time() - self._last_request_ts
        wait = self.min_delay - elapsed
        if wait > 0:
            time.sleep(wait + random.uniform(0, 0.5))  # small jitter (#0016 rule 2)

    def _log(self, res: FetchResult) -> None:
        with self.manifest_path.open("a", newline="") as fh:
            csv.writer(fh).writerow(
                [
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    res.url,
                    res.path.relative_to(self.source_dir).as_posix(),
                    res.status,
                    res.n_bytes,
                    res.sha256,
                    int(res.from_cache),
                ]
            )

    # -- main entry point ---------------------------------------------------
    def get(self, url: str, rel_path: str, *, max_retries: int = 3) -> FetchResult:
        """Fetch `url` into <source_dir>/<rel_path>, or return the cached copy.

        Returns a FetchResult. Raises on repeated network failure so the caller
        can decide whether to abort the whole run (#0016 rule 6).
        """
        dest = self.source_dir / rel_path
        gz_dest = dest.with_name(dest.name + ".gz")
        store = gz_dest if self.compress else dest

        # idempotency: never re-download. Accept either an uncompressed file from
        # an earlier run or the compressed one.
        for existing in (store, dest, gz_dest):
            if existing.exists():
                raw = _read_bytes(existing)
                res = FetchResult(url, existing, 200, len(raw), _sha256(raw), from_cache=True)
                self._log(res)
                return res

        if not self._allowed_by_robots(url):
            raise PermissionError(f"robots.txt disallows fetching {url}")

        dest.parent.mkdir(parents=True, exist_ok=True)
        last_err: Exception | None = None
        for attempt in range(1, max_retries + 1):
            self._throttle()
            try:
                self._last_request_ts = time.time()
                resp = self._session.get(url, timeout=60)
                if resp.status_code == 200:
                    raw = resp.content
                    if self.compress:
                        with gzip.open(store, "wb") as fh:
                            fh.write(raw)
                    else:
                        store.write_bytes(raw)
                    res = FetchResult(url, store, 200, len(raw), _sha256(raw), from_cache=False)
                    self._log(res)
                    return res
                if resp.status_code in (429, 500, 502, 503, 504):
                    # transient: exponential backoff then retry (#0016 rule 6)
                    time.sleep(min(60, 2 ** attempt))
                    last_err = RuntimeError(f"HTTP {resp.status_code} for {url}")
                    continue
                # other codes (404 etc.): do not retry
                res = FetchResult(url, dest, resp.status_code, 0, "", from_cache=False)
                self._log(res)
                raise RuntimeError(f"HTTP {resp.status_code} for {url}")
            except requests.RequestException as e:
                last_err = e
                time.sleep(min(60, 2 ** attempt))
        raise RuntimeError(f"Failed after {max_retries} attempts: {url}") from last_err


def free_mb(path: Path | str = ".") -> float:
    """Megabytes free on the filesystem holding `path`."""
    import shutil as _sh

    return _sh.disk_usage(Path(path)).free / 1e6


def require_free_mb(minimum: float, path: Path | str = ".") -> None:
    """Abort early if disk headroom is below `minimum` MB (learned the hard way)."""
    have = free_mb(path)
    if have < minimum:
        raise RuntimeError(
            f"Only {have:.0f} MB free at {path!s}; need >= {minimum:.0f} MB. Aborting."
        )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_bytes(path: Path) -> bytes:
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as fh:
            return fh.read()
    return path.read_bytes()


def read_maybe_gz(path: Path | str) -> bytes:
    """Read a raw file whether it is stored plain or gzip-compressed.

    Downstream parsing code should use this instead of Path.read_bytes() so it
    works regardless of the fetcher's `compress` setting. Pass either the plain
    path (``events/123.json``) or the ``.gz`` path — both resolve.
    """
    p = Path(path)
    if p.exists():
        return _read_bytes(p)
    gz = p.with_name(p.name + ".gz")
    if gz.exists():
        return _read_bytes(gz)
    raise FileNotFoundError(p)
