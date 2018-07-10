import argparse
from game.minesweeper import Minesweeper
from game.visualizers import *


class GameRunner:
    def __init__(self, windowed=False):
        self.game = Minesweeper()
        self.game.start()

        self.visualizer = WindowedVisualizer() if windowed else TextVisualizer()

    def run(self):
        while True:
            board, possible_moves, ended = self.game.step()

            # take action based on env

            result = self.game.act()  # on moves

            self.visualizer.display(self.game.get_displayable_grid())


args = argparse.ArgumentParser()

game_runner = GameRunner()
game_runner.run()
