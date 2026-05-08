"""Crawler configuration."""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CrawlerConfig:
    """Crawler settings."""

    poll_interval_seconds: int = 1800  # 30 minutes
    rate_limit_seconds: float = 1.0
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    user_agent: str = "UAP-NEXUS/1.0 (+https://uapnexus.com)"
    state_dir: Path = Path(__file__).parent / ".state"

    # PURSUE (war.gov/UFO)
    pursue_base_url: str = "https://www.aaro.mil/Reports/AR-Programs/All-DARPA-Programs/UAP/"
    pursue_index_paths: list[str] = field(default_factory=lambda: [
        "https://www.aaro.mil/Reports/AR-Programs/All-DARPA-Programs/UAP/FOIA-Request-Log.aspx",
        "https://www.aaro.mil/Reports/AR-Programs/All-DARPA-Programs/UAP/Whats-New.aspx",
    ])

    # AARO direct
    aaro_base_url: str = "https://www.aaro.mil/Reports/AR-Programs/UAP/"

    # Local state files
    pursue_state_file: str = "pursue_hashes.json"
    aaro_state_file: str = "aaro_hashes.json"
