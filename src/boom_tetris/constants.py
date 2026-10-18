"""Shared paths and simple record types used across the game."""

from collections import namedtuple
from pathlib import Path

_PACKAGE_DIRECTORY = Path(__file__).parent

# Main configuration file paths.
CONFIG_SOURCE_FILE_PATH = _PACKAGE_DIRECTORY / "configs" / "config_source.yaml"
CONFIG_RUNTIME_FILE_PATH = _PACKAGE_DIRECTORY / "configs" / "config_runtime.yaml"

# Polyomino properties paths.
TRIOMINO_PROPERTIES_FILE_PATH = (
    _PACKAGE_DIRECTORY / "configs" / "triomino_properties.json"
)
TETROMINO_PROPERTIES_FILE_PATH = (
    _PACKAGE_DIRECTORY / "configs" / "tetromino_properties.json"
)

# Font assets path.
FONT_FILE_PATH = _PACKAGE_DIRECTORY / "assets" / "fonts" / "8-bit-pusab.ttf"


"""`Dimensions` refers to the structural properties of a grid, matrix, or
layout, specifying the number of columns and rows into which the grid is
partitioned.

`Size` denotes the physical or spatial extent of an object, characterized by its
width and height. These measurements are typically expressed in pixels, but any
unit of physical distance may be employed.

`Position` specifies a location using `x` and `y` coordinates. These coordinates
may represent a position on the screen in pixel units, or a location within a
grid or board, expressed in terms of columns and rows.
"""

Dimensions = namedtuple("Dimensions", "rows cols")
_Size = namedtuple("_Size", "width height")
Position = namedtuple("Position", "x y")

# Determines the ratio between the PyGame window resolution and the screen resolution
WINDOW_SIZE_SCREEN_FRACTION = 0.95
