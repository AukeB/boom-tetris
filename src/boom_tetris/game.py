"""Core game loop: input, gravity, DAS, scoring, and rendering."""

import math
import os

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
    """Single-player session: pieces, timers, DAS, score, and pygame loop."""

    def __init__(self, config: ConfigModelRuntime) -> None:
        """Wire renderer, board, pieces, and timing state from ``config``.

        Args:
            config: Fully updated ``ConfigModel`` (after YAML update).
        """
        # General
        self.config = config

        pg.init()

        # General
        self.renderer = Renderer(config=self.config)
        self.board = Board(config=self.config)

        # Colors
        self.window_background_color = config.WINDOW.COLOR.BACKGROUND
        self.board_background_color = config.BOARD.COLOR.BACKGROUND

        # Polyomino's.
        self.polyomino = Polyomino(
            self.config.POLYOMINO.SPAWN_POSITION[0],
            self.config.POLYOMINO.SPAWN_POSITION[1],
        )
        self.next_polyomino = Polyomino(
            self.config.POLYOMINO.SPAWN_POSITION_NEXT[0],
            self.config.POLYOMINO.SPAWN_POSITION_NEXT[1],
            previous_polyomino_index=self.polyomino.index,
        )

        # Related to DAS (Delayed Auto Shift).
        self.clock = pg.time.Clock()
        self.frame_rate = self.config.GENERAL.NTSC_FRAMERATE
        self.das_directions = self.config.DAS.DIRECTIONS

        self.key_pressed = {key: False for key in self.das_directions}
        self.hold_timer = {key: 0 for key in self.das_directions}

        self.soft_drop_speed = gravity2ms(
            self.frame_rate, self.config.GENERAL.SOFT_DROP_SPEED
        )
        self.das_delay = {
            direction: frames2ms(self.frame_rate, self.config.DAS.DAS_DELAY_NTSC)
            for direction in self.das_directions
        }

        self.auto_repeat_rate = {
            direction: frames2ms(self.frame_rate, self.config.DAS.AUTO_REPEAT_RATE_NTSC)
            for direction in self.das_directions
        }

        # Manual correction for soft drop speed.
        self.das_delay["DOWN"] = self.soft_drop_speed
        self.auto_repeat_rate["DOWN"] = self.soft_drop_speed

        # ARE (Entry/appearance delay after a piece locks).
        self.in_are = False
        self.are_timer = 0
        self.are_duration = 0

        # Related to lines cleared and level.
        self.level = self.config.GENERAL.START_LEVEL
        self.leveled_up = False
        self.line_threshold_first_level_advancement = compute_first_level_advancement(
            self.level
        )

        self.line_counter = 0
        self.last_drop_time = pg.time.get_ticks()

        # Related to scoring
        self.score = 0
        self.score_dict = self.initialize_scoring_dictionary()

        # Probably best to merge these two functions.
        frames_per_cell = get_frames_per_cell(
            self.level, self.config.GENERAL.NTSC_DROP_FRAMES
        )

        self.drop_interval = convert_drop_frames_to_time(
            framerate=self.config.GENERAL.NTSC_FRAMERATE,
            frames_per_cell=frames_per_cell,
        )

    def initialize_scoring_dictionary(self) -> dict[int, int]:
        """Build line-clear score multipliers for 1–4 rows at once.

        Returns:
            dict[int, int]: Map from cleared line count to base points before
                level scaling.
        """
        single_points = self.config.SCORE.SINGLE
        double_points = int(single_points * self.config.SCORE.DOUBLE_MULTIPLIER)
        triple_points = int(double_points * self.config.SCORE.TRIPLE_MULTIPLIER)
        tetris_points = int(triple_points * self.config.SCORE.TETRIS_MULTIPLIER)

        score_dict = {
            1: single_points,
            2: double_points,
            3: triple_points,
            4: tetris_points,
        }

        return score_dict

    def update_key_hold(self, direction: str, is_pressed: bool) -> None:
        """Track key state for DAS and reset the hold timer on change.

        Args:
            direction: One of the configured DAS direction names.
            is_pressed: True on key down, False on key up.
        """
        self.key_pressed[direction] = is_pressed
        self.hold_timer[direction] = 0

    def update_das(self, dt: int) -> None:
        """Advance delayed auto-shift timers and repeat moves when eligible.

        Args:
            dt: Milliseconds since the last tick for timer accumulation.
        """
        for direction in self.das_directions:
            if self.key_pressed[direction]:
                self.hold_timer[direction] += dt
                move_direction = getattr(self.config.DIRECTIONS, direction)

                if not self.board.collision(self.polyomino, move_direction):
                    if self.hold_timer[direction] > self.das_delay[direction]:
                        if direction in ["LEFT", "RIGHT"]:
                            self.polyomino.x += move_direction[0]
                        if direction == "DOWN":
                            self.polyomino.y += move_direction[1]

                        self.hold_timer[direction] = (
                            self.das_delay[direction] - self.auto_repeat_rate[direction]
                        )
                else:
                    if direction in ["LEFT", "RIGHT"]:
                        self.hold_timer[direction] = self.das_delay[direction] + 1
                    elif direction == "DOWN":
                        self.lock_polyomino()
                        self.update_key_hold(direction, is_pressed=True)
                        return
            else:
                self.hold_timer[direction] = 0

    def charge_das(self, dt: int) -> None:
        """Charge horizontal DAS while a key is held during ARE, without moving

        Mirrors NES behaviour: holding left/right through the entry delay lets
        the next piece auto-shift the instant it appears.

        Args:
            dt (int): Milliseconds since the last tick for timer accumulation.
        """
        for direction in self.das_directions:
            if direction == "DOWN":
                continue
            if self.key_pressed[direction]:
                self.hold_timer[direction] = min(
                    self.hold_timer[direction] + dt, self.das_delay[direction] + 1
                )
            else:
                self.hold_timer[direction] = 0

    def handle_controls(self, event: pg.event.Event) -> None:
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
                self.update_key_hold("LEFT", is_pressed=True)
            elif event.key == KEY.RIGHT:
                self.update_key_hold("RIGHT", is_pressed=True)
            elif event.key == KEY.DOWN:
                self.update_key_hold("DOWN", is_pressed=True)

            # No controllable piece exists during the entry delay.
            if self.in_are:
                return

            # Horizontal and vertical movement.
            if event.key == KEY.LEFT and not self.board.collision(
                self.polyomino, move_direction=self.config.DIRECTIONS.LEFT
            ):
                self.polyomino.x += self.config.DIRECTIONS.LEFT[0]

            if event.key == KEY.RIGHT and not self.board.collision(
                self.polyomino, move_direction=self.config.DIRECTIONS.RIGHT
            ):
                self.polyomino.x += self.config.DIRECTIONS.RIGHT[0]

            if event.key == KEY.DOWN:
                if not self.board.collision(
                    self.polyomino, move_direction=self.config.DIRECTIONS.DOWN
                ):
                    self.polyomino.y += self.config.DIRECTIONS.DOWN[1]
                else:
                    self.lock_polyomino()

            # Rotational movement.
            if event.key == KEY.ROTATE_CLOCKWISE and not self.board.collision(
                self.polyomino,
                rotate_direction=self.config.DIRECTIONS.ROTATE_CLOCKWISE,
            ):
                self.polyomino.rotate(self.config.DIRECTIONS.ROTATE_CLOCKWISE)

            if event.key == KEY.ROTATE_COUNTERCLOCKWISE and not self.board.collision(
                self.polyomino,
                rotate_direction=self.config.DIRECTIONS.ROTATE_COUNTERCLOCKWISE,
            ):
                self.polyomino.rotate(self.config.DIRECTIONS.ROTATE_COUNTERCLOCKWISE)

            # Optional hard-drop.
            if event.key == KEY.HARDDROP:
                while not self.board.collision(
                    self.polyomino, move_direction=self.config.DIRECTIONS.DOWN
                ):
                    self.polyomino.y += self.config.DIRECTIONS.DOWN[1]

                self.lock_polyomino()

        elif event.type == pg.KEYUP:
            if event.key == KEY.LEFT:
                self.update_key_hold("LEFT", is_pressed=False)
            elif event.key == KEY.RIGHT:
                self.update_key_hold("RIGHT", is_pressed=False)
            elif event.key == KEY.DOWN:
                self.update_key_hold("DOWN", is_pressed=False)

    def handle_events(self) -> bool:
        """Drain the event queue; return False when the user quits.

        Returns:
            bool: False if the window should close; True to keep running.
        """
        for event in pg.event.get():
            if (
                event.type == pg.QUIT
                or event.type == pg.KEYDOWN
                and event.key == pg.K_ESCAPE
            ):
                return False

            self.handle_controls(event)

        return True

    def update_lines_and_level(self, lines_cleared: int) -> None:
        """Update total lines and level using NTSC-style advancement rules.

        Args:
            lines_cleared: Rows removed in the most recent lock step.
        """
        if not self.leveled_up:
            if (
                self.line_counter + lines_cleared
                >= self.line_threshold_first_level_advancement
            ):
                self.level += 1
                self.leveled_up = True
        else:
            if (self.line_counter + lines_cleared) // 10 != self.line_counter // 10:
                self.level += 1

        self.line_counter += lines_cleared

    def update_score(self, level: int, lines_cleared: int) -> None:
        """Add points for a line clear scaled by current level.

        Args:
            level: Level index before applying the score increment.
            lines_cleared: Number of simultaneous rows cleared (1–4).
        """
        score_to_add = (level + 1) * self.score_dict[lines_cleared]
        self.score += score_to_add

    def compute_are_frames(self, lock_row: int) -> int:
        """Return the entry-delay length in frames for a given lock row.

        Higher placements (small ``lock_row``) get the full delay; placements
        nearer the floor get progressively shorter delays, down to the
        configured minimum.

        Args:
            lock_row (int): Bottom-most row occupied by the piece as it locked
                (0 = top).

        Returns:
            int: Entry-delay duration in frames.
        """
        steps = max(
            0,
            math.ceil(
                (lock_row - self.config.ARE.FIRST_THRESHOLD_ROW)
                / self.config.ARE.ROWS_PER_STEP
            ),
        )
        frames = (
            self.config.ARE.BASE_DELAY_FRAMES - self.config.ARE.FRAMES_PER_STEP * steps
        )

        return max(frames, self.config.ARE.MIN_DELAY_FRAMES)

    def lock_polyomino(self) -> None:
        """Lock the pactive piece, clear lines, update score/level, and start
        ARE.
        """
        # Bottom-most row of the piece sets the entry-delay length.
        lock_row = max(self.polyomino.y + block[1] for block in self.polyomino)

        # Place the polyomino on the board.
        self.board.place(self.polyomino)

        # Possible update line clear, level and drop speed.
        lines_cleared = self.board.clear_lines()

        if lines_cleared:
            self.update_score(level=self.level, lines_cleared=lines_cleared)
            self.update_lines_and_level(lines_cleared=lines_cleared)

        if self.level in self.config.GENERAL.NTSC_DROP_FRAMES:
            self.drop_interval = convert_drop_frames_to_time(
                framerate=self.config.GENERAL.NTSC_FRAMERATE,
                frames_per_cell=self.config.GENERAL.NTSC_DROP_FRAMES[self.level],
            )

        self.are_duration = frames2ms(
            self.frame_rate, self.compute_are_frames(lock_row)
        )
        self.in_are = True
        self.are_timer = 0

    def spawn_next_polyomino(self) -> None:
        """Activate the previewed piece and create a new preview piece."""
        self.next_polyomino.x, self.next_polyomino.y = (
            self.config.POLYOMINO.SPAWN_POSITION[0],
            self.config.POLYOMINO.SPAWN_POSITION[1],
        )
        self.polyomino = self.next_polyomino
        self.next_polyomino = Polyomino(
            self.config.POLYOMINO.SPAWN_POSITION_NEXT[0],
            self.config.POLYOMINO.SPAWN_POSITION_NEXT[1],
            previous_polyomino_index=self.polyomino.index,
        )

        self.last_drop_time = pg.time.get_ticks()

    def handle_timers(self) -> None:
        """Move the piece down on each drop tick unless soft-dropping."""
        current_time = pg.time.get_ticks()

        if not self.key_pressed["DOWN"]:
            if current_time - self.last_drop_time >= self.drop_interval:
                if not self.board.collision(
                    self.polyomino, move_direction=self.config.DIRECTIONS.DOWN
                ):
                    self.polyomino.y += self.config.DIRECTIONS.DOWN[1]
                else:
                    self.lock_polyomino()
                self.last_drop_time = current_time

    def update(self) -> bool:
        """Render one frame, run timers and DAS, then process pygame events.

        Returns:
            bool: False when ``handle_events`` reports quit; True otherwise.
        """
        with self.renderer:
            self.renderer.draw_board(board=self.board)

            if not self.in_are:
                self.renderer.draw_polyomino(
                    self.polyomino, self.board.cell_rect.copy()
                )

            self.renderer.draw_grid_lines(board=self.board)

            self.renderer.draw_rect(
                rect=self.board.hidden_rows_rect, color=self.window_background_color
            )

            # Line counter related.
            self.renderer.draw_rect(
                rect=self.board.line_counter_rect, color=self.board_background_color
            )
            self.renderer.draw_text(
                text=f"{self.config.FIELDS.LINE_COUNTER.LABEL} - {self.line_counter:03d}",
                rect=self.board.line_counter_rect,
            )

            # Score related.
            self.renderer.draw_rect(
                rect=self.board.score_rect, color=self.board_background_color
            )
            self.renderer.draw_label_and_value(
                label=self.config.FIELDS.SCORE.LABEL,
                value=f"{self.score:06d}",
                rect=self.board.score_rect,
            )

            # Next related.
            self.renderer.draw_rect(
                rect=self.board.next_rect, color=self.board_background_color
            )

            # Level related.
            self.renderer.draw_rect(
                rect=self.board.level_rect, color=self.board_background_color
            )
            self.renderer.draw_label_and_value(
                label=self.config.FIELDS.LEVEL.LABEL,
                value=str(self.level),
                rect=self.board.level_rect,
            )

            # Type related.
            self.renderer.draw_rect(
                rect=self.board.type_rect, color=self.board_background_color
            )
            self.renderer.draw_text(
                text=self.config.FIELDS.TYPE.LABEL, rect=self.board.type_rect
            )

            # Statistics related.
            self.renderer.draw_rect(
                rect=self.board.statistics_rect, color=self.board_background_color
            )
            self.renderer.draw_text(
                text=self.config.FIELDS.STATISTICS.LABEL,
                rect=self.board.statistics_rect,
            )

            self.renderer.draw_polyomino(
                self.next_polyomino, self.board.cell_rect.copy()
            )

        dt = self.clock.tick(self.frame_rate)

        if self.in_are:
            self.charge_das(dt)
            self.are_timer += dt
            if self.are_timer >= self.are_duration:
                self.in_are = False
                self.are_timer = 0
                self.spawn_next_polyomino()
        else:
            self.handle_timers()
            self.update_das(dt=dt)

        return self.handle_events()
