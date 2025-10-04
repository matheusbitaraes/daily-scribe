"""Feature engineering utilities for Learning-to-Rank models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence
import os
import numpy as np


DEFAULT_HALF_LIFE_HOURS = float(os.getenv("LTR_TIME_HALF_LIFE_HOURS", "240"))


def _parse_datetime(value) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def build_feature_vector(
    *,
    article: dict,
    user_embedding: Optional[np.ndarray] = None,
    article_embedding: Optional[np.ndarray] = None,
    reference_time: Optional[datetime] = None,
    half_life_hours: Optional[float] = None,
) -> np.ndarray:
    """Return LTR feature vector in order [semantic, recency, urgency, impact]."""
    if half_life_hours is None:
        half_life_hours = DEFAULT_HALF_LIFE_HOURS
    if half_life_hours <= 0:
        half_life_hours = DEFAULT_HALF_LIFE_HOURS

    semantic_score = 0.0
    if user_embedding is not None and article_embedding is not None:
        denom = (np.linalg.norm(user_embedding) * np.linalg.norm(article_embedding)) + 1e-8
        semantic_score = float(np.dot(user_embedding, article_embedding) / denom)
        semantic_score = float(np.clip(semantic_score, -1.0, 1.0))

    published_at = _parse_datetime(article.get("published_at"))
    recency_score = 0.0
    ref_time = reference_time.astimezone(timezone.utc) if reference_time else datetime.now(timezone.utc)
    if published_at is not None:
        hours_since = (ref_time - published_at).total_seconds() / 3600
        if hours_since < 0:
            hours_since = 0
        decay = 0.5 ** (hours_since / max(half_life_hours, 1.0))
        recency_score = float(np.clip(decay, 0.0, 1.0))

    urgency = float(article.get("urgency_score") or 0.0) / 100.0
    impact = float(article.get("impact_score") or 0.0) / 100.0

    vector = np.array([semantic_score, recency_score, urgency, impact], dtype=np.float32)
    return vector


def serialize_feature_vector(vector: Sequence[float]) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()