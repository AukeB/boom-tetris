"""Tests for the playfield in `board`."""

import pytest

from boom_tetris.board import Board
from boom_tetris.constants import Dimensions
from boom_tetris.polyomino.polyomino import Polyomino


@pytest.fixture
def board(runtime_config):
    """Build an empty board from the committed configuration.

    Args:
        runtime_config (ConfigModelRuntime): The runtime configuration.

    Returns:
        board (Board): An empty playfield.
    """
    board = Board(config=runtime_config)

    return board


def _piece_at(x, y):
    """Build a square piece at a grid position.

    Args:
        x (int): Column of the piece origin.
        y (int): Row of the piece origin.

    Returns:
        piece (Polyomino): A square piece, which has no rotation.
    """
    piece = Polyomino(x=x, y=y)
    piece._blocks = [(0, 0), (1, 0), (0, 1), (1, 1)]

    return piece


# Testing the "__init__" method of the "Board" class.


def test_init_builds_an_empty_grid(board):
    assert board.dimensions == Dimensions(rows=22, cols=10)
    assert len(board.cells) == 22
    row_sums = [sum(row) for row in board.cells]

    assert all(total == 0 for total in row_sums)


def test_init_builds_pygame_rects_from_config(board, runtime_config):
    assert board.rect.left == runtime_config.BOARD.RECT.LEFT
    assert board.cell_rect.width == runtime_config.BOARD.CELL.WIDTH
    assert board.hidden_rows_rect.width == runtime_config.BOARD.RECT.WIDTH


# Testing the "collision" method.


def test_collision_is_false_for_a_free_position(board):
    piece = _piece_at(x=4, y=5)

    assert board.collision(piece) is False


@pytest.mark.parametrize(
    ("x", "y"),
    [(-1, 5), (9, 5), (4, -1), (4, 21)],
)
def test_collision_detects_walls_and_floor(board, x, y):
    piece = _piece_at(x=x, y=y)

    assert board.collision(piece) is True


def test_collision_detects_occupied_cells(board):
    board.cells[5][4] = 1
    piece = _piece_at(x=4, y=5)

    assert board.collision(piece) is True


def test_collision_accounts_for_the_move_direction(board):
    piece = _piece_at(x=0, y=5)

    assert board.collision(piece, move_direction=(-1, 0)) is True
    assert board.collision(piece, move_direction=(1, 0)) is False


def test_collision_accounts_for_the_rotation(board):
    piece = _piece_at(x=4, y=5)

    assert board.collision(piece, rotate_direction=1) is False


# Testing the "place" method.


def test_place_marks_the_piece_cells_as_occupied(board):
    piece = _piece_at(x=2, y=10)

    board.place(piece)

    assert board.cells[10][2] == 1
    assert board.cells[11][3] == 1
    row_sums = [sum(row) for row in board.cells]

    assert sum(row_sums) == 4


# Testing the "clear_lines" method.


def test_clear_lines_removes_full_rows_and_counts_them(board):
    for row in (20, 21):
        board.cells[row] = [1] * 10

    lines_cleared = board.clear_lines()

    assert lines_cleared == 2
    row_sums = [sum(row) for row in board.cells]

    assert all(total == 0 for total in row_sums)


def test_clear_lines_keeps_partial_rows(board):
    board.cells[21][0] = 1

    lines_cleared = board.clear_lines()

    assert lines_cleared == 0
    assert board.cells[21][0] == 1


# Testing the "__iter__" method of the "Board" class.


def test_iter_yields_every_cell_index_in_row_major_order(board):
    indices = list(board)

    assert len(indices) == 22 * 10
    assert indices[0] == (0, 0)
    assert indices[-1] == (21, 9)
