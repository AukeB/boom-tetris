"""Pygame drawing helpers for the window, board, pieces, and overlays."""

from types import TracebackType

import pygame as pg

from src.boom_tetris.board import Board
from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.constants import FONT_RELATIVE_FILE_PATH, Position
from src.boom_tetris.polyomino.polyomino import Polyomino
from src.boom_tetris.utils.utils_other import get_window_size_from_screen_resolution


class Renderer:
    """Owns the display surface and draws the current game state each frame."""

    def __init__(
        self,
        config: ConfigModelRuntime,
    ) -> None:
        """Create the window and cache colors and dimensions from config.

        Args:
            config: Augmented model with window and board layout.
        """
        self.config = config
        self.window_width, self.window_height = get_window_size_from_screen_resolution()

        self.background_color = self.config.WINDOW.COLOR.BACKGROUND

        self._initialize_window()

        self.surface = pg.display.get_surface()
        self.font = pg.font.Font(str(FONT_RELATIVE_FILE_PATH), self.config.FONT.SIZE)

    def __enter__(self) -> None:
        """Clear the framebuffer to the window background color."""
        self.surface.fill(color=self.background_color)

    def __exit__(
        self,
        exc_tupe: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_trace: TracebackType | None,
    ) -> None:
        """Flip buffers after the frame is drawn (context manager exit).

        Args:
            exc_tupe: Exception type if an error occurred, else ``None``.
            exc_value: Exception instance if any.
            exc_trace: Traceback object if any.
        """
        pg.display.update()

    def _initialize_window(self) -> None:
        """Open a pygame display with the configured pixel size."""
        pg.display.set_mode(size=(self.window_width, self.window_height))

    def draw_board(self, board: Board) -> None:
        """Fill the board rect and draw every locked block.

        Args:
            board: Playfield whose ``cells`` matrix drives occupied squares.
        """
        # Draw the background of the board.
        pg.draw.rect(
            surface=self.surface,
            color=self.config.BOARD.COLOR.BACKGROUND,
            rect=board.rect,
        )

        cell = board.cell_rect.copy()

        # Draw the placed pieces in the board.
        for row, col in board:
            if board.cells[row][col]:
                cell.y = board.rect.y + board.cell_rect.height * row
                cell.x = board.rect.x + board.cell_rect.width * col

                pg.draw.rect(
                    surface=self.surface,
                    color=self.config.POLYOMINO.COLOR,
                    rect=cell,
                )

    def draw_polyomino(self, polyomino: Polyomino, block_rect: pg.Rect) -> None:
        """Draw each block of a piece using a shared cell-sized rect template.

        Args:
            polyomino: Piece with grid offset and block list.
            block_rect: Prototype rect (size matches one cell); mutated while drawing.
        """
        polyomino_position = Position(
            x=block_rect.x + polyomino.x * block_rect.width,
            y=block_rect.y + polyomino.y * block_rect.height,
        )

        for block in polyomino:
            block_rect.x = polyomino_position.x + block[0] * block_rect.width
            block_rect.y = polyomino_position.y + block[1] * block_rect.height
            pg.draw.rect(self.surface, (self.config.POLYOMINO.COLOR), block_rect)

    def draw_grid_lines(self, board: Board) -> None:
        """Draw optional vertical and horizontal grid lines when enabled.

        Args:
            board: Board providing pixel geometry and visible row range.
        """
        if self.config.BOARD.GRID_LINES.ENABLED:
            for col in range(1, board.dimensions.cols):
                x = board.rect.x + col * board.cell_rect.width
                start_pos = (x, board.rect.y)
                end_pos = (x, board.rect.y + board.rect.height)
                pg.draw.line(
                    self.surface,
                    self.config.BOARD.GRID_LINES.LINE_COLOR,
                    start_pos,
                    end_pos,
                    self.config.BOARD.GRID_LINES.LINE_WIDTH,
                )

            for row in range(
                self.config.BOARD.DIMENSIONS.ROWS_HIDDEN + 1, board.dimensions.rows
            ):
                y = board.rect.y + row * board.cell_rect.height
                start_pos = (board.rect.x, y)
                end_pos = (board.rect.x + board.rect.width, y)
                pg.draw.line(
                    self.surface,
                    self.config.BOARD.GRID_LINES.LINE_COLOR,
                    start_pos,
                    end_pos,
                    self.config.BOARD.GRID_LINES.LINE_WIDTH,
                )

    def draw_rect(self, rect: pg.Rect, color: list[int]) -> None:
        """Draw a filled rectangle onto the surface.

        Args:
            rect: Pixel rectangle defining position and size.
            color: RGB color to fill the rectangle with.
        """
        pg.draw.rect(
            surface=self.surface,
            color=color,
            rect=rect,
        )

    def draw_text(
        self, text: str, rect: pg.Rect, color: list[int] | None = None
    ) -> None:
        """Render text centered within a field rect.

        Args:
            text (str): String to render.
            rect (pg.Rect): Field rectangle the text is centered in.
            color: RGB text color; falls back to the configured font color.
        """
        resolved_color = color or self.config.FONT.COLOR

        text_surface = self.font.render(text, True, resolved_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.surface.blit(text_surface, text_rect)

    def draw_label_and_value(
        self, label: str, value: str, rect: pg.Rect, color: list[int] | None = None
    ) -> None:
        """Stack a label above a value within a field rect.

        Args:
            label (str): Field title draw centered in the top half.
            value: Value drawn centered in the bottom half.
            rect: Field rectangle split vertically between label and value.
            color: RGB text color; falls back to the configured font color.
        """
        half_height = rect.height // 2
        label_rect = pg.Rect(rect.left, rect.top, rect.width, half_height)
        value_rect = pg.Rect(rect.left, rect.top + half_height, rect.width, half_height)

        self.draw_text(text=label, rect=label_rect, color=color)
        self.draw_text(text=value, rect=value_rect, color=color)
