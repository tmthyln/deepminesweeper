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
            result = self.game.act(move)

            # show result of move
            self._visualize()

        self._visualize()

    def _visualize(self):
        self.visualizer.display(self.game.get_displayable_grid())


shape = (25, 25)
game_runner = GameRunner(shape, seeder=RandomSeeder(shape=shape))
game_runner.run()

