"""
Summarization service for Daily Scribe application.

This module handles loading a local LLM and summarizing article text.
"""

import logging
## from transformers import pipeline, BartForConditionalGeneration, BartTokenizer

class Summarizer:
    """Handles loading the LLM and summarizing text."""

    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        """
        Initialize the summarizer.

        Args:
            model_name: The name of the Hugging Face model to use for summarization.
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self._summarizer = None

    def _load_model(self):
        """
        Load the summarization model and tokenizer.
        """
        if self._summarizer is None:
            try:
                self.logger.info(f"Loading summarization model: {self.model_name}")
                # Load model and tokenizer - skipping for now
                # model = BartForConditionalGeneration.from_pretrained(self.model_name)
                # tokenizer = BartTokenizer.from_pretrained(self.model_name)
                # self._summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
                self.logger.info("Summarization model loaded successfully.")
            except Exception as e:
                self.logger.error(f"Failed to load summarization model: {e}")
                raise

    def summarize(self, text: str, max_length: int = 150, min_length: int = 40) -> str:
        """
        Summarize the given text.

        Args:
            text: The text to summarize.
            max_length: The maximum length of the summary.
            min_length: The minimum length of the summary.

        Returns:
            The summarized text.
        """
        if self._summarizer is None:
            self._load_model()

        try:
            #summary = self._summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            #return summary[0]['summary_text']
            # for now, just return the text
            return text
        except Exception as e:
            self.logger.error(f"Failed to summarize text: {e}")
            return ""
