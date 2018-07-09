from enum import Enum
import numpy as np
import pygame
from pygame.locals import *

PRIMARY_COLOR = (55, 200, 100)


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
    def __init__(self, shape, mine_ratio=0.25, blocked_ratio=0.0, load_mines=True):
        self.shape = shape
        self.clear_grid()

        total_spots = shape[0] * shape[1]
        self.num_mines = total_spots * mine_ratio
        self.num_blocked = total_spots * blocked_ratio
        self.num_blank = total_spots - self.num_mines - self.num_blocked

        assert 0 <= self.num_blank <= total_spots

        if load_mines:
            self.load_random_mines()

    def get_state(self, row, col):
        self._validate(row, col)

        return self.states[row][col]

    def open(self, row, col):
        self._validate(row, col)

        if self.states[row][col] == Cell.INVISIBLE_MINE:
            self.states[row][col] = Cell.VISIBLE_MINE
        if self.states[row][col] == Cell.INVISIBLE_BLANK:
            self.states[row][col] = Cell.VISIBLE_BLANK

    def close(self, row, col):
        self._validate(row, col)

        if self.states[row][col] == Cell.VISIBLE_MINE or self.states[row][col] == Cell.VISIBLE_BLANK:
            self.states[row][col] /= 2

    def clear_grid(self):
        self.states = [[Cell.INVISIBLE_BLANK] * self.shape[1] for _ in range(self.shape[0])]

    def load_random_mines(self, random_state=17):
        np.random.rand(random_state)
        self.clear_grid()

        blocked = 0

        while blocked < self.num_blocked:
            r = np.random.randint(0, self.shape[0])
            c = np.random.randint(0, self.shape[1])

            if self.states[r][c] == Cell.INVISIBLE_BLANK:
                self.states[r][c] = Cell.BLOCKED
                blocked += 1

        mined = 0

        while mined < self.num_mines:
            r = np.random.randint(0, self.shape[0])
            c = np.random.randint(0, self.shape[1])

            if self.states[r][c] == Cell.INVISIBLE_BLANK:
                self.states[r][c] = Cell.INVISIBLE_MINE
                mined += 1

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


class Minesweeper:
    def start(self):
        pass

    def step(self):
        pass

    def act(self, action):
        pass

    def get_display(self):
        pass


def create_and_run_game():
    pygame.init()
    screen = pygame.display.set_mode((700, 900), pygame.RESIZABLE)
    pygame.display.set_caption('Deep Minesweeper')

    # Fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill(PRIMARY_COLOR)

    # Blit everything to the screen
    screen.blit(background, (0, 0))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        screen.blit(background, (0, 0))
        pygame.display.flip()


# create_and_run_game()

grid = Grid((15, 40))
print(grid)
grid.open(10, 38)
print(grid)
