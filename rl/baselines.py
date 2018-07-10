import numpy as np

from game.cell import Cell
from rl.agent import Agent


class RandomAgent(Agent):
    def __init__(self, random_state=17):
        np.random.randn(random_state)

    def think(self, visibility_matrix, proximity_matrix):
        rows, cols = proximity_matrix.shape

        while True:
            x, y = np.random.randint(0, rows), np.random.randint(0, cols)

            if visibility_matrix[x, y, 1]:
                break

        return x, y

