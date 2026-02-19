"""
LLM client abstraction using LiteLLM with multi-provider fallbacks.

Uses LiteLLM for unified completion calls across providers. Instructor is optional
(Python 3.10+); when unavailable, we use LiteLLM's native response_format with
Pydantic validation.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from litellm import completion
from pydantic import BaseModel

from .config import get_model_config

T = TypeVar("T", bound=BaseModel)


class CompletionError(Exception):
    """Raised when LLM completion fails after all fallbacks."""

    pass


class LLMClient:
    """
    Unified LLM client with automatic failover across free-tier and paid providers.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        fallbacks: Optional[List[str]] = None,
    ):
        """
        Initialize the LLM client.

        Args:
            model: Primary model (e.g. 'gemini/gemini-2.5-flash'). If None, loaded from config.
            fallbacks: List of fallback models. If None, loaded from config.
        """
        self.logger = logging.getLogger(__name__)
        if model is not None and fallbacks is not None:
            self._model = model
            self._fallbacks = fallbacks
        else:
            self._model, self._fallbacks = get_model_config()
        self.logger.info(
            "LLMClient initialized with model=%s, fallbacks=%s",
            self._model,
            self._fallbacks
        )

    def complete_with_schema(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        prompt_prefix: str = "",
        max_retries: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """
        Call the LLM and parse the response into the given Pydantic schema.

        Uses LiteLLM's response_format with fallbacks. Validates the response
        and returns a dict suitable for model_dump compatibility.

        Args:
            messages: Chat messages (e.g. [{"role": "user", "content": "..."}])
            response_model: Pydantic model class for structured output
            prompt_prefix: Optional system instruction prefix
            max_retries: Retries per model on transient/validation errors

        Returns:
            Validated dict from response_model.model_dump(), or None on failure
        """
        if prompt_prefix and messages:
            system_msg = messages[0]
            if system_msg.get("role") == "system":
                system_msg["content"] = f"{prompt_prefix}. {system_msg['content']}"
            else:
                messages = [{"role": "system", "content": prompt_prefix}] + messages

        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "response_format": response_model,
            "max_tokens": 2000,
            "temperature": 0.1,
        }
        if self._fallbacks:
            kwargs["fallbacks"] = self._fallbacks
        if max_retries > 0:
            kwargs["num_retries"] = max_retries

        try:
            response = completion(**kwargs)
        except Exception as e:
            self.logger.error("LLM completion failed after fallbacks: %s", e)
            return None

        content = (
            response.choices[0].message.content
            if response.choices and response.choices[0].message
            else None
        )
        if not content:
            self.logger.warning("Empty content in LLM response")
            return None

        try:
            raw = json.loads(content) if isinstance(content, str) else content
            validated = response_model(**raw)
            model_used = getattr(response, "model", None)
            if hasattr(response, "_hidden_params") and response._hidden_params:
                model_used = model_used or response._hidden_params.get("model")
            self.logger.info("LLM succeeded with model=%s", model_used or self._model)
            return validated.model_dump()
        except (json.JSONDecodeError, Exception) as e:
            self.logger.warning("Failed to parse or validate LLM response: %s", e)
            return None
