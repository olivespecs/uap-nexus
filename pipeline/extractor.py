"""Claude API structured extraction."""
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from .schemas import Source

logger = logging.getLogger(__name__)


# Default extraction prompt
EXTRACTION_PROMPT = """You are analyzing a declassified UAP government document.
Extract and return ONLY valid JSON matching this schema:

{
  "incident_date": "YYYY-MM-DD or null",
  "agency": "string",
  "location": {"name": "string", "lat": float or null, "lon": float or null},
  "craft_description": "string — shape, size, color, behavior",
  "witnesses": ["array of witness roles or names"],
  "anomalous_characteristics": ["list of observed anomalies"],
  "resolution": "UNRESOLVED|RESOLVED|UNKNOWN",
  "key_quotes": ["max 3 notable verbatim short quotes"]
}

Document text:
{DocumentText}
"""


@dataclass
class ExtractedIncident:
    """Structured incident data extracted from document."""

    incident_date: Optional[date] = None
    agency: str = ""
    location_name: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    craft_description: str = ""
    witnesses: list[str] = None
    anomalous_characteristics: list[str] = None
    resolution: str = "UNKNOWN"
    key_quotes: list[str] = None
    raw_json: str = ""

    def __post_init__(self):
        if self.witnesses is None:
            self.witnesses = []
        if self.anomalous_characteristics is None:
            self.anomalous_characteristics = []
        if self.key_quotes is None:
            self.key_quotes = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "agency": self.agency,
            "location": {
                "name": self.location_name,
                "lat": self.lat,
                "lon": self.lon,
            },
            "craft_description": self.craft_description,
            "witnesses": self.witnesses,
            "anomalous_characteristics": self.anomalous_characteristics,
            "resolution": self.resolution,
            "key_quotes": self.key_quotes,
        }


class ClaudeExtractor:
    """Claude API for structured document extraction."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        import os

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")

        if not self.api_key:
            logger.warning("Claude API key not configured")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        """Create Anthropic client with custom base URL support."""
        import anthropic

        # Use custom base URL if configured (for OpenCode, Bedrock, etc.)
        if self.base_url and self.base_url != "https://api.anthropic.com":
            return anthropic.AsyncAnthropic(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return anthropic.AsyncAnthropic(api_key=self.api_key)

    async def extract(self, text: str, prompt: Optional[str] = None) -> ExtractedIncident:
        """Extract structured incident from document text."""
        if not self.is_configured():
            return ExtractedIncident()

        full_prompt = (prompt or EXTRACTION_PROMPT).format(DocumentText=text[:50000])

        try:
            client = self._get_client()
        except ImportError:
            logger.error("anthropic SDK not installed")
            return ExtractedIncident()

        loop = asyncio.get_event_loop()

        def sync_call():
            return client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0,
                system="You are an expert at analyzing government documents about Unidentified Aerospace Phenomena (UAP). Extract structured data following the provided schema exactly. Return ONLY valid JSON, no markdown.",
                messages=[{"role": "user", "content": full_prompt}],
            )

        try:
            response = await loop.run_in_executor(None, sync_call)
            content = response.content[0].text

            # Parse JSON from response
            parsed = json.loads(content)

            return ExtractedIncident(
                incident_date=date.fromisoformat(parsed["incident_date"]) if parsed.get("incident_date") else None,
                agency=parsed.get("agency", ""),
                location_name=parsed.get("location", {}).get("name", ""),
                lat=parsed.get("location", {}).get("lat"),
                lon=parsed.get("location", {}).get("lon"),
                craft_description=parsed.get("craft_description", ""),
                witnesses=parsed.get("witnesses", []),
                anomalous_characteristics=parsed.get("anomalous_characteristics", []),
                resolution=parsed.get("resolution", "UNKNOWN"),
                key_quotes=parsed.get("key_quotes", []),
                raw_json=content,
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}, content: {content[:500]}")
            return ExtractedIncident(raw_json=content[:1000])
        except Exception as e:
            logger.error(f"Claude extraction failed: {e}")
            return ExtractedIncident()

    async def extract_from_ocr(self, ocr_text: str) -> ExtractedIncident:
        """Extract incident from pre-OCR'd text."""
        return await self.extract(ocr_text)

    async def summarize(self, text: str, max_words: int = 100) -> str:
        """Generate a brief summary of document content."""
        if not self.is_configured():
            return "[Claude not configured]"

        try:
            client = self._get_client()
        except ImportError:
            return "[anthropic SDK not installed]"

        prompt = f"""Summarize this UAP government document in {max_words} words or fewer. Focus on: date, location, craft description, anomalous behavior, and any government response.

Document:
{text[:30000]}"""

        def sync_call():
            return client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, sync_call)

        return response.content[0].text.strip()


async def extract_incident(text: str) -> ExtractedIncident:
    """Convenience function for quick extraction."""
    extractor = ClaudeExtractor()
    return await extractor.extract(text)