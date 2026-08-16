"""Post-process polyomino coordinates after generation.

`PolyominoGenerator` produces raw, game-agnostic polyomino shapes: sets of cells
that are connected and distinct up to rotation. Those shapes carry no notion of
"game" concerns, such as which orientation a piece should spawn in, where its
origin needs to sit relative to the board's spawn point, or that the board's
coordinate system grows downward while the generator's grows upward.

This module closes that gap. `PolyominoTransformer` loads the raw shapes
together with optional, hand-authored JSON correction metadata and applies it as
a small pipeline, turning generator output into coordinates that are ready to be
placed directly onto the board.
"""

import json

from src.boom_tetris.constants import (
    TETROMINO_PROPERTIES_FILE_PATH,
    TRIOMINO_PROPERTIES_FILE_PATH,
)
from src.boom_tetris.utils.utils_dict import DotDict

# A cell is represented by coordinates in 2 dimensions, matching
# `PolyominoGenerator`'s representation.
type Cell = tuple[int, int]

# A polyomino as stored and mutated during the correction pipeline: a list
# of mutable `[x, y]` blocks, so `_rotate`, `_shift`, and
# `_mirror_horizontally` can update coordinates in place.
type MutableCell = list[int]
type PolyominoBlocks = list[MutableCell]

# The immutable, hashable form of a shape used as a `polyomino_mapping`
# key, matching the canonical form `PolyominoGenerator` produces.
type PolyominoKey = tuple[Cell, ...]
type PolyominoMapping = dict[PolyominoKey, DotDict]


class PolyominoTransformer:
    """Adapt generator-produced polyomino shapes into board-ready coordinates.

    `PolyominoGenerator` only guarantees geometric distinctness; it says nothing
    about how a shape needs to behave once it enters a game board. This class
    closes that gap for polyomino sizes that have hand-authored correction
    metadata, by running each shape through a rotate → shift → mirror pipeline:
    `_rotate` turns a shape into its intended spawn orientation, `_shift` moves
    it into its intended spawn position, and `_mirror_horizontally` reconciles
    the generator's coordinate system with the board's. Sizes without correction
    metadata are returned unchanged.

    Attributes:
        polyominos (list[PolyominoBlocks]): The polyomino shapes being
            transformed, one entry per distinct shape.
        polyomino_size (int): The number of cells in each polyomino, used to
            decide whether correction metadata exists and should be applied.
        polyomino_mapping (PolyominoMapping): Per-shape correction metadata
            (rotation and position corrections), keyed by the shape's canonical,
            sorted cell tuple.
    """

    def __init__(self, config: DotDict) -> None:
        """Load shapes and their correction metadata, then bring both into a
        shared order.

        Args:
            config (DotDict): Augmented game configuration including
                `POLYOMINO.ALL_SHAPES` and `POLYOMINO.SIZE`.
        """
        self.polyominos: list[PolyominoBlocks] = (
            config.POLYOMINO.ALL_SHAPES
            if config.POLYOMINO.ALL_SHAPES is not None
            else []
        )
        self.polyomino_size = config.POLYOMINO.SIZE
        self.polyomino_mapping: PolyominoMapping = self._load_polyomino_properties()
        self._sort()

    def _load_polyomino_properties(self) -> PolyominoMapping:
        """Load per-shape correction metadata for sizes that have a hand-
        authored JSON file, keyed by each shape's canonical cell tuple.

        Only triominoes and tetrominoes currently have correction metadata
        authored for them; `execute` falls back to an untransformed pipeline for
        every other size, so no file is loaded for them here.

        1. Pick the properties file that matches `polyomino_size` and load its
           raw JSON content.
        2. Convert each string-encoded cell-tuple key back into an actual tuple
           of tuples, since JSON only supports string keys.
        3. Wrap each shape's property dict in a `DotDict` so its fields are
           accessible as attributes instead of dict lookups.

        Returns:
            polyomino_mapping (PolyominoMapping): Mapping from each shape's
                canonical cell tuple to its correction properties.
        """
        # TODO: sizes other than 3 or 4 leave `polyomino_mapping` unbound
        # below, since neither branch executes. Guard this once metadata
        # for other sizes is added, or raise an explicit error instead.
        if self.polyomino_size == 3:
            with open(TRIOMINO_PROPERTIES_FILE_PATH, "r") as file:
                polyomino_mapping = json.load(file)
        if self.polyomino_size == 4:
            with open(TETROMINO_PROPERTIES_FILE_PATH, "r") as file:
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

    def _sort(self) -> None:
        """Re-establish a shared, deterministic order across `polyominos` and
        `polyomino_mapping`.

        Every transform step in this pipeline (`_rotate`, `_shift`,
        `_mirror_horizontally`) pairs up `self.polyominos` and
        `self.polyomino_mapping` positionally via `zip`, trusting that index `i`
        in one refers to the same shape as index `i` in the other. Applying a
        correction changes a shape's underlying cell coordinates, which can
        change how it sorts relative to its neighbours. Re-sorting both
        collections by their (now updated) cell values after every step restores
        that shared order, so the next step's `zip` keeps pairing each shape
        with its own metadata instead of someone else's.
        """
        # Sort the polyominos.
        self.polyominos = list(
            sorted(sorted(polyomino) for polyomino in self.polyominos)
        )

        # Sort the polyomino mapping.
        sorted_polyomino_mapping: PolyominoMapping = {}

        for k, _ in self.polyomino_mapping.items():
            sorted_key = tuple(sorted(k))
            sorted_polyomino_mapping[sorted_key] = self.polyomino_mapping[k]

        self.polyomino_mapping = dict(sorted(sorted_polyomino_mapping.items()))

    def _rotate(self) -> None:
        """Apply each shape's `rotation_correction` to align it with its
        intended spawn orientation, then re-sort.

        The generator treats rotations of the same shape as duplicates and keeps
        whichever orientation it happens to encounter first during its search,
        which is not necessarily the orientation a piece should spawn in on the
        board. `rotation_correction` records that fix as a sign: a positive or
        negative value applies a single 90° turn in the corresponding direction,
        while `0` (or a missing value) leaves the shape untouched.
        """
        updated_polyomino_mapping: PolyominoMapping = {}

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
        """Apply each shape's `position_correction` offset to move it into its
        intended spawn position, then re-sort.

        The generator places a shape's origin wherever its search happened to
        start; it has no notion of where that origin needs to sit relative to
        the board's spawn point. `position_correction` is a `[dx, dy]` offset
        that moves the whole shape to fix that. Shapes without a correction, or
        with an all-zero offset, are left untouched.
        """
        updated_polyomino_mapping: PolyominoMapping = {}

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
        """Flip every shape across the horizontal axis to reconcile the
        generator's coordinate system with the board's, then re-sort.

        `PolyominoGenerator` builds shapes on a standard mathematical plane,
        where moving "up" increases y. The board instead uses a grid convention
        where row indices increase downward, so moving "down" increases y.
        Negating every cell's y-coordinate reconciles the two: a shape defined
        with an up-positive y-axis ends up correctly oriented once it is placed
        on the board's down-positive y-axis.
        """
        updated_polyomino_mapping: PolyominoMapping = {}

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
    ) -> tuple[list[list[Cell]], PolyominoMapping]:
        """Run the full rotate → shift → mirror pipeline for sizes that have
        correction metadata; return other sizes unchanged.

        Triominoes and tetrominoes are the only sizes with hand-authored
        correction metadata (see `_load_polyomino_properties`), so only they are
        transformed into board-ready coordinates. Other sizes have no metadata
        to apply, so their shapes pass through untransformed.

        Returns:
            polyominos (list[list[Cell]]): The corrected shapes for polyomino
                sizes, or the untouched shapes for any other size, with each
                cell as un immutable `(x,y)` tuple.
            polyomino_mapping (PolyominoMapping): The corresponding correction
                metadata, keyed by each shape's canonical cell tuple.
        """
        if self.polyomino_size in [3, 4]:
            self._rotate()
            self._shift()
            self._mirror_horizontally()

        polyominos = [[(x, y) for x, y in shape] for shape in self.polyominos]

        return polyominos, self.polyomino_mapping
