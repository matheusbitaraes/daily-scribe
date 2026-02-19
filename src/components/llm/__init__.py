"""
LLM abstraction layer for Daily Scribe.

Provides a unified interface to multiple LLM providers via LiteLLM and Instructor,
with automatic failover across free-tier and paid models.
"""

from .client import LLMClient
from .config import get_model_config

__all__ = ["LLMClient", "get_model_config"]
