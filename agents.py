from abc import abstractmethod, ABC

import numpy as np
import random

from actions import Action
from utils import TickRepeater

from typing import Sequence


class Agent(ABC):
    """
    Abstract class representing an actor-agent for a Minesweeper game.
    
    Game Simulation:
        start() will be called once to initialize the game board
        act() will be called with the next board configuration and must return a (non-None) sequence of actions to take
        react() will be called after the agent's actions have been taken and feedback is given to the agent
        
        Note: react() will (should) only be called if act() returned a non-trivial sequence of actions
    """
    
    @abstractmethod
    def start(self, grid_size, config):
        """
        The agent performs initialization work at the start of the game, which can be dependent on the grid size and
        the configuration parameters of the game. (See config.py for more details on possible configs.)
        
        :param grid_size: size of the board, in cells (not pixels)
        :param config: game or agent config
        """
        pass
    
    @abstractmethod
    def act(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray) -> Sequence[Action]:
        """
        The agent acts on the game state and returns actions to take on the board.
        
        :param openable_matrix: binary matrix with ones wherever a cell is not open, zeros elsewhere
        :param proximity_matrix: for open cells, matrix representing the number of neighboring mines
        :return: sequence of actions to take on the board
        """
        pass
    
    @abstractmethod
    def react(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray, status):
        """
        The agent reacts to the result of their actions on the board based on the new board state (and any saved
        state) and the status indicators.
        
        :param openable_matrix: binary matrix with ones wherever a cell is not open, zeros elsewhere
        :param proximity_matrix: for open cells, matrix representing the number of neighboring mines
        :param status: status indicators for the game and board
        """
        pass


################################################################################
#                                 Basic Agents                                 #
################################################################################

class RandomAgent(Agent):
    """
    A baseline agent that randomly selects a non-open cell until all cells are open.
    """

    def start(self, grid_size, config):
        self._ticker = TickRepeater(10, 60)

    def act(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray) -> Sequence[Action]:
        possible_coords = np.argwhere(openable_matrix)
        
        if possible_coords.size > 0 and self._ticker.tick():
            index = tuple(possible_coords[random.randint(0, len(possible_coords) - 1)])
            return [Action.select(index)]
        else:
            return []

    def react(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray, status):
        pass
