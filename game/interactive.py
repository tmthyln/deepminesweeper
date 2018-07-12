import numpy as np
import pygame
from pygame.locals import *

from game.mineseeders import RandomSeeder
from game.minesweeper import Minesweeper


class DrawableGrid:
    def __init__(self, surface: pygame.Surface, shape: tuple, global_offset=(0, 0), cell_length=5):
        grid_height, grid_width = shape
        global_left, global_top = global_offset

        # generate left and top offsets for all cells
        left_offsets = global_left + \
                       np.array(range(0, cell_length * grid_width, cell_length)).reshape((1, grid_width)) * \
                       np.ones((grid_height, 1))
        top_offsets = global_top + \
                       np.array(range(0, cell_length * grid_height, cell_length)).reshape((grid_height, 1)) * \
                       np.ones((1, grid_width))

        # preallocate grids for speed
        self._grid = np.empty(shape, dtype=pygame.Rect)
        self._subsurfaces = np.empty(shape, dtype=pygame.Surface)

        # create grid of Rect objects
        for row in range(grid_height):
            for col in range(grid_width):
                self._grid[row, col] = pygame.Rect(left_offsets[row, col], top_offsets[row, col],
                                                   cell_length, cell_length)

        # generate subsurfaces
        for row in range(grid_height):
            for col in range(grid_width):
                self._subsurfaces[row, col] = surface.subsurface(self._grid[row, col])
        print(self._subsurfaces)

    def click(self, point: tuple):
        pass

    def _find_cell(self, point: tuple):
        pass


class InteractiveGameWindow:
    PRIMARY_COLOR = (55, 200, 100)

    def __init__(self, game: Minesweeper):
        self._running = False

        # initialize pygame
        pygame.init()

        # set up window
        pygame.display.set_caption('Deep Minesweeper')
        pygame.display.set_icon(pygame.image.load('./resources/favicon.png'))
        pygame.mouse.set_cursor(*pygame.cursors.diamond)

        self.screen = pygame.display.set_mode((700, 900), pygame.RESIZABLE)

        # fill background
        self.base = pygame.Surface(self.screen.get_size()).convert()
        self.base.fill(self.PRIMARY_COLOR)

        # create drawable grid from screen
        self.grid = DrawableGrid(self.base, game.grid.shape)

        # blit everything to the screen
        self.screen.blit(self.base, (0, 0))
        pygame.display.flip()

    def run(self):
        self._running = True

        while self._running:
            self._display()

    def _display(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self._running = False
                return
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.grid.click(event.pos)

        self.screen.blit(self.base, (0, 0))
        pygame.display.flip()


shape = (40, 40)
game = Minesweeper(shape, seeder=RandomSeeder(shape))
gui = InteractiveGameWindow(game)

grid = DrawableGrid(gui.screen, (5, 7))

gui.run()

