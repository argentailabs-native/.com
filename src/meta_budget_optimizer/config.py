from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass
class RuntimeConfig:
    env_mode: str
    log_level: str
    timezone: str
    slack_webhook_url: str | None


class ConfigError(Exception):
    """Raised when configuration is invalid."""


def _expand_env(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: _expand_env(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_expand_env(v) for v in data]
    if isinstance(data, str):
        return os.path.expandvars(data)
    return data


def load_config(config_path: str | Path) -> tuple[dict[str, Any], RuntimeConfig]:
    load_dotenv()
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}

    cfg = _expand_env(loaded)

    runtime = RuntimeConfig(
        env_mode=os.getenv("EXECUTION_MODE", cfg.get("execution", {}).get("mode", "recommendation")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        timezone=os.getenv("TIMEZONE", "UTC"),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL") or None,
    )

    _validate_config(cfg, runtime)
    return cfg, runtime


def _validate_config(cfg: dict[str, Any], runtime: RuntimeConfig) -> None:
    required = ["account", "thresholds", "budget_rules", "execution", "reporting"]
    missing = [section for section in required if section not in cfg]
    if missing:
        raise ConfigError(f"Missing required config sections: {missing}")

    if cfg["account"].get("level") not in {"adset", "ad"}:
        raise ConfigError("account.level must be 'adset' or 'ad'")

    if runtime.env_mode not in {"recommendation", "live"}:
        raise ConfigError("EXECUTION_MODE must be recommendation or live")
