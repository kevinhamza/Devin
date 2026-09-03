"""
agent.llm.base
==============
Abstract base class every LLM provider implements.

A provider's only job is to turn a provider-neutral conversation (a list of
:class:`~agent.messages.Message`) plus a set of tool schemas into a single
normalized :class:`~agent.messages.LLMResponse`. All provider-specific request
and response translation lives inside the concrete subclasses.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from agent.config import AgentConfig
from agent.messages import LLMResponse, Message


class LLMProvider(ABC):
    """Common interface for all reasoning backends."""

    name: str = "base"

    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def complete(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Perform a single chat completion.

        :param messages: Full conversation so far, in provider-neutral form.
        :param tools: Tool JSON schemas (``{"name", "description", "parameters"}``)
            the model may call. ``None`` or empty disables tool use.
        :return: A normalized response with text and/or requested tool calls.
        """
        raise NotImplementedError
