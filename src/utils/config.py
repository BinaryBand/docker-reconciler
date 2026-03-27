"""Utility functions for application configuration."""

import tomllib
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    """Runtime configuration loaded from config/{env}.toml."""

    env: str
    log_level: str
    healthcheck_retries: int
    healthcheck_interval_s: int
    reconciler_max_retries: int


def load_config(env: str) -> AppConfig:
    """Load runtime config from config/{env}.toml."""
    path = Path("config") / f"{env}.toml"
    with path.open("rb") as f:
        data = tomllib.load(f)
    return AppConfig(**data)
