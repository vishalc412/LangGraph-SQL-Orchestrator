"""
OpenAI LLM provider implementation.

This module provides integration with OpenAI's API for SQL generation.
Uses GPT-4o-mini by default for cost-effective, high-quality responses.
"""

from typing import List, Dict, Optional
import logging

from openai import OpenAI
from openai import APIError, AuthenticationError, RateLimitError

from .base import BaseLLMProvider, LLMProviderError
from ..config.settings import get_config, OpenAIConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider using the official OpenAI Python client.

    This provider connects to OpenAI's API to generate SQL queries from
    natural language using models like GPT-4o-mini.

    Example usage:
        >>> provider = OpenAIProvider()
        >>> response = provider.generate([
        ...     {"role": "system", "content": "You are a SQL expert."},
        ...     {"role": "user", "content": "Show me all movies from 2020"}
        ... ])
    """

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        Initialize OpenAI provider.

        Args:
            config: OpenAI configuration. If None, uses app config.
        """
        if config is None:
            app_config = get_config()
            config = app_config.openai

        self.config = config
        self.client = None

        # Initialize client if API key is available
        if self.config.api_key:
            self.client = OpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            logger.info(f"OpenAI provider initialized with model: {self.config.model}")
        else:
            logger.warning("OpenAI API key not configured")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response using OpenAI API.

        Args:
            messages: List of message dictionaries
            temperature: Override temperature (default: config value)
            max_tokens: Override max tokens (default: config value)

        Returns:
            Generated text response

        Raises:
            LLMProviderError: If API call fails
        """
        if not self.client:
            raise LLMProviderError("OpenAI client not initialized. Check API key.")

        # Use config values or overrides
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        try:
            logger.debug(f"Calling OpenAI API with {len(messages)} messages")

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )

            # Extract response text
            result = response.choices[0].message.content

            logger.debug(f"OpenAI response received: {len(result)} characters")
            logger.debug(f"Tokens used: {response.usage.total_tokens}")

            return result

        except AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise LLMProviderError(f"Authentication failed: {e}")

        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise LLMProviderError(f"Rate limit exceeded: {e}")

        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMProviderError(f"API error: {e}")

        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise LLMProviderError(f"Unexpected error: {e}")

    def is_available(self) -> bool:
        """
        Check if OpenAI provider is available.

        Returns:
            True if API key is configured and client is initialized
        """
        if not self.client:
            return False

        try:
            # Quick test call to verify API key
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI availability check failed: {e}")
            return False

    def get_model_name(self) -> str:
        """Get the configured model name."""
        return self.config.model
