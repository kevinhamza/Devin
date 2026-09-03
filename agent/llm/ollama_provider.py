"""
agent.llm.ollama_provider
=========================
Local/self-hosted provider that talks to an Ollama server over HTTP.

Requires no API key. Tool calling is supported for models that expose it
(e.g. llama3.1); for models without tool support the request still returns a
plain text answer.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from agent.llm.base import LLMProvider
from agent.messages import LLMResponse, Message, ToolCall


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, config):
        super().__init__(config)
        self.base_url = (config.base_url or "http://localhost:11434").rstrip("/")

    def complete(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]] | None = None,
    ) -> LLMResponse:
        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [self._to_ollama(m) for m in messages],
            "stream": False,
            "options": {"temperature": self.config.temperature},
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]

        try:
            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=300
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to reach Ollama at {self.base_url}: {exc}. "
                "Is `ollama serve` running and the model pulled?"
            ) from exc

        return self._parse_response(response.json())

    @staticmethod
    def _parse_response(data: Dict[str, Any]) -> LLMResponse:
        message = data.get("message", {})

        tool_calls: List[ToolCall] = []
        for idx, tc in enumerate(message.get("tool_calls", []) or []):
            fn = tc.get("function", {})
            args = fn.get("arguments", {})
            if isinstance(args, str):
                args = _safe_json(args)
            tool_calls.append(
                ToolCall(
                    id=tc.get("id") or f"call_{idx}",
                    name=fn.get("name", ""),
                    arguments=args or {},
                )
            )

        return LLMResponse(
            content=message.get("content", "") or "",
            tool_calls=tool_calls,
            finish_reason=data.get("done_reason"),
            raw=data,
        )

    @staticmethod
    def _to_ollama(message: Message) -> Dict[str, Any]:
        if message.role == "tool":
            return {
                "role": "tool",
                "content": message.content,
                "name": message.name or "",
            }
        data: Dict[str, Any] = {"role": message.role, "content": message.content or ""}
        if message.tool_calls:
            data["tool_calls"] = [
                {
                    "id": tc.id,
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in message.tool_calls
            ]
        return data


def _safe_json(raw: str) -> Dict[str, Any]:
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except (json.JSONDecodeError, TypeError):
        return {}
