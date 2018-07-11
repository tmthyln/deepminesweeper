import pygame
from pygame.locals import *


class Visualizer:
    def display(self, grid):
        pass


class TextVisualizer(Visualizer):
    def __init__(self):
        self.step = 0

    def display(self, grid):
        self.step += 1

        print(f"Game on Cycle {self.step}:")
        print(grid.shape)
        print(grid)


class WindowedVisualizer(Visualizer):
    PRIMARY_COLOR = (55, 200, 100)

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((700, 900), pygame.RESIZABLE)
        pygame.display.set_caption('Deep Minesweeper')

        # Fill background
        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill(self.PRIMARY_COLOR)

        # Blit everything to the screen
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

    def display(self, grid):
        for event in pygame.event.get():
            if event.type == QUIT:
                return

        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

