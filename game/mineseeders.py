import numpy as np
from .cell import Cell


####################################
#  Parent (Abstract) Seeder class  #
####################################
class Seeder:
    def load_mines(self, grid):
        """
        Clears the grid and loads mines, blocked sites, and blank sites according to the seeder type.
        :param grid: grid to load mines into
        """
        pass


# AVAILABLE ARRANGEMENTS
# * random by percent fill
# * checkboard
# * random by percent fill using 2x2 boxes


class RandomSeeder(Seeder):
    def __init__(self, shape, mine_ratio=0.25, blocked_ratio=0.0, random_state=17):
        """
        Seeds the grid randomly based on a percent fill of mines and blocked sites (other sites are blank).
        :param shape: shape of the grid
        :param mine_ratio: ratio of total sites to seed as mines
        :param blocked_ratio: ratio of total sites to seed as blocked sites
        :param random_state: seed for the random selection of sites
        """
        total_spots = shape[0] * shape[1]
        self.num_mines = total_spots * mine_ratio
        self.num_blocked = total_spots * blocked_ratio
        self.num_blank = total_spots - self.num_mines - self.num_blocked

        assert 0 <= self.num_blank <= total_spots

        np.random.rand(random_state)

    def load_mines(self, grid):
        grid.clear_grid()

        blocked = 0

        while blocked < self.num_blocked:
            r = np.random.randint(0, grid.shape[0])
            c = np.random.randint(0, grid.shape[1])

            if grid.states[r][c] == Cell.INVISIBLE_BLANK:
                grid.states[r][c] = Cell.BLOCKED
                blocked += 1

        mined = 0

        while mined < self.num_mines:
            r = np.random.randint(0, grid.shape[0])
            c = np.random.randint(0, grid.shape[1])

            if grid.states[r][c] == Cell.INVISIBLE_BLANK:
                grid.states[r][c] = Cell.INVISIBLE_MINE
                mined += 1


class CheckerboardSeeder(Seeder):
    def load_mines(self, grid):
        for row in range(grid.shape[0]):
            for col in range(grid.shape[1]):
                grid.states[row][col] = Cell.INVISIBLE_BLANK if row + col % 2 == 0 else Cell.INVISIBLE_MINE


class RandomFoursSeeder(Seeder):
    def __init__(self, shape, mine_ratio=0.25, blocked_ratio=0.0, random_state=17):
        total_spots = shape[0] * shape[1]
        self.num_mines = total_spots * mine_ratio
        self.num_blocked = total_spots * blocked_ratio
        self.num_blank = total_spots - self.num_mines - self.num_blocked

        assert 0 <= self.num_blank <= total_spots

        np.random.rand(random_state)

    def load_mines(self, grid):
        # TODO load mines in 2x2's
        pass

