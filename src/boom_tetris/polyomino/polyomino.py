"""Falling polyomino state: random shape, rotations, and block iteration."""

import random as rd

from src.boom_tetris.config.config import Config
from src.boom_tetris.constants import MAIN_CONFIG_AUGMENTED_RELATIVE_FILE_PATH
from src.boom_tetris.polyomino.polyomino_transformer import PolyominoTransformer

config_main = Config.load_config(
    file_path=MAIN_CONFIG_AUGMENTED_RELATIVE_FILE_PATH, validate=False
)

polyomino_transformer = PolyominoTransformer(config=config_main)
ALL_POLYOMINOS, POLYOMINO_MAPPING = polyomino_transformer.execute()


class Polyomino:
    """One active piece with grid position, blocks, and rotation metadata."""

    def __init__(self, x: int, y: int) -> None:
        """Pick a random shape from module-level ``ALL_POLYOMINOS``.

        Args:
            x: Initial column in board cells.
            y: Initial row in board cells.
        """
        self.x = x
        self.y = y

        polyomino_index = rd.randint(0, len(ALL_POLYOMINOS) - 1)

        self.blocks = ALL_POLYOMINOS[polyomino_index]
        self.properties = POLYOMINO_MAPPING[
            tuple(tuple(block) for block in self.blocks)
        ]
        self.rotation_type = self.properties.rotation_type

        if self.rotation_type == "predefined":
            self.rotation_index = 0
            self.rotations = self.properties.rotations
            self.blocks = self.rotations[self.rotation_index]

    def rotate(self, direction: int) -> None:
        """Advance rotation for predefined types or recompute block coordinates.

        Args:
            direction: Clockwise/counter-clockwise sign from configuration.
        """
        if self.rotation_type == "predefined":
            self.rotation_index = (self.rotation_index + direction) % len(
                self.rotations
            )
            self.blocks = self.rotations[self.rotation_index]
        else:
            self.blocks = self.get_rotation(direction=direction)

    def get_rotation(self, direction: int) -> list[tuple]:
        """Return blocks for a rotation without mutating ``rotation_index``.

        Args:
            direction: Rotation delta; ``0`` means no change.

        Returns:
            List of ``(x, y)`` block offsets for that orientation.
        """
        if direction == 0:
            return self.blocks

        # If polyomino has None as rotation_type (such as the tetromino square),
        # do not perform rotational movement.
        if self.rotation_type is None:
            return self.blocks

        if self.rotation_type == "predefined":
            rotation_index = (self.rotation_index + direction) % len(self.rotations)
            return self.rotations[rotation_index]

        return [(-y * direction, x * direction) for (x, y) in self.blocks]

    def __iter__(self) -> None:
        """Iterate over the current block offset list.

        Yields:
            Each ``(dx, dy)`` cell relative to the piece origin.
        """
        return iter(self.blocks)
