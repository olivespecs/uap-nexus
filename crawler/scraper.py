"""Site scraper with rate limiting and retries."""
import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import httpx

from .config import CrawlerConfig

logger = logging.getLogger(__name__)


@dataclass
class DocumentRelease:
    """A detected document release."""

    source: str  # "PURSUE" | "AARO"
    url: str
    title: str
    file_type: Optional[str] = None  # PDF, HTML, etc
    discovered_at: datetime = None
    raw_hash: str = ""  # SHA256 of content

    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now(timezone.utc)


class Scraper:
    """Rate-limited site scraper with retry logic."""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(1)  # rate limit

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": self.config.user_agent},
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def fetch_with_retry(self, url: str) -> Optional[httpx.Response]:
        """Fetch URL with exponential backoff retry."""
        client = self._client
        if not client:
            raise RuntimeError("Scraper not initialized. Use async context manager.")

        for attempt in range(self.config.max_retries):
            try:
                async with self._semaphore:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"404 for {url} — not found")
                    return None
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    wait = self.config.retry_backoff_base ** attempt
                    await asyncio.sleep(wait)
            except httpx.RequestError as e:
                logger.warning(f"Network error {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_backoff_base ** attempt)

        logger.error(f"All retries exhausted for {url}")
        return None

    async def scrape_pursue_index(self) -> list[DocumentRelease]:
        """Scrape PURSUE/FOIA page for document links."""
        releases = []
        for path in self.config.pursue_index_paths:
            response = await self.fetch_with_retry(path)
            if not response:
                continue

            content = response.text
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            # Parse HTML for document links (PDFs, HTML files)
            links = self._extract_links(response.text, path)

            for link_url, title, file_type in links:
                raw_hash = await self._get_content_hash(link_url)
                releases.append(DocumentRelease(
                    source="PURSUE",
                    url=link_url,
                    title=title or link_url.split("/")[-1],
                    file_type=file_type,
                    raw_hash=raw_hash or "",
                ))

        return releases

    async def scrape_aaro_releases(self) -> list[DocumentRelease]:
        """Scrape AARO.mil for UAP report releases."""
        releases = []
        response = await self.fetch_with_retry(self.config.aaro_base_url)
        if not response:
            return releases

        links = self._extract_links(response.text, self.config.aaro_base_url)

        for link_url, title, file_type in links:
            if any(kw in link_url.lower() for kw in ["uap", "report", "pdf"]):
                raw_hash = await self._get_content_hash(link_url)
                releases.append(DocumentRelease(
                    source="AARO",
                    url=link_url,
                    title=title or link_url.split("/")[-1],
                    file_type=file_type,
                    raw_hash=raw_hash or "",
                ))

        return releases

    async def _get_content_hash(self, url: str) -> str:
        """Get SHA256 hash of remote content (first 64KB for large files)."""
        response = await self.fetch_with_retry(url)
        if not response:
            return ""
        content = response.content[:65536]  # First 64KB
        return hashlib.sha256(content).hexdigest()

    def _extract_links(self, html: str, base_url: str) -> list[tuple[str, str, str]]:
        """Extract document links from HTML."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href:
                continue

            # Resolve relative URLs
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)
            elif not href.startswith(("http://", "https://")):
                from urllib.parse import urljoin
                href = urljoin(base_url, href)

            # Filter for document types
            file_type = None
            lower_href = href.lower()
            if lower_href.endswith(".pdf"):
                file_type = "PDF"
            elif lower_href.endswith(".html") or lower_href.endswith(".htm"):
                file_type = "HTML"
            elif lower_href.endswith(".docx"):
                file_type = "DOCX"
            elif lower_href.endswith(".xlsx"):
                file_type = "XLSX"

            title = a.get_text(strip=True) or None

            # Include links that look like documents
            if file_type or any(kw in lower_href for kw in ["report", "release", "uap", "darpa", "foia"]):
                links.append((href, title, file_type))

        return links


def extract_links_sync(html: str, base_url: str) -> list[tuple[str, str, Optional[str]]]:
    """Synchronous link extraction for non-async use."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("beautifulsoup4 not installed, link extraction disabled")
        return []

    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue

        from urllib.parse import urljoin
        if href.startswith("/"):
            href = urljoin(base_url, href)
        elif not href.startswith(("http://", "https://")):
            href = urljoin(base_url, href)

        file_type = None
        lower_href = href.lower()
        if lower_href.endswith(".pdf"):
            file_type = "PDF"
        elif lower_href.endswith(".html") or lower_href.endswith(".htm"):
            file_type = "HTML"
        elif lower_href.endswith(".docx"):
            file_type = "DOCX"

        title = a.get_text(strip=True) or None
        links.append((href, title, file_type))

    return links
