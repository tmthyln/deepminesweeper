import minesweeper
from minesweeper.game import GameWindow
from minesweeper.config import DefaultConfig


def start_game():
    config = DefaultConfig
    config.update_from_args()
    
    window = GameWindow(config)
    
    if config.agent:
        agent = minesweeper.AGENT_REGISTRY[config.agent]()
        agent.start(window._grid.size, config)
        
        # run simulation
        for last_state, _ in (game_runner := window.run()):
            agent_actions = agent.act(last_state)
            
            last_state, status = game_runner.send(agent_actions)
            # TODO change yielding to 2-part
            if len(agent_actions) > 0:
                agent.react(last_state, status)
    else:
        for _ in window.run():
            continue


if __name__ == '__main__':
    start_game()
