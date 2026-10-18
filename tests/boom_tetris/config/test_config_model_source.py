"""Tests for the validation rules in `config_model_source`."""

import pytest
from pydantic import ValidationError

from boom_tetris.config.config_manager import ConfigManager
from boom_tetris.config.config_model_source import ConfigModelSource
from boom_tetris.constants import CONFIG_SOURCE_FILE_PATH

# Testing the "ConfigModelSource" model.


def test_model_validates_the_committed_source_file():
    data = ConfigManager().load_config_without_validation(CONFIG_SOURCE_FILE_PATH)

    config = ConfigModelSource(**data)

    assert config.GENERAL.START_LEVEL == 18


def test_model_rejects_unknown_keys():
    manager = ConfigManager()
    loaded = manager.load_config_without_validation(CONFIG_SOURCE_FILE_PATH)
    data = dict(loaded)
    data["UNKNOWN"] = 1

    with pytest.raises(ValidationError):
        ConfigModelSource(**data)
