from abc import abstractmethod, ABC
from collections import deque
from enum import Enum

import numpy as np
import pygame
from pygame.locals import *
import random
from scipy.signal import convolve2d
import sys

from typing import List, Iterable

from utils import Delayer


class OnScreen(ABC):
    
    @property
    @abstractmethod
    def rect(self) -> pygame.Rect:
        pass
    
    @property
    @abstractmethod
    def reference(self) -> np.ndarray:
        pass

    @property
    @abstractmethod
    def center(self) -> np.ndarray:
        pass
    
    @property
    @abstractmethod
    def size(self) -> np.ndarray:
        pass


class Cell(OnScreen):
    hidden_cell_image: pygame.Surface
    flagged_cell_image: pygame.Surface
    open_images: List[pygame.Surface]
    orig_image_size: np.ndarray
    cell_size: np.ndarray
    
    class State(Enum):
        """
        Set of values representing the visibility of a cell.
        """
        HIDDEN = 1
        FLAGGED = 2
        OPEN = 3
    
    def __init__(self, pos: Iterable, neighbors: int,
                 blit_ref: Iterable = (0, 0), hidden=True):
        
        Cell.init()
        
        self.pos = np.array(pos)
        self.blit_ref = np.array(blit_ref)
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
        
        return surface, self.reference
    
    @property
    def rect(self) -> pygame.Rect:
        return Rect(self.reference, self.size)
    
    @property
    def reference(self) -> np.ndarray:
        return self.blit_ref + self.pos * self.size
    
    @property
    def center(self) -> np.ndarray:
        return self.reference + self.size // 2
    
    @property
    def size(self) -> np.ndarray:
        return Cell.orig_image_size
    
    @classmethod
    def init(cls, _initialized=[False]):
        """
        Pre-cache the surfaces for the cells; runs once on the first time an
        instance is created.
        """
        
        if _initialized[0]:
            return

        _initialized[0] = True

        font = pygame.font.Font(pygame.font.match_font('arial', bold=True), 24)
        
        cls.hidden_cell_image = pygame.image.load('res/hidden_cell.png').convert()
        cls.orig_image_size = np.array([cls.hidden_cell_image.get_width(),
                                        cls.hidden_cell_image.get_height()])
        cls.cell_size = cls.orig_image_size
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


class Grid(OnScreen):
    
    def __init__(self, mine_layout: np.ndarray, blit_ref: Iterable = (0, 0)):
        self._mine_layout = mine_layout
        self.proximity = Grid.add_neighbors(mine_layout)
        self._game_size = np.array(mine_layout.shape)
        self.blit_ref = np.array(blit_ref)
        self.grid = np.array([[Cell((i, j), self.proximity[i, j])
                               for j in range(self.grid_size[1])]
                              for i in range(self.grid_size[0])])

    def draw_on(self, screen: pygame.Surface):
        for pos in np.ndindex(*self.proximity.shape):
            screen.blit(*self.grid[pos].get_drawable())

    ############################################################################
    #                                 Actions                                  #
    ############################################################################
    
    def select(self, coords, propagate=True):
        if not self.rect.collidepoint(*coords):
            return
        
        pos = self.get_cell_pos(coords)
        
        # propagate on empty, non-neighboring cells
        if propagate and self.proximity[pos] == 0:
            candidates = deque([pos])
    
            while len(candidates) != 0:
                next_blank = candidates.popleft()
        
                if self.proximity[next_blank] == 0 and self.grid[next_blank].state is Cell.State.HIDDEN:
                    for adj_cell in self._adjacents(*next_blank):
                        candidates.append(adj_cell)
        
                self.grid[next_blank].select()
        
        self.grid[pos].select()
        
    def toggle_flag(self, coords):
        if self.rect.collidepoint(*coords):
            return self.grid[self.get_cell_pos(coords)].toggle_flag()

    def chord(self, coords):
        if not self.rect.collidepoint(*coords):
            return

        pos = self.get_cell_pos(coords)
        
        if self.grid[pos].state is not Cell.State.OPEN:
            return
        
        flagged_cells = 0
        for adj_pos in self._adjacents(*pos):
            if self.grid[adj_pos].state is Cell.State.FLAGGED or \
                    (self.grid[adj_pos].state is Cell.State.OPEN and self.proximity[adj_pos] == -1):
                flagged_cells += 1
                
        if flagged_cells == self.proximity[pos]:
            for adj_pos in self._adjacents(*pos):
                self.select(self.grid[adj_pos].center)
    
    def superchord(self):
        pass
        
    def _adjacents(self, x, y):
        return filter(lambda pos: 0 <= pos[0] < self.grid_size[0] and 0 <= pos[1] < self.grid_size[1],
                      [(x + 1, y),
                       (x + 1, y + 1),
                       (x,     y + 1),
                       (x - 1, y + 1),
                       (x - 1, y),
                       (x - 1, y - 1),
                       (x,     y - 1),
                       (x + 1, y - 1)])
    
    def get_cell_pos(self, coords):
        return tuple((np.array(coords) - self.blit_ref) // Cell.cell_size)

    ############################################################################
    #                          Board Representations                           #
    ############################################################################
    
    @property
    def proximity_matrix(self):
        return self.proximity.copy()
    
    @property
    def mine_layout(self):
        return self._mine_layout.copy()
    
    @property
    def flag_layout(self):
        flagged = np.vectorize(lambda x: x.state is Cell.State.FLAGGED)
        
        return flagged(self.grid)

    @property
    def hidden_layout(self):
        hidden = np.vectorize(lambda x: x.state is Cell.State.HIDDEN)
    
        return hidden(self.grid)
    
    @property
    def open_layout(self):
        openness = np.vectorize(lambda x: x.state is Cell.State.OPEN)
        
        return openness(self.grid)

    ############################################################################
    #                             Board Statistics                             #
    ############################################################################
    
    @property
    def flags(self):
        return np.sum(self.flag_layout)
    
    @property
    def mines(self):
        return np.sum(self.mine_layout)
    
    @property
    def open_mines(self):
        return np.sum(self.mine_layout & self.open_layout)
    
    @property
    def open_cells(self):
        return np.sum(self.open_layout)
    
    @property
    def completed(self):
        # case 1: all non-mines are open
        # case 2: flags exactly mark all mines
        return np.all(self.mine_layout | self.open_layout) or \
               np.all(self.mine_layout == self.flag_layout)
    
    ############################################################################
    #                               Positioning                                #
    ############################################################################
    
    @property
    def rect(self):
        return Rect(self.blit_ref, self.size)
    
    @property
    def reference(self) -> np.ndarray:
        return self.blit_ref
    
    @property
    def center(self) -> np.ndarray:
        return self.blit_ref + self.size // 2
        
    @property
    def size(self):
        return self._game_size * Cell.cell_size

    @property
    def grid_size(self) -> np.ndarray:
        return self._game_size

    ############################################################################
    #                             Grid Generation                              #
    ############################################################################
    
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
        sites = game_size[0] * game_size[1]
        
        indices = [1]*min(num_mines, sites) + [0]*max(0, sites - num_mines)
        random.shuffle(indices)

        return cls(np.array(indices).reshape(game_size))
    
    @staticmethod
    def add_neighbors(mines: np.ndarray) -> np.ndarray:
        neighbors = convolve2d(mines, np.array([[1, 1, 1],
                                                [1, 0, 1],
                                                [1, 1, 1]]),
                               mode='same', boundary='fill')
        
        return neighbors * (1 - mines) - mines


class Config(object):
    # aesthetics
    window_title = 'Minesweeper'
    favicon_path = 'res/favicon.png'
    bg_color = (0, 120, 0)
    
    # windowing and sizing
    window_size = (1280, 780)
    grid_size = (40, 15)
    default_cell_size = (32, 32)
    
    # game play
    fps = 60
    end_on_first_mine = True
    
    # controls
    double_click_time = 400
    click_to_flag = True
    use_super_chord = False


class GameWindow(object):
    def __init__(self, config: Config):
        self.config = config

        pygame.init()
        pygame.display.set_caption(config.window_title)
        pygame.display.set_icon(pygame.image.load(config.favicon_path))
        self._screen = pygame.display.set_mode(config.window_size,
                                               flags=pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        
        Cell.init()
        
        self.resize()

    def run(self):
        tick_clock = Delayer(initial_fps=self.config.fps)
    
        while True:
            tick_clock.tick_start()
            action_taken = False
        
            # handle user events
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit(0)
                elif self._primary_double_clicked(event):
                    self.grid.chord(event.pos)
                    action_taken = True
                elif self._primary_clicked(event):
                    self.grid.toggle_flag(event.pos) if self.config.click_to_flag else self.grid.select(event.pos)
                    action_taken = True
                elif self._secondary_clicked(event):
                    self.grid.select(event.pos) if self.config.click_to_flag else self.grid.toggle_flag(event.pos)
                    action_taken = True
                elif event.type == VIDEORESIZE:
                    self.resize(new_available_space=(event.w, event.h))
        
            if action_taken:
                print(f'game completion: {self.grid.completed}')
        
            # yield to caller and process caller requests
            requests = (yield ~self.grid.open_layout, self.grid.proximity_matrix)
            # TODO process requests

            # update screen
            self.grid.draw_on(self._screen)
            pygame.display.update()
        
            # calculate processing time and amount of delay needed for desired framerate
            tick_clock.tick_delay()

    ############################################################################
    #                                 Graphics                                 #
    ############################################################################
    
    def resize(self, new_available_space: (int, int) = None):
        if new_available_space is not None:
            self._screen = pygame.display.set_mode(new_available_space,
                                                   flags=pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
        
        self._screen.fill(self.config.bg_color)
        
        grid_size = np.array(self._screen.get_rect().size) // Cell.cell_size

        self.grid = Grid.uniform_random(grid_size, 0.05)

    ############################################################################
    #                              Events & Input                              #
    ############################################################################
    
    def _primary_clicked(self, event: pygame.event.Event):
        return event.type == MOUSEBUTTONUP and event.button == 1
    
    def _secondary_clicked(self, event: pygame.event.Event):
        return event.type == MOUSEBUTTONUP and event.button == 3
    
    def _primary_double_clicked(self, event: pygame.event.Event,
                                _last_clicked_cell=[(-1, -1)], clock=pygame.time.Clock()):
        valid_dbl_click = False
        
        if event.type == MOUSEBUTTONUP and event.button == 1:
            if clock.tick() <= self.config.double_click_time and \
                    self.grid.get_cell_pos(event.pos) == _last_clicked_cell[0]:
                valid_dbl_click = True
            
            _last_clicked_cell[0] = self.grid.get_cell_pos(event.pos)
            
        return valid_dbl_click
        # TODO: maybe implement a multi-click feature


def start_game():
    config = Config()
    window = GameWindow(config)
    
    for _ in (game := window.run()):
        # TODO add agent into the mix
        game.send(0)

    
if __name__ == '__main__':
    start_game()
