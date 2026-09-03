"""
agent.llm.factory
=================
Maps a provider name from configuration to a concrete provider instance.
"""

from __future__ import annotations

from agent.config import AgentConfig
from agent.llm.base import LLMProvider

_PROVIDERS = {"openai", "anthropic", "ollama"}


def create_provider(config: AgentConfig) -> LLMProvider:
    """Instantiate the provider selected by ``config.provider``."""
    provider = config.provider.lower()
    if provider == "openai":
        from agent.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(config)
    if provider == "anthropic":
        from agent.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(config)
    if provider == "ollama":
        from agent.llm.ollama_provider import OllamaProvider

        return OllamaProvider(config)
    raise ValueError(
        f"Unknown provider '{config.provider}'. "
        f"Supported providers: {', '.join(sorted(_PROVIDERS))}."
    )
