"""
agent.messages
==============
Provider-neutral data structures for conversation messages and LLM responses.

These types are the common currency between the conversation manager and the
individual provider implementations, so that provider-specific request/response
shapes never leak into the rest of the codebase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """A single tool/function invocation requested by the model."""

    id: str
    name: str
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """A single conversation message in provider-neutral form.

    Roles follow the common chat convention: ``system``, ``user``,
    ``assistant`` and ``tool``. ``tool_calls`` is only set on ``assistant``
    messages that request tools; ``tool_call_id`` / ``name`` are only set on
    ``tool`` messages that carry a tool result.
    """

    role: str
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in self.tool_calls
            ]
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            data["name"] = self.name
        return data


@dataclass
class LLMResponse:
    """The normalized result of a single LLM call."""

    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    raw: Any = None

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)
