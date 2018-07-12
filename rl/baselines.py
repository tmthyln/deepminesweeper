import numpy as np

from rl.agent import Agent


class RandomAgent(Agent):
    def __init__(self, random_state=None):
        if random_state is not None:
            np.random.rand(random_state)

    def think(self, visibility_matrix, proximity_matrix):
        rows, cols = proximity_matrix.shape

        while True:
            x, y = np.random.randint(0, rows), np.random.randint(0, cols)

            if visibility_matrix[x, y, 1]:
                break

        return x, y


class SequentialAgent(Agent):
    def __init__(self):
        self._index = 0

    def think(self, visibility_matrix, proximity_matrix):
        _, cols = proximity_matrix.shape

        while True:
            x, y = self._index // cols, self._index % cols

            self._index += 1

            if visibility_matrix[x, y, 1]:
                break

        return x, y

