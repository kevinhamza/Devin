"""
agent.conversation
==================
The agent loop: holds conversation history, asks the configured LLM provider for
the next step, executes any tools the model requests, and feeds the results back
until the model produces a final answer.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from agent.config import AgentConfig
from agent.llm import LLMProvider, create_provider
from agent.messages import Message, ToolCall
from agent.prompts import build_system_prompt
from agent.tools import Tool, ToolRegistry, build_default_registry

# Called before a dangerous tool runs; return True to allow the action.
ConfirmCallback = Callable[[Tool, Dict[str, Any]], bool]
# Called with human-readable progress lines ("Calling tool X ...").
ProgressCallback = Callable[[str], None]


class Agent:
    """A Devin-style conversational agent with tool use."""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        provider: Optional[LLMProvider] = None,
        tools: Optional[ToolRegistry] = None,
        confirm: Optional[ConfirmCallback] = None,
        system_prompt: Optional[str] = None,
        on_progress: Optional[ProgressCallback] = None,
    ):
        self.config = config or AgentConfig.from_env()
        self.provider = provider or create_provider(self.config)
        self.tools = tools if tools is not None else build_default_registry(confirm=confirm)
        if confirm is not None and self.tools.confirm is None:
            self.tools.confirm = confirm
        if not self.config.require_confirmation:
            self.tools.confirm = None
        self.on_progress = on_progress
        self.system_prompt = system_prompt or build_system_prompt()
        self.messages: List[Message] = [Message(role="system", content=self.system_prompt)]

    # -- history -----------------------------------------------------------

    def reset(self) -> None:
        """Clear the conversation, keeping the system prompt."""
        self.messages = [Message(role="system", content=self.system_prompt)]

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))

    # -- main loop ---------------------------------------------------------

    def send(self, user_input: str) -> str:
        """Send a user message and run the reason/act loop until a final reply."""
        self.add_user_message(user_input)
        return self.run()

    def run(self) -> str:
        schemas = self.tools.schemas() if len(self.tools) else None
        for _ in range(max(1, self.config.max_tool_iterations)):
            response = self.provider.complete(self.messages, tools=schemas)
            self.messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            if not response.has_tool_calls:
                return response.content
            if response.content:
                self._progress(response.content)
            for call in response.tool_calls:
                self.messages.append(self._execute(call))
        return (
            "Stopped after reaching the maximum number of tool iterations "
            f"({self.config.max_tool_iterations}). The task may be incomplete."
        )

    # -- internals ---------------------------------------------------------

    def _execute(self, call: ToolCall) -> Message:
        self._progress(f"→ {call.name}({_format_args(call.arguments)})")
        result = self.tools.execute(call.name, call.arguments)
        self._progress(f"← {'ok' if result.ok else 'error'}")
        return Message(
            role="tool",
            content=result.output,
            tool_call_id=call.id,
            name=call.name,
        )

    def _progress(self, text: str) -> None:
        if self.on_progress is not None:
            self.on_progress(text)


def _format_args(arguments: Dict[str, Any]) -> str:
    parts = []
    for key, value in (arguments or {}).items():
        text = str(value)
        if len(text) > 60:
            text = text[:57] + "..."
        parts.append(f"{key}={text!r}")
    return ", ".join(parts)
