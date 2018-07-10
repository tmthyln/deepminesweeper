import numpy as np

from game.minesweeper import Minesweeper
from game.mineseeders import RandomSeeder

game = Minesweeper(seeder=RandomSeeder((25, 25)))

game.start()
vis, prox = game.step()

