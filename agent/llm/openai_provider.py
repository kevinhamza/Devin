"""
agent.llm.openai_provider
=========================
OpenAI (and OpenAI-compatible) chat-completions provider with tool calling.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from agent.llm.base import LLMProvider
from agent.messages import LLMResponse, Message, ToolCall


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, config):
        super().__init__(config)
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on env
            raise ImportError(
                "The 'openai' package is required for the OpenAI provider. "
                "Install it with `pip install openai`."
            ) from exc
        if not config.api_key:
            raise ValueError(
                "No OpenAI API key found. Set OPENAI_API_KEY in your environment "
                "or .env file."
            )
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url or None)

    def complete(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [self._to_openai(m) for m in messages],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]
            payload["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**payload)
        choice = response.choices[0]
        message = choice.message

        tool_calls: List[ToolCall] = []
        for tc in getattr(message, "tool_calls", None) or []:
            tool_calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=_safe_json(tc.function.arguments),
                )
            )

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            raw=response,
        )

    @staticmethod
    def _to_openai(message: Message) -> Dict[str, Any]:
        if message.role == "tool":
            return {
                "role": "tool",
                "tool_call_id": message.tool_call_id,
                "content": message.content,
            }
        data: Dict[str, Any] = {"role": message.role, "content": message.content or ""}
        if message.tool_calls:
            data["content"] = message.content or None
            data["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                    },
                }
                for tc in message.tool_calls
            ]
        return data


def _safe_json(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except json.JSONDecodeError:
        return {}
