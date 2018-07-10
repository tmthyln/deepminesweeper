import numpy as np
from scipy.signal import convolve2d

from game.minesweeper import Grid
from game.mineseeders import RandomSeeder

prox_conv_kern = np.ones((3, 3))
prox_conv_kern[1, 1] = 0

empty = np.round(np.random.uniform(0, 1, (10, 10))).astype(int)
print(empty)

print(convolve2d(empty, prox_conv_kern, 'same').astype(int))

shape = (10, 10)
grid = Grid(shape, seeder=RandomSeeder(shape))
grid.generate_proximity_matrix()
print(grid.prox)
