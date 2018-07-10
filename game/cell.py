from enum import Enum
import numpy as np


class Cell(Enum):
    BLOCKED = 0
    INVISIBLE_MINE = 2
    INVISIBLE_BLANK = 3
    VISIBLE_MINE = 4
    VISIBLE_BLANK = 6

    def __str__(self):
        if self == Cell.BLOCKED:
            return 'B'
        elif self == Cell.INVISIBLE_MINE or self == Cell.INVISIBLE_BLANK:
            return '#'
        elif self == Cell.VISIBLE_MINE:
            return 'X'
        elif self == Cell.VISIBLE_BLANK:
            return 'O'
        else:
            return '?'

    @staticmethod
    def can_be_opened(cell):
        return cell == Cell.INVISIBLE_BLANK or cell == Cell.INVISIBLE_MINE


CELL_TYPES = np.array([Cell.BLOCKED,
                       Cell.INVISIBLE_MINE,
                       Cell.INVISIBLE_BLANK,
                       Cell.VISIBLE_MINE,
                       Cell.VISIBLE_BLANK]).reshape((1, 1, 5))

