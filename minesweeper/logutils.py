import logging
import os
import numpy as np


def config():
    logging.basicConfig(format='[%(asctime)s %(levelname)s:%(name)s] %(message)s', datefmt='%m.%d.%y %H:%M:%S')


def get_logger(name):
    config()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # TODO make this dependent on config
    return logger


config()


def save_board(filename, mine_layout, open_layout, flag_layout, root='runs'):
    np.savez_compressed(os.path.join(root, filename),
                        mine_layout=mine_layout,
                        open_layout=open_layout,
                        flag_layout=flag_layout)
