import minesweeper
from minesweeper.game import GameWindow, Game
from minesweeper.config import Config


def start_game():
    config = Config
    config.update_from_args()
    
    game = Game(config)
    
    if config.agent:
        agent = minesweeper.AGENT_REGISTRY[config.agent]()
        agent.start(game.game_window.grid.size, config)
        
        # run simulation
        for last_state, _ in (game_runner := game.run()):
            agent_actions = agent.act(last_state)
            
            last_state, status = game_runner.send(agent_actions)
            # TODO change yielding to 2-part
            if len(agent_actions) > 0:
                agent.react(last_state, status)
    else:
        for _ in game.run():
            continue


if __name__ == '__main__':
    start_game()
