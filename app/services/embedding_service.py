"""
Embedding service with graceful mock fallback.

When OPENAI_API_KEY is not set the service falls back to a deterministic
pseudo-embedding so the full ingestion and search pipeline can be exercised
locally without any API credentials.
"""

import hashlib
import math
from typing import List

from app.config.settings import settings

EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_SIZE = 1536


def _mock_embedding(text: str) -> List[float]:
    """
    Generate a deterministic unit-length pseudo-vector from text.

    The vector is built by hashing overlapping 4-character windows of the
    text, spreading values across all 1536 dimensions, then L2-normalising
    the result.  Identical text always produces an identical vector; similar
    text produces nearby vectors (not as accurate as a real embedding model,
    but enough to validate the full RAG pipeline without API keys).
    """
    if not text:
        return [0.0] * VECTOR_SIZE

    vector = [0.0] * VECTOR_SIZE
    chunk_size = 4
    padded = text.lower()

    for i in range(len(padded) - chunk_size + 1):
        window = padded[i : i + chunk_size]
        digest = hashlib.sha256(window.encode()).digest()
        for j in range(min(len(digest), 8)):
            idx = (i * 8 + j) % VECTOR_SIZE
            # Map byte value to [-1, 1]
            vector[idx] += (digest[j] / 127.5) - 1.0

    # Add character-frequency signal so longer / richer texts differ more
    for ch in set(padded):
        freq = padded.count(ch) / max(len(padded), 1)
        idx = (ord(ch) * 97) % VECTOR_SIZE
        vector[idx] += freq * 2.0

    # L2-normalise to unit sphere (cosine similarity requires this)
    magnitude = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / magnitude for v in vector]


def _openai_embedding(text: str) -> List[float]:
    """Call the OpenAI Embeddings API and return the vector."""
    try:
        from openai import OpenAI, OpenAIError
    except ImportError as exc:
        raise RuntimeError("openai package is not installed.") from exc

    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY in ("", "your_api_key_here"):
        raise ValueError("OPENAI_API_KEY is not configured.")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.strip(),
        )
    except OpenAIError as exc:
        raise RuntimeError("OpenAI embedding request failed.") from exc

    if not response.data or not response.data[0].embedding:
        raise RuntimeError("OpenAI returned an invalid embedding response.")

    embedding = response.data[0].embedding

    if not isinstance(embedding, list) or not all(isinstance(v, float) for v in embedding):
        raise RuntimeError("OpenAI returned an embedding in an unexpected format.")

    return embedding


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding vector for normalized incident text.

    Uses the real OpenAI API when OPENAI_API_KEY is configured, otherwise
    falls back to a deterministic mock embedding so the pipeline works
    end-to-end without API keys.
    """
    if not text or not text.strip():
        raise ValueError("Text is required to generate an embedding.")

    use_real = (
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY not in ("", "your_api_key_here")
    )

    if use_real:
        return _openai_embedding(text.strip())

    print("[embedding] OPENAI_API_KEY not set – using mock embedding.")
    return _mock_embedding(text.strip())