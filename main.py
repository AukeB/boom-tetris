"""Entry point: load config, update it, then run the game loop."""

from src.boom_tetris.config.config_manager import ConfigManager


def main() -> None:
    """Load config, update it, and run the loop until the user quits."""
    config_manager = ConfigManager()
    config_runtime = config_manager.get_runtime_config()

    # The 'Game' class can only be imported after the `get_runtime_config` method
    # from the 'Config' class has been executed, as it generates a .yaml
    # file that is immediatly loaded.
    from src.boom_tetris.game import Game

    game = Game(config=config_runtime)

    while game.update():
        pass


if __name__ == "__main__":
    main()