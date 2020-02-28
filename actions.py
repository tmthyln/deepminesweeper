from abc import ABC
from enum import Enum


class ActionType(Enum):
    """
    Enumeration of Action types.
    """
    
    SELECT = (1, True)
    FLAG = (2, True)
    CHORD = (3, True)
    SUPERCHORD = (4, True)
    SURRENDER = (5, False)
    
    def __repr__(self):
        if self is ActionType.SELECT:
            base = 'Select cell at'
        elif self is ActionType.FLAG:
            base = 'Flag cell at'
        elif self is ActionType.CHORD:
            base = 'Chord starting with cell at'
        elif self is ActionType.SUPERCHORD:
            base = 'Superchord starting with cell at'
        elif self is ActionType.SURRENDER:
            base = 'Surrender'
        else:
            base = 'Unknown action'
        
        return base
    
    @property
    def has_pos(self):
        return self.value[1]


class Action(ABC):
    """
    Class representing an action to be taken on a Minesweeper game board. While a constructor is available,
    the factory methods (Action.select(), Action.flag(), ...) are preferred.
    """
    
    def __init__(self, action_type: ActionType, pos: (int, int) = (-1, -1)):
        if action_type.has_pos and pos == (-1, -1):
            raise ValueError('Certain action types require the pos(ition) argument')
        
        self.type = action_type
        self.pos = pos
        
    def __repr__(self):
        termination = f' {self.pos}' if self.type.has_pos else ''
        return f'{repr(self.type)}{termination}'

    @classmethod
    def select(cls, pos: (int, int)):
        return cls(ActionType.SELECT, pos)

    @classmethod
    def flag(cls, pos: (int, int)):
        return cls(ActionType.FLAG, pos)

    @classmethod
    def chord(cls, pos: (int, int)):
        return cls(ActionType.CHORD, pos)

    @classmethod
    def superchord(cls, pos: (int, int)):
        return cls(ActionType.SUPERCHORD, pos)
    
    @classmethod
    def surrender(cls):
        return cls(ActionType.SURRENDER)


