"""Tests for the validation rules in `config_model_runtime`."""

import pytest
from pydantic import ValidationError

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.constants import CONFIG_RUNTIME_FILE_PATH

# Testing the "ConfigModelRuntime" model.


def test_model_validates_the_committed_runtime_file():
    data = ConfigManager().load_config_without_validation(CONFIG_RUNTIME_FILE_PATH)

    config = ConfigModelRuntime(**data)

    assert config.BOARD.DIMENSIONS.ROWS_TOTAL == 22


def test_model_rejects_unknown_keys():
    manager = ConfigManager()
    loaded = manager.load_config_without_validation(CONFIG_RUNTIME_FILE_PATH)
    data = dict(loaded)
    data["UNKNOWN"] = 1

    with pytest.raises(ValidationError):
        ConfigModelRuntime(**data)
