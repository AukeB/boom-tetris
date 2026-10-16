"""Tests for the game session in `game`."""

import pygame as pg
import pytest

from src.boom_tetris.configs.controls import SINGLE_PLAYER_CONTROLS as KEY
from src.boom_tetris.game import Game
from src.boom_tetris.polyomino.polyomino import Polyomino


@pytest.fixture
def game(runtime_config, fake_time):
    """Build a game on a fixed clock.

    Args:
        runtime_config (ConfigModelRuntime): The runtime configuration.
        fake_time (dict[str, int]): Controllable pygame clock.

    Returns:
        game (Game): A new game session.
    """
    game = Game(config=runtime_config)

    return game


def _key_event(event_type, key):
    """Build a pygame keyboard event.

    Args:
        event_type (int): `pg.KEYDOWN` or `pg.KEYUP`.
        key (int): The pygame key code.

    Returns:
        event (pg.event.Event): The keyboard event.
    """
    event = pg.event.Event(event_type, key=key)

    return event


def _place_piece_on_floor(game):
    """Move the active piece so its lowest block touches the bottom row.

    Args:
        game (Game): The session whose piece is moved.
    """
    lowest = max(block[1] for block in game._polyomino)
    game._polyomino.y = game._board.dimensions.rows - 1 - lowest


def _fill_bottom_rows(game, count):
    """Fill the bottom rows of the board so they are complete.

    Args:
        game (Game): The session whose board is filled.
        count (int): Number of bottom rows to fill.
    """
    for row in range(game._board.dimensions.rows - count, game._board.dimensions.rows):
        game._board.cells[row] = [1] * game._board.dimensions.cols


# Testing the "__init__" method of the "Game" class.


def test_init_sets_up_timers_and_scoring(game):
    assert set(game._key_pressed) == set(game._das_directions)
    assert game._das_delay["DOWN"] == game._soft_drop_speed
    assert set(game._score_dict) == {1, 2, 3, 4}
    assert game._drop_interval > 0
    assert game._in_are is False


# Testing the "_initialize_scoring_dictionary" method.


def test_initialize_scoring_dictionary_scales_base_points(game):
    score_dict = game._initialize_scoring_dictionary()

    assert score_dict == {1: 40, 2: 100, 3: 300, 4: 1200}


# Testing the "_update_key_hold" method.


def test_update_key_hold_tracks_the_press_and_resets_the_timer(game):
    game._hold_timer["LEFT"] = 50

    game._update_key_hold("LEFT", is_pressed=True)

    assert game._key_pressed["LEFT"] is True
    assert game._hold_timer["LEFT"] == 0


# Testing the "_compute_are_frames" method.


@pytest.mark.parametrize(
    ("lock_row", "expected"),
    [(0, 18), (19, 10), (30, 10)],
)
def test_compute_are_frames_shortens_for_low_locks(game, lock_row, expected):
    frames = game._compute_are_frames(lock_row)

    assert frames == expected


# Testing the "_update_score" method.


def test_update_score_adds_points_scaled_by_level(game):
    game._update_score(level=2, lines_cleared=2)

    assert game._score == 3 * 100


# Testing the "_update_lines_and_level" method.


def test_update_lines_and_level_levels_up_at_first_threshold(game):
    game._line_threshold_first_level_advancement = 5
    game._line_counter = 4
    game._level = 3

    game._update_lines_and_level(lines_cleared=2)

    assert game._level == 4
    assert game._leveled_up is True
    assert game._line_counter == 6


def test_update_lines_and_level_waits_below_the_threshold(game):
    game._line_threshold_first_level_advancement = 50
    game._line_counter = 0
    game._level = 3

    game._update_lines_and_level(lines_cleared=1)

    assert game._level == 3
    assert game._leveled_up is False


def test_update_lines_and_level_levels_up_every_ten_lines_after_first(game):
    game._leveled_up = True
    game._line_counter = 9
    game._level = 3

    game._update_lines_and_level(lines_cleared=1)

    assert game._level == 4


def test_update_lines_and_level_keeps_level_within_a_decade(game):
    game._leveled_up = True
    game._line_counter = 2
    game._level = 3

    game._update_lines_and_level(lines_cleared=1)

    assert game._level == 3


# Testing the "_lock_polyomino" method.


def test_lock_polyomino_places_the_piece_and_starts_are(game):
    _place_piece_on_floor(game)

    game._lock_polyomino()

    assert game._in_are is True
    assert game._are_timer == 0
    assert game._are_duration > 0


def test_lock_polyomino_scores_cleared_lines(game):
    _fill_bottom_rows(game, count=1)
    game._polyomino.y = game._board.dimensions.rows - 2
    game._polyomino._blocks = [(0, 0), (1, 0), (2, 0), (3, 0)]

    game._lock_polyomino()

    assert game._line_counter == 1
    assert game._score > 0


def test_lock_polyomino_updates_drop_speed_for_known_levels(game):
    game._level = 19
    _place_piece_on_floor(game)
    framerate = game._config.GENERAL.NTSC_FRAMERATE

    game._lock_polyomino()

    assert game._drop_interval == pytest.approx(2 / framerate * 1000)


def test_lock_polyomino_sets_game_over_when_locked_in_hidden_rows(game):
    hidden_rows = game._config.BOARD.DIMENSIONS.ROWS_HIDDEN
    lowest = max(block[1] for block in game._polyomino)
    game._polyomino.y = hidden_rows - 1 - lowest

    game._lock_polyomino()

    assert game._game_over is True


def test_lock_polyomino_leaves_game_over_unset_when_locked_in_visible_rows(game):
    hidden_rows = game._config.BOARD.DIMENSIONS.ROWS_HIDDEN
    lowest = max(block[1] for block in game._polyomino)
    game._polyomino.y = hidden_rows - lowest

    game._lock_polyomino()

    assert game._game_over is False


# Testing the "_update_das" method.


def test_update_das_moves_horizontally_after_the_delay(game):
    game._key_pressed["LEFT"] = True
    game._hold_timer["LEFT"] = game._das_delay["LEFT"]
    game._polyomino.x = 5
    x_before = game._polyomino.x

    game._update_das(dt=20)

    assert game._polyomino.x == x_before - 1


def test_update_das_waits_before_the_delay(game):
    game._key_pressed["RIGHT"] = True
    game._hold_timer["RIGHT"] = 0
    game._polyomino.x = 5

    game._update_das(dt=1)

    assert game._polyomino.x == 5


def test_update_das_stops_at_the_wall(game):
    game._key_pressed["LEFT"] = True
    game._hold_timer["LEFT"] = 0
    game._polyomino.x = 0

    game._update_das(dt=1)

    assert game._hold_timer["LEFT"] == game._das_delay["LEFT"] + 1


def test_update_das_moves_down_after_the_delay(game):
    game._key_pressed["DOWN"] = True
    game._hold_timer["DOWN"] = game._das_delay["DOWN"]
    game._polyomino.y = 5
    game._polyomino.x = 4

    game._update_das(dt=20)

    assert game._polyomino.y == 6


def test_update_das_locks_when_soft_drop_hits_the_floor(game):
    game._key_pressed["DOWN"] = True
    game._hold_timer["DOWN"] = 0
    _place_piece_on_floor(game)

    game._update_das(dt=1)

    assert game._in_are is True
    assert game._key_pressed["DOWN"] is True


def test_update_das_ignores_directions_without_special_handling(game, monkeypatch):
    game._das_directions = ["UP"]
    game._key_pressed["UP"] = True
    game._hold_timer["UP"] = 0
    monkeypatch.setattr(game._board, "collision", lambda *args, **kwargs: True)

    game._update_das(dt=1)

    assert game._hold_timer["UP"] == 1


def test_update_das_resets_timers_of_released_keys(game):
    game._key_pressed["LEFT"] = False
    game._hold_timer["LEFT"] = 40

    game._update_das(dt=1)

    assert game._hold_timer["LEFT"] == 0


# Testing the "_charge_das" method.


def test_charge_das_builds_up_held_horizontal_keys(game):
    game._key_pressed["LEFT"] = True
    game._hold_timer["LEFT"] = 0

    game._charge_das(dt=5)

    assert game._hold_timer["LEFT"] == 5


def test_charge_das_resets_released_keys_and_skips_down(game):
    game._key_pressed["LEFT"] = False
    game._hold_timer["LEFT"] = 9
    game._hold_timer["DOWN"] = 9

    game._charge_das(dt=5)

    assert game._hold_timer["LEFT"] == 0
    assert game._hold_timer["DOWN"] == 9


# Testing the "_spawn_next_polyomino" method.


def test_spawn_next_polyomino_activates_the_preview(game):
    preview = game._next_polyomino

    game._spawn_next_polyomino()

    assert game._polyomino is preview
    assert game._polyomino.x == game._config.POLYOMINO.SPAWN_POSITION[0]
    assert isinstance(game._next_polyomino, Polyomino)
    assert game._next_polyomino is not preview


def test_spawn_next_polyomino_sets_game_over_when_spawn_is_blocked(game):
    _fill_bottom_rows(game, game._board.dimensions.rows)

    game._spawn_next_polyomino()

    assert game._game_over is True


def test_spawn_next_polyomino_leaves_game_over_unset_when_spawn_is_free(game):
    game._spawn_next_polyomino()

    assert game._game_over is False


# Testing the "_handle_timers" method.


def test_handle_timers_drops_the_piece_when_the_tick_elapses(game, fake_time):
    fake_time["now"] = game._drop_interval + 1
    game._last_drop_time = 0
    y_before = game._polyomino.y

    game._handle_timers()

    assert game._polyomino.y == y_before + 1
    assert game._last_drop_time == fake_time["now"]


def test_handle_timers_waits_before_the_tick(game, fake_time):
    fake_time["now"] = 1
    game._last_drop_time = 0
    y_before = game._polyomino.y

    game._handle_timers()

    assert game._polyomino.y == y_before


def test_handle_timers_locks_when_the_piece_cannot_fall(game, fake_time):
    fake_time["now"] = game._drop_interval + 1
    game._last_drop_time = 0
    _place_piece_on_floor(game)

    game._handle_timers()

    assert game._in_are is True


def test_handle_timers_pauses_while_soft_dropping(game, fake_time):
    fake_time["now"] = game._drop_interval + 1
    game._last_drop_time = 0
    game._key_pressed["DOWN"] = True
    y_before = game._polyomino.y

    game._handle_timers()

    assert game._polyomino.y == y_before


# Testing the "_handle_controls" method.


def test_handle_controls_moves_left_when_free(game):
    game._polyomino.x = 5

    event = _key_event(pg.KEYDOWN, KEY.LEFT)

    game._handle_controls(event)

    assert game._polyomino.x == 4
    assert game._key_pressed["LEFT"] is True


def test_handle_controls_does_not_move_into_a_wall(game):
    game._polyomino.x = 0

    event = _key_event(pg.KEYDOWN, KEY.LEFT)

    game._handle_controls(event)

    assert game._polyomino.x == 0


def test_handle_controls_moves_right_when_free(game):
    game._polyomino.x = 5

    event = _key_event(pg.KEYDOWN, KEY.RIGHT)

    game._handle_controls(event)

    assert game._polyomino.x == 6


def test_handle_controls_ignores_piece_actions_after_game_over(game):
    game._game_over = True
    game._polyomino.x = 5

    event = _key_event(pg.KEYDOWN, KEY.LEFT)

    game._handle_controls(event)

    assert game._polyomino.x == 5


def test_handle_controls_ignores_piece_actions_during_are(game):
    game._in_are = True
    game._polyomino.x = 5

    event = _key_event(pg.KEYDOWN, KEY.LEFT)

    game._handle_controls(event)

    assert game._polyomino.x == 5
    assert game._key_pressed["LEFT"] is True


def test_handle_controls_soft_drop_moves_down_when_free(game):
    y_before = game._polyomino.y

    event = _key_event(pg.KEYDOWN, KEY.DOWN)

    game._handle_controls(event)

    assert game._polyomino.y == y_before + 1


def test_handle_controls_soft_drop_locks_on_the_floor(game):
    _place_piece_on_floor(game)

    event = _key_event(pg.KEYDOWN, KEY.DOWN)

    game._handle_controls(event)

    assert game._in_are is True


def test_handle_controls_rotates_clockwise_when_free(game, monkeypatch):
    rotations = []
    monkeypatch.setattr(game._polyomino, "rotate", rotations.append)

    event = _key_event(pg.KEYDOWN, KEY.ROTATE_CLOCKWISE)

    game._handle_controls(event)

    assert rotations == [game._config.DIRECTIONS.ROTATE_CLOCKWISE]


def test_handle_controls_rotates_counter_clockwise_when_free(game, monkeypatch):
    rotations = []
    monkeypatch.setattr(game._polyomino, "rotate", rotations.append)

    event = _key_event(pg.KEYDOWN, KEY.ROTATE_COUNTERCLOCKWISE)

    game._handle_controls(event)

    assert rotations == [game._config.DIRECTIONS.ROTATE_COUNTERCLOCKWISE]


def test_handle_controls_blocked_rotation_does_nothing(game, monkeypatch):
    rotations = []
    monkeypatch.setattr(game._polyomino, "rotate", rotations.append)
    monkeypatch.setattr(game._board, "collision", lambda *args, **kwargs: True)

    event = _key_event(pg.KEYDOWN, KEY.ROTATE_CLOCKWISE)

    game._handle_controls(event)

    assert rotations == []


def test_handle_controls_hard_drop_falls_then_locks(game):
    event = _key_event(pg.KEYDOWN, KEY.HARDDROP)
    game._handle_controls(event)

    assert game._in_are is True
    row_sums = [sum(row) for row in game._board.cells]

    assert sum(row_sums) > 0


def test_handle_controls_releasing_a_held_key_clears_its_state(game):
    game._key_pressed["RIGHT"] = True

    event = _key_event(pg.KEYUP, KEY.RIGHT)

    game._handle_controls(event)

    assert game._key_pressed["RIGHT"] is False


@pytest.mark.parametrize(("key", "direction"), [(KEY.LEFT, "LEFT"), (KEY.DOWN, "DOWN")])
def test_handle_controls_releasing_left_and_down_clears_their_state(
    game, key, direction
):
    game._key_pressed[direction] = True

    event = _key_event(pg.KEYUP, key)

    game._handle_controls(event)

    assert game._key_pressed[direction] is False


def test_handle_controls_ignores_non_keyboard_events(game):
    x_before = game._polyomino.x

    event = pg.event.Event(pg.MOUSEMOTION)

    game._handle_controls(event)

    assert game._polyomino.x == x_before


def test_handle_controls_releasing_other_keys_has_no_effect(game):
    event = _key_event(pg.KEYUP, pg.K_z)
    game._handle_controls(event)

    states = game._key_pressed.values()

    assert all(state is False for state in states)


def test_handle_controls_ignores_unbound_key_presses(game):
    x_before = game._polyomino.x

    event = _key_event(pg.KEYDOWN, pg.K_z)

    game._handle_controls(event)

    assert game._polyomino.x == x_before


# Testing the "_handle_events" method.


def test_handle_events_stops_on_quit(game, monkeypatch):
    quit_event = pg.event.Event(pg.QUIT)
    monkeypatch.setattr(pg.event, "get", lambda: [quit_event])

    assert game._handle_events() is False


def test_handle_events_stops_on_escape(game, monkeypatch):
    escape_event = _key_event(pg.KEYDOWN, pg.K_ESCAPE)
    monkeypatch.setattr(pg.event, "get", lambda: [escape_event])

    assert game._handle_events() is False


def test_handle_events_stops_on_any_key_after_game_over(game, monkeypatch):
    game._game_over = True
    key_event = _key_event(pg.KEYDOWN, KEY.LEFT)
    monkeypatch.setattr(pg.event, "get", lambda: [key_event])

    assert game._handle_events() is False


def test_handle_events_forwards_other_events_to_the_controls(game, monkeypatch):
    forwarded = []
    monkeypatch.setattr(game, "_handle_controls", forwarded.append)
    event = _key_event(pg.KEYDOWN, KEY.LEFT)
    monkeypatch.setattr(pg.event, "get", lambda: [event])

    assert game._handle_events() is True
    assert forwarded == [event]


# Testing the "update" method.


def test_update_runs_a_frame_and_keeps_running(game, monkeypatch):
    monkeypatch.setattr(pg.event, "get", lambda: [])

    assert game.update() is True


def test_update_stops_when_the_user_quits(game, monkeypatch):
    quit_event = pg.event.Event(pg.QUIT)
    monkeypatch.setattr(pg.event, "get", lambda: [quit_event])

    assert game.update() is False


def test_update_hides_the_piece_during_are(game, monkeypatch):
    monkeypatch.setattr(pg.event, "get", lambda: [])
    game._in_are = True
    game._are_duration = 10_000

    assert game.update() is True
    assert game._are_timer == 16


def test_update_freezes_the_board_after_game_over(game, monkeypatch):
    monkeypatch.setattr(pg.event, "get", lambda: [])
    preview = game._next_polyomino
    game._in_are = True
    game._are_duration = 0
    game._game_over = True
    y_before = game._polyomino.y

    assert game.update() is True
    assert game._polyomino.y == y_before
    assert game._polyomino is not preview


def test_update_spawns_the_next_piece_when_are_ends(game, monkeypatch):
    monkeypatch.setattr(pg.event, "get", lambda: [])
    preview = game._next_polyomino
    game._in_are = True
    game._are_duration = 0

    game.update()

    assert game._in_are is False
    assert game._polyomino is preview


def test_update_runs_timers_and_das_outside_are(game, monkeypatch):
    monkeypatch.setattr(pg.event, "get", lambda: [])
    calls = []
    monkeypatch.setattr(game, "_handle_timers", lambda: calls.append("timers"))
    monkeypatch.setattr(game, "_update_das", lambda dt: calls.append(("das", dt)))

    game.update()

    assert calls == ["timers", ("das", 16)]
