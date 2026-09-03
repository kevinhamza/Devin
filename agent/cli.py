"""
agent.cli
=========
Interactive chat entrypoint::

    python -m agent
    python -m agent --provider ollama --model llama3.1
    python -m agent --once "list the files in this directory"

Dangerous actions (shell commands, file writes, keyboard/mouse control) prompt
for explicit permission before they run, unless ``--yes`` is passed.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Dict

from agent.config import AgentConfig
from agent.conversation import Agent
from agent.tools import Tool, build_default_registry

BANNER = """Devin agent — provider: {provider}, model: {model}
Type your request. Commands: /reset, /tools, /exit
"""


def make_confirmer(auto_approve: bool = False):
    """Return a confirmation callback that asks the user for permission."""

    def confirm(tool_obj: Tool, arguments: Dict[str, Any]) -> bool:
        if auto_approve:
            return True
        print(f"\n[permission required] {tool_obj.name}")
        for key, value in (arguments or {}).items():
            print(f"    {key}: {value}")
        try:
            answer = input("Allow this action? [y/N] ").strip().lower()
        except EOFError:
            return False
        return answer in ("y", "yes")

    return confirm


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent", description="Devin agent CLI")
    parser.add_argument("--provider", help="LLM provider: openai, anthropic or ollama")
    parser.add_argument("--model", help="Model name (defaults per provider)")
    parser.add_argument("--base-url", help="Override the provider base URL")
    parser.add_argument("--temperature", type=float, help="Sampling temperature")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-approve dangerous actions (use with care)",
    )
    parser.add_argument("--once", help="Run a single request and exit")
    return parser


def build_agent(args: argparse.Namespace) -> Agent:
    config = AgentConfig.from_env(provider=args.provider)
    if args.model:
        config.model = args.model
    if args.base_url:
        config.base_url = args.base_url
    if args.temperature is not None:
        config.temperature = args.temperature

    confirm = make_confirmer(auto_approve=args.yes)
    registry = build_default_registry(confirm=confirm)
    return Agent(
        config=config,
        tools=registry,
        confirm=confirm,
        on_progress=lambda line: print(f"  {line}"),
    )


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        agent = build_agent(args)
    except Exception as exc:
        print(f"Failed to start agent: {exc}", file=sys.stderr)
        return 1

    if args.once:
        try:
            print(agent.send(args.once))
        except Exception as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1
        return 0

    print(BANNER.format(provider=agent.config.provider, model=agent.config.model))
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not user_input:
            continue
        if user_input in ("/exit", "/quit"):
            return 0
        if user_input == "/reset":
            agent.reset()
            print("Conversation reset.")
            continue
        if user_input == "/tools":
            for schema in agent.tools.schemas():
                print(f"  {schema['name']}: {schema['description']}")
            continue
        try:
            print(f"\ndevin> {agent.send(user_input)}\n")
        except Exception as exc:
            print(f"\n[error] {exc}\n", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
