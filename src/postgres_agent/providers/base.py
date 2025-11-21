"""
Base LLM provider interface.

This module defines the abstract base class that all LLM providers must implement.
This ensures consistent behavior across different LLM backends.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM providers (OpenAI, Ollama, etc.) must implement this interface
    to ensure consistent behavior across the application.

    Example usage:
        >>> provider = OpenAIProvider()
        >>> response = provider.generate([{"role": "user", "content": "Hello"}])
    """

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
                     Roles can be 'system', 'user', or 'assistant'.
            temperature: Optional override for sampling temperature.
            max_tokens: Optional override for maximum response tokens.

        Returns:
            Generated text response from the LLM.

        Raises:
            LLMProviderError: If generation fails.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available and properly configured.

        Returns:
            True if provider is available, False otherwise.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the model being used.

        Returns:
            Model name string.
        """
        pass


class LLMProviderError(Exception):
    """Exception raised when LLM provider operations fail."""
    pass
