"""Post-process polyomino coordinates after generation.

Sort, rotate, mirror, and shift blocks using optional JSON metadata.
"""

import json

from src.boom_tetris.constants import (
    TRIOMINO_PROPERTIES_RELATIVE_FILE_PATH,
    TETROMINO_PROPERTIES_RELATIVE_FILE_PATH,
)
from src.boom_tetris.utils.utils_dict import DotDict


class PolyominoTransformer:
    """Apply JSON-defined corrections to shapes for tetromino-sized games."""

    def __init__(self, config: DotDict) -> None:
        """Load shapes from config and optional tetromino property metadata.

        Args:
            config: Augmented game configuration including ``ALL_SHAPES``.
        """
        self.polyominos: list[list[list[int]]] = (
            config.POLYOMINO.ALL_SHAPES
            if config.POLYOMINO.ALL_SHAPES is not None
            else []
        )
        self.polyomino_size = config.POLYOMINO.SIZE
        self.polyomino_mapping: dict[tuple[tuple[int, int], ...], DotDict] = (
            self._load_polyomino_properties()
        )
        self._sort()

    def _load_polyomino_properties(
        self,
    ) -> dict[tuple[tuple[int, int], ...], DotDict]:
        """Load per-shape metadata for size 4; otherwise return an empty map.

        Returns:
            Mapping from canonical cell-tuple keys to property ``DotDict``s.
        """
        if self.polyomino_size == 3:
            with open(TRIOMINO_PROPERTIES_RELATIVE_FILE_PATH, "r") as file:
                polyomino_mapping = json.load(file)
        if self.polyomino_size == 4:
            with open(TETROMINO_PROPERTIES_RELATIVE_FILE_PATH, "r") as file:
                polyomino_mapping = json.load(file)

        # Because the coordinate representation of the polyomino is used in
        # str format as key of the dictionary, we need to convert it to a tuple.
        polyomino_mapping = {
            tuple(map(tuple, json.loads(k))): v for k, v in polyomino_mapping.items()
        }

        # Because the dictionary keys are tuples, apply the DotDict one level deeper.
        for polyomino_index in polyomino_mapping:
            polyomino_mapping[polyomino_index] = DotDict(
                polyomino_mapping[polyomino_index]
            )

        return polyomino_mapping

        return {}

    def _sort(self) -> None:
        """Sort block lists and reorder the property map to match."""
        # Sort the polyominos.
        self.polyominos = list(
            sorted(sorted(polyomino) for polyomino in self.polyominos)
        )

        # Sort the polyomino mapping.
        sorted_polyomino_mapping: dict[tuple[tuple[int, int], ...], DotDict] = {}

        for k, _ in self.polyomino_mapping.items():
            sorted_key = tuple(sorted(k))
            sorted_polyomino_mapping[sorted_key] = self.polyomino_mapping[k]

        self.polyomino_mapping = dict(sorted(sorted_polyomino_mapping.items()))

    def _rotate(self) -> None:
        """Apply JSON ``rotation_correction`` to shapes, then re-sort."""
        updated_polyomino_mapping: dict[tuple[tuple[int, int], ...], DotDict] = {}

        for i, (polyomino, (_, polyomino_properties)) in enumerate(
            zip(self.polyominos, self.polyomino_mapping.items())
        ):
            if (
                "rotation_correction" in polyomino_properties
                and polyomino_properties.rotation_correction != 0
            ):
                rotated_polyomino = [
                    [
                        -y * polyomino_properties.rotation_correction,
                        x * polyomino_properties.rotation_correction,
                    ]
                    for [x, y] in polyomino
                ]

                self.polyominos[i] = rotated_polyomino
                updated_polyomino_mapping[
                    tuple((block[0], block[1]) for block in rotated_polyomino)
                ] = polyomino_properties
            else:
                updated_polyomino_mapping[
                    tuple((block[0], block[1]) for block in polyomino)
                ] = polyomino_properties

        self.polyomino_mapping = updated_polyomino_mapping

        self._sort()

    def _shift(self) -> None:
        """Apply JSON ``position_correction`` offsets, then re-sort."""
        updated_polyomino_mapping: dict[tuple[tuple[int, int], ...], DotDict] = {}

        for i, (polyomino, (_, polyomino_properties)) in enumerate(
            zip(self.polyominos, self.polyomino_mapping.items())
        ):
            if "position_correction" in polyomino_properties and any(
                x != 0 for x in polyomino_properties.position_correction
            ):
                shifted_polyomino = [
                    [
                        x + polyomino_properties.position_correction[0],
                        y + polyomino_properties.position_correction[1],
                    ]
                    for [x, y] in polyomino
                ]

                self.polyominos[i] = shifted_polyomino
                updated_polyomino_mapping[
                    tuple((block[0], block[1]) for block in shifted_polyomino)
                ] = polyomino_properties
            else:
                updated_polyomino_mapping[
                    tuple((block[0], block[1]) for block in polyomino)
                ] = polyomino_properties

        self.polyomino_mapping = updated_polyomino_mapping

        self._sort()

    def _mirror_horizontally(self) -> None:
        """
        Needs to happen because positive y-direction of the board is
        downwards, while the positive y-direction in a polyomino
        definition is upwards.
        """
        updated_polyomino_mapping: dict[tuple[tuple[int, int], ...], DotDict] = {}

        for i, (polyomino, (_, polyomino_properties)) in enumerate(
            zip(self.polyominos, self.polyomino_mapping.items())
        ):
            mirrored_polyomino = [[x, -y] for [x, y] in polyomino]

            self.polyominos[i] = mirrored_polyomino
            updated_polyomino_mapping[
                tuple((block[0], block[1]) for block in mirrored_polyomino)
            ] = polyomino_properties

        self.polyomino_mapping = updated_polyomino_mapping

        self._sort()

    def execute(
        self,
    ) -> (
        tuple[list[list[list[int]]], dict[tuple[tuple[int, int], ...], DotDict]]
        | list[list[list[int]]]
    ):
        """Run the full transform pipeline for tetrominoes; else return shapes.

        Returns:
            For size 4, ``(polyominos, mapping)``; otherwise ``polyominos``
            alone.
        """
        if self.polyomino_size in [3, 4]:
            self._rotate()
            self._shift()
            self._mirror_horizontally()

            return self.polyominos, self.polyomino_mapping

        return self.polyominos
