from typing import Sequence, Optional, Iterable, Callable

import numpy as np
import random

from minesweeper import logutils
from minesweeper.board import HiddenBoardState, neighbors
from minesweeper import register_agent
from minesweeper.actions import Action
from minesweeper import Agent
from minesweeper.utils import TickRepeater

__all__ = ['RulesBasedAgent']

log = logutils.get_logger('game.agent.strategic')


def superchord_once(state: HiddenBoardState):
    # which cells are open
    open_layout = ~state.openable_layout & ~state.flag_layout
    
    # number of adjacent known mines for each cell
    known_neighbors = neighbors(state.flag_layout)
    
    # positions for which it is okay to open all adjacent cells
    openable_adjacent_cells = (known_neighbors == state.proximity_matrix) & open_layout
    
    # cells that are adjacent to at least one cell that is "complete" (has known neighbors == neighbors)
    openable_cells = (neighbors(openable_adjacent_cells) > 0) & state.openable_layout
    
    # open cells
    return [Action.select(tuple(pos)) for pos in np.argwhere(openable_cells)]


def flag_all_obvious(state: HiddenBoardState):
    available_neighbors = neighbors(state.openable_layout | state.flag_layout)
    
    # cells with "complete information," i.e. know as many neighbors as there are supposed to be
    openable_adjacent_cells = available_neighbors == state.proximity_matrix
    
    # cells that are next to cells with "complete information"
    openable_cells = (neighbors(openable_adjacent_cells) > 0) & ~state.flag_layout & state.openable_layout

    # flag cells
    return [Action.flag(tuple(pos)) for pos in np.argwhere(openable_cells & ~state.flag_layout)]


def handle_adjoints(state: HiddenBoardState):
    # remaining neighbors for each cell
    remaining_neighbors = state.proximity_matrix - neighbors(state.flag_layout)
    
    return []


def make_random_decision(state: HiddenBoardState):
    # find ambiguous spots
    
    # open single, highest probability cell
    
    return []


def choose_random(state: HiddenBoardState):
    openable_pos = np.argwhere(state.openable_layout)
    cell_pos = openable_pos[random.randint(0, openable_pos.shape[0]) - 1]
    return [Action.select(tuple(cell_pos))]


@register_agent('strategic')
class RulesBasedAgent(Agent):
    def __init__(self):
        self._tick: Optional[TickRepeater] = None
        self.rules: Sequence[Callable[[HiddenBoardState], Iterable[Action]]] = [
            flag_all_obvious,
            superchord_once,
            handle_adjoints,
            make_random_decision,
            # choose_random
        ]
    
    def start(self, grid_size, config):
        self._tick = TickRepeater(400, 1000, time_based=True)

    def act(self, state: HiddenBoardState) -> Sequence[Action]:
        actions = []
        
        if self._tick.tick():
            for rule in self.rules:
                actions.extend(rule(state))
                if len(actions) != 0:
                    log.debug(f'Applying rule: {rule.__name__}')
                    break
            
        return actions

    def react(self, state: HiddenBoardState, status):
        pass

