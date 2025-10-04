import math
import os
import sys
from datetime import datetime, timezone, timedelta

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.ranking.feature_engineer import build_feature_vector
from components.ranking.user_ranker import UserRanker


class FakeDB:
    def __init__(self):
        self.model_store = {}
        self.feedback_store = {}

    def get_user_ranker_model(self, email):
        return self.model_store.get(email)

    def clear_user_ranker_model(self, email):
        self.model_store.pop(email, None)

    def store_user_ranker_model(self, email, weights, bias, feature_version):
        self.model_store[email] = (weights, bias, feature_version)

    def get_feedback_for_user(self, email):
        return self.feedback_store.get(email, [])

    def append_feedback(self, email, feature_vector, signal):
        self.feedback_store.setdefault(email, []).append((signal, feature_vector))


@pytest.fixture
def article():
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "published_at": (now - timedelta(hours=6)).isoformat(),
        "urgency_score": 80,
        "impact_score": 60,
    }


def test_build_feature_vector_with_embeddings(article):
    user_embedding = np.ones(4, dtype=np.float32)
    article_embedding = np.ones(4, dtype=np.float32)
    vector = build_feature_vector(
        article=article,
        user_embedding=user_embedding,
        article_embedding=article_embedding,
        reference_time=datetime.now(timezone.utc),
        half_life_hours=24,
    )
    assert vector.shape == (4,)
    # Semantic similarity of identical vectors should be close to 1
    assert pytest.approx(vector[0], rel=1e-3) == 1.0
    # Recency should be between 0 and 1
    assert 0.0 <= vector[1] <= 1.0
    # Urgency/impact normalized
    assert vector[2] == pytest.approx(0.8, rel=1e-3)
    assert vector[3] == pytest.approx(0.6, rel=1e-3)


def test_user_ranker_updates_weights(article):
    fake_db = FakeDB()
    ranker = UserRanker(fake_db, learning_rate=0.5)
    features = np.array([0.5, 0.5, 0.2, 0.1], dtype=np.float32)
    initial_score = ranker.score("user@example.com", features)
    assert isinstance(initial_score, float)

    ranker.update("user@example.com", features, signal=1)
    updated_weights, _, _ = fake_db.get_user_ranker_model("user@example.com")
    assert updated_weights is not None
    updated_score = ranker.score("user@example.com", features)
    assert updated_score > initial_score


def test_user_ranker_bulk_retrain(article):
    fake_db = FakeDB()
    features_positive = np.array([1.0, 0.9, 0.5, 0.4], dtype=np.float32)
    features_negative = np.array([-0.5, 0.1, 0.0, 0.0], dtype=np.float32)
    fake_db.append_feedback("user@example.com", features_positive, 1)
    fake_db.append_feedback("user@example.com", features_negative, -1)

    ranker = UserRanker(fake_db, learning_rate=0.1)
    model = ranker.bulk_retrain("user@example.com")
    assert model is not None
    assert math.isfinite(model.bias)
    assert model.weights.shape == features_positive.shape
    assert fake_db.get_user_ranker_model("user@example.com") is not None
