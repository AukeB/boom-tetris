""" """

import itertools
from collections.abc import Iterator

import pygame as pg

from src.boom_tetris.config.model import ConfigModel
from src.boom_tetris.constants import Dimensions, Position
from src.boom_tetris.polyomino.polyomino import Polyomino


class Board:
    """ """

    def __init__(
        self,
        config: ConfigModel,
    ) -> None:
        """ """
        self.config = config

        self.dimensions = Dimensions(
            rows=self.config.BOARD.DIMENSIONS.ROWS_TOTAL,
            cols=self.config.BOARD.DIMENSIONS.COLS,
        )

        self.rect = pg.Rect(
            self.config.BOARD.RECT.LEFT,
            self.config.BOARD.RECT.TOP,
            self.config.BOARD.RECT.WIDTH,
            self.config.BOARD.RECT.HEIGHT,
        )

        self.cells: list[list[int]] = [
            [0 for _ in range(self.dimensions.cols)]
            for _ in range(self.dimensions.rows)
        ]

        self.cell_rect = pg.Rect(
            self.rect.left,
            self.rect.top,
            self.config.BOARD.CELL.WIDTH,
            self.config.BOARD.CELL.HEIGHT,
        )

        hidden_rows_ratio = (
            self.config.BOARD.DIMENSIONS.ROWS_HIDDEN
            / self.config.BOARD.DIMENSIONS.ROWS_TOTAL
        )

        self.hidden_rows_rect = pg.Rect(
            self.config.BOARD.RECT.LEFT,
            self.config.BOARD.RECT.TOP,
            self.config.BOARD.RECT.WIDTH,
            self.config.BOARD.RECT.HEIGHT * hidden_rows_ratio,
        )

    def collision(
        self,
        polyomino: Polyomino,
        move_direction: Position = Position(0, 0),
        rotate_direction: int = 0,
    ) -> bool:
        """ """
        for block in polyomino.get_rotation(rotate_direction):
            boundary_position = Position(
                x=polyomino.x + block[0] + move_direction[0],
                y=polyomino.y + block[1] + move_direction[1],
            )

            collision: bool = (
                boundary_position.x < 0
                or boundary_position.x >= self.dimensions.cols
                or boundary_position.y < 0
                or boundary_position.y >= self.dimensions.rows
            )

            if collision:
                return True

            if self.cells[boundary_position.y][boundary_position.x]:
                return True

        return False

    def place(self, polyominal: Polyomino) -> None:
        """ """
        for block in polyominal:
            self.cells[polyominal.y + block[1]][polyominal.x + block[0]] = 1

    def clear_lines(self) -> int:
        """ """
        lines_cleared = 0

        for row in self.cells[:]:
            if 0 not in row:
                self.cells.remove(row)
                self.cells.insert(0, [0] * self.dimensions.cols)
                lines_cleared += 1

        return lines_cleared

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """ """
        return itertools.product(
            range(self.dimensions.rows), range(self.dimensions.cols)
        )
