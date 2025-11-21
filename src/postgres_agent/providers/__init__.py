"""
LLM Provider package.

This package contains LLM provider implementations for different backends.
Use the create_provider() factory function to get the appropriate provider.
"""

from typing import Optional

from .base import BaseLLMProvider, LLMProviderError
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider
from ..config.settings import get_config


def create_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """
    Factory function to create LLM provider instance.

    Args:
        provider_name: Name of provider ("openai" or "ollama").
                      If None, uses default from config.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider name is unknown

    Example:
        >>> provider = create_provider("openai")
        >>> response = provider.generate([{"role": "user", "content": "Hello"}])
    """
    config = get_config()

    if provider_name is None:
        provider_name = config.default_llm_provider

    provider_name = provider_name.lower()

    if provider_name == "openai":
        return OpenAIProvider(config.openai)
    elif provider_name == "ollama":
        return OllamaProvider(config.ollama)
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            "Available providers: openai, ollama"
        )


__all__ = [
    "BaseLLMProvider",
    "LLMProviderError",
    "OpenAIProvider",
    "OllamaProvider",
    "create_provider"
]
