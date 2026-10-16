"""Tests for the configuration loading and computation in `config_manager`."""

import pytest

from src.boom_tetris.config import config_manager as config_manager_module
from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.config.config_model_source import ConfigModelSource
from src.boom_tetris.constants import (
    CONFIG_RUNTIME_FILE_PATH,
    CONFIG_SOURCE_FILE_PATH,
    Position,
)
from src.boom_tetris.utils.utils_dict import DotDict

WINDOW_SIZE = (1280, 720)


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """Build a manager that writes its runtime file into a temporary folder.

    Args:
        tmp_path: Pytest temporary directory.
        monkeypatch: Pytest fixture used to fix the window size and paths.

    Returns:
        config_manager (ConfigManager): Manager with a deterministic window.
    """
    monkeypatch.setattr(
        config_manager_module,
        "get_window_size_from_screen_resolution",
        lambda: WINDOW_SIZE,
    )
    runtime_file = tmp_path / "config_runtime.yaml"
    monkeypatch.setattr(config_manager_module, "CONFIG_RUNTIME_FILE_PATH", runtime_file)
    config_manager = ConfigManager()
    config_manager._config_runtime_file_path = runtime_file

    return config_manager


def _build_until_window_and_board(manager):
    """Run the computation pipeline up to the board geometry.

    Args:
        manager (ConfigManager): The manager whose source config is loaded.

    Returns:
        config (DotDict): Config with window and board geometry added.
    """
    source = manager._load_source_config()
    source_dict = source.model_dump()
    config = DotDict(source_dict)
    config = manager._add_window_resolution(config=config)
    config = manager._add_board_and_line_counter_fields(config=config)

    return config


def _build_all(manager):
    """Run the whole computation pipeline, as `get_runtime_config` does.

    Args:
        manager (ConfigManager): The manager whose source config is loaded.

    Returns:
        config (DotDict): Config with every computed field added.
    """
    config = _build_until_window_and_board(manager)
    config = manager._add_all_remaining_fields(config=config)
    config = manager._add_font_size(config=config)
    config = manager._add_polyomino_spawn_positions(config=config)
    config = manager._add_all_polyonomios(config=config)

    return config


# Testing the "__init__" method of the "ConfigManager" class.


def test_init_uses_the_constant_file_paths():
    config_manager = ConfigManager()

    assert config_manager._config_source_file_path == CONFIG_SOURCE_FILE_PATH
    assert config_manager._config_runtime_file_path == CONFIG_RUNTIME_FILE_PATH


# Testing the "load_config_without_validation" method.


def test_load_config_without_validation_returns_dot_dict(manager):
    data = manager.load_config_without_validation(CONFIG_SOURCE_FILE_PATH)

    assert isinstance(data, DotDict)
    assert data.WINDOW.RATIO_MARGIN_TO_WINDOW_HEIGHT == 40


# Testing the "_load_source_config" method.


def test_load_source_config_validates_the_source_file(manager):
    config = manager._load_source_config()

    assert isinstance(config, ConfigModelSource)


# Testing the "_load_runtime_config" method.


def test_load_runtime_config_validates_the_runtime_file(manager):
    manager._config_runtime_file_path = CONFIG_RUNTIME_FILE_PATH

    config = manager._load_runtime_config()

    assert isinstance(config, ConfigModelRuntime)


# Testing the "_add_window_resolution" method.


def test_add_window_resolution_sets_window_size(manager):
    source = manager._load_source_config()
    source_dict = source.model_dump()
    config = DotDict(source_dict)

    config = manager._add_window_resolution(config=config)

    assert config.WINDOW.WIDTH == WINDOW_SIZE[0]
    assert config.WINDOW.HEIGHT == WINDOW_SIZE[1]


# Testing the "_add_board_and_line_counter_fields" method.


def test_board_geometry_has_square_cells_that_fit_the_window(manager):
    config = _build_until_window_and_board(manager)

    assert config.BOARD.DIMENSIONS.ROWS_TOTAL == 22
    assert config.BOARD.CELL.WIDTH == config.BOARD.CELL.HEIGHT
    assert config.BOARD.RECT.HEIGHT == 22 * config.BOARD.CELL.HEIGHT
    assert config.BOARD.RECT.LEFT >= 0
    assert config.BOARD.RECT.LEFT + config.BOARD.RECT.WIDTH <= config.WINDOW.WIDTH


def test_line_counter_sits_at_the_top_margin(manager):
    config = _build_until_window_and_board(manager)

    assert config.FIELDS.LINE_COUNTER.TOP == config.WINDOW.MARGIN


# Testing the "_add_all_remaining_fields" method.


def test_side_fields_are_placed_around_the_board(manager):
    config = _build_all(manager)
    rect = config.BOARD.RECT
    margin = config.WINDOW.MARGIN

    assert config.FIELDS.SCORE.LEFT == rect.LEFT + rect.WIDTH + margin
    assert config.FIELDS.SCORE.TOP == margin
    assert config.FIELDS.NEXT.LEFT == rect.LEFT + rect.WIDTH + margin
    assert config.FIELDS.LEVEL.TOP == (
        config.FIELDS.NEXT.TOP + config.FIELDS.NEXT.HEIGHT + margin
    )
    assert config.FIELDS.STATISTICS.LEFT == (
        rect.LEFT - margin - config.FIELDS.STATISTICS.WIDTH
    )
    assert config.FIELDS.STATISTICS.TOP == (
        rect.TOP + rect.HEIGHT - config.FIELDS.STATISTICS.HEIGHT
    )


def test_next_field_is_vertically_centred_on_the_board(manager):
    config = _build_all(manager)
    rect = config.BOARD.RECT
    next_field = config.FIELDS.NEXT

    expected_top = int(rect.TOP + rect.HEIGHT / 2 - next_field.HEIGHT / 2)

    assert next_field.TOP == expected_top


def test_type_field_is_centred_on_statistics_and_line_counter(manager):
    config = _build_all(manager)
    statistics = config.FIELDS.STATISTICS
    line_counter = config.FIELDS.LINE_COUNTER
    type_field = config.FIELDS.TYPE

    expected_left = int(statistics.LEFT + statistics.WIDTH / 2 - type_field.WIDTH / 2)
    expected_top = int(line_counter.TOP + line_counter.HEIGHT / 2)

    assert type_field.LEFT == expected_left
    assert type_field.TOP == expected_top


# Testing the "_add_font_size" method.


def test_font_size_scales_with_the_cell_height(manager):
    config = _build_all(manager)

    assert config.FONT.SIZE == int(0.7 * config.BOARD.CELL.HEIGHT)


# Testing the "_add_polyomino_spawn_positions" method.


def test_spawn_positions_are_in_grid_coordinates(manager):
    config = _build_all(manager)

    assert config.POLYOMINO.SPAWN_POSITION == [5, 2]
    assert config.POLYOMINO.SPAWN_POSITION_NEXT == [13, 10]


# Testing the "_add_all_polyonomios" method.


def test_all_polyominos_are_generated_for_the_configured_size(manager):
    config = _build_all(manager)

    assert len(config.POLYOMINO.ALL_SHAPES) == 7
    blocks = [block for shape in config.POLYOMINO.ALL_SHAPES for block in shape]
    block_sizes = [len(block) for block in blocks]

    assert all(size == 2 for size in block_sizes)


# Testing the "_change_data_types" method.


def test_change_data_types_turns_directions_into_positions(manager):
    manager._config_runtime_file_path = CONFIG_RUNTIME_FILE_PATH
    config = manager._load_runtime_config()

    config = manager._change_data_types(config=config)

    assert config.DIRECTIONS.LEFT == Position(-1, 0)
    assert isinstance(config.DIRECTIONS.DOWN, Position)


# Testing the "_write_config" method.


def test_write_config_saves_yaml_that_can_be_read_back(manager, tmp_path):
    output_file = tmp_path / "written.yaml"

    data = DotDict({"A": {"B": 1}})

    manager._write_config(file_path=output_file, config=data)

    assert "B: 1" in output_file.read_text(encoding="utf-8")


# Testing the "get_runtime_config" method.


def test_get_runtime_config_writes_and_validates_runtime_file(manager, tmp_path):
    config = manager.get_runtime_config()

    assert isinstance(config, ConfigModelRuntime)
    assert (tmp_path / "config_runtime.yaml").exists()
    assert config.WINDOW.WIDTH <= WINDOW_SIZE[0]
