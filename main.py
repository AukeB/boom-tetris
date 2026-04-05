"""Entry point: load config, augment it, then run the game loop."""

from src.boom_tetris.config.config_manager import ConfigManager
from src.boom_tetris.constants import MAIN_CONFIG_RELATIVE_FILE_PATH


def main() -> None:
    """Load config, augment it, and run the loop until the user quits."""
    config_main = ConfigManager.load_config(file_path=MAIN_CONFIG_RELATIVE_FILE_PATH)

    config_instance = ConfigManager(config_path=MAIN_CONFIG_RELATIVE_FILE_PATH)
    config_updated = config_instance.update_config(config=config_main)

    # The 'Game' class can only be imported after the `update_config` from
    # the 'Config' class has been executed, because it generates a .yaml
    # file that is immediatly loaded.
    from src.boom_tetris.game import Game

    game = Game(config=config_updated)

    while game.update():
        pass


if __name__ == "__main__":
    main()


"""
Todo:

- Directions naar config (inclusief up, down, up, down)                     DONE
- Reverse all y,x coordinates back to x,y                                   DONE
- Replace yaml with more elaborate yaml package                             DONE
- Class van polyomino/utils.py maken genaamd PolynomioTransformer           DONE
    Bedoeld voor postprocessing de polyomino's na de generation             DONE
- Fix all rotaties voor tetromino's                                         DONE
    Inclusief geen rotatie voor O-piece                                     DONE
    En manually defined rotations voor I, Z and S-piece.                    DONE
- Fixen Pydantic parameters meegeven die niet in BaseModel staat            DONE
- Board size computen gebaseerd op window size                              DONE
- Implement grid_lines                                                      DONE
- Juiste rotaties alle tetrominos implementeren                             DONE
- Juiste spawn positions fixen voor alle tetrominos                         DONE
    Block namedtuple uit code halen                                         DONE
- Hidden rows toevoegen                                                     DONE
- Board resizen met hidden rows en hidden rows blokkeren                    DONE
- New line toevoegen met ruamel package na elke level1 dict item            DONE
- PolyominoTranformer class optimaliseren
- Bug fixen met kleine ruimte over als board_size 30 rows heeft



    
- MyPy toevoegen
    - Template repo updaten
- Blok met tijd om laag laten vallen
- DAS implementeren

Backlog:

- Ook pentomino mapping maken op dezelfde manier is tetromino mapping       
"""