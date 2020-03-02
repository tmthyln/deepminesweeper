import argparse

import minesweeper

from minesweeper.agents import RandomAgent
from minesweeper.game import GameWindow

from typing import Union


def get_args():
    parser = argparse.ArgumentParser('Minesweeper')
    
    parser.add_argument('--version', action='version', version=minesweeper.VERSION)
    
    resources = parser.add_argument_group('resources')
    resources.add_argument('--res-dir', default='res',
                           metavar='RESOURCE_DIRECTORY',
                           help='root directory for all resources')
    resources.add_argument('--favicon-file', default='favicon.png',
                           metavar='FILENAME')
    resources.add_argument('--hidden-cell-file', default='hidden_cell.png',
                           metavar='FILENAME')
    resources.add_argument('--open-cell-file', default='open_cell.png',
                           metavar='FILENAME')
    
    aesthetic = parser.add_argument_group('aesthetic and appearance')
    aesthetic.add_argument('--window-title', default='Minesweeper')
    aesthetic.add_argument('--bg-color', type=int, nargs=3, default=(0, 120, 0),
                           metavar=('R', 'G', 'B'))
    
    windowing = parser.add_argument_group('windowing and sizing')
    windowing.add_argument('--window-size', type=int, nargs=2, default=(1280, 780),
                           metavar=('WIDTH', 'HEIGHT'))
    windowing.add_argument('--cell-size', type=int, nargs=2, default=(32, 32),
                           metavar=('WIDTH', 'HEIGHT'))
    windowing.add_argument('--fps', type=int, default=60)
    
    gameplay = parser.add_argument_group('game play')
    gameplay.add_argument('--good-first-select', action='store_true',
                          help='guarantee that the first select will be on an empty cell (no neighbors)')
    gameplay.add_argument('--end-on-first-mine', default=True,
                          help='whether to end a game on the first mine selected (see also: forgiveness)')
    gameplay.add_argument('--forgiveness', type=Union[int, float], default=5,
                          metavar='MINES',
                          help='number of mines to allow before ending the game, if not ending on first mine')
    gameplay.add_argument('--use-agent', default=None, choices=minesweeper.AGENT_REGISTRY.keys())
    gameplay.add_argument('--shape', default='square', choices=['square'],  # TODO support other shapes?
                          help='shape of the cell')
    
    controls = parser.add_argument_group('controls')
    controls.add_argument('--double-click-time', type=int, default=400,
                          metavar='TIME_MS')
    controls.add_argument('--click-to-flag', default=True)
    controls.add_argument('--use-super-chord', action='store_true')
    
    logs = parser.add_argument_group('logging')
    logs.add_argument('--log-dir', default='runs',
                      metavar='LOG_DIRECTORY',
                      help='root directory for all log files created')
    logs.add_argument('--save-board-runs', default=True,  # TODO eventually default to False, make store_true
                      help='whether to save the board configurations for each game played')
    
    args = parser.parse_args()
    
    return args


def start_game(config):
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
    start_game(get_args())
