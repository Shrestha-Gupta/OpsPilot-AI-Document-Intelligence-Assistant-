"""
Gemini Embedding Service.
Handles generating vector embeddings for document chunks and user queries using Google Gemini via the modern google.genai SDK.
Model: gemini-embedding-001 with 768 dimensions and L2 normalization.
Optimized for high throughput, adaptive rate limiting, smart retry backoff with jitter,
and rapid daily quota exhaustion detection.
"""
import logging
import math
import random
import re
import time
from typing import Callable, List, Optional

from google import genai
from google.genai import types

from app.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.embeddings")

DEFAULT_BATCH_SIZE = 20
MAX_RETRIES = 5
INITIAL_RETRY_DELAY_SECONDS = 2.0
MAX_RETRY_DELAY_SECONDS = 65.0


def _normalize(vector: List[float]) -> List[float]:
    """Normalize vector to unit length (L2 norm) for cosine similarity."""
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def _is_daily_quota_exhausted(error: Exception) -> bool:
    """Identify Gemini daily quota exhaustion (non-retryable within current day)."""
    message = str(error).lower()
    return (
        "requests_per_day" in message
        or "per day" in message
        or "per_day" in message
        or "daily" in message
        or "embedcontentrequestsperday" in message
    )


def _parse_retry_delay(error: Exception) -> Optional[float]:
    """Extract recommended retry delay (seconds) from Gemini 429 response if present."""
    message = str(error)
    # Check details JSON: 'retryDelay': '55s' or '55.2s'
    match = re.search(r"['\"]retryDelay['\"]\s*:\s*['\"](\d+(?:\.\d+)?)s?['\"]", message)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    # Check text message: 'Please retry in 55.166318505s.'
    match = re.search(r"retry in\s+(\d+(?:\.\d+)?)\s*s", message, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return None


def _is_rate_limited(error: Exception) -> bool:
    """Identify Gemini rate/resource exhaustion responses that are retryable."""
    if _is_daily_quota_exhausted(error):
        return False
    message = str(error).lower()
    # Reject permanent configuration/request errors
    if any(term in message for term in ["invalid_argument", "api key not valid", "400", "401", "403", "404"]):
        return False
    return (
        "429" in message
        or "resource_exhausted" in message
        or "rate_limit_exceeded" in message
        or "too many requests" in message
        or "503" in message
        or "unavailable" in message
    )


class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.gemini_api_key)
        self.model = self.settings.embedding_model
        self.dimensions = self.settings.embedding_dimensions
        self.batch_size = getattr(self.settings, "embedding_batch_size", DEFAULT_BATCH_SIZE)

    def embed_query(self, query: str) -> List[float]:
        """Generate a 768-dimensional normalized embedding for a search query."""
        try:
            response = self.client.models.embed_content(
                model=self.model,
                contents=query,
                config=types.EmbedContentConfig(
                    task_type="retrieval_query",
                    output_dimensionality=self.dimensions,
                ),
            )
            return _normalize(response.embeddings[0].values)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise AppError(
                message=f"Embedding generation failed: {str(e)}",
                status_code=500,
                error_code="EMBEDDING_FAILED",
            )

    def embed_documents(
        self,
        texts: List[str],
        title: Optional[str] = None,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[List[float]]:
        """
        Generate document embeddings with rate-limit-aware batching,
        smart retry backoff with jitter, immediate healthy dispatch,
        and rapid daily quota exhaustion failure.
        """
        if not texts:
            return []

        active_batch_size = batch_size or self.batch_size or DEFAULT_BATCH_SIZE
        all_embeddings: List[List[float]] = []
        total_batches = math.ceil(len(texts) / active_batch_size)

        logger.info(
            "Generating embeddings for %d chunks in %d batches (batch_size=%d)",
            len(texts), total_batches, active_batch_size,
        )

        for batch_number, i in enumerate(range(0, len(texts), active_batch_size), start=1):
            batch = texts[i:i + active_batch_size]
            response = None

            for attempt in range(MAX_RETRIES + 1):
                try:
                    response = self.client.models.embed_content(
                        model=self.model,
                        contents=batch,
                        config=types.EmbedContentConfig(
                            task_type="retrieval_document",
                            title=title,
                            output_dimensionality=self.dimensions,
                        ),
                    )
                    break
                except Exception as e:
                    # Check for permanent daily quota exhaustion first
                    if _is_daily_quota_exhausted(e):
                        logger.error(
                            "Gemini daily quota exhausted at batch %d/%d: %s",
                            batch_number, total_batches, e,
                        )
                        raise AppError(
                            message=(
                                "Gemini embedding daily quota has been exceeded (1,000 requests/day on Free Tier). "
                                "Please retry tomorrow or upgrade your Gemini API tier in Google AI Studio."
                            ),
                            status_code=429,
                            error_code="DAILY_QUOTA_EXHAUSTED",
                        )

                    # Non-retryable error
                    if not _is_rate_limited(e):
                        logger.error(
                            "Embedding failed at batch %d/%d: %s",
                            batch_number, total_batches, e,
                        )
                        raise AppError(
                            message=f"Document embedding generation failed: {str(e)}",
                            status_code=500,
                            error_code="EMBEDDING_FAILED",
                        )

                    # Max retries reached
                    if attempt >= MAX_RETRIES:
                        logger.error(
                            "Gemini rate limit persisted at batch %d/%d after %d retries: %s",
                            batch_number, total_batches, MAX_RETRIES, e,
                        )
                        raise AppError(
                            message=(
                                "Gemini embedding rate limit persisted after retries. "
                                "Please retry the document upload after a short wait."
                            ),
                            status_code=429,
                            error_code="EMBEDDING_RATE_LIMITED",
                        )

                    # Smart backoff: prefer API-suggested retryDelay, otherwise exponential with jitter
                    parsed_delay = _parse_retry_delay(e)
                    if parsed_delay is not None:
                        delay = min(parsed_delay, MAX_RETRY_DELAY_SECONDS) + random.uniform(0.5, 1.5)
                    else:
                        delay = min(
                            INITIAL_RETRY_DELAY_SECONDS * (2 ** attempt) + random.uniform(0.2, 1.0),
                            MAX_RETRY_DELAY_SECONDS,
                        )

                    logger.warning(
                        "Gemini rate limit: batch %d/%d (retry %d/%d in %.1fs)",
                        batch_number, total_batches, attempt + 1, MAX_RETRIES, delay,
                    )
                    time.sleep(delay)

            if response is None:
                raise AppError(
                    message="Document embedding generation failed: no response from Gemini",
                    status_code=500,
                    error_code="EMBEDDING_FAILED",
                )

            if len(response.embeddings) != len(batch):
                raise AppError(
                    message=(
                        "Gemini returned an unexpected number of embeddings "
                        f"({len(response.embeddings)} for {len(batch)} chunks)"
                    ),
                    status_code=500,
                    error_code="EMBEDDING_COUNT_MISMATCH",
                )

            all_embeddings.extend(_normalize(emb.values) for emb in response.embeddings)
            logger.info(
                "Embedded batch %d/%d (%d/%d chunks)",
                batch_number, total_batches, len(all_embeddings), len(texts),
            )

            if progress_callback:
                try:
                    progress_callback(len(all_embeddings), len(texts))
                except Exception as cb_err:
                    logger.debug("Progress callback error: %s", cb_err)

            # Process healthy batches immediately without artificial sleep delay

        return all_embeddings


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
