"""Falling polyomino state: random shape, rotations, and block iteration."""

import random as rd
from collections.abc import Iterator

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.constants import CONFIG_RUNTIME_FILE_PATH
from src.boom_tetris.polyomino.polyomino_transformer import PolyominoTransformer

config_runtime = ConfigManager().load_config_without_validation(
    file_path=CONFIG_RUNTIME_FILE_PATH
)

polyomino_transformer = PolyominoTransformer(config=config_runtime)
ALL_POLYOMINOS, POLYOMINO_MAPPING = polyomino_transformer.execute()


class Polyomino:
    """One active piece with grid position, blocks, and rotation metadata."""

    def __init__(
        self, x: int, y: int, previous_polyomino_index: int | None = None
    ) -> None:
        """Pick a shape using NEST-style anti-repeat RNG.

        The roll draws one value beyond the piece count; landing on that spare
        value or repeating ``previous_index`` triggers a single re-roll, which
        halves the odds of the same piece twice in a row.

        Args:
            x: Initial column in board cells.
            y: Initial row in board cells.
            previous_polyomino_index (int | None): Index of the previously
                spanwed piece, or ``None`` for the first piece. Defaults to
                ``None``.
        """
        self.x = x
        self.y = y

        self.index = self._roll_index(previous_polyomino_index)

        self.blocks = ALL_POLYOMINOS[self.index]
        self.properties = POLYOMINO_MAPPING[tuple(self.blocks)]
        self.rotation_type = self.properties.rotation_type

        if self.rotation_type == "predefined":
            self.rotation_index = 0
            self.rotations = self.properties.rotations
            self.blocks = self.rotations[self.rotation_index]

    @staticmethod
    def _roll_index(previous_polyomino_index: int | None) -> int:
        """Return a piece index using the NES anti-repeat re-roll rule.

        Args:
            previous_index (int | None): Index of the previous piece, or
                ``None`` to skip the repeat check.

        Returns:
            int: Index into ``ALL_POLYOMINOS`` for the new piece.
        """
        count = len(ALL_POLYOMINOS)
        roll = rd.randint(0, count)

        if roll == count or roll == previous_polyomino_index:
            roll = rd.randint(0, count - 1)

        return roll

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

    def get_rotation(self, direction: int) -> list[tuple[int, int]]:
        """Return blocks for a rotation without mutating ``rotation_index``.

        Args:
            direction: Rotation delta; ``0`` means no change.

        Returns:
            list[tuple[int, int]]: List of ``(x, y)`` block offsets for that
                orientation.
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

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """Iterate over the current block offset list.

        Returns:
            Iterator[tuple[int, int]]: Iterator over ``(dx, dy)`` cells relative
                to the piece origin.
        """
        return iter(self.blocks)
