"""Playfield grid: collision tests, locking pieces, and line clears."""

import itertools
from collections.abc import Iterator, Sequence

import pygame as pg

from boom_tetris.config.config_model_runtime import ConfigModelRuntime
from boom_tetris.constants import Dimensions, Position
from boom_tetris.polyomino.polyomino import Polyomino


class Board:
    """Rectangular cell matrix with hidden rows above the visible field.

    Attributes:
        dimensions (Dimensions): Number of rows (including hidden rows) and
            columns of the cell grid.
        rect (pg.Rect): Pixel rectangle of the whole board.
        cells (list[list[int]]): Occupancy grid, 1 for an occupied cell.
        cell_rect (pg.Rect): Pixel rectangle that sizes one cell.
        hidden_rows_rect (pg.Rect): Pixel rectangle covering the hidden rows.
        line_counter_rect (pg.Rect): Pixel rectangle of the line counter field.
        score_rect (pg.Rect): Pixel rectangle of the score field.
        next_rect (pg.Rect): Pixel rectangle of the next piece preview field.
        level_rect (pg.Rect): Pixel rectangle of the level field.
        type_rect (pg.Rect): Pixel rectangle of the type field.
        statistics_rect (pg.Rect): Pixel rectangle of the statistics field.
        _config (ConfigModelRuntime): The runtime configuration this board was
            built from.

    Example:
        >>> board = Board(config=config_runtime)
        >>> board.place(polyomino)
        >>> lines_cleared = board.clear_lines()
    """

    def __init__(
        self,
        config: ConfigModelRuntime,
    ) -> None:
        """Build dimensions, pygame rects, and an empty cell grid from config.

        Args:
            config: Updated model with board geometry and colors.
        """

        self._config = config

        self.dimensions = Dimensions(
            rows=self._config.BOARD.DIMENSIONS.ROWS_TOTAL,
            cols=self._config.BOARD.DIMENSIONS.COLS,
        )

        self.rect = pg.Rect(
            self._config.BOARD.RECT.LEFT,
            self._config.BOARD.RECT.TOP,
            self._config.BOARD.RECT.WIDTH,
            self._config.BOARD.RECT.HEIGHT,
        )

        self.cells: list[list[int]] = [
            [0 for _ in range(self.dimensions.cols)]
            for _ in range(self.dimensions.rows)
        ]

        self.cell_rect = pg.Rect(
            self.rect.left,
            self.rect.top,
            self._config.BOARD.CELL.WIDTH,
            self._config.BOARD.CELL.HEIGHT,
        )

        hidden_rows_ratio = (
            self._config.BOARD.DIMENSIONS.ROWS_HIDDEN
            / self._config.BOARD.DIMENSIONS.ROWS_TOTAL
        )

        self.hidden_rows_rect = pg.Rect(
            self._config.BOARD.RECT.LEFT,
            self._config.BOARD.RECT.TOP,
            self._config.BOARD.RECT.WIDTH,
            self._config.BOARD.RECT.HEIGHT * hidden_rows_ratio,
        )

        self.line_counter_rect = pg.Rect(
            self._config.FIELDS.LINE_COUNTER.LEFT,
            self._config.FIELDS.LINE_COUNTER.TOP,
            self._config.FIELDS.LINE_COUNTER.WIDTH,
            self._config.FIELDS.LINE_COUNTER.HEIGHT,
        )

        self.score_rect = pg.Rect(
            self._config.FIELDS.SCORE.LEFT,
            self._config.FIELDS.SCORE.TOP,
            self._config.FIELDS.SCORE.WIDTH,
            self._config.FIELDS.SCORE.HEIGHT,
        )

        self.next_rect = pg.Rect(
            self._config.FIELDS.NEXT.LEFT,
            self._config.FIELDS.NEXT.TOP,
            self._config.FIELDS.NEXT.WIDTH,
            self._config.FIELDS.NEXT.HEIGHT,
        )

        self.level_rect = pg.Rect(
            self._config.FIELDS.LEVEL.LEFT,
            self._config.FIELDS.LEVEL.TOP,
            self._config.FIELDS.LEVEL.WIDTH,
            self._config.FIELDS.LEVEL.HEIGHT,
        )

        self.type_rect = pg.Rect(
            self._config.FIELDS.TYPE.LEFT,
            self._config.FIELDS.TYPE.TOP,
            self._config.FIELDS.TYPE.WIDTH,
            self._config.FIELDS.TYPE.HEIGHT,
        )

        self.statistics_rect = pg.Rect(
            self._config.FIELDS.STATISTICS.LEFT,
            self._config.FIELDS.STATISTICS.TOP,
            self._config.FIELDS.STATISTICS.WIDTH,
            self._config.FIELDS.STATISTICS.HEIGHT,
        )

    def collision(
        self,
        polyomino: Polyomino,
        move_direction: Sequence[int] = Position(0, 0),
        rotate_direction: int = 0,
    ) -> bool:
        """Return True if the piece would overlap walls, floor, or blocks.

        Args:
            polyomino: Active piece with integer grid position.
            move_direction: Delta ``(dx, dy)`` applied before testing.
            rotate_direction: Rotation index or delta passed to the piece.

        Returns:
            overlaps (bool): True if any occupied cell would be illegal after
                the move.
        """

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
        """Write the piece's blocks into the cell grid as occupied.

        Args:
            polyominal: Locked piece (name kept for call-site compatibility).
        """

        for block in polyominal:
            self.cells[polyominal.y + block[1]][polyominal.x + block[0]] = 1

    def clear_lines(self) -> int:
        """Remove full rows, shift cells down, and count cleared lines.

        Returns:
            lines_cleared (int): Number of rows removed this call.
        """

        lines_cleared = 0

        for row in self.cells[:]:
            if 0 not in row:
                self.cells.remove(row)
                self.cells.insert(0, [0] * self.dimensions.cols)
                lines_cleared += 1

        return lines_cleared

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """Yield ``(row, col)`` indices for every cell in row-major order.

        Yields:
            Iterator[tuple[int, int]]: Row and column indices from ``(0,0)``
                through the board extent.
        """

        row_indices = range(self.dimensions.rows)
        col_indices = range(self.dimensions.cols)
        cell_indices = itertools.product(row_indices, col_indices)

        return cell_indices
