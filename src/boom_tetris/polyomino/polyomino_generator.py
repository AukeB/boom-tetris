"""Enumerate distinct free polyominoes up to a fixed cell count."""


class PolyominoGenerator:
    """Backtracking generator with rotation-normalized shape deduplication."""

    def __init__(
        self, number_of_polyomino_cells: int, directions: dict[str, list[int]]
    ) -> None:
        """Set target size and neighbor directions for expansion.

        Args:
            number_of_polyomino_cells: Target size (e.g. 4 for tetrominoes).
            directions: Step vectors (values are ``[dx, dy]`` lists).
        """
        self.number_of_polyomino_cells = number_of_polyomino_cells
        self.directions = directions
        self.unique_coordinates: set = set()

    def _normalize(
        self,
        coordinates: set[tuple[int, int]] | tuple[tuple[int, int], ...],
    ) -> tuple[tuple[int, int], ...]:
        """Translate coordinates so the minimum cell is at the origin.

        Args:
            coordinates: Occupied cells as a set or sorted tuple of pairs.

        Returns:
            Sorted tuple of cells with minimum ``x`` and ``y`` equal to zero.
        """
        coord_list = list(coordinates)
        x_min = min(x for x, _ in coord_list)
        y_min = min(y for _, y in coord_list)
        normalized_coordinates = tuple(
            sorted((x - x_min, y - y_min) for x, y in coord_list)
        )

        return normalized_coordinates

    def _rotate(self, coordinates: tuple[tuple[int, int], ...]) -> set[tuple[int, int]]:
        """Rotate 90° counter-clockwise around the origin (grid units).

        Args:
            coordinates: Canonical cell tuple after normalization.

        Returns:
            Set of rotated cell coordinates.
        """
        rotated_coordinates = set((y, -x) for x, y in coordinates)

        return rotated_coordinates

    def _obtain_all_rotations(
        self, coordinates: set[tuple[int, int]] | tuple[tuple[int, int], ...]
    ) -> list[tuple[tuple[int, int], ...]]:
        rotations: list[tuple[tuple[int, int], ...]] = []
        normalized = self._normalize(coordinates)

        for _ in range(len(self.directions)):
            rotated = self._rotate(normalized)
            normalized = self._normalize(rotated)
            rotations.append(normalized)

        return rotations

    def generate(
        self, coordinates: set[tuple[int, int]] = {(0, 0)}
    ) -> set[tuple[tuple[int, int], ...]]:
        """Grow polyominoes by DFS; record unique shapes at the target size.

        Args:
            coordinates: Current occupied cells; default is a single origin
                cell.

        Returns:
            Set of canonical sorted tuples, one per distinct free polyomino.
        """
        number_of_cells = len(coordinates)

        if number_of_cells == self.number_of_polyomino_cells:
            normalized_coordinates = self._normalize(coordinates=coordinates)
            rotation_invariant_coordinates = self._obtain_all_rotations(
                coordinates=normalized_coordinates
            )

            if any(
                coordinates in self.unique_coordinates
                for coordinates in rotation_invariant_coordinates
            ):
                pass
            else:
                normalized_coordinates = tuple(sorted(normalized_coordinates))
                self.unique_coordinates.add(normalized_coordinates)

        for x, y in list(coordinates):
            for _, (dx, dy) in self.directions.items():
                nx, ny = x + dx, y + dy

                if (nx, ny) in coordinates:
                    continue

                new_coordinates = coordinates | {(nx, ny)}

                if number_of_cells <= self.number_of_polyomino_cells:
                    self.generate(coordinates=new_coordinates)

        return self.unique_coordinates
