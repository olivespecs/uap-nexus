"""Crawler API routes."""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter()


class CrawlRequest(BaseModel):
    """Manual crawl trigger request."""

    source: Optional[str] = None  # "pursue", "aaro", or None for all


class CrawlStatus(BaseModel):
    """Crawl status response."""

    status: str
    last_run: Optional[str] = None
    new_releases: int = 0
    updated_releases: int = 0


# Crawler state
_crawler_state: dict = {"last_run": None, "new_releases": 0, "updated_releases": 0}


@router.get("/status")
async def get_status():
    """Get crawler status."""
    return CrawlStatus(
        status="running" if _crawler_state.get("running") else "idle",
        last_run=_crawler_state.get("last_run"),
        new_releases=_crawler_state.get("new_releases", 0),
        updated_releases=_crawler_state.get("updated_releases", 0),
    )


@router.post("/trigger")
async def trigger_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """Manually trigger a crawl."""
    from crawler import CrawlerConfig

    async def run_crawl():
        _crawler_state["running"] = True

        try:
            from crawler.run import crawl_cycle

            config = CrawlerConfig()
            result = await crawl_cycle(config)

            _crawler_state["last_run"] = datetime.utcnow().isoformat()
            _crawler_state["new_releases"] = result
        finally:
            _crawler_state["running"] = False

    background_tasks.add_task(run_crawl())

    return {"status": "triggered", "message": "Crawl started in background"}


@router.get("/history")
async def get_history(hours: int = 24):
    """Get crawl history."""
    from crawler.diff_engine import ReleaseHistory

    history = ReleaseHistory()
    recent = history.recent(hours)

    return {"releases": recent, "count": len(recent)}


@router.get("/state")
async def get_crawler_state():
    """Get raw crawler state (debug)."""
    import json
    from pathlib import Path

    state_dir = Path(__file__).parent.parent / "crawler" / ".state"
    state = {}

    for f in state_dir.glob("*.json"):
        if f.name != "release_history.json":
            try:
                state[f.stem] = json.loads(f.read_text())
            except:
                pass

    return {"state_files": state, "memory": dict(_crawler_state)}