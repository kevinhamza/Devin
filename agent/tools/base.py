"""
agent.tools.base
================
Tool abstraction, registry, and a decorator for declaring tools.

A :class:`Tool` couples a JSON-schema description (what the model sees) with a
Python callable (what actually runs). The :class:`ToolRegistry` exposes the
schemas to a provider and dispatches tool calls back to their callables.

Tools may be marked ``dangerous=True``. Dangerous tools perform actions with
real-world side effects (running shell commands, controlling the keyboard and
mouse, writing files) and are gated behind an explicit user-permission
confirmation callback before they run.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolResult:
    """The outcome of running a tool."""

    output: str
    ok: bool = True

    def __str__(self) -> str:
        return self.output


@dataclass
class Tool:
    """A single callable action exposed to the model."""

    name: str
    description: str
    parameters: Dict[str, Any]
    func: Callable[..., Any]
    dangerous: bool = False

    def schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def run(self, arguments: Dict[str, Any]) -> ToolResult:
        try:
            result = self.func(**(arguments or {}))
        except TypeError as exc:
            return ToolResult(f"Invalid arguments for tool '{self.name}': {exc}", ok=False)
        except Exception as exc:  # surface the error to the model, don't crash
            return ToolResult(f"Tool '{self.name}' failed: {exc}", ok=False)
        if isinstance(result, ToolResult):
            return result
        if isinstance(result, (dict, list)):
            return ToolResult(json.dumps(result, default=str, indent=2))
        return ToolResult("" if result is None else str(result))


# Callback signature: (tool, arguments) -> bool (True = allow the action).
ConfirmCallback = Callable[[Tool, Dict[str, Any]], bool]


class ToolRegistry:
    """Holds the set of tools available to an agent."""

    def __init__(self, confirm: Optional[ConfirmCallback] = None):
        self._tools: Dict[str, Tool] = {}
        self.confirm = confirm

    def register(self, tool_obj: Tool) -> None:
        self._tools[tool_obj.name] = tool_obj

    def add(self, *tool_objs: Tool) -> None:
        for t in tool_objs:
            self.register(t)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def schemas(self) -> List[Dict[str, Any]]:
        return [t.schema() for t in self._tools.values()]

    def execute(self, name: str, arguments: Dict[str, Any]) -> ToolResult:
        tool_obj = self._tools.get(name)
        if tool_obj is None:
            return ToolResult(f"Unknown tool: {name}", ok=False)
        if tool_obj.dangerous and self.confirm is not None:
            if not self.confirm(tool_obj, arguments or {}):
                return ToolResult(
                    f"Permission denied by user for '{name}'. Action not performed.",
                    ok=False,
                )
        return tool_obj.run(arguments or {})


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    dangerous: bool = False,
) -> Callable[[Callable[..., Any]], Tool]:
    """Decorator that turns a plain function into a :class:`Tool`.

    If ``parameters`` is omitted, a best-effort JSON schema is inferred from the
    function signature (all string properties, required unless they have a
    default).
    """

    def decorator(func: Callable[..., Any]) -> Tool:
        return Tool(
            name=name or func.__name__,
            description=description or (func.__doc__ or "").strip(),
            parameters=parameters or _infer_schema(func),
            func=func,
            dangerous=dangerous,
        )

    return decorator


_PY_TO_JSON = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
    dict: "object",
    list: "array",
}


def _infer_schema(func: Callable[..., Any]) -> Dict[str, Any]:
    sig = inspect.signature(func)
    properties: Dict[str, Any] = {}
    required: List[str] = []
    for param_name, param in sig.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        json_type = _PY_TO_JSON.get(param.annotation, "string")
        properties[param_name] = {"type": json_type}
        if param.default is inspect.Parameter.empty:
            required.append(param_name)
    schema: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema
