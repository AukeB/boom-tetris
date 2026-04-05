"""Load YAML config, augment with computed fields, and write derived files."""

from pathlib import Path
from ruamel.yaml import YAML

from src.boom_tetris.config.config_model import ConfigModel
from src.boom_tetris.utils.screen_utils import get_window_size_from_screen_resolution
from src.boom_tetris.polyomino.polyomino_generator import PolyominoGenerator
from src.boom_tetris.utils.dict_utils import DotDict, format_for_writing_to_yaml_file
from src.boom_tetris.constants import MAIN_CONFIG_UPDATED_RELATIVE_FILE_PATH, Position

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


class ConfigManager:
    """High-level configuration I/O and augmentation pipeline."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    @staticmethod
    def load_config(
        file_path: Path, validate: bool = True, file_type: str = "yaml"
    ) -> ConfigModel | DotDict:
        """Load a configuration file from disk.

        Args:
            file_path: Path to the YAML file.
            validate: If True, return a ``ConfigModel``; else a ``DotDict``.
            file_type: Format identifier; only ``yaml`` is implemented.

        Returns:
            Parsed configuration as ``ConfigModel`` or ``DotDict``.
        """
        if file_type == "yaml":
            with open(file_path) as file:
                config = yaml.load(file)

            if validate:
                config = ConfigModel(**config)
            else:
                config = DotDict(config)

        return config

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
        Computations:

        - Total number of rows on board, there are a couple of hidden
            rows to make sure pieces can rotate right at the spawn
            location.
        - Board size (left, top, width, height), based on the window
            size (width, height and margin).
        - Cell width and height, based on the board width and height and
            the number of cells the board consists of (default values
            are 20 rows and 10 columns).
        """

        # Computations.
        rows_total = config.BOARD.DIMENSIONS.ROWS + config.BOARD.DIMENSIONS.ROWS_HIDDEN

        window_horizontal_mid = config.WINDOW.WIDTH / 2
        board_height = config.WINDOW.HEIGHT - (2 * config.WINDOW.MARGIN)
        board_width = board_height * (config.BOARD.DIMENSIONS.COLS / rows_total)
        board_left = window_horizontal_mid - board_width / 2
        board_top = config.WINDOW.MARGIN

        cell_width = board_width / config.BOARD.DIMENSIONS.COLS
        cell_height = board_height / rows_total

        # Computations so that we can block the hidden rows.
        scale_ratio = rows_total / config.BOARD.DIMENSIONS.ROWS

        cell_height *= scale_ratio
        cell_width *= scale_ratio

        board_top -= config.BOARD.DIMENSIONS.ROWS_HIDDEN * cell_height
        board_height *= scale_ratio
        board_width *= scale_ratio
        board_left = window_horizontal_mid - board_width / 2

        # Adding computed parameters back to config.
        config.BOARD.DIMENSIONS.ROWS_TOTAL = rows_total

        config.BOARD.RECT = {
            "LEFT": board_left,
            "TOP": board_top,
            "WIDTH": board_width,
            "HEIGHT": board_height,
        }

        config.BOARD.CELL = {"WIDTH": cell_width, "HEIGHT": cell_height}

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
        """Generate all free polyomino shapes and attach ``ALL_SHAPES``.

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

    def _change_data_types(self, config: ConfigModel) -> ConfigModel:
        """Replace direction lists with ``Position`` named tuples.

        Args:
            config: Validated model loaded after augmentation.

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
        """Serialize dot-config to YAML with ruamel formatting.

        Args:
            file_path: Output path for the YAML file.
            config: Dot-access configuration to dump.
        """
        config_dict = config.to_dict()
        config_dict_formatted = format_for_writing_to_yaml_file(obj=config_dict)

        with open(file_path, "w") as file:
            yaml.dump(config_dict_formatted, file)

    def augment_config(self, config: ConfigModel | DotDict) -> ConfigModel:
        """Compute board metrics, shapes, write YAML, reload, and fix types.

        Args:
            config: Base validated model from the main config file.

        Returns:
            Final ``ConfigModel`` ready for the game (with ``Position`` dirs).
        """
        # Convert from Pydantic Basemodel to dictionary and then to DotDict
        # instance, to keep using dot notation for dictionary keys and values.
        config = DotDict(config.model_dump())

        updated_config = self._add_window_resolution(config=config)
        updated_config = self._add_computational_parameters(config=config)
        updated_config = self._add_all_polyonomios(config=config)

        self._write_config(
            file_path=MAIN_CONFIG_UPDATED_RELATIVE_FILE_PATH, config=updated_config
        )

        updated_config = ConfigManager.load_config(
            file_path=MAIN_CONFIG_UPDATED_RELATIVE_FILE_PATH
        )
        assert isinstance(updated_config, ConfigModel)

        updated_config = self._change_data_types(config=updated_config)

        return updated_config
