"""Module for pygame-specific display and initialisation utilities."""

import pygame as pg

from src.boom_tetris.constants import WINDOW_SIZE_SCREEN_FRACTION


def get_window_size_from_screen_resolution(
    monitor_index: int = 0,
    min_width: int = 400,
    min_height: int = 300,
) -> tuple[int, int]:
    """
    Compute a windowed (non-fullscreen) size as a fraction of the primary desktop resolution.

    1. Initialise the pygame display module if not already active.
    2. Attempt to read the desktop resolution via get_desktop_sizes() (pygame >= 2.0).
    3. Fall back to display.Info() for older pygame versions.
    4. Apply WINDOW_SIZE_SCREEN_FRACTION and clamp to the minimum dimensions.

    Args:
        monitor_index (int): Index of the monitor to use from get_desktop_sizes().
        min_width (int): Minimum window width in pixels.
        min_height (int): Minimum window height in pixels.

    Returns:
        tuple[int, int]: The window width and height in pixels.
    """
    # Init
    if not pg.display.get_init():
        pg.display.init()

    # Resolve desktop resolution
    if pg.version.vernum >= (2, 0, 0):
        desktop_width, desktop_height = pg.display.get_desktop_sizes()[monitor_index]
    else:
        info = pg.display.Info()
        desktop_width = info.current_w if info.current_w > 0 else 1920
        desktop_height = info.current_h if info.current_h > 0 else 1080

    # Scale
    width = max(min_width, int(desktop_width * WINDOW_SIZE_SCREEN_FRACTION))
    height = max(min_height, int(desktop_height * WINDOW_SIZE_SCREEN_FRACTION))

    return width, height


def normalize_float(value: float, ndigits: int = 4) -> float:
    """
    Normalize a floating-point value by rounding it to a fixed precision.

    This helps eliminate floating-point representation artifacts (e.g.
    ``-199.20000000000002``) that can appear during arithmetic operations,
    ensuring cleaner and more stable values for serialization (e.g. YAML)
    and rendering logic.

    Args:
        value (float): The floating-point number to normalize.
        ndigits (int): Number of decimal places to round to (default: 4).

    Returns:
        float: The rounded floating-point value.
    """
    return round(value, ndigits)
