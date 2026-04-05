"""Time and level helpers for drop speed and gravity (NTSC-oriented)."""


def convert_drop_frames_to_time(framerate: float, frames_per_cell: int) -> float:
    """Convert per-cell drop duration from frames to milliseconds.

    Args:
        framerate: Video frame rate in Hz.
        frames_per_cell: Number of frames spent per one cell drop.

    Returns:
        Drop interval in milliseconds.
    """
    return frames_per_cell / framerate * 1000


def compute_first_level_advancement(start_level: int) -> int:
    """Lines cleared needed before the first level increase.

    Args:
        start_level: Starting level index from configuration.

    Returns:
        Line count threshold for the first level-up.
    """
    return min(start_level * 10 + 10, max(100, start_level * 10 - 50))


def get_frames_per_cell(level: int, frames_per_cell: dict[int, int]) -> int:
    """Look up drop frames per cell, stepping down until a key exists.

    Args:
        level: Current game level.
        frames_per_cell: Map from level to frames per one cell drop.

    Returns:
        Frames per cell for the effective level used for lookup.
    """
    while level not in frames_per_cell:
        level -= 1

    return frames_per_cell[level]


def frames2ms(frame_rate: float, frames: int) -> float:
    """Convert a whole number of frames to milliseconds.

    Args:
        frame_rate: Video frame rate in Hz.
        frames: Duration in frames.

    Returns:
        Duration in milliseconds.
    """
    return frames / frame_rate * 1000


def gravity2ms(frame_rate: float, gravity: float) -> float:
    """Convert soft-drop gravity (cells per frame) to milliseconds per cell.

    Args:
        frame_rate: Video frame rate in Hz.
        gravity: Cells moved downward per frame when soft dropping.

    Returns:
        Time in milliseconds per cell at that gravity.
    """
    return (1 / gravity) * 1000 / frame_rate
