from typing import Sequence, Optional, Iterable, Callable, Set

import numpy as np
import random

from minesweeper import logutils
from minesweeper.board import HiddenBoardState, neighbors, adjacents
from minesweeper import register_agent
from minesweeper.actions import Action
from minesweeper import Agent
from minesweeper.utils import TickRepeater

__all__ = ['RulesBasedAgent']

log = logutils.get_logger('game.agent.strategic')


def superchord_once(state: HiddenBoardState):
    # number of adjacent known mines for each cell
    known_neighbors = neighbors(state.flagged)
    
    # positions for which it is okay to open all adjacent cells
    openable_adjacent_cells = (known_neighbors == state.proximity) & state.open
    
    # cells that are adjacent to at least one cell that is "complete" (has known neighbors == neighbors)
    openable_cells = (neighbors(openable_adjacent_cells) > 0) & state.openable
    
    # open cells
    return [Action.select(tuple(pos)) for pos in np.argwhere(openable_cells)]


def flag_all_obvious(state: HiddenBoardState):
    available_neighbors = neighbors(state.openable | state.flagged)
    
    # cells with "complete information," i.e. know as many neighbors as there are supposed to be
    openable_adjacent_cells = available_neighbors == state.proximity
    
    # cells that are next to cells with "complete information"
    openable_cells = (neighbors(openable_adjacent_cells) > 0) & ~state.flagged & state.openable

    # flag cells
    return [Action.flag(tuple(pos)) for pos in np.argwhere(openable_cells & ~state.flagged)]


def handle_adjoints(state: HiddenBoardState):
    # remaining neighbors for each cell
    remaining_neighbors = state.proximity - neighbors(state.flagged)
    
    # neighbors sets
    numbered_cells = np.argwhere(state.proximity > 0)
    
    neighbor_sets = np.empty(state.size, dtype=frozenset)
    for pos in np.ndindex(state.size):
        neighbor_sets[pos] = frozenset(
                adj_pos for adj_pos in adjacents(pos, state.size) if state.openable[adj_pos])
    
    flag_pos = []
    open_pos = []
    
    for pos1 in numbered_cells:
        for pos2 in adjacents(pos1, state.size):
            pos1 = tuple(pos1)
            pos2 = tuple(pos2)

            if remaining_neighbors[pos1] == 0 or remaining_neighbors[pos2] == 0:
                continue
            if pos2 not in numbered_cells:
                continue
            
            shared = neighbor_sets[pos1] & neighbor_sets[pos2]
            pos1_disjoint = neighbor_sets[pos1] - shared
            pos2_disjoint = neighbor_sets[pos2] - shared
            
            # shared can have at most the min number of mines, disjoints may be saturated
            shared_max = min(remaining_neighbors[pos1], remaining_neighbors[pos2])
            
            if remaining_neighbors[pos1] - shared_max == len(pos1_disjoint):
                flag_pos.extend(pos1_disjoint)
            if remaining_neighbors[pos2] - shared_max == len(pos2_disjoint):
                flag_pos.extend(pos2_disjoint)
            
    return [Action.flag(pos) for pos in flag_pos if state.openable[pos]] + [Action.select(pos) for pos in open_pos]


def make_random_decision(state: HiddenBoardState):
    # find ambiguous spots
    
    # open single, highest probability cell
    
    return []


def choose_random(state: HiddenBoardState):
    openable_pos = np.argwhere(state.openable)
    cell_pos = openable_pos[random.randint(0, openable_pos.shape[0]) - 1]
    return [Action.select(tuple(cell_pos))]


@register_agent('strategic')
class RulesBasedAgent(Agent):
    def __init__(self):
        self._tick: Optional[TickRepeater] = None
        self.rules: Sequence[Callable[[HiddenBoardState], Iterable[Action]]] = [
            flag_all_obvious,
            superchord_once,
            # handle_adjoints,
            # make_random_decision,
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


class Conjunction(tuple):
    pass


class Disjunction(tuple):
    pass


def distribute(a, b):
    pass


class LogicGate:
    
    def __init__(self, state: HiddenBoardState):
        self.global_conjunctives: Set[Disjunction] = set()

        remaining_neighbors = state.proximity - neighbors(state.flagged)
        
        for pos in np.ndindex(state.size):
            k = remaining_neighbors[pos]
            
            # (openable neighbors) choose (remaining neighbors) number of choices
            pass


@register_agent('logical')
class LogicAgent(Agent):
    
    def __init__(self):
        self._tick: Optional[TickRepeater] = None
    
    def start(self, grid_size, config):
        self._tick = TickRepeater(400, 1000, time_based=True)
    
    def act(self, state: HiddenBoardState) -> Sequence[Action]:
        if self._tick.tick():
            pass
    
    def react(self, state: HiddenBoardState, status):
        pass
