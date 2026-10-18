"""Tests for the YAML formatting helper and `DotDict` in `utils_dict`."""

import pytest
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from boom_tetris.utils.utils_dict import DotDict, format_for_writing_to_yaml_file

# Testing the "format_for_writing_to_yaml_file" function.


def test_format_returns_scalars_unchanged():
    formatted = format_for_writing_to_yaml_file(obj=42)

    assert formatted == 42


def test_format_wraps_dict_as_commented_map():
    formatted = format_for_writing_to_yaml_file(obj={"A": 1, "B": {"C": 2}})

    assert isinstance(formatted, CommentedMap)
    keys = formatted.keys()

    assert list(keys) == ["A", "B"]
    assert isinstance(formatted["B"], CommentedMap)


def test_format_forces_inline_lists():
    formatted = format_for_writing_to_yaml_file(obj={"COLOR": [1, 2, 3]})

    assert isinstance(formatted["COLOR"], CommentedSeq)
    assert formatted["COLOR"].fa.flow_style() is True


def test_format_special_cases_polyomino_shapes():
    shapes = [[[0, 0], [0, 1]]]

    formatted = format_for_writing_to_yaml_file(
        obj=shapes, path=["POLYOMINO", "ALL_SHAPES"]
    )

    assert isinstance(formatted, CommentedSeq)
    assert isinstance(formatted[0], CommentedSeq)
    assert formatted[0].fa.flow_style() is True


# Testing the "DotDict" class.


def test_dotdict_wraps_nested_dicts_and_lists():
    config = DotDict({"WINDOW": {"WIDTH": 800}, "ITEMS": [{"A": 1}, 2]})

    assert isinstance(config.WINDOW, DotDict)
    assert config.WINDOW.WIDTH == 800
    assert isinstance(config.ITEMS[0], DotDict)
    assert config.ITEMS[1] == 2


def test_dotdict_accepts_missing_data():
    config = DotDict()

    assert config == {}


def test_dotdict_attribute_access_for_missing_key_raises():
    config = DotDict({"A": 1})

    with pytest.raises(AttributeError, match="no attribute 'B'"):
        _ = config.B


def test_dotdict_setattr_wraps_dicts():
    config = DotDict()

    config.WINDOW = {"WIDTH": 10}

    assert isinstance(config.WINDOW, DotDict)
    assert config.WINDOW.WIDTH == 10


def test_dotdict_delattr_removes_key():
    config = DotDict({"A": 1})

    del config.A

    assert "A" not in config


def test_dotdict_delattr_for_missing_key_raises():
    config = DotDict({"A": 1})

    with pytest.raises(AttributeError, match="no attribute 'B'"):
        del config.B


def test_dotdict_to_dict_returns_plain_structures():
    config = DotDict({"WINDOW": {"WIDTH": 800}, "ITEMS": [{"A": 1}, 2], "N": 3})

    plain = config.to_dict()

    assert plain == {"WINDOW": {"WIDTH": 800}, "ITEMS": [{"A": 1}, 2], "N": 3}
    assert type(plain["WINDOW"]) is dict
    assert type(plain["ITEMS"][0]) is dict
