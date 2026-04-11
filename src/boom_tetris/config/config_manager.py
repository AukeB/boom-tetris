"""Load YAML config, update with computed fields, and write derived files."""

from pathlib import Path

from ruamel.yaml import YAML

from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.config.config_model_source import ConfigModelSource
from src.boom_tetris.constants import (
    CONFIG_RUNTIME_FILE_PATH,
    CONFIG_SOURCE_FILE_PATH,
    Position,
)
from src.boom_tetris.polyomino.polyomino_generator import PolyominoGenerator
from src.boom_tetris.utils.utils_dict import DotDict, format_for_writing_to_yaml_file
from src.boom_tetris.utils.utils_other import get_window_size_from_screen_resolution

# YAML parser and serializer using ruamel.yaml.
# This instance allows reading and writing YAML files with indentation preserved.
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


class ConfigManager:
    """
    High-level configuration I/O and update pipeline for Boom Tetris.

    Responsibilities:
        - Load configuration files from disk.
        - Compute derived runtime parameters (board dimensions, polyomino shapes, etc.).
        - Serialize updated configuration to disk for runtime use.

    Key Concepts:
        - `config_source`: The editable, authoritative configuration loaded from
          the source YAML file (`CONFIG_SOURCE_FILE_PATH`). Validated against
          `ConfigModelSource`.
        - `config_runtime`: The derived runtime configuration validated against
          `ConfigModelRuntime`, including computed fields required for the
          game to run. NOT edited manually.

    Workflow:
        The main workflow of this class is executed via the `get_runtime_config` method.

        1. Loads the source config and validates it.
        2. Converts it to a `DotDict` for easier mutation and addition of
            computed fields (Pydantic models are immutable, so DotDict
            makes adding dynamic fields convenient).
        3. Computes board metrics, polyomino shapes, and other runtime parameters.
        4. Writes the derived configuration to the runtime YAML file.
        5. Reloads the runtime config and validates it as a `ConfigModelRuntime`.
        6. Adjusts certain field types (e.g., directions to `Position` tuples).

    Notes:
        - `load_config_without_validation` is public because other modules
          may need to load YAML data without converting it to a Pydantic model,
          e.g., for temporary or partial inspection, manipulation, or testing.
    """

    def __init__(self) -> None:
        """
        Initialisation of the `ConfigManager` class.

        Args:
            config_path (Path): Path to the configuration file.
        """
        self.config_source_file_path = CONFIG_SOURCE_FILE_PATH
        self.config_runtime_file_path = CONFIG_RUNTIME_FILE_PATH

    def load_config_without_validation(self, file_path: Path) -> DotDict:
        """
        Load a YAML configuration file as a mutable DotDict.

        This method reads a YAML file from disk and wraps its contents
        in a `DotDict` to allow convenient dot-access for keys.

        Args:
            file_path (Path): The path to the YAML file to load.

        Returns:
            DotDict: The contents of the YAML file as a mutable dictionary
                supporting attribute-style access.
        """
        with open(file_path) as file:
            return DotDict(yaml.load(file))

    def _load_source_config(self) -> ConfigModelSource:
        """
        Load the source configuration file and validate it against
        `ConfigModelSource`.

        Returns:
            ConfigModelSource: A validated configuration model representing
            the editable source configuration.

        Notes:
            This is the “authoritative” config that you can edit manually
            (`config.yaml`). It is converted to the Pydantic model to enforce
            schema and type safety.
        """
        data = self.load_config_without_validation(self.config_source_file_path)

        return ConfigModelSource(**data)

    def _load_runtime_config(self) -> ConfigModelRuntime:
        """
        Load the runtime configuration file and validate it against
        `ConfigModelRuntime`.

        Returns:
            ConfigModelRuntime: A validated configuration model ready for
                use in the game runtime, with all computed fields included.

        Notes:
            This configuration is typically derived from the source config
            via internal computations (board size, polyomino shapes, etc.).
            It should not be manually edited. Use this for all runtime
            operations.
        """
        data = self.load_config_without_validation(self.config_runtime_file_path)

        return ConfigModelRuntime(**data)

    def _add_window_resolution(self, config: DotDict) -> DotDict:
        """
        Resolve the pygame window dimensions from the current screen size.

        1. Call window_size_from_screen() to get the scaled desktop resolution.
        2. Write the resulting width and height into config.WINDOW.

        Args:
            config: Mutable dot-config with a WINDOW section.

        Returns:
            Same config with WINDOW.WIDTH and WINDOW.HEIGHT populated.
        """
        window_width, window_height = get_window_size_from_screen_resolution()

        config.WINDOW.WIDTH = window_width
        config.WINDOW.HEIGHT = window_height

        return config

    def _add_board_and_line_counter_fields(self, config: DotDict) -> DotDict:
        """
        Adds computed layout parameters to config.

        Computes board geometry in four phases. The core challenge is a
        chicken-and-egg problem: cell size depends on board size, but board
        size depends on the space reserved for UI elements like the line
        counter field, which is ideally expressed in terms of cell size.

        This is resolved by computing geometry twice via a scale_ratio,
        first for a board that fills all available space, then rescaling to
        fit the actual available space after accounting for UI elements. This
        works because all dimensions scale linearly, so the ratios remain
        correct regardless of the initial values.

        The four phases are:
        - Initial: base dimensions from window size and margin.
        - Hidden rows: rescale so that hidden rows sit above the visible
            area, allowing pieces to rotate at spawn without being visible.
        - Line counter: rescale again to reserve space for the line counter
            field above the board, maintaining square cells throughout.
        - Snap: round cell size to the nearest integer pixel, then recompute
            all dependent dimensions from that snapped value. This is required
            because pygame's Rect silently truncates float dimensions to
            integers on construction, which causes sub-pixel gaps to accumulate
            across rows and columns during rendering.

        Args:
            config: DotDict containing window and board configuration,
                including dimensions, margin ratio, and polyomino settings.

        Returns:
            The same config object with computed layout parameters added,
                including board rect, cell size, margin, and spawn positions.
        """
        # Computations.

        # Intitial computations.
        rows_total = config.BOARD.DIMENSIONS.ROWS + config.BOARD.DIMENSIONS.ROWS_HIDDEN
        window_horizontal_mid = config.WINDOW.WIDTH / 2
        margin = config.WINDOW.HEIGHT / config.WINDOW.RATIO_MARGIN_TO_WINDOW_HEIGHT
        unscaled_board_height = config.WINDOW.HEIGHT - (2 * margin)
        board_width = unscaled_board_height * config.BOARD.DIMENSIONS.COLS / rows_total
        board_left = window_horizontal_mid - board_width / 2
        board_top = margin
        cell_width = board_width / config.BOARD.DIMENSIONS.COLS
        cell_height = unscaled_board_height / rows_total

        # Computations so that we can block the hidden rows.
        scale_ratio = rows_total / config.BOARD.DIMENSIONS.ROWS
        cell_height *= scale_ratio
        cell_width *= scale_ratio
        board_top -= config.BOARD.DIMENSIONS.ROWS_HIDDEN * cell_height
        board_height = unscaled_board_height * scale_ratio
        board_width *= scale_ratio
        board_left = window_horizontal_mid - board_width / 2

        # Computations to add line counter field above the board.
        line_counter_height_in_cells = config.FIELDS.LINE_COUNTER.HEIGHT_CELLS
        line_counter_height = line_counter_height_in_cells * cell_height
        scale_ratio = (config.WINDOW.HEIGHT - 3 * margin) / (
            unscaled_board_height + line_counter_height_in_cells * cell_height
        )
        cell_height *= scale_ratio
        cell_width *= scale_ratio
        line_counter_height = line_counter_height_in_cells * cell_height
        board_height *= scale_ratio
        board_width *= scale_ratio
        board_left = window_horizontal_mid - board_width / 2
        board_top = (
            margin
            + line_counter_height
            + margin
            - (config.BOARD.DIMENSIONS.ROWS_HIDDEN * cell_height)
        )

        # Snap cell size to nearest integer and recompute all dependent dimensions.
        snap_ratio = round(cell_height) / cell_height
        cell_height = round(cell_height)
        cell_width = round(cell_width)
        board_height = rows_total * cell_height
        board_width = config.BOARD.DIMENSIONS.COLS * cell_width
        line_counter_height = round(line_counter_height * snap_ratio)
        margin = round(margin * snap_ratio)
        window_width = round(config.WINDOW.WIDTH * snap_ratio)
        window_height = round(config.WINDOW.HEIGHT * snap_ratio)
        board_left = round(window_width / 2 - board_width / 2)
        board_top = (
            margin
            + line_counter_height
            + margin
            - (config.BOARD.DIMENSIONS.ROWS_HIDDEN * cell_height)
        )

        # Line counter field
        line_counter_height = cell_height * config.FIELDS.LINE_COUNTER.HEIGHT_CELLS

        config.FIELDS.LINE_COUNTER.LEFT = board_left
        config.FIELDS.LINE_COUNTER.TOP = margin
        config.FIELDS.LINE_COUNTER.WIDTH = board_width
        config.FIELDS.LINE_COUNTER.HEIGHT = line_counter_height

        # Adding computed parameters back to config.
        config.WINDOW.MARGIN = margin
        config.WINDOW.WIDTH = window_width
        config.WINDOW.HEIGHT = window_height

        config.BOARD.DIMENSIONS.ROWS_TOTAL = rows_total

        config.BOARD.RECT = {
            "LEFT": board_left,
            "TOP": board_top,
            "WIDTH": board_width,
            "HEIGHT": board_height,
        }

        config.BOARD.CELL = {
            "WIDTH": cell_width,
            "HEIGHT": cell_height,
        }

        return config

    def _add_score_field(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for the score field.

        The score field sits to the right of the board, aligned with the top margin.

        1. Set LEFT to the right edge of the board plus one margin.
        2. Set TOP to the top margin.
        3. Derive WIDTH and HEIGHT from cell size and configured cell units.

        Args:
            config: Mutable dot-config with snapped board geometry.

        Returns:
            Same config with SCORE pixel geometry populated.
        """
        config.FIELDS.SCORE.LEFT = (
            config.BOARD.RECT.LEFT + config.BOARD.RECT.WIDTH + config.WINDOW.MARGIN
        )
        config.FIELDS.SCORE.TOP = config.WINDOW.MARGIN
        config.FIELDS.SCORE.WIDTH = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.SCORE.WIDTH_CELLS
        )
        config.FIELDS.SCORE.HEIGHT = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.SCORE.HEIGHT_CELLS
        )

        return config

    def _add_next_field(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for the next piece preview field.

        The next field sits to the right of the board, vertically centered
        on the board's midpoint.

        1. Derive pixel height from cell size and configured cell units.
        2. Set LEFT to the right edge of the board plus one margin.
        3. Set TOP so the field is vertically centered on the board.
        4. Derive WIDTH from cell size and configured cell units.

        Args:
            config: Mutable dot-config with snapped board geometry.

        Returns:
            Same config with NEXT pixel geometry populated.
        """
        next_height = config.FIELDS.NEXT.HEIGHT_CELLS * config.BOARD.CELL.HEIGHT

        config.FIELDS.NEXT.LEFT = (
            config.BOARD.RECT.LEFT + config.BOARD.RECT.WIDTH + config.WINDOW.MARGIN
        )
        config.FIELDS.NEXT.TOP = int(
            config.BOARD.RECT.TOP + config.BOARD.RECT.HEIGHT / 2 - next_height / 2
        )
        config.FIELDS.NEXT.WIDTH = (
            config.FIELDS.NEXT.WIDTH_CELLS * config.BOARD.CELL.HEIGHT
        )
        config.FIELDS.NEXT.HEIGHT = next_height

        return config

    def _add_level_field(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for the level field.

        The level field sits to the right of the board, directly below
        the next piece preview field.

        1. Set LEFT to the right edge of the board plus one margin.
        2. Set TOP to the bottom edge of the next field plus one margin.
        3. Derive WIDTH and HEIGHT from cell size and configured cell units.

        Args:
            config: Mutable dot-config with snapped board and next field geometry.

        Returns:
            Same config with LEVEL pixel geometry populated.
        """
        config.FIELDS.LEVEL.LEFT = (
            config.BOARD.RECT.LEFT + config.BOARD.RECT.WIDTH + config.WINDOW.MARGIN
        )
        config.FIELDS.LEVEL.TOP = (
            config.FIELDS.NEXT.TOP + config.FIELDS.NEXT.HEIGHT + config.WINDOW.MARGIN
        )
        config.FIELDS.LEVEL.WIDTH = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.LEVEL.WIDTH_CELLS
        )
        config.FIELDS.LEVEL.HEIGHT = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.LEVEL.HEIGHT_CELLS
        )

        return config

    def _add_statistics_field(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for the statistics field.

        The statistics field sits to the left of the board, aligned with
        the bottom edge of the board.

        1. Derive WIDTH and HEIGHT from cell size and configured cell units.
        2. Set LEFT to the left edge of the board minus one margin and field width.
        3. Set TOP so the field's bottom edge aligns with the board's bottom edge.

        Args:
            config: Mutable dot-config with snapped board geometry.

        Returns:
            Same config with STATISTICS pixel geometry populated.
        """
        statistics_width = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.STATISTICS.WIDTH_CELLS
        )
        statistics_height = (
            config.BOARD.CELL.HEIGHT * config.FIELDS.STATISTICS.HEIGHT_CELLS
        )

        config.FIELDS.STATISTICS.LEFT = (
            config.BOARD.RECT.LEFT - config.WINDOW.MARGIN - statistics_width
        )
        config.FIELDS.STATISTICS.TOP = (
            config.BOARD.RECT.TOP + config.BOARD.RECT.HEIGHT - statistics_height
        )
        config.FIELDS.STATISTICS.WIDTH = statistics_width
        config.FIELDS.STATISTICS.HEIGHT = statistics_height

        return config

    def _add_type_field(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for the type field.

        The type field sits to the left of the board, horizontally centered
        on the statistics field and vertically centered on the line counter field.

        1. Derive WIDTH and HEIGHT from cell size and configured cell units.
        2. Set LEFT so the field is horizontally centered on the statistics field.
        3. Set TOP so the field is vertically centered on the line counter field.

        Args:
            config: Mutable dot-config with snapped board, statistics, and
                line counter geometry.

        Returns:
            Same config with TYPE pixel geometry populated.
        """
        type_width = config.BOARD.CELL.HEIGHT * config.FIELDS.TYPE.WIDTH_CELLS
        type_height = config.BOARD.CELL.HEIGHT * config.FIELDS.TYPE.HEIGHT_CELLS

        config.FIELDS.TYPE.LEFT = int(
            config.FIELDS.STATISTICS.LEFT
            + config.FIELDS.STATISTICS.WIDTH / 2
            - type_width / 2
        )
        config.FIELDS.TYPE.TOP = int(
            config.FIELDS.LINE_COUNTER.TOP + config.FIELDS.LINE_COUNTER.HEIGHT / 2
        )
        config.FIELDS.TYPE.WIDTH = type_width
        config.FIELDS.TYPE.HEIGHT = type_height

        return config

    def _add_all_remaining_fields(self, config: DotDict) -> DotDict:
        """
        Compute and store pixel geometry for all UI fields except the tetris
        board and the line counter field, because those were already added.

        Fields must be added in dependency order, as some fields derive their
        position from previously computed fields.

        1. Add score field to the right of the board.
        2. Add next piece preview field to the right of the board.
        3. Add level field below the next piece preview field.
        4. Add statistics field to the left of the board.
        5. Add type field centered on the statistics and line counter fields.

        Args:
            config: Mutable dot-config with snapped board geometry.

        Returns:
            Same config with all remaining field pixel geometries populated.
        """
        updated_config = self._add_score_field(config=config)
        updated_config = self._add_next_field(config=updated_config)
        updated_config = self._add_level_field(config=updated_config)
        updated_config = self._add_statistics_field(config=updated_config)
        updated_config = self._add_type_field(config=updated_config)

        return updated_config

    def _add_polyomino_spawn_positions(self, config: DotDict) -> DotDict:
        """
        Compute and store polyomino spawn positions in grid coordinates.

        1. Set active piece spawn at horizontal centre, just inside hidden rows.
        2. Set next piece preview spawn to the right of the board.

        Args:
            config: Mutable dot-config with snapped board dimensions.

        Returns:
            Same config with SPAWN_POSITION and SPAWN_POSITION_NEXT populated.
        """
        # Add other parameters.
        config.POLYOMINO.SPAWN_POSITION = [
            config.BOARD.DIMENSIONS.COLS // 2,
            config.BOARD.DIMENSIONS.ROWS_HIDDEN,
        ]
        config.POLYOMINO.SPAWN_POSITION_NEXT = [
            config.BOARD.DIMENSIONS.COLS + 3,
            config.BOARD.DIMENSIONS.ROWS_HIDDEN + 1,
        ]

        return config

    def _add_all_polyonomios(self, config: DotDict) -> DotDict:
        """
        Generate all free polyomino shapes and attach ``ALL_SHAPES``.

        Args:
            config: Mutable dot-config with ``POLYOMINO.SIZE`` and directions.

        Returns:
            Same ``config`` with ``POLYOMINO.ALL_SHAPES`` populated.
        """
        # Exclude `rotations` from `directions`.
        directions = {
            key: value
            for key, value in config.DIRECTIONS.items()
            if isinstance(value, list)
        }

        polyomino_generator = PolyominoGenerator(
            number_of_polyomino_cells=config.POLYOMINO.SIZE, directions=directions
        )

        unique_coordinates = polyomino_generator.generate()

        config.POLYOMINO.ALL_SHAPES = [
            [[x, y] for (x, y) in shape] for shape in unique_coordinates
        ]

        return config

    def _change_data_types(self, config: ConfigModelRuntime) -> ConfigModelRuntime:
        """
        Replace direction lists with ``Position`` named tuples.

        Args:
            config: Validated model loaded after update.

        Returns:
            A copy with updated ``DIRECTIONS`` field types.
        """
        new_directions = config.DIRECTIONS.model_copy(
            update={
                "UP": Position(*config.DIRECTIONS.UP),
                "DOWN": Position(*config.DIRECTIONS.DOWN),
                "LEFT": Position(*config.DIRECTIONS.LEFT),
                "RIGHT": Position(*config.DIRECTIONS.RIGHT),
            }
        )

        config = config.model_copy(update={"DIRECTIONS": new_directions})

        return config

    def _write_config(self, file_path: Path, config: DotDict) -> None:
        """
        Serialize dot-config to YAML with ruamel formatting.

        Args:
            file_path: Output path for the YAML file.
            config: Dot-access configuration to dump.
        """
        config_dict = config.to_dict()
        config_dict_formatted = format_for_writing_to_yaml_file(obj=config_dict)

        with open(file_path, "w") as file:
            yaml.dump(config_dict_formatted, file)

    def get_runtime_config(self) -> ConfigModelRuntime:
        """
        Compute board metrics, shapes, write YAML, reload, and fix types.

        Args:
            config: Base validated model from the main config file.ConfigModelRuntime

        Returns:
            Final ``ConfigModel`` ready for the game (with ``Position`` dirs).
        """
        # Load and validate source configuration file.
        config_source = self._load_source_config()

        # Convert from Pydantic Basemodel to dictionary and then to DotDict
        # instance, to keep using dot notation for dictionary keys and values.
        config_source = DotDict(config_source.model_dump())

        # Add computational parameters.
        updated_config = self._add_window_resolution(config=config_source)
        updated_config = self._add_board_and_line_counter_fields(config=updated_config)
        updated_config = self._add_all_remaining_fields(config=updated_config)
        updated_config = self._add_polyomino_spawn_positions(config=updated_config)
        updated_config = self._add_all_polyonomios(config=updated_config)

        # Write the updated configurationt to disk.
        self._write_config(file_path=CONFIG_RUNTIME_FILE_PATH, config=updated_config)

        # Validate updated configuration file. These settings will be used during runtime.
        config_runtime = self._load_runtime_config()

        # Change the data types of certain parameters.
        config_runtime = self._change_data_types(config=config_runtime)

        return config_runtime
