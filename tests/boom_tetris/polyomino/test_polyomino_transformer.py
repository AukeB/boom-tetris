"""Tests for the correction pipeline in `polyomino_transformer`."""

import pytest

from boom_tetris.polyomino.polyomino_generator import PolyominoGenerator
from boom_tetris.polyomino.polyomino_transformer import PolyominoTransformer
from boom_tetris.utils.utils_dict import DotDict

DIRECTIONS = {
    "UP": [0, -1],
    "DOWN": [0, 1],
    "LEFT": [-1, 0],
    "RIGHT": [1, 0],
}


UNCORRECTED_ROTATIONS = [DotDict({"rotation_correction": 0}), DotDict({})]
UNCORRECTED_OFFSETS = [DotDict({"position_correction": [0, 0]}), DotDict({})]


def _config(size):
    """Build the config section the transformer reads.

    Args:
        size (int): Number of cells per polyomino.

    Returns:
        config (DotDict): Config with the generated shapes for that size.
    """
    generator = PolyominoGenerator(number_of_polyomino_cells=size, directions=DIRECTIONS)
    generated = generator.generate()
    shapes = [[[x, y] for (x, y) in shape] for shape in generated]

    polyomino_section = {"SIZE": size, "ALL_SHAPES": shapes}
    config = DotDict({"POLYOMINO": polyomino_section})

    return config


def _transformer_with_state(polyominos, mapping):
    """Build a transformer and replace its shapes and metadata.

    Args:
        polyominos (list[list[list[int]]]): Shapes to transform.
        mapping (dict): Correction metadata keyed by canonical cell tuples.

    Returns:
        transformer (PolyominoTransformer): Transformer holding that state.
    """
    config = _config(4)
    transformer = PolyominoTransformer(config=config)
    transformer._polyominos = polyominos
    transformer._polyomino_mapping = mapping

    return transformer


# Testing the "__init__" method of the "PolyominoTransformer" class.


@pytest.mark.parametrize("size", [3, 4])
def test_init_loads_metadata_for_supported_sizes(size):
    config = _config(size)
    transformer = PolyominoTransformer(config=config)

    assert len(transformer._polyomino_mapping) > 0
    assert len(transformer._polyominos) > 0


def test_init_accepts_missing_shapes():
    config = DotDict({"POLYOMINO": {"SIZE": 4, "ALL_SHAPES": None}})

    transformer = PolyominoTransformer(config=config)

    assert transformer._polyominos == []


def test_init_raises_for_sizes_without_metadata():
    config = _config(5)

    with pytest.raises(ValueError, match="No correction metadata"):
        PolyominoTransformer(config=config)


# Testing the "_sort" method.


def test_sort_orders_shapes_and_metadata_together():
    empty = DotDict({})
    transformer = _transformer_with_state(
        polyominos=[[[2, 0]], [[0, 1]]],
        mapping={((2, 0),): empty, ((0, 1),): empty},
    )

    transformer._sort()

    assert transformer._polyominos == [[[0, 1]], [[2, 0]]]
    keys_view = transformer._polyomino_mapping.keys()
    keys = list(keys_view)

    assert keys == [((0, 1),), ((2, 0),)]


# Testing the "_rotate" method.


def test_rotate_applies_a_nonzero_rotation_correction():
    properties = DotDict({"rotation_correction": 1})
    transformer = _transformer_with_state(
        polyominos=[[[1, 0]]],
        mapping={((1, 0),): properties},
    )

    transformer._rotate()

    assert transformer._polyominos == [[[0, 1]]]


@pytest.mark.parametrize("properties", UNCORRECTED_ROTATIONS)
def test_rotate_leaves_shapes_without_correction(properties):
    transformer = _transformer_with_state(
        polyominos=[[[1, 0]]],
        mapping={((1, 0),): properties},
    )

    transformer._rotate()

    assert transformer._polyominos == [[[1, 0]]]


# Testing the "_shift" method.


def test_shift_applies_a_nonzero_position_correction():
    properties = DotDict({"position_correction": [1, -1]})
    transformer = _transformer_with_state(
        polyominos=[[[1, 0]]],
        mapping={((1, 0),): properties},
    )

    transformer._shift()

    assert transformer._polyominos == [[[2, -1]]]


@pytest.mark.parametrize("properties", UNCORRECTED_OFFSETS)
def test_shift_leaves_shapes_without_offset(properties):
    transformer = _transformer_with_state(
        polyominos=[[[1, 0]]],
        mapping={((1, 0),): properties},
    )

    transformer._shift()

    assert transformer._polyominos == [[[1, 0]]]


# Testing the "_mirror_horizontally" method.


def test_mirror_negates_the_y_coordinate():
    properties = DotDict({})
    transformer = _transformer_with_state(
        polyominos=[[[1, 2]]],
        mapping={((1, 2),): properties},
    )

    transformer._mirror_horizontally()

    assert transformer._polyominos == [[[1, -2]]]


# Testing the "execute" method.


@pytest.mark.parametrize("size", [3, 4])
def test_execute_returns_tuple_shapes_and_metadata(size):
    config = _config(size)
    transformer = PolyominoTransformer(config=config)

    polyominos, mapping = transformer.execute()
    blocks = [block for shape in polyominos for block in shape]

    is_tuple = [isinstance(block, tuple) for block in blocks]

    assert all(is_tuple)
    assert mapping is transformer._polyomino_mapping


def test_execute_returns_shapes_unchanged_for_other_sizes():
    config = _config(4)
    transformer = PolyominoTransformer(config=config)
    transformer._polyomino_size = 5
    transformer._polyominos = [[[1, 0], [0, 0]]]

    polyominos, _ = transformer.execute()

    assert polyominos == [[(1, 0), (0, 0)]]
