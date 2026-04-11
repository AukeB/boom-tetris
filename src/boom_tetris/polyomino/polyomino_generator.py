"""
Generate all distinct polyominoes for a fixed size via brute-force
backtracking DFS.

Notes:
- In the case for Tetris, distinct polyominoes means rotations do not count,
but inversions do. For example, the L-piece and the J-piece are inversions
and two separate tetromino pieces. However, if you rotate an L-piece, this does
not generate a 'new' tetromino.
- If the fixed size is set to, for example, 4, then it will generate all
polyominoes with size 4, which are called tetrominoes.
"""

type Cell = tuple[int, int]


class PolyominoGenerator:
    """
    Enumerate one-sided polyominoes of a fixed size using backtracking and
    rotation-invariant deduplication.

    A one-sided polyomino is a connected shape made of unit squares on a grid,
    where two shapes are considered identical if one can be rotated into the
    other, but mirror images are counted as distinct.
    This generator grows shapes cell-by-cell via DFS and discards any new shape
    whose canonical form matches any rotation of a shape already seen.
    """

    def __init__(
        self, number_of_polyomino_cells: int, directions: dict[str, list[int]]
    ) -> None:
        """
        Initialisation of the `PolyominoGenerator` class.

        Args:
            number_of_polyomino_cells: The exact number of cells each polyomino
                must contain (e.g. 4 for tetrominoes, 5 for pentominoes, etc.).
            directions: Named step vectors used to find neighbouring cells.
                Each value is a two-element list ``[dx, dy]``.
        """
        self.number_of_polyomino_cells = number_of_polyomino_cells
        self.directions = directions
        self.unique_shapes: set[tuple[Cell, ...]] = set()

    def _normalize(self, polyomino_shape: tuple[Cell, ...]) -> tuple[Cell, ...]:
        """
        Translate a shape so its bounding box starts at the origin, then sort
        its cells.

        Normalisation gives every shape a unique positional representation
        independent of where on the grid it was constructed, which is a
        prerequisite before any rotation-based comparison can be made.

        1. Find the minimum x and minimum y across all cells.
        2. Subtract those minima from every cell so the leftmost column becomes
           x=0 and the bottom row becomes y=0.
        3. Return the cells as a sorted tuple so the representation is stable.

        Args:
            polyomino_shape: Occupied cells as a tuple of ``(x, y)`` integer pairs.

        Returns:
            A sorted tuple of ``(x, y)`` pairs with min-x = 0 and min-y = 0.
        """
        x_min = min(x for x, _ in polyomino_shape)
        y_min = min(y for _, y in polyomino_shape)
        normalized_shape = tuple(
            sorted((x - x_min, y - y_min) for x, y in polyomino_shape)
        )

        return normalized_shape

    def _rotate(self, polyomino_shape: tuple[Cell, ...]) -> tuple[Cell, ...]:
        """
        Apply a single 90° counter-clockwise rotation to a shape's cells.

        The transformation ``(x, y) → (y, −x)`` rotates each cell around the
        origin by 90° counter-clockwise. Calling this method four times in
        succession returns the shape to its original orientation.

        Args:
            polyomino_shape: A normalised, sorted tuple of ``(x, y)`` cell pairs.

        Returns:
            A tuple of rotated ``(x, y)`` cell pairs.
        """
        rotated_shape = tuple((y, -x) for x, y in polyomino_shape)

        return rotated_shape

    def _obtain_all_rotations(
        self, polyomino_shape: tuple[Cell, ...]
    ) -> list[tuple[Cell, ...]]:
        """
        Return the four normalised orientations produced by successive 90° rotations.

        Because ``directions`` has four entries, a shape has at most four
        distinct orientations. Shapes with rotational symmetry will produce
        duplicate entries in the list, but that does not affect correctness —
        the caller only checks membership.

        1. Rotate the input 90° counter-clockwise and normalise; repeat four times.
        2. Collect each normalised rotation and return all four.

        Args:
            polyomino_shape: Occupied cells as a normalised tuple of ``(x, y)`` pairs.

        Returns:
            A list of four normalised cell tuples, one per 90° rotation step.
        """
        rotations: list[tuple[Cell, ...]] = []
        current_shape = polyomino_shape

        for _ in range(len(self.directions)):
            rotated_shape = self._rotate(current_shape)
            current_shape = self._normalize(rotated_shape)
            rotations.append(current_shape)

        return rotations

    def generate(self, polyomino_shape: set[Cell] = {(0, 0)}) -> set[tuple[Cell, ...]]:
        """
        Recursively grow a polyomino and record each unique shape at the target size.

        Expansion works depth-first: for every cell already in the shape, each
        neighbouring cell not yet occupied is added to form a new candidate, and
        ``generate`` is called again on that candidate. When the candidate
        reaches the target size, it is normalised and checked against all four of
        its rotations; if none of those rotations is already recorded, the shape
        is added to ``unique_shapes``.

        1. Check whether the current shape has reached the target cell count.
        2. If so, normalise the shape and compute its four rotations.
        3. If none of the rotations appear in ``unique_shapes``, record the
           normalised shape.
        4. If the target has not been reached, iterate over every occupied cell
           and every direction; skip neighbours already in the shape; recurse
           with each new candidate set.

        Args:
            polyomino_shape: The set of cells occupied by the polyomino so far.
                Defaults to a single cell at the origin to start the search.

        Returns:
            The set of all distinct polyominoes as canonical sorted tuples,
            accumulated across the full recursion.
        """
        number_of_cells = len(polyomino_shape)

        # Record shape
        if number_of_cells == self.number_of_polyomino_cells:
            normalized_shape = self._normalize(tuple(polyomino_shape))
            all_rotations = self._obtain_all_rotations(normalized_shape)

            if not any(rotation in self.unique_shapes for rotation in all_rotations):
                self.unique_shapes.add(normalized_shape)

            return self.unique_shapes

        # Expand shape
        for x, y in polyomino_shape:
            for _, (dx, dy) in self.directions.items():
                nx, ny = x + dx, y + dy

                if (nx, ny) in polyomino_shape:
                    continue

                new_polyomino_shape = polyomino_shape | {(nx, ny)}
                self.generate(polyomino_shape=new_polyomino_shape)

        return self.unique_shapes
