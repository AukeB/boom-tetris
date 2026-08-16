"""Entry point: load config, update it, then run the game loop."""

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.game import Game


def main() -> None:
    """Load config, update it, and run the loop until the user quits."""
    config_manager = ConfigManager()
    config_runtime = config_manager.get_runtime_config()
    
    game = Game(config=config_runtime)

    while game.update():
        pass


if __name__ == "__main__":
    main()