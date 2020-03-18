from .board import Board
from .agent import Agent

VERSION = 'Deep Minesweeper 0.0.1'

BOARD_REGISTRY = {}
AGENT_REGISTRY = {}


def register_board(name, grid_cls):
    """Decorator to register a new board & grid pair."""
    
    def register_board_class(cls):
        if name in BOARD_REGISTRY:
            raise ValueError(f'Cannot register duplicate board {name}')
        if not issubclass(cls, Board):
            raise ValueError(f'Board {name} ({cls.__name__} class) must extend Board')
        BOARD_REGISTRY[name] = (cls, grid_cls)
        return cls
    
    return register_board_class


def register_agent(name):
    """Decorator to register a new agent."""
    
    def register_agent_class(cls):
        if name in AGENT_REGISTRY:
            raise ValueError(f'Cannot register duplicate agent {name}')
        if not issubclass(cls, Agent):
            raise ValueError(f'Agent {name} ({cls.__name__} class) must extend Agent')
        AGENT_REGISTRY[name] = cls
        return cls
    
    return register_agent_class


from .actions import Action, ActionType
from minesweeper.agents import *