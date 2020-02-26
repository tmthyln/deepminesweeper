from collections import deque
from enum import Enum

import numpy as np
import pygame
from pygame.locals import *
import random
from scipy.signal import convolve2d
import sys

from typing import List

pygame.init()


class Cell(object):
    hidden_cell_image: pygame.Surface
    flagged_cell_image: pygame.Surface
    open_images: List[pygame.Surface]
    orig_image_size: (int, int)
    
    class State(Enum):
        """
        Set of values representing the visibility of a cell.
        """
        HIDDEN = 1
        FLAGGED = 2
        OPEN = 3
    
    def __init__(self, pos: (int, int), neighbors, blit_ref: (int, int) = (0, 0), hidden=True):
        Cell.load_cells()
        
        self.pos = pos
        self.blit_ref = blit_ref
        self.neighbors = neighbors
        self.state: Cell.State = Cell.State.HIDDEN if hidden else Cell.State.OPEN
    
    def select(self) -> bool:
        if self.state is Cell.State.HIDDEN:
            self.state = Cell.State.OPEN
        return self.neighbors == -1
    
    def toggle_flag(self):
        if self.state is Cell.State.HIDDEN:
            self.state = Cell.State.FLAGGED
        elif self.state is Cell.State.FLAGGED:
            self.state = Cell.State.HIDDEN
    
    def get_drawable(self) -> (pygame.Surface, pygame.Rect):
        surface: pygame.Surface
        
        if self.state is Cell.State.HIDDEN:
            surface = Cell.hidden_cell_image
        elif self.state is Cell.State.FLAGGED:
            surface = Cell.flagged_cell_image
        else:
            surface = Cell.open_images[self.neighbors]
        
        return surface, self.get_top_left_corner()
    
    def get_rect(self):
        return Rect(self.get_top_left_corner(), Cell.orig_image_size)
    
    def get_top_left_corner(self):
        return (self.blit_ref[0] + self.pos[0] * Cell.orig_image_size[0],
                self.blit_ref[1] + self.pos[1] * Cell.orig_image_size[1])
    
    def get_center(self):
        x, y = self.get_top_left_corner()
        return (x + Cell.orig_image_size[0] // 2,
                y + Cell.orig_image_size[1] // 2)
    
    @classmethod
    @property
    def cell_size(cls):
        return Cell.orig_image_size
    
    @classmethod
    def load_cells(cls, _initialized=[False]):
        """
        Pre-cache the surfaces for the cells; runs once on the first time an
        instance is created.
        """
        
        if _initialized[0]:
            return

        _initialized[0] = True

        font = pygame.font.Font(pygame.font.match_font('arial', bold=True), 24)
        
        cls.hidden_cell_image = pygame.image.load('res/hidden_cell.png').convert()
        cls.orig_image_size = (cls.hidden_cell_image.get_width(),
                               cls.hidden_cell_image.get_height())
        center = (cls.orig_image_size[0] // 2,
                  cls.orig_image_size[1] // 2)
        
        cls.flagged_cell_image = pygame.image.load('res/hidden_cell.png').convert()
        flag = font.render('F', True, (255, 0, 0), (255,) * 4)
        flag_rect = flag.get_rect()
        flag_rect.center = center
        cls.flagged_cell_image.blit(flag, flag_rect)
        
        cls.open_images = [pygame.image.load('res/open_cell.png').convert() for _ in range(10)]
        for num in range(1, 9):
            text = font.render(str(num), True, (255, 0, 0), (255,)*4)
            rect = text.get_rect()
            rect.center = center
            
            cls.open_images[num].blit(text, rect)

        mine = font.render('*', True, (255, 0, 0), (255,) * 4)
        mine_rect = mine.get_rect()
        mine_rect.center = center
        cls.open_images[-1].blit(mine, mine_rect)


class Grid(object):
    
    def __init__(self, mine_layout: np.ndarray, blit_ref: (int, int) = (0, 0)):
        self.layout = Grid.add_neighbors(mine_layout)
        self._game_size = mine_layout.shape
        self.blit_ref = blit_ref
        self.grid = np.array([[Cell((i, j), self.layout[i, j])
                               for j in range(self.game_size[1])]
                              for i in range(self.game_size[0])])

    def draw_on(self, screen: pygame.Surface):
        for i in range(self.game_size[0]):
            for j in range(self.game_size[1]):
                screen.blit(*self.grid[i, j].get_drawable())
    
    def select(self, coords, propagate=True):
        if not self.get_rect().collidepoint(*coords):
            return
        
        pos = self._get_grid_pos(coords)
        
        # propagate on empty, non-neighboring cells
        if propagate and self.layout[pos] == 0:
            candidates = deque([pos])
            
            while len(candidates) != 0:
                next_blank = candidates.popleft()
                
                if self.layout[next_blank] == 0 and self.grid[next_blank].state is Cell.State.HIDDEN:
                    for adj_cell in self._adjacents(*next_blank):
                        candidates.append(adj_cell)

                self.grid[next_blank].select()
        elif not self.grid[pos].select():
            pass  # TODO game ended
            
        # TODO selectively update
        
    def toggle_flag(self, coords):
        if self.get_rect().collidepoint(*coords):
            return self.grid[self._get_grid_pos(coords)].toggle_flag()

    def chord(self, coords):
        if not self.get_rect().collidepoint(*coords):
            return

        x, y = self._get_grid_pos(coords)
        
        flagged_cells = 0
        for adj_pos in self._adjacents(x, y):
            if self.grid[adj_pos].state is Cell.State.FLAGGED:
                flagged_cells += 1
            elif self.grid[adj_pos].state is Cell.State.OPEN and self.layout[adj_pos] == -1:
                flagged_cells += 1
                
        if flagged_cells == self.layout[x, y]:
            for adj_pos in self._adjacents(x, y):
                self.select(self.grid[adj_pos].get_center())
        
    def _adjacents(self, x, y):
        return filter(lambda pos: 0 <= pos[0] < self.game_size[0] and 0 <= pos[1] < self.game_size[1],
                      [(x + 1, y),
                       (x + 1, y + 1),
                       (x, y + 1),
                       (x - 1, y + 1),
                       (x - 1, y),
                       (x - 1, y - 1),
                       (x, y - 1),
                       (x + 1, y - 1)])
    
    def _get_grid_pos(self, coords):
        coord_x, coord_y = coords
        x = (coord_x - self.blit_ref[0]) // Cell.orig_image_size[0]
        y = (coord_y - self.blit_ref[1]) // Cell.orig_image_size[1]
        return x, y
        
    def get_rect(self):
        return Rect(self.blit_ref, self.grid_size)
    
    @property
    def game_size(self) -> (int, int):
        return self._game_size
    
    @property
    def grid_size(self) -> (int, int):
        width, height = self.game_size
        cell_width, cell_height = Cell.orig_image_size
        return width * cell_width, width * cell_height
    
    @classmethod
    def uniform_random(cls, game_size: (int, int), mine_prob: float):
        return cls(np.random.uniform(0., 1., game_size) <= mine_prob)
    
    @classmethod
    def percent_mines(cls, game_size: (int, int), mine_percent: float):
        if not 0. <= mine_percent <= 1.:
            raise ValueError(f'Not a valid percent: {mine_percent}')
        
        return cls.number_mines(game_size, int(mine_percent * mine_percent))
    
    @classmethod
    def number_mines(cls, game_size: (int, int), num_mines: int):
        mines = np.zeros(game_size)
        
        indices = list(np.ndindex(mines))
        random.shuffle(indices)

        for mine_pos in indices[:min(num_mines, mines.size)]:
            mines[mine_pos] = 1.

        return cls(mines)
    
    @staticmethod
    def add_neighbors(mines: np.ndarray) -> np.ndarray:
        neighbors = convolve2d(mines, np.array([[1, 1, 1],
                                                [1, 0, 1],
                                                [1, 1, 1]]),
                               mode='same', boundary='fill')
        
        return neighbors * (1 - mines) - mines
    

class Config(object):
    fps = 60
    double_click_time = 500
    window_title = 'Minesweeper'
    window_size = (1280, 640)
    grid_size = (40, 15)
    click_to_flag = True
    
    bg_color = (0, 255, 0)


def start_game():
    config = Config()
    
    pygame.display.set_caption(config.window_title)
    pygame.display.set_icon(pygame.image.load('res/favicon.png'))
    screen = pygame.display.set_mode(config.window_size, flags=pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
    screen.fill(config.bg_color)

    grid = Grid.uniform_random(config.grid_size, 0.2)
    
    process_clock = pygame.time.Clock()
    dbl_click_clock = pygame.time.Clock()
    
    while True:
        process_clock.tick()
        
        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit(0)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if dbl_click_clock.tick() < config.double_click_time:
                        grid.chord(event.pos)
                    else:
                        if config.click_to_flag:
                            grid.toggle_flag(event.pos)
                        else:
                            grid.select(event.pos)
                elif event.button == 3:
                    if config.click_to_flag:
                        grid.select(event.pos)
                    else:
                        grid.toggle_flag(event.pos)
            elif event.type == VIDEORESIZE:
                pass
        
        grid.draw_on(screen)
        pygame.display.update()
        
        pygame.time.delay(max(0, 1000 // config.fps - process_clock.tick()))
    
    
if __name__ == '__main__':
    start_game()
