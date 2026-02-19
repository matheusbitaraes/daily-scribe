"""
Unit tests for the Summarizer component.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from components.summarizer import NewsMetadata, Summarizer


@pytest.fixture
def sample_metadata():
    """Valid NewsMetadata-compatible dict for mocking."""
    return {
        "summary": "This is a brief summary in English.",
        "summary_pt": "Este é um resumo breve em português.",
        "title_pt": "Título traduzido",
        "sentiment": "Neutral",
        "keywords": ["Brazil", "economy"],
        "category": "Business",
        "region": "Brazil",
        "urgency_score": 50,
        "impact_score": 60,
        "subject_pt": "Economia brasileira",
    }


def test_news_metadata_schema():
    """NewsMetadata has expected fields."""
    fields = list(NewsMetadata.model_fields.keys())
    assert "summary" in fields
    assert "summary_pt" in fields
    assert "title_pt" in fields
    assert "sentiment" in fields
    assert "keywords" in fields
    assert "category" in fields
    assert "region" in fields
    assert "urgency_score" in fields
    assert "impact_score" in fields
    assert "subject_pt" in fields


def test_summarizer_returns_empty_dict_on_failure(monkeypatch):
    """When LLM fails, summarize returns empty dict."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch("components.summarizer.LLMClient") as MockLLM:
        mock_client = MagicMock()
        mock_client.complete_with_schema.return_value = None
        MockLLM.return_value = mock_client

        summarizer = Summarizer()
        result = summarizer.summarize("Some article text")

        assert result == {}
        mock_client.complete_with_schema.assert_called_once()


def test_summarizer_returns_metadata_on_success(monkeypatch, sample_metadata):
    """When LLM succeeds, summarize returns metadata dict with expected keys."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    with patch("components.summarizer.LLMClient") as MockLLM:
        mock_client = MagicMock()
        mock_client.complete_with_schema.return_value = sample_metadata
        MockLLM.return_value = mock_client

        summarizer = Summarizer()
        result = summarizer.summarize("Some article text")

        assert result == sample_metadata
        assert result.get("summary") == sample_metadata["summary"]
        assert result.get("summary_pt") == sample_metadata["summary_pt"]
        assert result.get("urgency_score") == 50
        mock_client.complete_with_schema.assert_called_once()
