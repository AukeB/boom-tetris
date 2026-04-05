""" """

from pydantic import BaseModel, ConfigDict, conint
from typing import Annotated, Literal

UInt8 = Annotated[int, conint(ge=0, le=255)]
IntDirection = Literal[-1, 0, 1]


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class General(StrictBaseModel):
    START_LEVEL: int
    SOFT_DROP_SPEED: float
    ARE_DELAY: int
    NTSC_FRAMERATE: float
    PAL_FRAMERATE: float
    NTSC_DROP_FRAMES: dict[int, int]
    PAL_DROP_FRAMES: dict[int, int]


class Score(StrictBaseModel):
    SINGLE: int
    DOUBLE_MULTIPLIER: float
    TRIPLE_MULTIPLIER: float
    TETRIS_MULTIPLIER: float
    SOFT_DROP_PER_LINE: int
    HARD_DROP_PER_LINE: int


class Das(StrictBaseModel):
    DIRECTIONS: list[str]
    DAS_DELAY_NTSC: int
    DAS_DELAY_PAL: int
    AUTO_REPEAT_RATE_NTSC: int
    AUTO_REPEAT_RATE_PAL: int


class Directions(StrictBaseModel):
    UP: list[IntDirection]
    DOWN: list[IntDirection]
    LEFT: list[IntDirection]
    RIGHT: list[IntDirection]
    ROTATE_CLOCKWISE: Literal[1, -1]
    ROTATE_COUNTERCLOCKWISE: Literal[1, -1]


class Polyomino(StrictBaseModel):
    COLOR: list[UInt8]
    SIZE: int
    ALL_SHAPES: list[list[list[int]]] | None = None
    SPAWN_POSITION: list[int] | None = None
    SPAWN_POSITION_NEXT: list[int] | None = None


class BoardGridLines(StrictBaseModel):
    ENABLED: bool
    LINE_COLOR: list[UInt8]
    LINE_WIDTH: int


class BoardCell(StrictBaseModel):
    WIDTH: int | float
    HEIGHT: int | float


class BoardColor(StrictBaseModel):
    BACKGROUND: list[UInt8]


class BoardRect(StrictBaseModel):
    LEFT: int | float | None = None
    TOP: int | float | None = None
    WIDTH: int | float | None = None
    HEIGHT: int | float | None = None


class BoardDimensions(StrictBaseModel):
    ROWS: int
    COLS: int
    ROWS_HIDDEN: int
    ROWS_TOTAL: int | None = None


class Board(StrictBaseModel):
    DIMENSIONS: BoardDimensions
    RECT: BoardRect | None = None
    COLOR: BoardColor
    CELL: BoardCell | None = None
    GRID_LINES: BoardGridLines


class WindowColor(StrictBaseModel):
    BACKGROUND: list[UInt8]


class Window(StrictBaseModel):
    WIDTH: int
    HEIGHT: int
    MARGIN: int
    COLOR: WindowColor


class ConfigModel(StrictBaseModel):
    WINDOW: Window
    BOARD: Board
    POLYOMINO: Polyomino
    DIRECTIONS: Directions
    DAS: Das
    SCORE: Score
    GENERAL: General
