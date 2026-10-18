"""Tests for the pygame display helpers in `utils_other`."""

from types import SimpleNamespace

import pygame as pg

from boom_tetris.utils.utils_other import (
    get_window_size_from_screen_resolution,
)

# Testing the "get_window_size_from_screen_resolution" function.


def test_window_size_scales_desktop_size_on_pygame_2(monkeypatch):
    monkeypatch.setattr(pg.version, "vernum", (2, 6, 1))
    monkeypatch.setattr(pg.display, "get_init", lambda: True)
    monkeypatch.setattr(pg.display, "get_desktop_sizes", lambda: [(1000, 800)])

    window_size = get_window_size_from_screen_resolution()

    assert window_size == (950, 760)


def test_window_size_is_clamped_to_minimum(monkeypatch):
    monkeypatch.setattr(pg.version, "vernum", (2, 6, 1))
    monkeypatch.setattr(pg.display, "get_init", lambda: True)
    monkeypatch.setattr(pg.display, "get_desktop_sizes", lambda: [(100, 100)])

    window_size = get_window_size_from_screen_resolution()

    assert window_size == (400, 300)


def test_window_size_initialises_display_when_inactive(monkeypatch):
    calls = []
    monkeypatch.setattr(pg.version, "vernum", (2, 6, 1))
    monkeypatch.setattr(pg.display, "get_init", lambda: False)
    monkeypatch.setattr(pg.display, "init", lambda: calls.append("init"))
    monkeypatch.setattr(pg.display, "get_desktop_sizes", lambda: [(1000, 800)])

    get_window_size_from_screen_resolution()

    assert calls == ["init"]


def test_window_size_uses_display_info_on_older_pygame(monkeypatch):
    info = SimpleNamespace(current_w=1280, current_h=720)
    monkeypatch.setattr(pg.version, "vernum", (1, 9, 6))
    monkeypatch.setattr(pg.display, "get_init", lambda: True)
    monkeypatch.setattr(pg.display, "Info", lambda: info)

    window_size = get_window_size_from_screen_resolution()

    assert window_size == (1216, 684)


def test_window_size_falls_back_to_full_hd_on_older_pygame(monkeypatch):
    info = SimpleNamespace(current_w=0, current_h=0)
    monkeypatch.setattr(pg.version, "vernum", (1, 9, 6))
    monkeypatch.setattr(pg.display, "get_init", lambda: True)
    monkeypatch.setattr(pg.display, "Info", lambda: info)

    window_size = get_window_size_from_screen_resolution()

    assert window_size == (1824, 1026)
