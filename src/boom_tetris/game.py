"""Core game loop: input, gravity, DAS, scoring, and rendering."""

import math

import pygame as pg

from src.boom_tetris.board import Board
from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.configs.controls import SINGLE_PLAYER_CONTROLS as KEY
from src.boom_tetris.polyomino.polyomino import Polyomino
from src.boom_tetris.renderer import Renderer
from src.boom_tetris.utils.utils_game import (
    compute_first_level_advancement,
    convert_drop_frames_to_time,
    frames2ms,
    get_frames_per_cell,
    gravity2ms,
)


class Game:
    """Single-player session: pieces, timers, DAS, score, and pygame loop.

    Attributes:
        _config (ConfigModelRuntime): The runtime configuration of the session.
        _renderer (Renderer): Draws the board and the side fields.
        _board (Board): The playfield the pieces fall into.
        _window_background_color (list[int]): Color the window is cleared to.
        _board_background_color (list[int]): Color of the field backgrounds.
        _polyomino (Polyomino): The piece currently under player control.
        _next_polyomino (Polyomino): The piece previewed in the next field.
        _clock (pg.time.Clock): Clock that limits the loop to the frame rate.
        _frame_rate (float): Frame rate of the game in Hz.
        _das_directions (list[str]): Names of the directions that use DAS.
        _key_pressed (dict[str, bool]): Whether each DAS direction is held.
        _hold_timer (dict[str, float]): Time each DAS direction has been held.
        _soft_drop_speed (float): Milliseconds per cell while soft dropping.
        _das_delay (dict[str, float]): Milliseconds before auto-repeat starts.
        _auto_repeat_rate (dict[str, float]): Milliseconds between repeats.
        _in_are (bool): Whether the entry delay after a lock is running.
        _are_timer (float): Milliseconds spent in the entry delay so far.
        _are_duration (float): Length of the entry delay in milliseconds.
        _level (int): Current level.
        _leveled_up (bool): Whether the first level advancement has happened.
        _line_threshold_first_level_advancement (int): Lines needed for the
            first level-up.
        _line_counter (int): Total number of lines cleared.
        _last_drop_time (int): Pygame ticks at the last automatic drop.
        _score (int): Current score.
        _score_dict (dict[int, int]): Base points for 1 to 4 cleared lines.
        _drop_interval (float): Milliseconds between automatic drops.

    Example:
        >>> game = Game(config=config_runtime)
        >>> while game.update():
        ...     pass
    """

    def __init__(self, config: ConfigModelRuntime) -> None:
        """Wire renderer, board, pieces, and timing state from ``config``.

        Args:
            config: Fully updated ``ConfigModel`` (after YAML update).
        """

        # General
        self._config = config

        pg.init()

        # General
        self._renderer = Renderer(config=self._config)
        self._board = Board(config=self._config)

        # Colors
        self._window_background_color = config.WINDOW.COLOR.BACKGROUND
        self._board_background_color = config.BOARD.COLOR.BACKGROUND

        # Polyomino's.
        self._polyomino = Polyomino(
            self._config.POLYOMINO.SPAWN_POSITION[0],
            self._config.POLYOMINO.SPAWN_POSITION[1],
        )

        self._next_polyomino = Polyomino(
            self._config.POLYOMINO.SPAWN_POSITION_NEXT[0],
            self._config.POLYOMINO.SPAWN_POSITION_NEXT[1],
            previous_polyomino_index=self._polyomino.index,
        )

        # Related to DAS (Delayed Auto Shift).
        self._clock = pg.time.Clock()
        self._frame_rate = self._config.GENERAL.NTSC_FRAMERATE
        self._das_directions = self._config.DAS.DIRECTIONS

        self._key_pressed = {key: False for key in self._das_directions}
        self._hold_timer = {key: 0.0 for key in self._das_directions}

        self._soft_drop_speed = gravity2ms(
            self._frame_rate, self._config.GENERAL.SOFT_DROP_SPEED
        )

        das_delay_frames = self._config.DAS.DAS_DELAY_NTSC

        self._das_delay = {
            direction: frames2ms(self._frame_rate, das_delay_frames)
            for direction in self._das_directions
        }

        auto_repeat_frames = self._config.DAS.AUTO_REPEAT_RATE_NTSC

        self._auto_repeat_rate = {
            direction: frames2ms(self._frame_rate, auto_repeat_frames)
            for direction in self._das_directions
        }

        # Manual correction for soft drop speed.
        self._das_delay["DOWN"] = self._soft_drop_speed
        self._auto_repeat_rate["DOWN"] = self._soft_drop_speed

        # ARE (Entry/appearance delay after a piece locks).
        self._in_are = False
        self._are_timer = 0
        self._are_duration = 0

        # Related to lines cleared and level.
        self._level = self._config.GENERAL.START_LEVEL
        self._leveled_up = False

        self._line_threshold_first_level_advancement = compute_first_level_advancement(
            self._level
        )

        self._line_counter = 0
        self._last_drop_time = pg.time.get_ticks()

        # Related to scoring
        self._score = 0
        self._score_dict = self._initialize_scoring_dictionary()

        # Probably best to merge these two functions.
        frames_per_cell = get_frames_per_cell(
            self._level, self._config.GENERAL.NTSC_DROP_FRAMES
        )

        self._drop_interval = convert_drop_frames_to_time(
            framerate=self._config.GENERAL.NTSC_FRAMERATE,
            frames_per_cell=frames_per_cell,
        )

    def _initialize_scoring_dictionary(self) -> dict[int, int]:
        """Build line-clear score multipliers for 1–4 rows at once.

        Returns:
            score_dict (dict[int, int]): Map from cleared line count to base
                points before level scaling.
        """

        single_points = self._config.SCORE.SINGLE
        double_points = int(single_points * self._config.SCORE.DOUBLE_MULTIPLIER)
        triple_points = int(double_points * self._config.SCORE.TRIPLE_MULTIPLIER)
        tetris_points = int(triple_points * self._config.SCORE.TETRIS_MULTIPLIER)

        score_dict = {
            1: single_points,
            2: double_points,
            3: triple_points,
            4: tetris_points,
        }

        return score_dict

    def _update_key_hold(self, direction: str, is_pressed: bool) -> None:
        """Track key state for DAS and reset the hold timer on change.

        Args:
            direction: One of the configured DAS direction names.
            is_pressed: True on key down, False on key up.
        """

        self._key_pressed[direction] = is_pressed
        self._hold_timer[direction] = 0

    def _compute_are_frames(self, lock_row: int) -> int:
        """Return the entry-delay length in frames for a given lock row.

        Higher placements (small ``lock_row``) get the full delay; placements
        nearer the floor get progressively shorter delays, down to the
        configured minimum.

        Args:
            lock_row (int): Bottom-most row occupied by the piece as it locked
                (0 = top).

        Returns:
            clamped_frames (int): Entry-delay duration in frames.
        """

        rows_below_threshold = lock_row - self._config.ARE.FIRST_THRESHOLD_ROW
        steps_raw = rows_below_threshold / self._config.ARE.ROWS_PER_STEP
        rounded_steps = math.ceil(steps_raw)
        steps = max(0, rounded_steps)

        frames = (
            self._config.ARE.BASE_DELAY_FRAMES
            - self._config.ARE.FRAMES_PER_STEP * steps
        )

        clamped_frames = max(frames, self._config.ARE.MIN_DELAY_FRAMES)

        return clamped_frames

    def _update_score(self, level: int, lines_cleared: int) -> None:
        """Add points for a line clear scaled by current level.

        Args:
            level: Level index before applying the score increment.
            lines_cleared: Number of simultaneous rows cleared (1–4).
        """

        score_to_add = (level + 1) * self._score_dict[lines_cleared]
        self._score += score_to_add

    def _update_lines_and_level(self, lines_cleared: int) -> None:
        """Update total lines and level using NTSC-style advancement rules.

        Args:
            lines_cleared: Rows removed in the most recent lock step.
        """

        if not self._leveled_up:
            if (
                self._line_counter + lines_cleared
                >= self._line_threshold_first_level_advancement
            ):
                self._level += 1
                self._leveled_up = True
        else:
            if (self._line_counter + lines_cleared) // 10 != self._line_counter // 10:
                self._level += 1

        self._line_counter += lines_cleared

    def _lock_polyomino(self) -> None:
        """Lock the active piece, clear lines, update score/level, and start
        ARE.
        """

        # Bottom-most row of the piece sets the entry-delay length.
        lock_row = max(self._polyomino.y + block[1] for block in self._polyomino)

        # Place the polyomino on the board.
        self._board.place(self._polyomino)

        # Possible update line clear, level and drop speed.
        lines_cleared = self._board.clear_lines()

        if lines_cleared:
            self._update_score(level=self._level, lines_cleared=lines_cleared)
            self._update_lines_and_level(lines_cleared=lines_cleared)

        if self._level in self._config.GENERAL.NTSC_DROP_FRAMES:
            frames_per_cell = self._config.GENERAL.NTSC_DROP_FRAMES[self._level]

            self._drop_interval = convert_drop_frames_to_time(
                framerate=self._config.GENERAL.NTSC_FRAMERATE,
                frames_per_cell=frames_per_cell,
            )

        entry_delay_frames = self._compute_are_frames(lock_row)
        self._are_duration = frames2ms(self._frame_rate, entry_delay_frames)
        self._in_are = True
        self._are_timer = 0

    def _update_das(self, dt: int) -> None:
        """Advance delayed auto-shift timers and repeat moves when eligible.

        Args:
            dt: Milliseconds since the last tick for timer accumulation.
        """

        for direction in self._das_directions:
            if self._key_pressed[direction]:
                self._hold_timer[direction] += dt
                move_direction = getattr(self._config.DIRECTIONS, direction)

                if not self._board.collision(self._polyomino, move_direction):
                    if self._hold_timer[direction] > self._das_delay[direction]:
                        if direction in ["LEFT", "RIGHT"]:
                            self._polyomino.x += move_direction[0]

                        if direction == "DOWN":
                            self._polyomino.y += move_direction[1]

                        repeat_timer = (
                            self._das_delay[direction]
                            - self._auto_repeat_rate[direction]
                        )

                        self._hold_timer[direction] = repeat_timer
                else:
                    if direction in ["LEFT", "RIGHT"]:
                        self._hold_timer[direction] = self._das_delay[direction] + 1
                    elif direction == "DOWN":
                        self._lock_polyomino()
                        self._update_key_hold(direction, is_pressed=True)

                        return
            else:
                self._hold_timer[direction] = 0

    def _charge_das(self, dt: int) -> None:
        """Charge horizontal DAS while a key is held during ARE, without moving

        Mirrors NES behaviour: holding left/right through the entry delay lets
        the next piece auto-shift the instant it appears.

        Args:
            dt (int): Milliseconds since the last tick for timer accumulation.
        """

        for direction in self._das_directions:
            if direction == "DOWN":
                continue

            if self._key_pressed[direction]:
                charged_time = self._hold_timer[direction] + dt
                capped_time = self._das_delay[direction] + 1
                self._hold_timer[direction] = min(charged_time, capped_time)
            else:
                self._hold_timer[direction] = 0

    def _spawn_next_polyomino(self) -> None:
        """Activate the previewed piece and create a new preview piece."""
        spawn_x = self._config.POLYOMINO.SPAWN_POSITION[0]
        spawn_y = self._config.POLYOMINO.SPAWN_POSITION[1]
        self._next_polyomino.x, self._next_polyomino.y = (spawn_x, spawn_y)
        self._polyomino = self._next_polyomino

        next_x = self._config.POLYOMINO.SPAWN_POSITION_NEXT[0]
        next_y = self._config.POLYOMINO.SPAWN_POSITION_NEXT[1]

        self._next_polyomino = Polyomino(
            next_x,
            next_y,
            previous_polyomino_index=self._polyomino.index,
        )

        self._last_drop_time = pg.time.get_ticks()

    def _handle_timers(self) -> None:
        """Move the piece down on each drop tick unless soft-dropping."""
        current_time = pg.time.get_ticks()

        if not self._key_pressed["DOWN"]:
            if current_time - self._last_drop_time >= self._drop_interval:
                if not self._board.collision(
                    self._polyomino, move_direction=self._config.DIRECTIONS.DOWN
                ):
                    self._polyomino.y += self._config.DIRECTIONS.DOWN[1]
                else:
                    self._lock_polyomino()

                self._last_drop_time = current_time

    def _handle_controls(self, event: pg.event.Event) -> None:
        """React to one pygame input event (move, rotate, hard drop).

        Key state is always tracked so DAS keeps charging during ARE; piece
        actions only apply once the next piece has appeared.

        Args:
            event (pg.event.Event): A keyboard or other pygame event from the
                queue.
        """

        if event.type == pg.KEYDOWN:
            # Always track held movement keys so DAS charges, even during ARE.
            if event.key == KEY.LEFT:
                self._update_key_hold("LEFT", is_pressed=True)
            elif event.key == KEY.RIGHT:
                self._update_key_hold("RIGHT", is_pressed=True)
            elif event.key == KEY.DOWN:
                self._update_key_hold("DOWN", is_pressed=True)

            # No controllable piece exists during the entry delay.
            if self._in_are:
                return

            # Horizontal and vertical movement.
            left_move = self._config.DIRECTIONS.LEFT

            if event.key == KEY.LEFT and not self._board.collision(
                self._polyomino, move_direction=left_move
            ):
                self._polyomino.x += left_move[0]

            right_move = self._config.DIRECTIONS.RIGHT

            if event.key == KEY.RIGHT and not self._board.collision(
                self._polyomino, move_direction=right_move
            ):
                self._polyomino.x += right_move[0]

            down_move = self._config.DIRECTIONS.DOWN

            if event.key == KEY.DOWN:
                if not self._board.collision(self._polyomino, move_direction=down_move):
                    self._polyomino.y += down_move[1]
                else:
                    self._lock_polyomino()

            # Rotational movement.
            clockwise = self._config.DIRECTIONS.ROTATE_CLOCKWISE

            if event.key == KEY.ROTATE_CLOCKWISE and not self._board.collision(
                self._polyomino,
                rotate_direction=clockwise,
            ):
                self._polyomino.rotate(clockwise)

            counterclockwise = self._config.DIRECTIONS.ROTATE_COUNTERCLOCKWISE

            if event.key == KEY.ROTATE_COUNTERCLOCKWISE and not self._board.collision(
                self._polyomino,
                rotate_direction=counterclockwise,
            ):
                self._polyomino.rotate(counterclockwise)

            # Optional hard-drop.
            if event.key == KEY.HARDDROP:
                while not self._board.collision(
                    self._polyomino, move_direction=down_move
                ):
                    self._polyomino.y += down_move[1]

                self._lock_polyomino()
        elif event.type == pg.KEYUP:
            if event.key == KEY.LEFT:
                self._update_key_hold("LEFT", is_pressed=False)
            elif event.key == KEY.RIGHT:
                self._update_key_hold("RIGHT", is_pressed=False)
            elif event.key == KEY.DOWN:
                self._update_key_hold("DOWN", is_pressed=False)

    def _handle_events(self) -> bool:
        """Drain the event queue; return False when the user quits.

        Returns:
            keep_running (bool): False if the window should close; True to keep
                running.
        """

        for event in pg.event.get():
            if (
                event.type == pg.QUIT
                or event.type == pg.KEYDOWN
                and event.key == pg.K_ESCAPE
            ):
                return False

            self._handle_controls(event)

        return True

    def update(self) -> bool:
        """Render one frame, run timers and DAS, then process pygame events.

        Returns:
            keep_running (bool): False when ``_handle_events`` reports quit;
                True otherwise.
        """

        with self._renderer:
            self._renderer.draw_board(board=self._board)

            if not self._in_are:
                block_rect = self._board.cell_rect.copy()
                self._renderer.draw_polyomino(self._polyomino, block_rect)

            self._renderer.draw_grid_lines(board=self._board)

            self._renderer.draw_rect(
                rect=self._board.hidden_rows_rect, color=self._window_background_color
            )

            # Line counter related.
            self._renderer.draw_rect(
                rect=self._board.line_counter_rect, color=self._board_background_color
            )

            line_counter_text = (
                f"{self._config.FIELDS.LINE_COUNTER.LABEL} - {self._line_counter:03d}"
            )

            self._renderer.draw_text(
                text=line_counter_text,
                rect=self._board.line_counter_rect,
            )

            # Score related.
            self._renderer.draw_rect(
                rect=self._board.score_rect, color=self._board_background_color
            )

            score_text = f"{self._score:06d}"

            self._renderer.draw_label_and_value(
                label=self._config.FIELDS.SCORE.LABEL,
                value=score_text,
                rect=self._board.score_rect,
            )

            # Next related.
            self._renderer.draw_rect(
                rect=self._board.next_rect, color=self._board_background_color
            )

            # Level related.
            self._renderer.draw_rect(
                rect=self._board.level_rect, color=self._board_background_color
            )

            level_text = str(self._level)

            self._renderer.draw_label_and_value(
                label=self._config.FIELDS.LEVEL.LABEL,
                value=level_text,
                rect=self._board.level_rect,
            )

            # Type related.
            self._renderer.draw_rect(
                rect=self._board.type_rect, color=self._board_background_color
            )

            self._renderer.draw_text(
                text=self._config.FIELDS.TYPE.LABEL, rect=self._board.type_rect
            )

            # Statistics related.
            self._renderer.draw_rect(
                rect=self._board.statistics_rect, color=self._board_background_color
            )

            self._renderer.draw_text(
                text=self._config.FIELDS.STATISTICS.LABEL,
                rect=self._board.statistics_rect,
            )

            next_block_rect = self._board.cell_rect.copy()
            self._renderer.draw_polyomino(self._next_polyomino, next_block_rect)

        dt = self._clock.tick(self._frame_rate)

        if self._in_are:
            self._charge_das(dt)
            self._are_timer += dt

            if self._are_timer >= self._are_duration:
                self._in_are = False
                self._are_timer = 0
                self._spawn_next_polyomino()
        else:
            self._handle_timers()
            self._update_das(dt=dt)

        keep_running = self._handle_events()

        return keep_running
