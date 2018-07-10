import numpy as np

adjacent_deltas = np.array([[0, 1], [1, 0], [-1, 0], [0, -1], [1, 1], [1, -1], [-1, 1], [-1, -1]])
start = np.array([[1, 1]])
vertices = adjacent_deltas + start

print(vertices)

