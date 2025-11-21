"""
Ollama LLM provider implementation.

This module provides integration with Ollama for local LLM inference.
Supports models like Llama 3.1 for privacy-preserving, cost-free SQL generation.
"""

from typing import List, Dict, Optional
import logging
import requests

from .base import BaseLLMProvider, LLMProviderError
from ..config.settings import get_config, OllamaConfig

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider for local model inference.

    This provider connects to a local Ollama server to run models like
    Llama 3.1 for SQL generation without sending data to external APIs.

    Prerequisites:
        - Ollama installed and running: https://ollama.com
        - Model pulled: `ollama pull llama3.1`

    Example usage:
        >>> provider = OllamaProvider()
        >>> response = provider.generate([
        ...     {"role": "system", "content": "You are a SQL expert."},
        ...     {"role": "user", "content": "Show me all movies from 2020"}
        ... ])
    """

    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama provider.

        Args:
            config: Ollama configuration. If None, uses app config.
        """
        if config is None:
            app_config = get_config()
            config = app_config.ollama

        self.config = config
        self.api_url = f"{self.config.host}/api/chat"

        logger.info(f"Ollama provider initialized with model: {self.config.model}")
        logger.info(f"Ollama host: {self.config.host}")

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response using Ollama API.

        Args:
            messages: List of message dictionaries
            temperature: Override temperature (default: config value)
            max_tokens: Override max tokens (not directly supported by Ollama)

        Returns:
            Generated text response

        Raises:
            LLMProviderError: If API call fails
        """
        # Use config values or overrides
        temp = temperature if temperature is not None else self.config.temperature

        # Build request payload
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temp
            }
        }

        try:
            logger.debug(f"Calling Ollama API with {len(messages)} messages")

            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.config.timeout
            )

            response.raise_for_status()

            result = response.json()

            # Extract response text
            content = result.get("message", {}).get("content", "")

            logger.debug(f"Ollama response received: {len(content)} characters")

            return content

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise LLMProviderError(
                f"Cannot connect to Ollama at {self.config.host}. "
                "Make sure Ollama is running."
            )

        except requests.exceptions.Timeout as e:
            logger.error(f"Ollama request timed out: {e}")
            raise LLMProviderError(
                f"Request timed out after {self.config.timeout}s. "
                "Try increasing timeout or using a smaller model."
            )

        except requests.exceptions.HTTPError as e:
            logger.error(f"Ollama HTTP error: {e}")

            # Check for specific error types
            if response.status_code == 404:
                raise LLMProviderError(
                    f"Model '{self.config.model}' not found. "
                    f"Run 'ollama pull {self.config.model}' to download it."
                )

            raise LLMProviderError(f"HTTP error: {e}")

        except Exception as e:
            logger.error(f"Unexpected error calling Ollama: {e}")
            raise LLMProviderError(f"Unexpected error: {e}")

    def is_available(self) -> bool:
        """
        Check if Ollama provider is available.

        Returns:
            True if Ollama server is running and model is available
        """
        try:
            # Check server health
            health_url = f"{self.config.host}/api/tags"
            response = requests.get(health_url, timeout=5)
            response.raise_for_status()

            # Check if model is available
            models = response.json().get("models", [])
            model_names = [m.get("name", "").split(":")[0] for m in models]

            if self.config.model.split(":")[0] in model_names:
                return True

            logger.warning(
                f"Model '{self.config.model}' not found. "
                f"Available models: {model_names}"
            )
            return False

        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False

    def get_model_name(self) -> str:
        """Get the configured model name."""
        return self.config.model

    def list_models(self) -> List[str]:
        """
        List available models on the Ollama server.

        Returns:
            List of available model names
        """
        try:
            response = requests.get(
                f"{self.config.host}/api/tags",
                timeout=5
            )
            response.raise_for_status()

            models = response.json().get("models", [])
            return [m.get("name", "") for m in models]

        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
