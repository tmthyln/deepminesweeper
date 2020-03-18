
import numpy as np
import random

from minesweeper.board import HiddenBoardState
from minesweeper import register_agent
from minesweeper.actions import Action
from minesweeper import Agent
from minesweeper.utils import TickRepeater

from typing import Sequence


################################################################################
#                                 Basic Agents                                 #
################################################################################

@register_agent(name='random')
class RandomAgent(Agent):
    """
    A baseline agent that randomly selects a non-open cell until all cells are open.
    """
    
    __slots__ = ['_ticker']
    
    def start(self, grid_size, config):
        self._ticker = TickRepeater(1000, 2000, time_based=True)
    
    def act(self, state: HiddenBoardState) -> Sequence[Action]:
        possible_coords = np.argwhere(state.openable_layout)
        
        if possible_coords.size > 0 and self._ticker.tick():
            index = tuple(possible_coords[random.randint(0, len(possible_coords) - 1)])
            return [Action.select(index)]
        else:
            return []
    
    def react(self, state: HiddenBoardState, status):
        pass
