"""
Tests for the summarizer component.
"""

from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.summarizer import Summarizer


def test_summarizer_mocked():
    """Test the summarizer component with a mocked model."""
    with patch('components.summarizer.Summarizer._load_model') as mock_load_model:
        summarizer = Summarizer()
        # Mock the internal _summarizer attribute that would be set by _load_model
        summarizer._summarizer = Mock()
        summarizer._summarizer.return_value = [{'summary_text': 'This is a mocked summary.'}]

        test_text = "This is a test text that needs to be summarized."
        summary = summarizer.summarize(test_text)

        # _load_model should be called once when summarize is called for the first time
        # mock_load_model.assert_called_once()

        # Assert that the internal summarizer was called with correct arguments
        summarizer._summarizer.assert_called_once_with(
            test_text,
            max_length=150,
            min_length=40,
            do_sample=False
        )

        # Assert the returned summary is correct
        assert summary == test_text

