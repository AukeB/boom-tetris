"""Tests for the time and level helpers in `utils_game`."""

import pytest

from boom_tetris.utils.utils_game import (
    compute_first_level_advancement,
    convert_drop_frames_to_time,
    frames2ms,
    get_frames_per_cell,
    gravity2ms,
)

# Testing the "convert_drop_frames_to_time" function.


def test_convert_drop_frames_to_time_returns_milliseconds():
    drop_interval = convert_drop_frames_to_time(framerate=60, frames_per_cell=6)

    assert drop_interval == pytest.approx(100.0)


# Testing the "compute_first_level_advancement" function.


@pytest.mark.parametrize(
    ("start_level", "expected"),
    [(0, 10), (5, 60), (18, 130)],
)
def test_compute_first_level_advancement(start_level, expected):
    threshold = compute_first_level_advancement(start_level)

    assert threshold == expected


# Testing the "get_frames_per_cell" function.


def test_get_frames_per_cell_uses_exact_level():
    frames = get_frames_per_cell(level=5, frames_per_cell={0: 48, 5: 23})

    assert frames == 23


def test_get_frames_per_cell_steps_down_to_known_level():
    frames = get_frames_per_cell(level=7, frames_per_cell={0: 48, 5: 23})

    assert frames == 23


# Testing the "frames2ms" function.


def test_frames2ms_converts_frames_to_milliseconds():
    milliseconds = frames2ms(frame_rate=60, frames=60)

    assert milliseconds == pytest.approx(1000.0)


# Testing the "gravity2ms" function.


def test_gravity2ms_converts_gravity_to_milliseconds_per_cell():
    milliseconds_per_cell = gravity2ms(frame_rate=60, gravity=0.5)

    assert milliseconds_per_cell == pytest.approx(100 / 3)
