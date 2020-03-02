from .actions import Action, ActionType

from .agent import Agent

VERSION = 'Deep Minesweeper 0.0.1'

AGENT_REGISTRY = {}


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
