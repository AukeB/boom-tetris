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
    """Root configuration model for the Tetris game.

    Attributes:
        WINDOW (Window): Window settings.
        BOARD (Board): Board settings.
        FONT (Font): Font settings.
        FIELDS (Fields): Settings of the fields around the board.
        POLYOMINO (Polyomino): Polyomino settings.
        DIRECTIONS (Directions): Movement and rotation vectors.
        DAS (Das): Delayed auto-shift settings.
        SCORE (Score): Scoring settings.
        ARE (Are): Entry delay (ARE) settings.
        GENERAL (General): General game settings.

    Example:
        >>> data = ConfigManager().load_config_without_validation(
        ...     file_path=CONFIG_SOURCE_FILE_PATH
        ... )
        >>> config_source = ConfigModelSource(**data)
        >>> config_source.GENERAL.START_LEVEL
        18
    """

    class Window(ConfiguredBaseModel):
        """Window configuration for the game canvas.

        Attributes:
            RATIO_MARGIN_TO_WINDOW_HEIGHT (int): Ratio that sets the margin from
                the window height. Larger values mean less margin.
            WIDTH (Computed): Width in pixels.
            HEIGHT (Computed): Height in pixels.
            MARGIN (Computed): Space between the fields and the window border in
                pixels.
            COLOR (Color): RGB color settings of the window.
        """

        class Color(ConfiguredBaseModel):
            """Window color settings.

            Attributes:
                BACKGROUND (list[UInt8]): RGB background color.
            """

            BACKGROUND: list[UInt8]

        RATIO_MARGIN_TO_WINDOW_HEIGHT: int
        WIDTH: Computed
        HEIGHT: Computed
        MARGIN: Computed
        COLOR: Color

    class Board(ConfiguredBaseModel):
        """Board layout, sizing, and visual configuration.

        Attributes:
            DIMENSIONS (Dimensions): Row and column counts of the board.
            RECT (Rect): Pixel rectangle of the board.
            COLOR (Color): RGB color settings of the board.
            CELL (Cell): Pixel size of one board cell.
            GRID_LINES (GridLines): Grid line rendering settings.
        """

        class Dimensions(ConfiguredBaseModel):
            """Row and column counts including hidden rows.

            Attributes:
                ROWS (int): Number of visible rows.
                COLS (int): Number of columns.
                ROWS_HIDDEN (int): Number of hidden rows above the visible rows.
                ROWS_TOTAL (Computed): Total number of rows, including hidden
                    rows.
            """

            ROWS: int
            COLS: int
            ROWS_HIDDEN: int
            ROWS_TOTAL: Computed

        class Rect(ConfiguredBaseModel):
            """Pixel coordinates and size of the board rectangle.

            Attributes:
                LEFT (Computed): Left edge of the board in pixels.
                TOP (Computed): Top edge of the board in pixels.
                WIDTH (Computed): Width of the board in pixels.
                HEIGHT (Computed): Height of the board in pixels.
            """

            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Color(ConfiguredBaseModel):
            """Board color settings.

            Attributes:
                BACKGROUND (list[UInt8]): RGB background color.
            """

            BACKGROUND: list[UInt8]

        class Cell(ConfiguredBaseModel):
            """Pixel dimensions of a single board cell.

            Attributes:
                WIDTH (Computed): Width of one board cell in pixels.
                HEIGHT (Computed): Height of one board cell in pixels.
            """

            WIDTH: Computed
            HEIGHT: Computed

        class GridLines(ConfiguredBaseModel):
            """Grid line rendering configuration.

            Attributes:
                ENABLED (bool): Whether grid lines are drawn.
                LINE_COLOR (list[UInt8]): RGB color of the grid lines.
                LINE_WIDTH (int): Width of the grid lines in pixels.
            """

            ENABLED: bool
            LINE_COLOR: list[UInt8]
            LINE_WIDTH: int

        DIMENSIONS: Dimensions
        RECT: Rect
        COLOR: Color
        CELL: Cell
        GRID_LINES: GridLines

    class Font(ConfiguredBaseModel):
        """Font sizing and color for on-screen text.

        Attributes:
            SIZE_CELLS (float): Font size relative to the cell height.
            SIZE (Computed): Font size in pixels, computed from the cell height.
            COLOR (list[UInt8]): RGB color of the font.
        """

        SIZE_CELLS: float
        SIZE: Computed
        COLOR: list[UInt8]

    class Fields(ConfiguredBaseModel):
        """Defines all fields besides the Board (The fields where Tetris is
        played).

        Attributes:
            LINE_COUNTER (LineCounter): Line counter field settings.
            SCORE (Score): Score field settings.
            NEXT (Next): Next piece preview field settings.
            LEVEL (Level): Level field settings.
            STATISTICS (Statistics): Statistics field settings.
            TYPE (Type): Type field settings.
        """

        class LineCounter(ConfiguredBaseModel):
            """Defines the size and position of the 'LineCounter' field.

            Attributes:
                LABEL (str): Text shown as the title of the field.
                HEIGHT_CELLS (int): Height of the field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            LABEL: str
            HEIGHT_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Score(ConfiguredBaseModel):
            """Defines the size an position of the 'Score' field.

            Attributes:
                LABEL (str): Text shown as the title of the score field.
                HEIGHT_CELLS (int): Height of the score field in board cells.
                WIDTH_CELLS (int): Width of the score field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            LABEL: str
            HEIGHT_CELLS: int
            WIDTH_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Next(ConfiguredBaseModel):
            """Defines the size an position of the 'Next' field.

            Attributes:
                HEIGHT_CELLS (int): Height of the field in board cells.
                WIDTH_CELLS (int): Width of the field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            HEIGHT_CELLS: int
            WIDTH_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Level(ConfiguredBaseModel):
            """Defines the size an position of the 'Level' field.

            Attributes:
                LABEL (str): Text shown as the title of the field.
                HEIGHT_CELLS (int): Height of the field in board cells.
                WIDTH_CELLS (int): Width of the field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            LABEL: str
            HEIGHT_CELLS: int
            WIDTH_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Statistics(ConfiguredBaseModel):
            """Defines the size an position of the 'Statistics' field.

            Attributes:
                LABEL (str): Text shown as the title of the field.
                HEIGHT_CELLS (int): Height of the field in board cells.
                WIDTH_CELLS (int): Width of the field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            LABEL: str
            HEIGHT_CELLS: int
            WIDTH_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        class Type(ConfiguredBaseModel):
            """Defines the size an position of the 'Type' field.

            Attributes:
                LABEL (str): Text shown as the title of the field.
                HEIGHT_CELLS (int): Height of the field in board cells.
                WIDTH_CELLS (int): Width of the field in board cells.
                LEFT (Computed): Left edge of the field in pixels.
                TOP (Computed): Top edge of the field in pixels.
                WIDTH (Computed): Width in pixels.
                HEIGHT (Computed): Height in pixels.
            """

            LABEL: str
            HEIGHT_CELLS: int
            WIDTH_CELLS: int
            LEFT: Computed
            TOP: Computed
            WIDTH: Computed
            HEIGHT: Computed

        LINE_COUNTER: LineCounter
        SCORE: Score
        NEXT: Next
        LEVEL: Level
        STATISTICS: Statistics
        TYPE: Type

    class Polyomino(ConfiguredBaseModel):
        """Polyomino shape, color, and spawn configuration.

        Attributes:
            SIZE (int): Number of cells in each polyomino.
            COLOR (list[UInt8]): RGB color of the polyomino blocks.
            ALL_SHAPES (Computed): All distinct polyomino shapes, as cell
                coordinates.
            SPAWN_POSITION (Computed): Grid position where the active piece
                spawns.
            SPAWN_POSITION_NEXT (Computed): Grid position of the next piece
                preview.
        """

        SIZE: int
        COLOR: list[UInt8]
        ALL_SHAPES: Computed
        SPAWN_POSITION: Computed
        SPAWN_POSITION_NEXT: Computed

    class Directions(ConfiguredBaseModel):
        """Movement and rotation direction vectors.

        Attributes:
            UP (list[IntDirection]): Step vector [dx, dy] for moving up.
            DOWN (list[IntDirection]): Step vector [dx, dy] for moving down.
            LEFT (list[IntDirection]): Step vector [dx, dy] for moving left.
            RIGHT (list[IntDirection]): Step vector [dx, dy] for moving right.
            ROTATE_CLOCKWISE (Literal[1, -1]): Rotation step for clockwise
                rotation.
            ROTATE_COUNTERCLOCKWISE (Literal[1, -1]): Rotation step for counter-
                clockwise rotation.
        """

        UP: list[IntDirection]
        DOWN: list[IntDirection]
        LEFT: list[IntDirection]
        RIGHT: list[IntDirection]
        ROTATE_CLOCKWISE: Literal[1, -1]
        ROTATE_COUNTERCLOCKWISE: Literal[1, -1]

    class Das(ConfiguredBaseModel):
        """Delayed auto-shift timing configuration.

        Attributes:
            DIRECTIONS (list[str]): Directions that use delayed auto-shift.
            DAS_DELAY_NTSC (int): Frames before auto-repeat starts, with NTSC
                timing.
            DAS_DELAY_PAL (int): Frames before auto-repeat starts, with PAL
                timing.
            AUTO_REPEAT_RATE_NTSC (int): Frames between repeated moves, with
                NTSC timing.
            AUTO_REPEAT_RATE_PAL (int): Frames between repeated moves, with PAL
                timing.
        """

        DIRECTIONS: list[str]
        DAS_DELAY_NTSC: int
        DAS_DELAY_PAL: int
        AUTO_REPEAT_RATE_NTSC: int
        AUTO_REPEAT_RATE_PAL: int

    class Are(ConfiguredBaseModel):
        """Entry/appearance delay configuration, scaled by the the lock row.

        Attributes:
            BASE_DELAY_FRAMES (int): Maximum entry delay in frames, for the
                highest placements.
            MIN_DELAY_FRAMES (int): Minimum entry delay in frames, for the
                lowest placements.
            FIRST_THRESHOLD_ROW (int): Lock row at or above which the full delay
                applies.
            ROWS_PER_STEP (int): Rows lower that reduce the entry delay by one
                step.
            FRAMES_PER_STEP (int): Frames removed from the entry delay per step.
        """

        BASE_DELAY_FRAMES: int
        MIN_DELAY_FRAMES: int
        FIRST_THRESHOLD_ROW: int
        ROWS_PER_STEP: int
        FRAMES_PER_STEP: int

    class Score(ConfiguredBaseModel):
        """Scoring multipliers and per-line drop values.

        Attributes:
            SINGLE (int): Points for clearing one line at level 0.
            DOUBLE_MULTIPLIER (float): Multiplier of the single-line points for
                a double.
            TRIPLE_MULTIPLIER (float): Multiplier of the double points for a
                triple.
            TETRIS_MULTIPLIER (float): Multiplier of the triple points for a
                tetris.
            SOFT_DROP_PER_LINE (int): Points per cell moved by soft drop.
            HARD_DROP_PER_LINE (int): Points per cell moved by hard drop.
        """

        SINGLE: int
        DOUBLE_MULTIPLIER: float
        TRIPLE_MULTIPLIER: float
        TETRIS_MULTIPLIER: float
        SOFT_DROP_PER_LINE: int
        HARD_DROP_PER_LINE: int

    class General(ConfiguredBaseModel):
        """General game settings, framerates, and drop frame tables.

        Attributes:
            START_LEVEL (int): Level the game starts at.
            SOFT_DROP_SPEED (float): Soft drop speed in gravity units G.
            NTSC_FRAMERATE (float): Frame rate with NTSC timing, in Hz.
            PAL_FRAMERATE (float): Frame rate with PAL timing, in Hz.
            NTSC_DROP_FRAMES (dict[int, int]): Frames per cell drop for each
                level, with NTSC timing.
            PAL_DROP_FRAMES (dict[int, int]): Frames per cell drop for each
                level, with PAL timing.
        """

        START_LEVEL: int
        SOFT_DROP_SPEED: float
        NTSC_FRAMERATE: float
        PAL_FRAMERATE: float
        NTSC_DROP_FRAMES: dict[int, int]
        PAL_DROP_FRAMES: dict[int, int]

    WINDOW: Window
    BOARD: Board
    FONT: Font
    FIELDS: Fields
    POLYOMINO: Polyomino
    DIRECTIONS: Directions
    DAS: Das
    SCORE: Score
    ARE: Are
    GENERAL: General
