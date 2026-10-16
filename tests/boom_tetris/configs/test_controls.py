"""Tests for the keyboard bindings in `configs/controls`."""

import pygame as pg

from src.boom_tetris.configs.controls import SINGLE_PLAYER_CONTROLS

# Testing the "SINGLE_PLAYER_CONTROLS" mapping.


def test_movement_keys_use_wasd():
    assert SINGLE_PLAYER_CONTROLS.LEFT == pg.K_a
    assert SINGLE_PLAYER_CONTROLS.RIGHT == pg.K_d
    assert SINGLE_PLAYER_CONTROLS.UP == pg.K_w
    assert SINGLE_PLAYER_CONTROLS.DOWN == pg.K_s


def test_rotation_and_harddrop_keys_use_arrows_and_space():
    assert SINGLE_PLAYER_CONTROLS.ROTATE_CLOCKWISE == pg.K_RIGHT
    assert SINGLE_PLAYER_CONTROLS.ROTATE_COUNTERCLOCKWISE == pg.K_LEFT
    assert SINGLE_PLAYER_CONTROLS.HARDDROP == pg.K_SPACE
