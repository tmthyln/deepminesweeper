from typing import Sequence

import numpy as np

from minesweeper import register_agent
from minesweeper.actions import Action
from minesweeper import Agent
from minesweeper.utils import TickRepeater


@register_agent('RulesBasedAgent')
class RulesBasedAgent(Agent):
    def start(self, grid_size, config):
        pass

    def act(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray) -> Sequence[Action]:
        pass

    def react(self, openable_matrix: np.ndarray, proximity_matrix: np.ndarray, status):
        pass

