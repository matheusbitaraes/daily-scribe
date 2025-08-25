"""
Summarization service for Daily Scribe application.

This module handles summarizing article text using the Gemini API.
"""

import logging
import re
import time
import google.generativeai as genai
from components.config import GeminiConfig
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class NewsMetadata(BaseModel):
    summary: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN THE ORIGINAL LANGUAGE OF THE ARTICLE")
    sentiment: str = Field(description="The overall sentiment of the article (Positive, Negative, Neutral).")
    keywords: List[str] = Field(description="A list of key people, organizations, or locations mentioned.")
    category: str = Field(description="The main category of the news. Select one of those options: 'Politics', 'Technology', 'Science and Health', 'Business', 'Entertainment', 'Sports'. Use the category 'Other' if none of the options fit.")
    region: str = Field(description="The primary geographical place the news is about (e.g., Brazil, USA, Europe, Asia).")

class Summarizer:
    """Handles summarizing text using the Gemini API."""

    def __init__(self, config: GeminiConfig):
        """
        Initialize the summarizer.

        Args:
            config: The Gemini API configuration.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self._initialize_gemini()

    def _initialize_gemini(self):
        """
        Initialize the Gemini client.
        """
        try:
            self.logger.info("Initializing Gemini client.")
            genai.configure(api_key=self.config.api_key)
            self.logger.info("Gemini client initialized successfully.")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    def summarize(self, text: str, max_retries: int = 5) -> Dict[str, Any]:
        """
        Summarize the given text and extract metadata.

        Args:
            text: The text to summarize.
            max_length: The maximum length of the summary.
            min_length: The minimum length of the summary.
            max_retries: The maximum number of retries.

        Returns:
            A dict with summary, sentiment, keywords, category, region.
        """
        # Use genai.GenerativeModel instead of genai.Client
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Extract the requested metadata from the following news content: {text}"
        for attempt in range(max_retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=NewsMetadata,
                    )
                )
                # Try to parse the response as JSON from the first part
                try:
                    # Gemini's response may have a 'text' field with JSON string
                    part = response.candidates[0].content.parts[0]
                    if hasattr(part, 'text'):
                        import json
                        return json.loads(part.text)
                    # Fallback: if part is already a dict
                    if isinstance(part, dict):
                        return part
                except Exception as parse_exc:
                    self.logger.error(f"Failed to parse Gemini response as JSON: {parse_exc}")
                    return {}
            except Exception as e:
                error_message = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed: {error_message}")
                if "rate limit" in error_message.lower():
                    wait_time = self._extract_wait_time(error_message)
                    if wait_time:
                        self.logger.info(f"Rate limit exceeded. Waiting for {wait_time} seconds.")
                        time.sleep(wait_time)
                    else:
                        self.logger.warning("Could not extract wait time. Using default backoff.")
                        time.sleep(2 ** attempt)
                else:
                    self.logger.error(f"An unexpected error occurred: {error_message}")
                    break
        self.logger.error("Failed to summarize text after multiple retries.")
        return {}

    def _extract_wait_time(self, error_message: str) -> int:
        """
        Extract the wait time from the error message.

        Args:
            error_message: The error message from the API.

        Returns:
            The wait time in seconds, or None if not found.
        """
        # Try to extract retry_delay { seconds: N } (with or without whitespace)
        match = re.search(r"retry_delay\s*\{[^}]*seconds:\s*(\d+)", error_message)
        if match:
            return int(match.group(1))
        # Try to extract retry after N
        match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # Try to extract wait N seconds
        match = re.search(r"wait (\d+) seconds", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None