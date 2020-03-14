import os

import numpy as np


def save_board(filename, mine_layout, open_layout, flag_layout, root='runs'):
    np.savez_compressed(os.path.join(root, filename),
                        mine_layout=mine_layout,
                        open_layout=open_layout,
                        flag_layout=flag_layout)
