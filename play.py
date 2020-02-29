from minesweeper.agents import RandomAgent
from minesweeper.game import GameWindow, Config


def start_game():
    config = Config()
    window = GameWindow(config)
    
    if config.use_agent:
        agent = RandomAgent()
        agent.start(window.grid.grid_size, config)
        
        # run simulation
        for openable_layout, proximity_matrix, _ in (game_runner := window.run()):
            agent_actions = agent.act(openable_layout, proximity_matrix)
            
            openable_layout, proximity_matrix, status = game_runner.send(agent_actions)
            if len(agent_actions) > 0:
                agent.react(openable_layout, proximity_matrix, status)
    else:
        for _ in window.run():
            continue


if __name__ == '__main__':
    start_game()
