"""
agent
=====
A provider-agnostic AI agent core for Devin.

Gives Devin the ability to reason with a large language model, hold a
conversation, and take real actions through a tool layer — switchable between
multiple LLM providers (OpenAI, Anthropic, Ollama) purely through configuration.

Typical usage::

    from agent import Agent, AgentConfig

    agent = Agent(AgentConfig.from_env())
    print(agent.chat("List the files in the current directory."))
"""

from agent.config import AgentConfig
from agent.conversation import Agent
from agent.messages import LLMResponse, Message, ToolCall

__all__ = ["Agent", "AgentConfig", "Message", "ToolCall", "LLMResponse"]
