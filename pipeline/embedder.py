"""Embedding via pgvector."""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Text embedding result."""

    vector: list[float]
    model: str
    token_count: int = 0


EMBEDDING_MODEL = "amazon-embeddings-bedrock"


class Embedder:
    """Text embedding for similarity search."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "amazon-embeddings-bedrock",
    ):
        import os

        self.api_key = api_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model = model

        if not self.api_key:
            logger.warning("AWS credentials not configured — embedder disabled")

        self._client = None

    @property
    def client(self):
        """Lazy boto3 client."""
        if not self._client and self.api_key:
            import boto3

            self._client = boto3.client(
                "bedrock-runtime",
                aws_access_key_id=self.api_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
        return self._client

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for text."""
        if not self.is_configured():
            logger.warning("Embedder not configured, returning zero vector")
            return EmbeddingResult(vector=[0.0] * 1536, model="none")

        # Truncate text to fit model context
        text = text[:8000]

        try:
            import boto3

            body = json.dumps({"inputText": text})

            response = self.client.invoke_model(
                modelId=self.model,
                contentType="application/json",
                accept="application/json",
                body=body,
            )

            import json as json_mod

            result = json_mod.loads(response["body"].read())
            embedding = result["embedding"]

            return EmbeddingResult(
                vector=embedding,
                model=self.model,
                token_count=len(text.split()),
            )
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return EmbeddingResult(vector=[0.0] * 1536, model=self.model)


# Fallback: simple hash-based embedding for testing
class SimpleEmbedder:
    """Fallback embedder using hash (for testing without AWS)."""

    @staticmethod
    def embed(text: str) -> list[float]:
        """Generate deterministic pseudo-embedding from text hash."""
        import hashlib

        text = text[:1000]  # Limit input

        # Generate multiple hashes for dimension
        vector = []
        for i in range(1536):
            h = hashlib.sha256(f"{text}:{i}".encode()).hexdigest()
            # Convert hex to -1 to 1 range
            value = (int(h[:8], 16) - 0x80000000) / 0x100000000
            vector.append(value)

        return vector


async def embed_text(text: str) -> list[float]:
    """Convenience function for quick embedding."""
    embedder = Embedder()
    result = await embedder.embed(text)
    return result.vector


import json