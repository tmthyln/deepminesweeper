import numpy as np
from scipy.signal import convolve2d

from .mineseeders import Seeder
from .cell import Cell


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
        """
        Opens the given position and determines if the underlying cell has a mine.
        :param row: row of the cell
        :param col: col of the cell
        :return: True if game is still running; False if the game has ended from opening this cell
        """
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
    def __init__(self, shape=(25, 25), seeder=Seeder()):
        self.running = False

        self.grid = Grid(shape, seeder=seeder)
        self.grid.generate_proximity_matrix()

    def start(self):
        """
        Starts this minesweeper game.
        """
        self.running = True

    def step(self):
        """
        Generates the next state of the game and provides the environment of the game.
        :return: (visibility matrix, proximity matrix) of the environment

        visibility matrix: 3D bit-tensor [height, width, 3] (3 = blocked sites, invisible sites, visible blank sites)
        proximity matrix: 2D tensor [height, width] describing the number of proximal mines (only valid for visible
        blank sites)
        """
        if not self.running:
            raise ValueError("game is not running")

        tensor_grid = np.reshape(self.grid.states, self.grid.shape + (1,))
        blocked_sites = (tensor_grid == Cell.BLOCKED).astype(int)
        open_sites = (tensor_grid == Cell.VISIBLE_BLANK).astype(int)
        invisible_sites = np.ones(blocked_sites.shape, dtype=int) - blocked_sites - open_sites

        vis_matrix = np.concatenate((blocked_sites, invisible_sites, open_sites), axis=2)
        prox_matrix = open_sites[..., 0] * self.grid.prox

        return vis_matrix, prox_matrix

    def act(self, position):
        """
        Opens the cell at the position given and determines the running state of the game.
        :param position: tuple of length 2: (row, column)
        :return: boolean, whether the game has ended
        """
        if not self.running:
            raise ValueError("can't act; game is not running")
        self.running = self.grid.open(position[0], position[1])

        return self.running

    def running(self):
        return self.running

    def get_displayable_grid(self):
        """
        Returns a set of grids representing the state of the board well-suited for display.
        :return: grid representing the environment
        """
        return self.grid

