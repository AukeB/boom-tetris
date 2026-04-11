"""Shared paths and simple record types used across the game."""

from collections import namedtuple
from pathlib import Path

# Main configuration relative file path.
CONFIG_SOURCE_FILE_PATH = Path("src/boom_tetris/configs/config_source.yaml")
CONFIG_RUNTIME_FILE_PATH = Path("src/boom_tetris/configs/config_runtime.yaml")

# Polyomino properpties paths.
TRIOMINO_PROPERTIES_RELATIVE_FILE_PATH = Path(
    "src/boom_tetris/configs/triomino_properties.json"
)
TETROMINO_PROPERTIES_RELATIVE_FILE_PATH = Path(
    "src/boom_tetris/configs/tetromino_properties.json"
)


"""
`Dimensions` refers to the structural properties of a grid, 
    matrix, or layout, specifying the number of columns and 
    rows into which the grid is partitioned.
`Size` denotes the physical or spatial extent of an object,
    characterized by its width and height. These measurements
    are typically expressed in pixels, but any unit of physical 
    distance may be employed.
`Position` specifies a location using `x` and `y` coordinates.
    These coordinates may represent a position on the screen 
    in pixel units, or a location within a grid or board, 
    expressed in terms of columns and rows.
"""
Dimensions = namedtuple("Dimensions", "rows cols")
Size = namedtuple("Size", "width height")
Position = namedtuple("Position", "x y")

# Determines the ratio between the PyGame window resolution and the screen resolution
WINDOW_SIZE_SCREEN_FRACTION = 0.99
