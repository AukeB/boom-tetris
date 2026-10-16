"""Tests for the entry point in `main.py`."""

import runpy
from pathlib import Path

import pytest

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.game import Game

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def stub_game(runtime_config, monkeypatch):
    """Use the committed runtime config and a scripted game loop.

    Args:
        runtime_config (ConfigModelRuntime): The runtime configuration.
        monkeypatch: Pytest fixture used to replace the config and game loop.

    Returns:
        updates (list[bool]): Results the game loop reports, one per frame.
    """
    monkeypatch.setattr(
        ConfigManager, "get_runtime_config", lambda self: runtime_config
    )
    updates = [True, True, False]
    calls = []

    def fake_update(self):
        calls.append(self)
        index = len(calls) - 1
        result = updates[index]

        return result

    monkeypatch.setattr(Game, "update", fake_update)

    return calls


# Testing the "main" function.


def test_main_runs_the_game_until_it_quits(stub_game):
    from main import main

    main()

    assert len(stub_game) == 3


def test_running_the_script_starts_the_game(stub_game):
    main_script = str(REPO_ROOT / "main.py")

    runpy.run_path(main_script, run_name="__main__")

    assert len(stub_game) == 3
