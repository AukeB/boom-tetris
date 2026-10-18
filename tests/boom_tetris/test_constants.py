"""Tests for the shared paths and record types in `constants`."""

from boom_tetris import constants

# Testing the file path constants.


def test_configuration_and_asset_files_exist():
    paths = [
        constants.CONFIG_SOURCE_FILE_PATH,
        constants.CONFIG_RUNTIME_FILE_PATH,
        constants.TRIOMINO_PROPERTIES_FILE_PATH,
        constants.TETROMINO_PROPERTIES_FILE_PATH,
        constants.FONT_FILE_PATH,
    ]

    existence = [path.exists() for path in paths]

    assert all(existence)


# Testing the record types.


def test_record_types_have_expected_fields():
    assert constants.Dimensions._fields == ("rows", "cols")
    assert constants.Position._fields == ("x", "y")
    assert constants._Size._fields == ("width", "height")


def test_window_size_fraction_is_a_ratio():
    assert 0 < constants.WINDOW_SIZE_SCREEN_FRACTION <= 1
