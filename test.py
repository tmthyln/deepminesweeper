import numpy as np

from game.mineseeders import RandomSeeder
from project.runner import AutoGameRunner, WindowedVisualizer

shape = (25, 25)
game_runner = AutoGameRunner(shape, seeder=RandomSeeder(shape=shape, random_state=np.random.randint(0, 1000)),
                             visualizer=WindowedVisualizer())
game_runner.run()

