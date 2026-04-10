"""Load YAML config, update with computed fields, and write derived files."""

from pathlib import Path
from ruamel.yaml import YAML

from src.boom_tetris.utils.utils_dict import DotDict
from src.boom_tetris.config.config_model_source import ConfigModelSource
from src.boom_tetris.config.config_model_runtime import ConfigModelRuntime
from src.boom_tetris.polyomino.polyomino_generator import PolyominoGenerator

from src.boom_tetris.constants import (
    Position,
    CONFIG_SOURCE_FILE_PATH,
    CONFIG_RUNTIME_FILE_PATH,
)

from src.boom_tetris.utils.utils_other import get_window_size_from_screen_resolution
from src.boom_tetris.utils.utils_dict import format_for_writing_to_yaml_file


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

    def _add_computational_parameters(self, config: DotDict) -> DotDict:
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
        board_width = unscaled_board_height * (
            config.BOARD.DIMENSIONS.COLS / rows_total
        )
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
        line_counter_height = 2 * cell_height
        scale_ratio = (
            config.WINDOW.HEIGHT - (2 * margin) - line_counter_height - margin
        ) / unscaled_board_height
        cell_height *= scale_ratio
        cell_width *= scale_ratio
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
        updated_config = self._add_computational_parameters(config=updated_config)
        updated_config = self._add_all_polyonomios(config=updated_config)

        # Write the updated configurationt to disk.
        self._write_config(file_path=CONFIG_RUNTIME_FILE_PATH, config=updated_config)

        # Validate updated configuration file. These settings will be used during runtime.
        config_runtime = self._load_runtime_config()

        # Change the data types of certain parameters.
        config_runtime = self._change_data_types(config=config_runtime)

        return config_runtime
