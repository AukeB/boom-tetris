"""Pydantic models for validating and typing game YAML configuration."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, conint

# Used for defining colors in RGB notation.
UInt8 = Annotated[int, conint(ge=0, le=255)]
IntDirection = Literal[-1, 0, 1]

# Used for parameters that will be computed based on other parameters.
Computed = Literal["COMPUTED"]


class ConfiguredBaseModel(BaseModel):
    """Config model that forbids extra parameter"""

    model_config = ConfigDict(extra="forbid")


class ConfigModelSource(ConfiguredBaseModel):
    """Root configuration model for the Tetris game."""

    class Window(ConfiguredBaseModel):
        """Window configuration for the game canvas."""

        class Color(ConfiguredBaseModel):
            """Window color settings."""

            BACKGROUND: list[UInt8]

        RATIO_MARGIN_TO_WINDOW_HEIGHT: int
        WIDTH: Computed
        HEIGHT: Computed
        MARGIN: Computed
        COLOR: Color

    class Board(ConfiguredBaseModel):
        """Board layout, sizing, and visual configuration."""

        class Dimensions(ConfiguredBaseModel):
            """Row and column counts including hidden rows."""

            ROWS: int
            COLS: int
            ROWS_HIDDEN: int
            ROWS_TOTAL: Computed

        class Rect(ConfiguredBaseModel):
            """Pixel coordinates and size of the board rectangle."""

            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Color(ConfiguredBaseModel):
            """Board color settings."""

            BACKGROUND: list[UInt8]

        class Cell(ConfiguredBaseModel):
            """Pixel dimensions of a single board cell."""

            WIDTH: Computed
            HEIGHT: Computed

        class GridLines(ConfiguredBaseModel):
            """Grid line rendering configuration."""

            ENABLED: bool
            LINE_COLOR: list[UInt8]
            LINE_WIDTH: int

        DIMENSIONS: Dimensions
        RECT: Rect
        COLOR: Color
        CELL: Cell
        GRID_LINES: GridLines

    class Fields(ConfiguredBaseModel):
        """Defines all fields besides the Board (The fields where Tetris is played)."""

        class LineCounter(ConfiguredBaseModel):
            """Defines the size and position of the 'line_counter' field."""

            HEIGHT_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        LINE_COUNTER: LineCounter

    class Polyomino(ConfiguredBaseModel):
        """Polyomino shape, color, and spawn configuration."""

        SIZE: int
        COLOR: list[UInt8]
        ALL_SHAPES: Computed
        SPAWN_POSITION: Computed
        SPAWN_POSITION_NEXT: Computed

    class Directions(ConfiguredBaseModel):
        """Movement and rotation direction vectors."""

        UP: list[IntDirection]
        DOWN: list[IntDirection]
        LEFT: list[IntDirection]
        RIGHT: list[IntDirection]
        ROTATE_CLOCKWISE: Literal[1, -1]
        ROTATE_COUNTERCLOCKWISE: Literal[1, -1]

    class Das(ConfiguredBaseModel):
        """Delayed auto-shift timing configuration."""

        DIRECTIONS: list[str]
        DAS_DELAY_NTSC: int
        DAS_DELAY_PAL: int
        AUTO_REPEAT_RATE_NTSC: int
        AUTO_REPEAT_RATE_PAL: int

    class Score(ConfiguredBaseModel):
        """Scoring multipliers and per-line drop values."""

        SINGLE: int
        DOUBLE_MULTIPLIER: float
        TRIPLE_MULTIPLIER: float
        TETRIS_MULTIPLIER: float
        SOFT_DROP_PER_LINE: int
        HARD_DROP_PER_LINE: int

    class General(ConfiguredBaseModel):
        """General game settings, framerates, and drop frame tables."""

        START_LEVEL: int
        SOFT_DROP_SPEED: float
        ARE_DELAY: int
        NTSC_FRAMERATE: float
        PAL_FRAMERATE: float
        NTSC_DROP_FRAMES: dict[int, int]
        PAL_DROP_FRAMES: dict[int, int]

    WINDOW: Window
    BOARD: Board
    FIELDS: Fields
    POLYOMINO: Polyomino
    DIRECTIONS: Directions
    DAS: Das
    SCORE: Score
    GENERAL: General
