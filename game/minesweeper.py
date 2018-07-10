import numpy as np
from scipy.signal import convolve2d

from .mineseeders import Seeder
from .cell import Cell, CELL_TYPES


###############################################################
#  Minesweeper Board: Grid Model (static) & Proximity Matrix  #
###############################################################
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
        self.states = np.array([[Cell.INVISIBLE_BLANK] * self.shape[1] for _ in range(self.shape[0])])

    def generate_proximity_matrix(self):
        prox_conv_kern = np.ones((3, 3))
        prox_conv_kern[1, 1] = 0

        base_kern = (self.states == Cell.INVISIBLE_MINE).astype(int)

        self.prox = convolve2d(base_kern, prox_conv_kern, 'same').astype(int)

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
        self.running = False

        self.grid = Grid()
        pass

    def start(self):
        self.running = True
        pass

    def step(self):
        pass

    def act(self, action):
        pass

    def running(self):
        return self.running

    def get_displayable_grid(self):
        return self.grid

