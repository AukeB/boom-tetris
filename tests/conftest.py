"""Shared setup for the test suite: headless pygame and common fixtures."""

import os
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame as pg  # noqa: E402
import pytest  # noqa: E402

from boom_tetris.config import config_manager as config_manager_module  # noqa: E402
from boom_tetris.config.config_manager import ConfigManager  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_WINDOW_SIZE = (1280, 720)


class FakeClock:
    """Stand-in for `pg.time.Clock` that always reports a 16 ms frame."""

    def tick(self, framerate: float = 0) -> int:
        """Return the duration of one frame in milliseconds.

        Args:
            framerate: Ignored; kept so the signature matches `pg.time.Clock`.

        Returns:
            frame_ms (int): Milliseconds since the previous tick.
        """
        frame_ms = 16

        return frame_ms


@pytest.fixture(autouse=True)
def run_from_repo_root(monkeypatch):
    """Resolve the relative configuration paths from the repository root.

    Args:
        monkeypatch: Pytest fixture used to change the working directory.
    """
    monkeypatch.chdir(REPO_ROOT)


@pytest.fixture
def runtime_config(tmp_path, monkeypatch):
    """Compute a runtime configuration for a fixed window size.

    The file is written into a temporary folder, so the committed runtime
    file is never touched, and the window size does not depend on the screen.

    Args:
        tmp_path (Path): Pytest temporary directory for the runtime file.
        monkeypatch: Pytest fixture used to fix the window size and file path.

    Returns:
        config_runtime (ConfigModelRuntime): The runtime configuration with
            `Position` directions, as the game receives it.
    """
    runtime_file = tmp_path / "config_runtime.yaml"
    monkeypatch.setattr(
        config_manager_module,
        "get_window_size_from_screen_resolution",
        lambda: TEST_WINDOW_SIZE,
    )
    monkeypatch.setattr(config_manager_module, "CONFIG_RUNTIME_FILE_PATH", runtime_file)
    manager = ConfigManager()
    manager._config_runtime_file_path = runtime_file
    config_runtime = manager.get_runtime_config()

    return config_runtime


@pytest.fixture
def fake_time(monkeypatch):
    """Replace pygame's clock and tick counter with controllable fakes.

    Args:
        monkeypatch: Pytest fixture used to replace the pygame functions.

    Returns:
        state (dict[str, int]): Holds the current time under the `now` key.
    """
    state = {"now": 0}
    monkeypatch.setattr(pg.time, "get_ticks", lambda: state["now"])
    monkeypatch.setattr(pg.time, "Clock", FakeClock)

    return state
