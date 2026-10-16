"""Tests for the falling piece in `polyomino`."""

import random

import pytest

from src.boom_tetris.polyomino import polyomino as polyomino_module
from src.boom_tetris.polyomino.polyomino import Polyomino


def _index_with_rotation_type(rotation_type):
    """Find the shape index whose metadata has the given rotation type.

    Args:
        rotation_type (str | None): Rotation type to look for.

    Returns:
        index (int): Index into the list of all shapes.
    """
    for index, blocks in enumerate(polyomino_module._ALL_POLYOMINOS):
        properties = polyomino_module._POLYOMINO_MAPPING[tuple(blocks)]
        if properties.rotation_type == rotation_type:
            return index

    raise AssertionError(f"no shape with rotation type {rotation_type!r}")


def _force_index(monkeypatch, index):
    """Make the next piece use the given shape index.

    Args:
        monkeypatch: Pytest fixture used to replace the random roll.
        index (int): Shape index to force.
    """
    monkeypatch.setattr(Polyomino, "_roll_index", staticmethod(lambda previous: index))


# Testing the "_roll_index" method.


def test_roll_index_rerolls_the_spare_value(monkeypatch):
    rolls = iter([7, 2])
    monkeypatch.setattr(random, "randint", lambda low, high: next(rolls))

    index = Polyomino._roll_index(previous_polyomino_index=None)

    assert index == 2


def test_roll_index_rerolls_a_repeat_of_the_previous_piece(monkeypatch):
    rolls = iter([3, 5])
    monkeypatch.setattr(random, "randint", lambda low, high: next(rolls))

    index = Polyomino._roll_index(previous_polyomino_index=3)

    assert index == 5


def test_roll_index_keeps_a_fresh_roll(monkeypatch):
    monkeypatch.setattr(random, "randint", lambda low, high: 4)

    index = Polyomino._roll_index(previous_polyomino_index=1)

    assert index == 4


# Testing the "__init__" method of the "Polyomino" class.


def test_init_sets_position_and_shape(monkeypatch):
    index = _index_with_rotation_type(None)
    _force_index(monkeypatch, index)

    piece = Polyomino(x=3, y=1)

    assert (piece.x, piece.y) == (3, 1)
    assert piece.index == _index_with_rotation_type(None)


def test_init_uses_first_predefined_rotation(monkeypatch):
    index = _index_with_rotation_type("predefined")
    _force_index(monkeypatch, index)

    piece = Polyomino(x=0, y=0)

    assert piece._rotation_index == 0
    assert piece._blocks == piece._rotations[0]


# Testing the "get_rotation" method.


def test_get_rotation_without_change_returns_current_blocks(monkeypatch):
    index = _index_with_rotation_type("matrix_rotation")
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)

    blocks = piece.get_rotation(direction=0)

    assert blocks is piece._blocks


def test_get_rotation_for_square_returns_current_blocks(monkeypatch):
    index = _index_with_rotation_type(None)
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)

    blocks = piece.get_rotation(direction=1)

    assert blocks is piece._blocks


def test_get_rotation_for_predefined_shape_picks_next_orientation(monkeypatch):
    index = _index_with_rotation_type("predefined")
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)

    blocks = piece.get_rotation(direction=1)

    assert blocks == piece._rotations[1 % len(piece._rotations)]


def test_get_rotation_for_matrix_shape_turns_the_blocks(monkeypatch):
    index = _index_with_rotation_type("matrix_rotation")
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)
    piece._blocks = [(1, 0)]

    blocks = piece.get_rotation(direction=1)

    assert blocks == [(0, 1)]


# Testing the "rotate" method.


def test_rotate_advances_predefined_orientation(monkeypatch):
    index = _index_with_rotation_type("predefined")
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)

    piece.rotate(direction=1)

    assert piece._rotation_index == 1
    assert piece._blocks == piece._rotations[1]


def test_rotate_recomputes_matrix_shape_blocks(monkeypatch):
    index = _index_with_rotation_type("matrix_rotation")
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)
    piece._blocks = [(1, 0)]

    piece.rotate(direction=1)

    assert piece._blocks == [(0, 1)]


# Testing the "__iter__" method of the "Polyomino" class.


def test_iter_yields_the_block_offsets(monkeypatch):
    index = _index_with_rotation_type(None)
    _force_index(monkeypatch, index)
    piece = Polyomino(x=0, y=0)

    assert list(piece) == list(piece._blocks)
