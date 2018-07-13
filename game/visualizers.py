import matplotlib.pyplot as plt

from game.cell import Cell
from game.minesweeper import Grid


class Visualizer:
    def display(self, grid: Grid):
        pass


class TextVisualizer(Visualizer):
    def __init__(self):
        self.step = 0

    def display(self, grid: Grid):
        self.step += 1

        print(f"Game on Cycle {self.step}:")
        print(grid.shape)
        print(grid)


class WindowedVisualizer(Visualizer):
    def __init__(self):
        plt.ion()
        plt.show()

    def display(self, grid: Grid):
        background = 2 * (grid.states == Cell.VISIBLE_BLANK).astype(int) + \
                     (grid.states == Cell.INVISIBLE_MINE).astype(int) + \
                     (grid.states == Cell.INVISIBLE_BLANK).astype(int)
        plt.imshow(background)

