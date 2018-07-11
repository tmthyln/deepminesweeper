from game.mineseeders import Seeder, RandomSeeder
from game.minesweeper import Minesweeper
from game.visualizers import *
from rl.baselines import RandomAgent


class AutoGameRunner:
    def __init__(self, shape, agent=RandomAgent(), seeder=Seeder(), windowed=False, delay=0):
        self.game = Minesweeper(shape, seeder=seeder)
        self.game.start()

        self.agent = agent
        agent.start()

        self.visualizer = WindowedVisualizer() if windowed else TextVisualizer()
        self.delay = delay
        self._tick = 0

    def run(self):
        # display initial board
        self._visualize()

        while self.game.running:
            self._tick += 1

            # get environment state
            vis_matrix, prox_matrix = self.game.step()

            # decide on move to make
            move = self.agent.think(vis_matrix, prox_matrix)

            # implement move in game
            reward = self.game.act(move)
            self.agent.feedback(reward)

            # show result of move
            self._visualize()

    @property
    def tick(self):
        return self._tick

    def _visualize(self):
        self.visualizer.display(self.game.get_displayable_grid())


class InteractiveGameRunner:
    def __init__(self, shape, seeder=Seeder()):
        self.game = Minesweeper(shape, seeder=seeder)
        self.game.start()

