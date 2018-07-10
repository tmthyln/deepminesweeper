import numpy as np

from game.mineseeders import Seeder, RandomSeeder
from game.minesweeper import Minesweeper
from game.visualizers import *
from rl.baselines import RandomAgent


class GameRunner:
    def __init__(self, shape, agent=RandomAgent(), seeder=Seeder(), windowed=False, delay=0):
        self.game = Minesweeper(shape, seeder=seeder)
        self.game.start()

        self.agent = agent
        agent.start()

        self.visualizer = WindowedVisualizer() if windowed else TextVisualizer()
        self.delay = delay

    def run(self):
        # display initial board
        self._visualize()

        while self.game.running:
            # get environment state
            vis_matrix, prox_matrix = self.game.step()

            # decide on move to make
            move = self.agent.think(vis_matrix, prox_matrix)

            # implement move in game
            reward = self.game.act(move)
            self.agent.feedback(reward)

            # show result of move
            self._visualize()

    def _visualize(self):
        self.visualizer.display(self.game.get_displayable_grid())


shape = (25, 25)
game_runner = GameRunner(shape, seeder=RandomSeeder(shape=shape, mine_ratio=0.1, random_state=np.random.randint(0, 1000)))
game_runner.run()

