"""
agent.config
============
Configuration for the agent core.

Configuration is resolved with the following precedence (highest first):

1. Explicit keyword arguments passed to :class:`AgentConfig`.
2. Environment variables (loaded from a ``.env`` file if present).
3. An optional YAML file (``config/agent.yaml`` by default).
4. Built-in defaults.

The active provider is selected by ``DEVIN_PROVIDER`` (``openai``,
``anthropic`` or ``ollama``) so the reasoning backend can be switched without
touching any code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:  # optional dependency; config still works without it
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - dotenv is a soft dependency
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False

try:
    import yaml
except Exception:  # pragma: no cover - yaml is a soft dependency
    yaml = None  # type: ignore[assignment]


DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-latest",
    "ollama": "llama3.1",
}


@dataclass
class AgentConfig:
    """Runtime configuration for the agent."""

    provider: str = "openai"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.2
    max_tokens: int = 2048
    max_tool_iterations: int = 12
    require_confirmation: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.provider = (self.provider or "openai").lower()
        if not self.model:
            self.model = DEFAULT_MODELS.get(self.provider, DEFAULT_MODELS["openai"])

    @classmethod
    def from_env(
        cls,
        yaml_path: str = "config/agent.yaml",
        provider: Optional[str] = None,
    ) -> "AgentConfig":
        """Build a config from environment variables and an optional YAML file.

        ``provider`` overrides ``DEVIN_PROVIDER`` (e.g. from a CLI flag).
        """
        load_dotenv()
        file_cfg = _load_yaml(yaml_path)

        provider = (
            provider
            or os.getenv("DEVIN_PROVIDER")
            or file_cfg.get("provider")
            or "openai"
        ).lower()

        provider_cfg = (file_cfg.get("providers") or {}).get(provider, {})

        def pick(env_name: str, key: str, default: Any = None) -> Any:
            return os.getenv(env_name) or provider_cfg.get(key) or file_cfg.get(key) or default

        api_key = _resolve_api_key(provider, provider_cfg)
        model = pick("DEVIN_MODEL", "model", DEFAULT_MODELS.get(provider))
        base_url = pick("DEVIN_BASE_URL", "base_url")

        require_confirmation = _as_bool(
            os.getenv("DEVIN_REQUIRE_CONFIRMATION"),
            provider_cfg.get("require_confirmation", file_cfg.get("require_confirmation", True)),
        )

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=float(pick("DEVIN_TEMPERATURE", "temperature", 0.2)),
            max_tokens=int(pick("DEVIN_MAX_TOKENS", "max_tokens", 2048)),
            max_tool_iterations=int(pick("DEVIN_MAX_TOOL_ITERATIONS", "max_tool_iterations", 12)),
            require_confirmation=require_confirmation,
            extra=file_cfg.get("extra", {}) or {},
        )


def _resolve_api_key(provider: str, provider_cfg: Dict[str, Any]) -> Optional[str]:
    env_names = {
        "openai": ["OPENAI_API_KEY", "CHATGPT_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        "ollama": ["OLLAMA_API_KEY"],
    }.get(provider, [])
    for name in env_names:
        value = os.getenv(name)
        if value and not value.lower().startswith("your_"):
            return value
    key = provider_cfg.get("api_key")
    if key and not str(key).lower().startswith("your_"):
        return key
    return None


def _load_yaml(path: str) -> Dict[str, Any]:
    if not path or yaml is None or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _as_bool(env_value: Optional[str], default: Any) -> bool:
    if env_value is None:
        return bool(default)
    return env_value.strip().lower() in {"1", "true", "yes", "on"}
