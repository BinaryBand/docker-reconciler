import pytest

from src.utils.config import load_config


def test_load_config_dev() -> None:
    config = load_config("dev")
    assert config.env == "dev"
    assert config.log_level == "INFO"
    assert config.reconciler_max_retries == 10


def test_load_config_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent")
