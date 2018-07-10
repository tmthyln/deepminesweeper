import numpy as np
from scipy.signal import convolve2d

from .mineseeders import Seeder
from .cell import Cell


###############################################################
#  Minesweeper Board: Grid Model (static) & Proximity Matrix  #
###############################################################
class Grid(object):
    adjacent_deltas = np.array([[0, 1], [1, 0], [-1, 0], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]])

    def __init__(self, shape, seeder=Seeder()):
        self.shape = shape
        self.states = np.array([[Cell.INVISIBLE_BLANK] * self.shape[1] for _ in range(self.shape[0])])
        self._running = True

        seeder.load_mines(self)

        self._generate_proximity_matrix()
        self._count_sites()

    def get_state(self, row, col):
        self._validate(row, col)

        return self.states[row, col]

    def get_degree(self, row, col):
        self._validate(row, col)

        return self.prox[row, col]

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
            self._open += 1
            self._running = False
        if self.states[row][col] == Cell.INVISIBLE_BLANK:
            self.states[row][col] = Cell.VISIBLE_BLANK
            self._open += 1

    def close(self, row, col):
        self._validate(row, col)

        if self.states[row][col] == Cell.VISIBLE_MINE:
            self._open -= 1
            self.states[row][col] = Cell.INVISIBLE_MINE
        if self.states[row][col] == Cell.VISIBLE_BLANK:
            self._open -= 1
            self.states[row][col] = Cell.INVISIBLE_BLANK

    def propagate(self, row, col):
        self._validate(row, col)

        assert self.states[row, col] == Cell.VISIBLE_BLANK

        if self.prox[row, col] == 0:
            self._propagate(row, col)

    def _propagate(self, row, col):
        start = np.array([[row, col]])
        vertices = start + self.adjacent_deltas

        for vertex in vertices:
            x, y = vertex[0], vertex[1]

            try:
                self._validate(x, y)
            except ValueError:
                continue

            if self.states[x, y] == Cell.INVISIBLE_BLANK:
                self.open(x, y)
                if self.prox[x, y] == 0:
                    self._propagate(x, y)

    def _generate_proximity_matrix(self):
        prox_conv_kern = np.ones((3, 3))
        prox_conv_kern[1, 1] = 0

        base_kern = (self.states == Cell.INVISIBLE_MINE).astype(int)

        self.prox = convolve2d(base_kern, prox_conv_kern, 'same').astype(int)

    def _count_sites(self):
        self._mines = np.sum((self.states == Cell.INVISIBLE_MINE).astype(int)) + \
                      np.sum((self.states == Cell.VISIBLE_MINE).astype(int))
        self._sites = np.sum((self.states == Cell.INVISIBLE_BLANK).astype(int)) + \
                      np.sum((self.states == Cell.INVISIBLE_MINE).astype(int))
        self._open = 0

    @property
    def sites(self):
        return self._sites

    @property
    def mines(self):
        return self._mines

    @property
    def open_sites(self):
        return self._open

    @property
    def running(self):
        return self._running and self._open < self._sites

    @property
    def MoS_difficulty(self):
        return self.mines / self.sites

    @property
    def OoS_reward(self):
        return self._open / self.sites

    def _validate(self, row, col):
        if row < 0 or row >= self.shape[0]:
            raise ValueError('row selection should be within the range for current grid')
        if col < 0 or col >= self.shape[1]:
            raise ValueError('col selection should be within the range for current grid')

    def __str__(self):
        string = ''

        for row in range(self.shape[0]):
            for col in range(self.shape[1]):
                state = self.states[row, col]

                if state == Cell.VISIBLE_BLANK:
                    prox = self.prox[row, col]

                    if prox == 0:
                        string += '  '
                    else:
                        string += str(prox) + ' '
                else:
                    string += str(self.states[row, col]) + ' '
            string += '\n'

        return string


########################################
#  Minesweeper class (outward facing)  #
########################################
class Minesweeper:
    def __init__(self, shape=(25, 25), seeder=Seeder()):
        self._running = False

        self.grid = Grid(shape, seeder=seeder)

    def start(self):
        """
        Starts this minesweeper game.
        """
        self._running = True

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

        # sub-matrices for computation
        tensor_grid = np.reshape(self.grid.states, self.grid.shape + (1,))
        blocked_sites = (tensor_grid == Cell.BLOCKED).astype(int)
        open_sites = (tensor_grid == Cell.VISIBLE_BLANK).astype(int)
        invisible_sites = np.ones(blocked_sites.shape, dtype=int) - blocked_sites - open_sites

        # visibility matrix
        vis_matrix = np.concatenate((blocked_sites, invisible_sites, open_sites), axis=2)

        # proximity matrix
        prox_matrix = open_sites[..., 0] * self.grid.prox

        return vis_matrix, prox_matrix

    def act(self, position):
        """
        Opens the cell at the position given and determines the running state of the game.
        :param position: tuple of length 2: (row, column)
        :return: OoS score (reward metric)
        """
        if not self.running:
            raise ValueError("can't act; game is not running")

        # open site
        self.grid.open(position[0], position[1])
        self._running = self.grid.running

        # propagate site opening
        if self._running:
            self.grid.propagate(position[0], position[1])

        return self.grid.OoS_reward

    @property
    def running(self):
        return self._running

    @property
    def difficulty(self):
        return self.grid.MoS_difficulty

    def get_displayable_grid(self):
        """
        Returns a set of grids representing the state of the board well-suited for display.
        :return: grid representing the environment
        """
        return self.grid

