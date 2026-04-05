""" """

import pygame as pg

from types import TracebackType

from src.boom_tetris.board import Board
from src.boom_tetris.config.model import ConfigModel
from src.boom_tetris.polyomino.polyomino import Polyomino
from src.boom_tetris.constants import Position


class Renderer:
    """ """

    def __init__(
        self,
        config: ConfigModel,
    ) -> None:
        """ """
        self.config = config
        self.window_width = self.config.WINDOW.WIDTH
        self.window_height = self.config.WINDOW.HEIGHT
        self.background_color = self.config.WINDOW.COLOR.BACKGROUND

        self._initialize_window()

        self.surface = pg.display.get_surface()

    def __enter__(self) -> None:
        """ """
        self.surface.fill(color=self.background_color)

    def __exit__(
        self,
        exc_tupe: type[BaseException] | None,
        exc_value: BaseException | None,
        exc_trace: TracebackType | None,
    ) -> None:
        """ """
        pg.display.update()

    def _initialize_window(self) -> None:
        """ """
        pg.display.set_mode(size=(self.window_width, self.window_height))

    def draw_board(self, board: Board) -> None:
        """ """
        # Draw the background of the board.
        pg.draw.rect(
            surface=self.surface,
            color=self.config.BOARD.COLOR.BACKGROUND,
            rect=board.rect,
        )

        cell = board.cell_rect.copy()

        # Draw the place pieces in the board.
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
        """ """
        polyomino_position = Position(
            x=block_rect.x + polyomino.x * block_rect.width,
            y=block_rect.y + polyomino.y * block_rect.height,
        )

        for block in polyomino:
            block_rect.x = polyomino_position.x + block[0] * block_rect.width
            block_rect.y = polyomino_position.y + block[1] * block_rect.height
            pg.draw.rect(self.surface, (self.config.POLYOMINO.COLOR), block_rect)

    def draw_grid_lines(self, board: Board) -> None:
        """ """
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

    def draw_block_hidden_rows(self, board: Board) -> None:
        """ """
        pg.draw.rect(
            surface=self.surface,
            color=self.background_color,
            rect=board.hidden_rows_rect,
        )
