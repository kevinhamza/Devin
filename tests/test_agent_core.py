"""Unit tests for the agent core (no network / no real LLM required)."""

import os
import sys
from typing import Any, Dict, List

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import Agent, AgentConfig, LLMResponse, Message, ToolCall  # noqa: E402
from agent.llm import LLMProvider, create_provider  # noqa: E402
from agent.llm.anthropic_provider import AnthropicProvider  # noqa: E402
from agent.llm.ollama_provider import OllamaProvider  # noqa: E402
from agent.llm.openai_provider import OpenAIProvider  # noqa: E402
from agent.tools import ToolRegistry, ToolResult, build_default_registry, tool  # noqa: E402


class FakeProvider(LLMProvider):
    """Replays a scripted list of responses and records what it was sent."""

    name = "fake"

    def __init__(self, config: AgentConfig, responses: List[LLMResponse]):
        super().__init__(config)
        self.responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def complete(self, messages, tools=None):
        self.calls.append({"messages": list(messages), "tools": tools})
        return self.responses.pop(0)


# --- config ------------------------------------------------------------------


def test_config_defaults_model_per_provider():
    assert AgentConfig(provider="anthropic").model.startswith("claude")
    assert AgentConfig(provider="OLLAMA").provider == "ollama"


def test_config_from_env_reads_provider_and_key(monkeypatch):
    monkeypatch.setenv("DEVIN_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("DEVIN_REQUIRE_CONFIRMATION", "false")
    cfg = AgentConfig.from_env(yaml_path="/nonexistent.yaml")
    assert cfg.provider == "openai"
    assert cfg.api_key == "sk-test"
    assert cfg.require_confirmation is False


def test_config_ignores_placeholder_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_api_key")
    monkeypatch.delenv("CHATGPT_API_KEY", raising=False)
    cfg = AgentConfig.from_env(yaml_path="/nonexistent.yaml", provider="openai")
    assert cfg.api_key is None


def test_config_provider_argument_overrides_env(monkeypatch):
    monkeypatch.setenv("DEVIN_PROVIDER", "openai")
    cfg = AgentConfig.from_env(yaml_path="/nonexistent.yaml", provider="ollama")
    assert cfg.provider == "ollama"


# --- provider factory --------------------------------------------------------


def test_factory_selects_provider():
    assert isinstance(create_provider(AgentConfig(provider="ollama")), OllamaProvider)
    assert isinstance(
        create_provider(AgentConfig(provider="openai", api_key="k")), OpenAIProvider
    )
    assert isinstance(
        create_provider(AgentConfig(provider="anthropic", api_key="k")), AnthropicProvider
    )


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError):
        create_provider(AgentConfig(provider="nope"))


# --- tools -------------------------------------------------------------------


def test_tool_decorator_infers_schema():
    @tool(description="add numbers")
    def add(a: int, b: int = 1) -> int:
        return a + b

    schema = add.schema()
    assert schema["name"] == "add"
    assert schema["parameters"]["properties"]["a"]["type"] == "integer"
    assert schema["parameters"]["required"] == ["a"]
    assert add.run({"a": 2, "b": 3}).output == "5"


def test_tool_errors_are_returned_not_raised():
    @tool()
    def boom():
        raise RuntimeError("kaboom")

    result = boom.run({})
    assert result.ok is False
    assert "kaboom" in result.output
    assert boom.run({"unexpected": 1}).ok is False


def test_registry_denies_dangerous_tool_without_permission():
    @tool(dangerous=True)
    def rm_everything() -> str:
        return "deleted"

    registry = ToolRegistry(confirm=lambda t, args: False)
    registry.add(rm_everything)
    result = registry.execute("rm_everything", {})
    assert result.ok is False
    assert "Permission denied" in result.output


def test_registry_allows_dangerous_tool_with_permission():
    seen = {}

    @tool(dangerous=True)
    def touch(path: str) -> str:
        return f"touched {path}"

    def confirm(t, args):
        seen["tool"] = t.name
        seen["args"] = args
        return True

    registry = ToolRegistry(confirm=confirm)
    registry.add(touch)
    assert registry.execute("touch", {"path": "/tmp/x"}).output == "touched /tmp/x"
    assert seen == {"tool": "touch", "args": {"path": "/tmp/x"}}


def test_registry_unknown_tool():
    assert ToolRegistry().execute("missing", {}).ok is False


def test_default_registry_marks_os_control_dangerous():
    registry = build_default_registry(confirm=lambda t, a: False)
    for name in ("run_shell", "write_file", "os_control"):
        assert registry.get(name).dangerous is True
    for name in ("read_file", "list_directory", "system_info"):
        assert registry.get(name).dangerous is False
    # blocked by the confirm callback, so nothing actually runs
    assert "Permission denied" in registry.execute("os_control", {"action": "type", "text": "hi"}).output
    assert "Permission denied" in registry.execute("run_shell", {"command": "echo hi"}).output


def test_run_shell_and_list_directory(tmp_path):
    registry = build_default_registry(confirm=lambda t, a: True)
    (tmp_path / "a.txt").write_text("hello")
    out = registry.execute("list_directory", {"path": str(tmp_path)}).output
    assert "a.txt" in out
    assert registry.execute("read_file", {"path": str(tmp_path / "a.txt")}).output == "hello"
    shell = registry.execute("run_shell", {"command": "echo shell-ok"})
    assert shell.ok and "shell-ok" in shell.output


def test_os_control_rejects_unknown_action():
    registry = build_default_registry(confirm=lambda t, a: True)
    assert registry.execute("os_control", {"action": "fly"}).ok is False


# --- agent loop --------------------------------------------------------------


def test_agent_returns_plain_answer():
    cfg = AgentConfig(provider="ollama")
    provider = FakeProvider(cfg, [LLMResponse(content="Hi there")])
    agent = Agent(config=cfg, provider=provider, tools=ToolRegistry())
    assert agent.send("hello") == "Hi there"
    roles = [m.role for m in agent.messages]
    assert roles == ["system", "user", "assistant"]
    assert provider.calls[0]["tools"] is None  # empty registry -> no tools sent


def test_agent_executes_tool_calls_and_feeds_results_back():
    @tool(description="echo")
    def echo(text: str) -> str:
        return f"echo:{text}"

    registry = ToolRegistry()
    registry.add(echo)
    cfg = AgentConfig(provider="ollama")
    provider = FakeProvider(
        cfg,
        [
            LLMResponse(tool_calls=[ToolCall(id="c1", name="echo", arguments={"text": "x"})]),
            LLMResponse(content="done"),
        ],
    )
    agent = Agent(config=cfg, provider=provider, tools=registry)
    assert agent.send("go") == "done"
    tool_msgs = [m for m in agent.messages if m.role == "tool"]
    assert len(tool_msgs) == 1
    assert tool_msgs[0].content == "echo:x"
    assert tool_msgs[0].tool_call_id == "c1"
    assert provider.calls[0]["tools"][0]["name"] == "echo"


def test_agent_denied_permission_is_reported_to_model():
    @tool(dangerous=True)
    def nuke() -> str:
        return "boom"

    registry = ToolRegistry()
    registry.add(nuke)
    cfg = AgentConfig(provider="ollama")
    provider = FakeProvider(
        cfg,
        [
            LLMResponse(tool_calls=[ToolCall(id="c1", name="nuke", arguments={})]),
            LLMResponse(content="ok, skipped"),
        ],
    )
    agent = Agent(config=cfg, provider=provider, tools=registry, confirm=lambda t, a: False)
    assert agent.send("nuke it") == "ok, skipped"
    assert "Permission denied" in [m for m in agent.messages if m.role == "tool"][0].content


def test_agent_stops_at_max_iterations():
    @tool()
    def loop() -> str:
        return "again"

    registry = ToolRegistry()
    registry.add(loop)
    cfg = AgentConfig(provider="ollama", max_tool_iterations=2)
    provider = FakeProvider(
        cfg,
        [LLMResponse(tool_calls=[ToolCall(id=str(i), name="loop")]) for i in range(2)],
    )
    agent = Agent(config=cfg, provider=provider, tools=registry)
    assert "maximum number of tool iterations" in agent.send("loop")


# --- provider message conversion (offline) ----------------------------------


def _history():
    return [
        Message(role="system", content="sys"),
        Message(role="user", content="hi"),
        Message(role="assistant", content="", tool_calls=[ToolCall(id="t1", name="echo", arguments={"a": 1})]),
        Message(role="tool", content="result", tool_call_id="t1", name="echo"),
    ]


def test_openai_message_conversion():
    converted = [OpenAIProvider._to_openai(m) for m in _history()]
    assert converted[0]["role"] == "system" and converted[0]["content"] == "sys"
    assert converted[2]["tool_calls"][0]["function"]["name"] == "echo"
    assert converted[3]["role"] == "tool"
    assert converted[3]["tool_call_id"] == "t1"
    assert converted[3]["content"] == "result"


def test_anthropic_message_conversion_moves_system_and_tool_results():
    converted = AnthropicProvider._to_anthropic(_history())
    assert all(m["role"] != "system" for m in converted)
    tool_use = [b for b in converted[1]["content"] if b["type"] == "tool_use"]
    assert tool_use[0]["name"] == "echo" and tool_use[0]["input"] == {"a": 1}
    tool_result = converted[2]["content"][0]
    assert tool_result["type"] == "tool_result" and tool_result["tool_use_id"] == "t1"


def test_ollama_message_conversion():
    converted = [OllamaProvider._to_ollama(m) for m in _history()]
    assert converted[2]["tool_calls"][0]["function"]["arguments"] == {"a": 1}
    assert converted[3] == {"role": "tool", "content": "result", "name": "echo"}


def test_ollama_response_parsing():
    parsed = OllamaProvider._parse_response(
        {
            "message": {
                "content": "",
                "tool_calls": [{"function": {"name": "echo", "arguments": {"text": "x"}}}],
            },
            "done_reason": "stop",
        }
    )
    assert parsed.has_tool_calls
    assert parsed.tool_calls[0].name == "echo"
    assert parsed.tool_calls[0].arguments == {"text": "x"}


def test_tool_result_str():
    assert str(ToolResult("abc")) == "abc"
