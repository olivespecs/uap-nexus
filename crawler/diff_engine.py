"""Diff engine for detecting new document releases."""
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .scraper import DocumentRelease

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Result of comparing new vs known releases."""

    new_releases: list[DocumentRelease]
    updated_releases: list[DocumentRelease]  # Same URL, new hash
    unchanged: int
    total_checked: int


@dataclass
class ReleaseSnapshot:
    """Snapshot of known releases for persistence."""

    source: str
    checked_at: str  # ISO timestamp
    releases: dict[str, dict]  # url -> release data


class DiffEngine:
    """Detects new and changed documents by comparing hashes."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path(__file__).parent / ".state"
        self.state_dir.mkdir(exist_ok=True, parents=True)
        self._memory: dict[str, dict[str, str]] = {}  # source -> {url: hash}

    def load_state(self, source: str) -> dict[str, str]:
        """Load persisted hashes for a source."""
        state_file = self.state_dir / f"{source.lower()}_hashes.json"

        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                logger.info(f"Loaded {len(data)} known URLs for {source}")
                self._memory[source] = data
                return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load state for {source}: {e}")

        self._memory[source] = {}
        return {}

    def save_state(self, source: str, hashes: dict[str, str]):
        """Persist hashes for a source."""
        state_file = self.state_dir / f"{source.lower()}_hashes.json"
        try:
            state_file.write_text(json.dumps(hashes, indent=2))
            logger.debug(f"Saved {len(hashes)} hashes for {source}")
        except IOError as e:
            logger.error(f"Failed to save state for {source}: {e}")

    def diff(self, new_releases: list[DocumentRelease]) -> DiffResult:
        """Compare new releases against known state."""
        if not new_releases:
            return DiffResult(new_releases=[], updated_releases=[], unchanged=0, total_checked=0)

        # Group by source
        by_source: dict[str, list[DocumentRelease]] = {}
        for r in new_releases:
            by_source.setdefault(r.source, []).append(r)

        new_list = []
        updated_list = []
        unchanged = 0

        for source, releases in by_source.items():
            known = self.load_state(source)

            for release in releases:
                known_hash = known.get(release.url)

                if known_hash is None:
                    # New URL
                    new_list.append(release)
                    known[release.url] = release.raw_hash
                elif known_hash != release.raw_hash and release.raw_hash:
                    # Same URL, different content
                    updated_list.append(release)
                    known[release.url] = release.raw_hash
                    logger.info(f"Content changed: {release.url}")
                else:
                    unchanged += 1

            # Persist updated hashes
            self.save_state(source, known)

        total = len(new_releases)
        logger.info(
            f"Diff complete: {len(new_list)} new, {len(updated_list)} updated, "
            f"{unchanged}/{total} unchanged"
        )

        return DiffResult(
            new_releases=new_list,
            updated_releases=updated_list,
            unchanged=unchanged,
            total_checked=total,
        )

    def get_new_only(self, releases: list[DocumentRelease]) -> list[DocumentRelease]:
        """Filter to only truly new releases."""
        result = self.diff(releases)
        return result.new_releases


class ReleaseHistory:
    """Track release history for analytics."""

    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path(__file__).parent / ".state"
        self.state_dir.mkdir(exist_ok=True, parents=True)
        self.history_file = self.state_dir / "release_history.json"

    def record(self, releases: list[DocumentRelease], event_type: str = "discovered"):
        """Record releases to history."""
        history = self.load()

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "count": len(releases),
            "sources": list(set(r.source for r in releases)),
            "urls": [{"url": r.url, "title": r.title, "source": r.source} for r in releases],
        }

        history.append(entry)

        # Keep last 1000 entries
        history = history[-1000:]

        try:
            self.history_file.write_text(json.dumps(history, indent=2))
        except IOError as e:
            logger.error(f"Failed to record history: {e}")

    def load(self) -> list[dict]:
        """Load history from disk."""
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def recent(self, hours: int = 24) -> list[dict]:
        """Get releases from last N hours."""
        history = self.load()
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent = []

        for entry in history:
            try:
                ts = datetime.fromisoformat(entry["timestamp"])
                if ts >= cutoff:
                    recent.append(entry)
            except (KeyError, ValueError):
                continue

        return recent
