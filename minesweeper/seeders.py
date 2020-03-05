import numpy as np
import random

from typing import Callable, Tuple


Seeder = Callable[[Tuple[int, int]], np.ndarray]


def uniform_random(mine_prob: float) -> Seeder:
    def seeder(game_size: (int, int)) -> np.ndarray:
        return np.random.uniform(0., 1., game_size) <= mine_prob
    
    return seeder


def number_mines(num_mines: int) -> Seeder:
    def seeder(game_size: (int, int)) -> np.ndarray:
        sites = game_size[0] * game_size[1]
    
        indices = [True] * min(num_mines, sites) + [False] * max(0, sites - num_mines)
        random.shuffle(indices)
    
        return np.array(indices).reshape(game_size)
    
    return seeder


def percent_mines(mine_percent: float) -> Seeder:
    if not 0. <= mine_percent <= 1.:
        raise ValueError(f'Not a valid percent: {mine_percent}')
    
    def seeder(game_size: (int, int)) -> np.ndarray:
        return number_mines(int(mine_percent * mine_percent))(game_size)
    
    return seeder
