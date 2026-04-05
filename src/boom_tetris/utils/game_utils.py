""" """


def convert_drop_frames_to_time(framerate: float, frames_per_cell: int) -> float:
    """ """
    return frames_per_cell / framerate * 1000


def compute_first_level_advancement(start_level: int) -> int:
    """ """
    return min(start_level * 10 + 10, max(100, start_level * 10 - 50))


def get_frames_per_cell(level: int, frames_per_cell: dict[int, int]) -> int:
    """ """
    while level not in frames_per_cell:
        level -= 1

    return frames_per_cell[level]


def frames2ms(frame_rate: float, frames: int) -> float:
    """ """
    return frames / frame_rate * 1000


def gravity2ms(frame_rate: float, gravity: float) -> float:
    """ """
    return (1 / gravity) * 1000 / frame_rate
