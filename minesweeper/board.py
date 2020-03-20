from dataclasses import dataclass
from abc import abstractmethod, ABC
import numpy as np


def neighbors(mines: np.ndarray) -> np.ndarray:
    from scipy.signal import convolve2d

    neighbors = convolve2d(mines, np.array([[1, 1, 1],
                                            [1, 0, 1],
                                            [1, 1, 1]]),
                           mode='same', boundary='fill')
    
    return neighbors * (1 - mines) - mines


class Grid(ABC):
    
    ############################################################################
    #                                 Actions                                  #
    ############################################################################
    
    @abstractmethod
    def select(self, pos):
        pass
    
    @abstractmethod
    def toggle_flag(self, pos):
        pass
    
    ############################################################################
    #                            Grid-Wide Changes                             #
    ############################################################################
    
    @abstractmethod
    def resize(self):
        pass
    
    @abstractmethod
    def refill(self, proximity, open_layout=None):
        pass
    
    @abstractmethod
    def shift(self, dx, dy):
        pass
    
    ############################################################################
    #                                 Queries                                  #
    ############################################################################
    
    @property
    @abstractmethod
    def size(self):
        pass
    
    @abstractmethod
    def pos_of(self, coords):
        pass
    
    @abstractmethod
    def is_flagged(self, pos):
        pass
    
    @abstractmethod
    def is_open(self, pos):
        pass
    
    ############################################################################
    #                                 Graphics                                 #
    ############################################################################
    
    def redraw(self):
        pass


class Board(ABC):
    
    @abstractmethod
    def select(self, pos, propagate=True):
        pass
    
    @abstractmethod
    def toggle_flag(self, pos):
        pass
    
    @abstractmethod
    def chord(self, pos):
        pass
    
    @abstractmethod
    def superchord(self):
        pass
    
    ############################################################################
    #                          Board Representations                           #
    ############################################################################
    
    @property
    @abstractmethod
    def proximity_matrix(self):
        pass
    
    @property
    @abstractmethod
    def mine_layout(self):
        pass
    
    @property
    @abstractmethod
    def flag_layout(self):
        pass
    
    @property
    @abstractmethod
    def hidden_layout(self):
        pass
    
    @property
    @abstractmethod
    def open_layout(self):
        pass
    
    ############################################################################
    #                             Board Statistics                             #
    ############################################################################
    
    @property
    @abstractmethod
    def flags(self) -> int:
        pass
    
    @property
    @abstractmethod
    def mines(self) -> int:
        pass
    
    @property
    @abstractmethod
    def open_mines(self) -> int:
        pass
    
    @property
    @abstractmethod
    def open_cells(self) -> int:
        pass
    
    @property
    @abstractmethod
    def completed(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def failed(self) -> bool:
        pass


@dataclass
class HiddenBoardState:
    openable_layout: np.ndarray
    flag_layout: np.ndarray
    proximity_matrix: np.ndarray
    last_state: 'HiddenBoardState' = None
    
    last_state_stored = None
    
    def __post_init__(self):
        self.last_state = HiddenBoardState.last_state_stored  # TODO may be a bad idea if different threads of creation
        HiddenBoardState.last_state_stored = self


@dataclass
class CompleteBoardState:
    open_layout: np.ndarray
    mine_layout: np.ndarray
    flag_layout: np.ndarray
