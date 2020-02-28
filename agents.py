from abc import abstractmethod, ABC

import numpy as np
import random

from actions import Action
from utils import TickRepeater

from typing import Sequence


class Agent(ABC):
    
    @abstractmethod
    def start(self, grid_size, config):
        pass
    
    @abstractmethod
    def act(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray) -> Sequence[Action]:
        pass
    
    @abstractmethod
    def react(self, reward):
        pass


################################################################################
#                                 Basic Agents                                 #
################################################################################

class RandomAgent(Agent):

    def start(self, grid_size, config):
        self._ticker = TickRepeater(200, 60)

    def act(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray) -> Sequence[Action]:
        possible_coords = np.argwhere(openable_matrix)
        
        if possible_coords.size > 0 and self._ticker.tick():
            index = tuple(possible_coords[random.randint(0, len(possible_coords) - 1)])
            return [Action.select(index)]
        else:
            return []
    
    def react(self, reward):
        pass
