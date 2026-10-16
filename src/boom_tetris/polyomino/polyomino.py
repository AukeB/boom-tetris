"""Falling polyomino state: random shape, rotations, and block iteration."""

import random as rd
from collections.abc import Iterator

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.constants import CONFIG_RUNTIME_FILE_PATH
from src.boom_tetris.polyomino.polyomino_transformer import PolyominoTransformer

_config_manager = ConfigManager()

_config_runtime = _config_manager.load_config_without_validation(
    file_path=CONFIG_RUNTIME_FILE_PATH
)

_polyomino_transformer = PolyominoTransformer(config=_config_runtime)
_ALL_POLYOMINOS, _POLYOMINO_MAPPING = _polyomino_transformer.execute()


class Polyomino:
    """One active piece with grid position, blocks, and rotation metadata.

    Attributes:
        x (int): Column of the piece origin in board cells.
        y (int): Row of the piece origin in board cells.
        index (int): Index into ``ALL_POLYOMINOS`` for this piece's shape.
        _blocks (list[tuple[int, int]]): Block offsets of the current
            orientation.
        _properties (DotDict): Correction metadata for this shape.
        _rotation_type (str | None): How the piece rotates, from its metadata.
        _rotation_index (int): Current index into ``_rotations`` for predefined
            rotation types.
        _rotations (list): Predefined orientations, when the piece has them.

    Example:
        >>> piece = Polyomino(x=5, y=0)
        >>> piece.rotate(direction=1)
        >>> blocks = list(piece)
    """

    @staticmethod
    def _roll_index(previous_polyomino_index: int | None) -> int:
        """Return a piece index using the NES anti-repeat re-roll rule.

        Args:
            previous_index (int | None): Index of the previous piece, or
                ``None`` to skip the repeat check.

        Returns:
            roll (int): Index into ``ALL_POLYOMINOS`` for the new piece.
        """

        count = len(_ALL_POLYOMINOS)
        roll = rd.randint(0, count)

        if roll == count or roll == previous_polyomino_index:
            roll = rd.randint(0, count - 1)

        return roll

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

        self._blocks = _ALL_POLYOMINOS[self.index]
        shape_key = tuple(self._blocks)
        self._properties = _POLYOMINO_MAPPING[shape_key]
        self._rotation_type = self._properties.rotation_type

        if self._rotation_type == "predefined":
            self._rotation_index = 0
            self._rotations = self._properties.rotations
            self._blocks = self._rotations[self._rotation_index]

    def get_rotation(self, direction: int) -> list[tuple[int, int]]:
        """Return blocks for a rotation without mutating ``_rotation_index``.

        Args:
            direction: Rotation delta; ``0`` means no change.

        Returns:
            blocks (list[tuple[int, int]]): List of ``(x, y)`` block offsets for
                that orientation.
        """

        if direction == 0:
            return self._blocks

        # If polyomino has None as rotation_type (such as the tetromino square),
        # do not perform rotational movement.
        if self._rotation_type is None:
            return self._blocks

        if self._rotation_type == "predefined":
            rotation_count = len(self._rotations)
            rotation_index = (self._rotation_index + direction) % rotation_count
            rotated_blocks = self._rotations[rotation_index]

            return rotated_blocks

        rotated_blocks = [(-y * direction, x * direction) for (x, y) in self._blocks]

        return rotated_blocks

    def rotate(self, direction: int) -> None:
        """Advance rotation for predefined types or recompute block coordinates.

        Args:
            direction: Clockwise/counter-clockwise sign from configuration.
        """

        if self._rotation_type == "predefined":
            rotation_count = len(self._rotations)
            self._rotation_index = (self._rotation_index + direction) % rotation_count
            self._blocks = self._rotations[self._rotation_index]
        else:
            self._blocks = self.get_rotation(direction=direction)

    def __iter__(self) -> Iterator[tuple[int, int]]:
        """Iterate over the current block offset list.

        Returns:
            blocks_iterator (Iterator[tuple[int, int]]): Iterator over ``(dx,
                dy)`` cells relative to the piece origin.
        """

        blocks_iterator = iter(self._blocks)

        return blocks_iterator
