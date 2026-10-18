"""Tests for the drawing helpers in `renderer`."""

import pygame as pg
import pytest

from boom_tetris import renderer as renderer_module
from boom_tetris.board import Board
from boom_tetris.polyomino.polyomino import Polyomino
from boom_tetris.renderer import Renderer


@pytest.fixture
def renderer(runtime_config, monkeypatch):
    """Open a headless window for drawing tests.

    Args:
        runtime_config (ConfigModelRuntime): The runtime configuration.
        monkeypatch: Pytest fixture used to fix the window size.

    Returns:
        renderer (Renderer): A renderer on a dummy display.
    """
    monkeypatch.setattr(
        renderer_module,
        "get_window_size_from_screen_resolution",
        lambda: (1280, 720),
    )

    renderer = Renderer(config=runtime_config)

    return renderer


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


# Testing the "__init__" method of the "Renderer" class.


def test_init_opens_a_window_of_the_configured_size(renderer, runtime_config):
    assert renderer._window_width == renderer._surface.get_width()
    assert renderer._window_height == renderer._surface.get_height()
    assert renderer._background_color == runtime_config.WINDOW.COLOR.BACKGROUND


# Testing the "__enter__" and "__exit__" methods.


def test_enter_clears_the_frame_to_the_background(renderer, runtime_config):
    renderer._surface.fill((1, 2, 3))

    renderer.__enter__()

    assert renderer._surface.get_at((0, 0))[:3] == tuple(
        runtime_config.WINDOW.COLOR.BACKGROUND
    )


def test_exit_flips_the_display(renderer, monkeypatch):
    calls = []
    monkeypatch.setattr(pg.display, "update", lambda: calls.append("update"))

    renderer.__exit__(None, None, None)

    assert calls == ["update"]


# Testing the "draw_board" method.


def test_draw_board_fills_occupied_cells(renderer, board, runtime_config):
    board.cells[21][0] = 1

    renderer.draw_board(board=board)

    cell_x = board.rect.x + board.cell_rect.width * 0 + 2
    cell_y = board.rect.y + board.cell_rect.height * 21 + 2
    assert renderer._surface.get_at((cell_x, cell_y))[:3] == tuple(
        runtime_config.POLYOMINO.COLOR
    )


# Testing the "draw_polyomino" method.


def test_draw_polyomino_draws_each_block(renderer, board, monkeypatch):
    drawn = []
    monkeypatch.setattr(pg.draw, "rect", lambda surface, color, rect: drawn.append(rect))
    piece = Polyomino(x=0, y=0)
    piece._blocks = [(0, 0), (1, 0)]

    block_rect = board.cell_rect.copy()

    renderer.draw_polyomino(piece, block_rect)

    assert len(drawn) == 2


# Testing the "draw_grid_lines" method.


def test_draw_grid_lines_draws_lines_when_enabled(renderer, board, monkeypatch):
    lines = []
    monkeypatch.setattr(pg.draw, "line", lambda *args: lines.append(args))

    renderer.draw_grid_lines(board=board)

    assert len(lines) == 9 + 19


def test_draw_grid_lines_draws_nothing_when_disabled(
    renderer, board, runtime_config, monkeypatch
):
    lines = []
    monkeypatch.setattr(pg.draw, "line", lambda *args: lines.append(args))
    runtime_config.BOARD.GRID_LINES.ENABLED = False

    renderer.draw_grid_lines(board=board)

    assert lines == []


# Testing the "draw_rect" method.


def test_draw_rect_fills_the_rectangle(renderer):
    rect = pg.Rect(5, 5, 10, 10)

    renderer.draw_rect(rect=rect, color=[9, 8, 7])

    assert renderer._surface.get_at((6, 6))[:3] == (9, 8, 7)


# Testing the "draw_text" method.


@pytest.mark.parametrize("color", [None, [255, 0, 0]])
def test_draw_text_renders_within_the_rect(renderer, color):
    rect = pg.Rect(0, 0, 100, 40)

    renderer.draw_text(text="HELLO", rect=rect, color=color)

    assert renderer._font is not None


# Testing the "draw_label_and_value" method.


def test_draw_label_and_value_draws_label_above_value(renderer, monkeypatch):
    texts = []
    monkeypatch.setattr(
        renderer, "draw_text", lambda text, rect, color: texts.append((text, rect))
    )
    rect = pg.Rect(0, 0, 100, 200)

    renderer.draw_label_and_value(label="SCORE", value="000040", rect=rect)

    assert [text for text, _ in texts] == ["SCORE", "000040"]
    assert texts[0][1].centery < texts[1][1].centery


# Testing the "draw_game_over" method.


def test_draw_game_over_draws_banner_centered_in_the_rect(renderer, monkeypatch):
    texts = []
    monkeypatch.setattr(
        renderer,
        "draw_text",
        lambda text, rect, color=None: texts.append((text, rect)),
    )
    area = pg.Rect(100, 100, 200, 400)

    renderer.draw_game_over(rect=area)

    assert [text for text, _ in texts] == ["GAME OVER"]
    assert texts[0][1].center == area.center
