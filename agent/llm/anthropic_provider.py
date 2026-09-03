"""
agent.llm.anthropic_provider
============================
Anthropic (Claude) Messages API provider with tool calling.

Anthropic differs from OpenAI in two important ways that this adapter hides:
- the system prompt is a top-level ``system`` field, not a message;
- tool calls arrive as ``tool_use`` content blocks and tool results are sent
  back as ``tool_result`` blocks inside a ``user`` message.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent.llm.base import LLMProvider
from agent.messages import LLMResponse, Message, ToolCall


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, config):
        super().__init__(config)
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError(
                "The 'anthropic' package is required for the Anthropic provider. "
                "Install it with `pip install anthropic`."
            ) from exc
        if not config.api_key:
            raise ValueError(
                "No Anthropic API key found. Set ANTHROPIC_API_KEY in your "
                "environment or .env file."
            )
        self._client = anthropic.Anthropic(
            api_key=config.api_key, base_url=config.base_url or None
        )

    def complete(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]] | None = None,
    ) -> LLMResponse:
        system_prompt = "\n\n".join(
            m.content for m in messages if m.role == "system" and m.content
        )
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": self._to_anthropic(messages),
        }
        if system_prompt:
            payload["system"] = system_prompt
        if tools:
            payload["tools"] = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
                }
                for t in tools
            ]

        response = self._client.messages.create(**payload)

        text_parts: List[str] = []
        tool_calls: List[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=dict(block.input or {}),
                    )
                )

        return LLMResponse(
            content="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            raw=response,
        )

    @staticmethod
    def _to_anthropic(messages: List[Message]) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = []
        for message in messages:
            if message.role == "system":
                continue
            if message.role == "tool":
                converted.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.tool_call_id,
                                "content": message.content,
                            }
                        ],
                    }
                )
                continue
            if message.role == "assistant" and message.tool_calls:
                content: List[Dict[str, Any]] = []
                if message.content:
                    content.append({"type": "text", "text": message.content})
                for tc in message.tool_calls:
                    content.append(
                        {
                            "type": "tool_use",
                            "id": tc.id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    )
                converted.append({"role": "assistant", "content": content})
                continue
            converted.append({"role": message.role, "content": message.content or ""})
        return converted
