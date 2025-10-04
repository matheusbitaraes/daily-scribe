"""Online Learning-to-Rank utilities for personalized email digests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np

from components.database import DatabaseService


@dataclass
class RankerModel:
    weights: np.ndarray
    bias: float
    feature_version: str


class UserRanker:
    FEATURE_VERSION = "v1_semantic_recency_urgency_impact"

    def __init__(self, db_service: DatabaseService, learning_rate: float = 0.2):
        self.db = db_service
        self.learning_rate = learning_rate

    def _default_model(self, feature_count: int) -> RankerModel:
        weights = np.array([0.6, 0.2, 0.1, 0.1], dtype=np.float32)
        if len(weights) != feature_count:
            weights = np.ones(feature_count, dtype=np.float32) / max(feature_count, 1)
        return RankerModel(weights=weights, bias=0.0, feature_version=self.FEATURE_VERSION)

    def get_model(self, email: str, feature_count: int) -> RankerModel:
        stored = self.db.get_user_ranker_model(email)
        if stored is None:
            return self._default_model(feature_count)
        weights, bias, version = stored
        if version != self.FEATURE_VERSION or len(weights) != feature_count:
            self.db.clear_user_ranker_model(email)
            return self._default_model(feature_count)
        return RankerModel(weights=weights.astype(np.float32), bias=float(bias), feature_version=version)

    def score(self, email: str, features: Sequence[float]) -> float:
        feature_vec = np.asarray(features, dtype=np.float32)
        model = self.get_model(email, len(feature_vec))
        return float(np.dot(model.weights, feature_vec) + model.bias)

    def update(self, email: str, features: Sequence[float], signal: int) -> RankerModel:
        feature_vec = np.asarray(features, dtype=np.float32)
        model = self.get_model(email, len(feature_vec))
        direction = 1.0 if signal > 0 else -1.0
        new_weights = model.weights + self.learning_rate * direction * feature_vec
        norm = np.linalg.norm(new_weights)
        if norm > 0:
            new_weights = new_weights / norm
        new_bias = model.bias + self.learning_rate * direction
        updated = RankerModel(weights=new_weights.astype(np.float32), bias=float(new_bias), feature_version=self.FEATURE_VERSION)
        self.db.store_user_ranker_model(email, updated.weights, updated.bias, updated.feature_version)
        return updated

    def bulk_retrain(self, email: str, regularization: float = 0.01) -> Optional[RankerModel]:
        feedback = self.db.get_feedback_for_user(email)
        if not feedback:
            return None
        features = [np.asarray(fv, dtype=np.float32) for _, fv in feedback if fv is not None]
        labels = [1 if signal > 0 else -1 for signal, fv in feedback if fv is not None]
        if not features:
            return None
        feature_matrix = np.vstack(features)
        label_vec = np.asarray(labels, dtype=np.float32)
        feature_count = feature_matrix.shape[1]
        model = self._default_model(feature_count)

        weights = model.weights.copy()
        bias = model.bias
        lr = self.learning_rate
        for epoch in range(10):
            predictions = feature_matrix @ weights + bias
            errors = label_vec - predictions
            gradient = feature_matrix.T @ errors / len(label_vec) - regularization * weights
            bias_gradient = float(np.mean(errors))
            weights += lr * gradient
            bias += lr * bias_gradient
        norm = np.linalg.norm(weights)
        if norm > 0:
            weights = weights / norm
        retrained = RankerModel(weights=weights.astype(np.float32), bias=float(bias), feature_version=self.FEATURE_VERSION)
        self.db.store_user_ranker_model(email, retrained.weights, retrained.bias, retrained.feature_version)
        return retrained