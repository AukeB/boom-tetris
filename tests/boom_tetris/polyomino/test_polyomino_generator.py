"""Tests for the polyomino enumeration in `polyomino_generator`."""

import pytest

from boom_tetris.polyomino.polyomino_generator import PolyominoGenerator

DIRECTIONS = {
    "UP": [0, -1],
    "DOWN": [0, 1],
    "LEFT": [-1, 0],
    "RIGHT": [1, 0],
}


# Testing the "PolyominoGenerator" class.


@pytest.mark.parametrize(
    ("cells", "expected_count"),
    [(1, 1), (2, 1), (3, 2), (4, 7)],
)
def test_generate_counts_one_sided_polyominoes(cells, expected_count):
    generator = PolyominoGenerator(
        number_of_polyomino_cells=cells, directions=DIRECTIONS
    )

    shapes = generator.generate()

    assert len(shapes) == expected_count


def test_generate_records_only_shapes_of_the_target_size():
    generator = PolyominoGenerator(number_of_polyomino_cells=3, directions=DIRECTIONS)

    shapes = generator.generate()

    shape_sizes = [len(shape) for shape in shapes]

    assert all(size == 3 for size in shape_sizes)


# Testing the "_normalize" method.


def test_normalize_moves_the_shape_to_the_origin():
    generator = PolyominoGenerator(number_of_polyomino_cells=2, directions=DIRECTIONS)

    normalized = generator._normalize(((2, 3), (3, 3)))

    assert normalized == ((0, 0), (1, 0))


# Testing the "_rotate" method.


def test_rotate_turns_each_cell_counter_clockwise():
    generator = PolyominoGenerator(number_of_polyomino_cells=2, directions=DIRECTIONS)

    rotated = generator._rotate(((0, 0), (1, 0)))

    assert rotated == ((0, 0), (0, -1))


# Testing the "_obtain_all_rotations" method.


def test_obtain_all_rotations_returns_four_orientations():
    generator = PolyominoGenerator(number_of_polyomino_cells=2, directions=DIRECTIONS)

    rotations = generator._obtain_all_rotations(((0, 0), (1, 0)))

    assert len(rotations) == 4
    assert rotations[0] == ((0, 0), (0, 1))
