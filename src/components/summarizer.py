"""
Summarization service for Daily Scribe application.

This module handles summarizing article text using the Gemini API.
"""

import logging
import re
import time
import google.generativeai as genai
from components.config import GeminiConfig

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

    def summarize(self, text: str, max_length: int = 150, min_length: int = 40, max_retries: int = 5) -> str:
        """
        Summarize the given text.

        Args:
            text: The text to summarize.
            max_length: The maximum length of the summary.
            min_length: The minimum length of the summary.
            max_retries: The maximum number of retries.

        Returns:
            The summarized text.
        """
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Summarize the following text in approximately {min_length} to {max_length} words: {text}"
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                return response.text
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
                        time.sleep(5 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"An unexpected error occurred: {error_message}")
                    break  # Break on non-rate-limit errors

        self.logger.error("Failed to summarize text after multiple retries.")
        return ""

    def _extract_wait_time(self, error_message: str) -> int:
        """
        Extract the wait time from the error message.

        Args:
            error_message: The error message from the API.

        Returns:
            The wait time in seconds, or None if not found.
        """
        match = re.search(r"retry_delay {\s*seconds: (\d+)", error_message)
        if match:
            return int(match.group(1))
        
        match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        match = re.search(r"wait (\d+) seconds", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
            
        return None