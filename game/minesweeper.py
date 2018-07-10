from enum import Enum
from .mineseeders import *


###########################################
#  Minesweeper Board Grid Model (static)  #
###########################################
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
            return '!'
        elif self == Cell.VISIBLE_BLANK:
            return 'O'
        else:
            return '?'


class Grid(object):
    def __init__(self, shape, seeder=Seeder()):
        self.shape = shape
        self.clear_grid()

        seeder.load_mines(self)

    def get_state(self, row, col):
        self._validate(row, col)

        return self.states[row][col]

    def open(self, row, col):
        self._validate(row, col)

        if self.states[row][col] == Cell.INVISIBLE_MINE:
            self.states[row][col] = Cell.VISIBLE_MINE
            return False
        if self.states[row][col] == Cell.INVISIBLE_BLANK:
            self.states[row][col] = Cell.VISIBLE_BLANK
            return True

    def close(self, row, col):
        self._validate(row, col)

        if self.states[row][col] == Cell.VISIBLE_MINE:
            self.states[row][col] = Cell.INVISIBLE_MINE
        if self.states[row][col] == Cell.VISIBLE_BLANK:
            self.states[row][col] = Cell.INVISIBLE_BLANK

    def clear_grid(self):
        self.states = [[Cell.INVISIBLE_BLANK] * self.shape[1] for _ in range(self.shape[0])]

    def _validate(self, row, col):
        if row < 0 or row >= self.shape[0]:
            raise ValueError('row selection should be within the range for current grid')
        if col < 0 or col >= self.shape[1]:
            raise ValueError('col selection should be within the range for current grid')

    def __str__(self):
        string = ''

        for row in self.states:
            for elem in row:
                string += str(elem) + ' '
            string += '\n'

        return string


########################################
#  Minesweeper class (outward facing)  #
########################################
class Minesweeper:
    def __init__(self):

        self.grid = Grid()
        pass

    def start(self):
        pass

    def step(self):
        pass

    def act(self, action):
        pass

    def get_displayable_grid(self):
        return self.grid


shape = (15, 40)
grid = Grid(shape, seeder=RandomSeeder(shape))
print(grid)
