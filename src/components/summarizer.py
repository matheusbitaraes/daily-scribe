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
        self._pro_quota_exceeded = False
        self._flash_quota_exceeded = False

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

    def summarize(self, text: str, max_retries: int = 3) -> Dict[str, Any]:
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
        # Try pro first unless quota exceeded, then fallback to flash
        model_order = []
        if not self._pro_quota_exceeded:
            model_order.append('gemini-2.5-pro')
        if not self._flash_quota_exceeded:
            model_order.append('gemini-2.5-flash')
        if not model_order:
            self.logger.error("All Gemini model quotas exceeded. Aborting summarization.")
            return {}
        for model_name in model_order:
            model = genai.GenerativeModel(model_name)
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
                        part = response.candidates[0].content.parts[0]
                        if hasattr(part, 'text'):
                            import json
                            return json.loads(part.text)
                        if isinstance(part, dict):
                            return part
                    except Exception as parse_exc:
                        self.logger.error(f"Failed to parse Gemini response as JSON: {parse_exc}")
                        return {}
                except Exception as e:
                    error_message = str(e)
                    self.logger.warning(f"[{model_name}] Attempt {attempt + 1} failed: {error_message}")
                    # Check for daily quota exceeded for this model
                    if "GenerateRequestsPerDayPerProjectPerModel" in error_message:
                        self.logger.error(f"Gemini API daily quota exceeded for {model_name}. Will not use this model anymore today.")
                        if model_name == 'gemini-2.5-pro':
                            self._pro_quota_exceeded = True
                        elif model_name == 'gemini-2.5-flash':
                            self._flash_quota_exceeded = True
                        break  # Try next model if available
                    
                    # Check for per-minute rate limit
                    if "GenerateRequestsPerMinutePerProjectPerModel" in error_message:
                        wait_time = self._extract_wait_time(error_message)
                        if wait_time:
                            self.logger.info(f"Per-minute rate limit exceeded. Waiting for {wait_time} seconds.")
                            time.sleep(wait_time)
                        else:
                            self.logger.warning("Per-minute rate limit exceeded. Using default backoff.")
                            time.sleep(2 ** attempt)
                        continue  # Retry this model after waiting
                    else:
                        self.logger.error(f"An unexpected error occurred: {error_message}")
                        break
            # If we get here, try next model if available
        self.logger.error("Failed to summarize text after trying all available Gemini models and retries.")
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