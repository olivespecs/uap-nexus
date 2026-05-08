"""Crawler module for PURSUE tracker."""
from .config import CrawlerConfig
from .scraper import DocumentRelease, Scraper, extract_links_sync
from .diff_engine import DiffEngine, DiffResult, ReleaseHistory
from .alert_dispatch import (
    AlertChannel,
    AlertDispatcher,
    AlertPayload,
    DiscordChannel,
    EmailChannel,
    TelegramChannel,
)

__all__ = [
    "CrawlerConfig",
    "DocumentRelease",
    "Scraper",
    "extract_links_sync",
    "DiffEngine",
    "DiffResult",
    "ReleaseHistory",
    "AlertChannel",
    "AlertDispatcher",
    "AlertPayload",
    "TelegramChannel",
    "DiscordChannel",
    "EmailChannel",
]