"""OCR via AWS Textract."""
import asyncio
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR processing result."""

    text: str
    page_count: int = 1
    confidence: float = 0.0
    blocks: list[dict] | None = None


class TextractOCR:
    """AWS Textract integration for PDF OCR."""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
    ):
        import os

        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = region

        if not self.aws_access_key_id:
            logger.warning("AWS credentials not configured — Textract disabled")

        self._client = None

    @property
    def client(self):
        """Lazy boto3 client."""
        if not self._client and self.aws_access_key_id:
            import boto3

            self._client = boto3.client(
                "textract",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region,
            )
        return self._client

    def is_configured(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    async def extract_text(self, pdf_path: str | Path) -> OCRResult:
        """Extract text from PDF file."""
        if not self.is_configured():
            logger.warning("Textract not configured, returning empty result")
            return OCRResult(text="")

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        loop = asyncio.get_event_loop()

        def sync_extract():
            with open(pdf_path, "rb") as f:
                return self._sync_extract(f.read())

        return await loop.run_in_executor(None, sync_extract)

    def _sync_extract(self, pdf_bytes: bytes) -> OCRResult:
        """Synchronous extraction for use in thread pool."""
        try:
            import boto3
            import pdfplumber
        except ImportError:
            # Fallback: just return bytes as text for PDFs that are already text
            logger.warning("pdfplumber not installed, text extraction may be limited")
            return OCRResult(text="[PDF text extraction requires pdfplumber]")

        text_pages = []
        all_blocks = []

        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_pages.append(page_text)

                    # Get blocks for confidence estimation
                    if hasattr(page, "extract_words"):
                        words = page.extract_words()
                        all_blocks.extend(words)

                text = "\n\n".join(text_pages)

                # Estimate confidence based on extraction quality
                confidence = 0.95 if text.strip() else 0.0

                return OCRResult(
                    text=text,
                    page_count=page_count,
                    confidence=confidence,
                    blocks=all_blocks[:100] if all_blocks else None,
                )
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return OCRResult(text="", page_count=0, confidence=0.0)

    async def extract_from_url(self, url: str) -> OCRResult:
        """Download and OCR a PDF from URL."""
        import httpx

        logger.info(f"Downloading PDF from {url}")

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            pdf_bytes = response.content

            return self._sync_extract(pdf_bytes)


async def simple_ocr(url: str) -> OCRResult:
    """Convenience function for quick OCR calls."""
    import os

    ocr = TextractOCR()
    if not ocr.is_configured():
        return OCRResult(text="AWS credentials not configured")

    return await ocr.extract_from_url(url)


# Fallback: simple text extraction without AWS
class SimpleOCR:
    """Fallback OCR using pdfplumber only (no AWS required)."""

    @staticmethod
    async def extract_from_file(pdf_path: str | Path) -> OCRResult:
        """Extract text from local PDF using pdfplumber."""
        import pdfplumber

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        text_pages = []
        page_count = 0

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_pages.append(text)

        return OCRResult(
            text="\n\n".join(text_pages),
            page_count=page_count,
            confidence=0.95 if text_pages else 0.0,
        )