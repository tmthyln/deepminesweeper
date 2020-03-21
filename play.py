import minesweeper
from minesweeper.game import Game
from minesweeper.config import Config


def start_game():
    config = Config
    config.update_from_args()
    
    game = Game(config)
    game.run(agent=minesweeper.AGENT_REGISTRY[config.agent]() if config.agent else None)


if __name__ == '__main__':
    start_game()
