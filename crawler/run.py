#!/usr/bin/env python3
"""
UAP NEXUS Crawler — PURSUE tracker runner.

Usage:
    python -m crawler.run          # normal poll cycle
    python -m crawler.run --once  # single run, no loop
    python -m crawler.run --url https://... # test specific URL

Environment variables:
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_IDS
    DISCORD_WEBHOOK_URL
    SENDGRID_API_KEY, ALERT_FROM_EMAIL, ALERT_TO_EMAILS
"""
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler import CrawlerConfig, Scraper, DiffEngine, ReleaseHistory, AlertDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("crawler")


async def crawl_cycle(config: CrawlerConfig) -> int:
    """Run one full crawl cycle. Returns number of new releases detected."""
    logger.info("Starting crawl cycle...")

    async with Scraper(config) as scraper:
        all_releases = []

        # Scrape PURSUE index pages
        logger.info("Scraping PURSUE index...")
        pursue_releases = await scraper.scrape_pursue_index()
        all_releases.extend(pursue_releases)
        logger.info(f"PURSUE: found {len(pursue_releases)} documents")

        # Scrape AARO direct releases
        logger.info("Scraping AARO releases...")
        aaro_releases = await scraper.scrape_aaro_releases()
        all_releases.extend(aaro_releases)
        logger.info(f"AARO: found {len(aaro_releases)} documents")

        # Diff against known state
        diff_engine = DiffEngine(config.state_dir)
        diff_result = diff_engine.diff(all_releases)

        # Record to history
        history = ReleaseHistory(config.state_dir)
        history.record(diff_result.new_releases, "new_release")
        history.record(diff_result.updated_releases, "content_update")

        # Dispatch alerts
        if diff_result.new_releases or diff_result.updated_releases:
            dispatcher = AlertDispatcher().from_env()
            if dispatcher.channels:
                await dispatcher.dispatch(
                    diff_result.new_releases + diff_result.updated_releases
                )
            else:
                logger.info("No alert channels configured — skipping dispatch")

        logger.info(
            f"Crawl complete: {len(diff_result.new_releases)} new, "
            f"{len(diff_result.updated_releases)} updated"
        )

        return len(diff_result.new_releases)


async def run_continuous(config: CrawlerConfig):
    """Run crawl loop indefinitely."""
    logger.info(
        f"Starting continuous crawler (poll every {config.poll_interval_seconds}s)..."
    )

    while True:
        try:
            new_count = await crawl_cycle(config)
        except Exception as e:
            logger.exception(f"Crawl cycle failed: {e}")

        await asyncio.sleep(config.poll_interval_seconds)


def main():
    parser = argparse.ArgumentParser(description="UAP NEXUS Crawler")
    parser.add_argument("--once", action="store_true", help="Run single cycle, no loop")
    parser.add_argument("--url", type=str, help="Test scrape a specific URL")
    args = parser.parse_args()

    config = CrawlerConfig()

    if args.url:
        # Test mode — scrape single URL
        async def test_url():
            async with Scraper(config) as scraper:
                response = await scraper.fetch_with_retry(args.url)
                if response:
                    print(f"Status: {response.status_code}")
                    print(f"Content length: {len(response.content)}")
                    print(f"Content-Type: {response.headers.get('content-type')}")
                else:
                    print("Failed to fetch URL")

        asyncio.run(test_url())
        return

    if args.once:
        new_count = asyncio.run(crawl_cycle(config))
        sys.exit(0 if new_count > 0 else 0)  # Exit 0 regardless, don't fail on no new docs
    else:
        asyncio.run(run_continuous(config))


if __name__ == "__main__":
    main()