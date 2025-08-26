"""
Summarization service for Daily Scribe application.

This module handles summarizing article text using the Gemini API.
"""

import logging
import re
import time
import datetime
import google.generativeai as genai
from components.config import GeminiConfig
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class NewsMetadata(BaseModel):
    summary: str = Field(description="Summarize the following text in approximately 40 to 100 words and DO IT ALWAYS IN THE ORIGINAL LANGUAGE OF THE ARTICLE (LIMITED TO ENGLISH OR BRAZILIAN PORTUGUESE).")
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
        
        # Store quota exceeded status for each model in a dict
        self._quota_exceeded = {
            'gemini-2.5-pro': True, # not using pro for now
            'gemini-2.5-flash': False,
            'gemini-2.5-flash-lite': False,
            'gemini-2.0-flash': False,
            'gemini-2.0-flash-lite': False,
        }
        # List of model names in order of preference
        self._model_order = [
            'gemini-2.0-flash-lite',
            'gemini-2.5-flash-lite',
            'gemini-2.0-flash',
            'gemini-2.5-flash',
            'gemini-2.5-pro',
        ]
        # Track per-minute rate limit for each model
        self._rate_limited_until = {model: None for model in self._model_order}

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
        """
        while True: # start all models iteration
            any_model_usable = False
            now = datetime.datetime.now()
            soonest_ready = None
            for model_name in self._model_order:
                until = self._rate_limited_until.get(model_name)
                if self._quota_exceeded.get(model_name):
                    continue
                if until and now < until:
                    if soonest_ready is None or until < soonest_ready:
                        soonest_ready = until
                    continue
                any_model_usable = True
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
                        if "GenerateRequestsPerDayPerProjectPerModel" in error_message:
                            self.logger.error(f"Gemini API daily quota exceeded for {model_name}. Will not use this model anymore today.")
                            self._quota_exceeded[model_name] = True
                            break
                        if "GenerateRequestsPerMinutePerProjectPerModel" in error_message:
                            wait_time = self._extract_wait_time(error_message) or 60
                            until = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
                            self._rate_limited_until[model_name] = until
                            self.logger.info(f"Model {model_name} is rate-limited until {until:%Y-%m-%d %H:%M:%S}.")
                            break
                        else:
                            self.logger.error(f"An unexpected error occurred: {error_message}")
                            break
            if any_model_usable:
                # We tried all usable models, none succeeded, so exit
                break
            if soonest_ready:
                sleep_seconds = max(1, int((soonest_ready - datetime.datetime.now()).total_seconds()))
                self.logger.info(f"All models are rate-limited. Waiting {sleep_seconds} seconds for next available model.")
                time.sleep(sleep_seconds)
            else:
                break
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