import os
from collections import deque

import numpy as np
import pygame
from pygame.locals import *
import re
from scipy.signal import convolve2d
import sys

from typing import List

from minesweeper.actions import Action, ActionType
import minesweeper.gamelog as gamelog
from minesweeper.utils import Delayer


################################################################################
#                                   Graphics                                   #
################################################################################
from seeders import Seeder, uniform_random


class Grid:
    
    def __init__(self, screen: pygame.Surface, grid_rect: pygame.Rect, config):
        self._screen = screen
        self._rect = grid_rect
        self._config = config
        self._load_cells()

        ref_x, ref_y = grid_rect.topleft
        cell_x, cell_y = self.cell_size
        screen_x, screen_y = grid_rect.size
        self._size = grid_size = screen_x // cell_x, screen_y // cell_y
        
        assert screen_x % cell_x == 0
        assert screen_y % cell_y == 0
        
        self.flags = np.zeros(grid_size, dtype=bool)
        self.open = np.zeros(grid_size, dtype=bool)
        self._proximity = np.zeros(grid_size, dtype=np.int8)
        self._subrects = np.empty(grid_size, dtype=pygame.Rect)
        
        for x, y in np.ndindex(grid_size):
            self._subrects[x, y] = Rect(ref_x + x*cell_x, ref_y + y*cell_y, cell_x, cell_y)

        self._changelist = []
        
        self.redraw(force=True)
    
    def _load_cells(self):
        from pygame.transform import smoothscale
        load_image = pygame.image.load
        
        font = pygame.font.Font(pygame.font.match_font('arial', bold=True), 24)
        
        self.cell_size = np.array(self._config.cell_size)
        center = self.cell_size // 2
        
        hidden_base_file = os.path.join(self._config.res_dir, self._config.hidden_cell_file)
        open_base_file = os.path.join(self._config.res_dir, self._config.open_cell_file)
        
        hidden_base = smoothscale(load_image(hidden_base_file).convert_alpha(), self.cell_size)
        open_base = smoothscale(load_image(open_base_file).convert_alpha(), self.cell_size)

        self._hidden_image = hidden_base.copy()

        self._flag_image = hidden_base.copy()
        flag = font.render('F', True, (255, 0, 0))
        flag_rect = flag.get_rect()
        flag_rect.center = center
        self._flag_image.blit(flag, flag_rect)
        
        self._open_images = [open_base.copy() for _ in range(10)]
        for num in range(1, 9):
            text = font.render(str(num), True, (255, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = center
            
            self._open_images[num].blit(text, text_rect)

        mine = font.render('*', True, (255, 0, 0))
        mine_rect = mine.get_rect()
        mine_rect.center = center
        self._open_images[-1].blit(mine, mine_rect)

    ############################################################################
    #                                 Actions                                  #
    ############################################################################

    def select(self, pos: (int, int)):
        self.open[pos] = ~self.flags[pos]
        self._changelist.append(pos)

    def toggle_flag(self, pos: (int, int)):
        self.flags[pos] = ~self.open[pos] & ~self.flags[pos]
        self._changelist.append(pos)

    ############################################################################
    #                            Grid-Wide Changes                             #
    ############################################################################
    
    def resize(self):
        pass
    
    def refill(self, proximity: np.ndarray, open_layout: np.ndarray = None):
        assert proximity.shape == self._proximity.shape
        
        self._proximity = proximity
        
        self.flags[...] = False
        self.open[...] = False
        if open_layout is not None:
            self.open[open_layout] = True
            
        self.redraw(force=True)
    
    def shift(self, dx, dy):
        pass

    ############################################################################
    #                                 Queries                                  #
    ############################################################################

    @property
    def size(self):
        return self._size

    def pos_of(self, coords):
        return (coords[0] - self._rect.left) // self.cell_size[0], (coords[1] - self._rect.top) // self.cell_size[1]

    def is_flagged(self, pos):
        return self.flags[pos]
    
    def is_open(self, pos):
        return self.open[pos]

    ############################################################################
    #                                 Graphics                                 #
    ############################################################################
    
    def _cell_image(self, pos):
        if self.open[pos]:
            return self._open_images[self._proximity[pos]]
        else:
            return self._flag_image if self.flags[pos] else self._hidden_image
    
    def redraw(self, force=False):
        for pos in (np.ndindex(self.size) if force else self._changelist):
            self._screen.blit(self._cell_image(pos), self._subrects[pos])
        
        updated_rectangles = [self._rect] if force else [self._subrects[pos] for pos in self._changelist]
        self._changelist = []
        return updated_rectangles


class Board:
    def __init__(self, grid: Grid, seeder: Seeder, config, open_layout: np.ndarray = None):
        self._grid = grid
        self._seeder = seeder
        self._config = config
        self._mine_layout = seeder(grid.size)
        self._proximity = Board.add_neighbors(self._mine_layout)
        
        self._grid.refill(self._proximity, open_layout)

    def select(self, pos, propagate=True):
        if propagate and self._proximity[pos] == 0:
            candidates = deque([pos])
        
            while len(candidates) != 0:
                next_empty = candidates.popleft()
            
                if self._proximity[next_empty] == 0 and not self._grid.is_open(next_empty):
                    for adj_cell in self._adjacents(*next_empty):
                        candidates.append(adj_cell)
            
                self._grid.select(next_empty)
    
        self._grid.select(pos)

    def toggle_flag(self, pos):
        return self._grid.toggle_flag(pos)

    def chord(self, pos):
        if not self._grid.is_open(pos):
            return
    
        flagged_cells = 0
        for adj_pos in self._adjacents(*pos):
            if self._grid.is_flagged(adj_pos) or (self._grid.is_open(adj_pos) and self._mine_layout[adj_pos]):
                flagged_cells += 1
    
        if flagged_cells == self._proximity[pos]:
            for adj_pos in self._adjacents(*pos):
                self.select(adj_pos)

    def superchord(self):
        pass

    ############################################################################
    #                          Board Representations                           #
    ############################################################################

    @property
    def proximity_matrix(self):
        return self._proximity

    @property
    def mine_layout(self):
        return self._mine_layout

    @property
    def flag_layout(self):
        return self._grid.flags

    @property
    def hidden_layout(self):
        return ~self._grid.open

    @property
    def open_layout(self):
        return self._grid.open

    ############################################################################
    #                             Board Statistics                             #
    ############################################################################

    @property
    def flags(self) -> int:
        return np.sum(self._grid.flags).item()

    @property
    def mines(self) -> int:
        return np.sum(self.mine_layout).item()

    @property
    def open_mines(self) -> int:
        return np.sum(self.mine_layout & self.open_layout).item()

    @property
    def open_cells(self) -> int:
        return np.sum(self.open_layout).item()

    @property
    def completed(self) -> bool:
        # case 1: all non-mines are open
        # case 2: flags exactly mark all mines
        return np.all(self.mine_layout | self.open_layout) or \
               np.all(self.mine_layout == self.flag_layout)
    
    @property
    def failed(self) -> bool:
        return self._config.end_on_first_mine and self.open_mines > 0
    
    def _adjacents(self, x, y):
        return filter(lambda pos: 0 <= pos[0] < self._grid.size[0] and 0 <= pos[1] < self._grid.size[1],
                      [(x + 1, y),
                       (x + 1, y + 1),
                       (x, y + 1),
                       (x - 1, y + 1),
                       (x - 1, y),
                       (x - 1, y - 1),
                       (x, y - 1),
                       (x + 1, y - 1)])

    @staticmethod
    def add_neighbors(mines: np.ndarray) -> np.ndarray:
        neighbors = convolve2d(mines, np.array([[1, 1, 1],
                                                [1, 0, 1],
                                                [1, 1, 1]]),
                               mode='same', boundary='fill')
    
        return neighbors * (1 - mines) - mines


################################################################################
#                                  Game Logic                                  #
################################################################################

class GameWindow(object):
    def __init__(self, config):
        self.config = config

        pygame.init()
        pygame.display.set_caption(config.window_title)
        pygame.display.set_icon(pygame.image.load(os.path.join(config.res_dir, config.favicon_file)))
        
        self.resize(config.window_size)
        self.new_game()
        
    def new_game(self):
        self._board = Board(self._grid, uniform_random(0.2), self.config)
        self._last_reward = 0.
        self._grid.redraw(force=True)
        pygame.display.update()

    def run(self):
        tick_clock = Delayer(initial_fps=self.config.fps)
        games_finished = 0
        
        _, _, files = next(os.walk('runs/'))
        for filename in files:
            match = re.search(r'^game_user_(\d+).npz$', filename)
            games_finished = max(games_finished, int(match.group(1)))
        games_finished += 1
        
        self._grid.redraw(force=True)
        pygame.display.update()
        
        tick_clock.tick_start()
        
        while True:
            actions: List[Action] = []
            add_action = actions.append
            cell_pos = self._grid.pos_of

            # handle user events
            for event in pygame.event.get():
                if event.type == QUIT:
                    sys.exit(0)
                elif self._primary_double_clicked(event):  # TODO: add back in intersection checks
                    add_action(Action.chord(cell_pos(event.pos)))
                elif self._primary_clicked(event):
                    pos = cell_pos(event.pos)
                    add_action(Action.flag(pos) if self.config.click_to_flag else Action.select(pos))
                elif self._secondary_clicked(event):
                    pos = cell_pos(event.pos)
                    add_action(Action.select(pos) if self.config.click_to_flag else Action.flag(pos))
                elif event.type == VIDEORESIZE:
                    self.resize(new_size=(event.w, event.h))
                    self.new_game()
        
            # yield to caller
            agent_actions = (yield (~self._board.open_layout,
                             self._board.proximity_matrix[self._board.open_layout],
                             self._last_reward))  # TODO change reward to a status dict/object
            if agent_actions is not None:
                actions.extend(agent_actions)
            
            # process all actions and determine next reward
            for action in actions:
                if action.type == ActionType.SELECT:
                    self._board.select(action.pos)
                elif action.type == ActionType.FLAG:
                    self._board.toggle_flag(action.pos)
                elif action.type == ActionType.CHORD:
                    self._board.chord(action.pos)
                elif action.type == ActionType.SUPERCHORD:
                    self._board.superchord()
                elif action.type == ActionType.SURRENDER:
                    pass
                else:
                    print(f'Unknown action: {action}, skipping processing')
            
            # TODO add game end callbacks/hooks
            if self._board.completed or self._board.failed:
                gamelog.save_board(f'game_user_{games_finished}.npz',
                                   self._board.mine_layout,
                                   self._board.open_layout,
                                   self._board.flag_layout)
                games_finished += 1
                self.new_game()
            
            if len(actions) > 0:
                print(f'game completion: {self._board.completed}, '
                      f'game failed: {self._board.failed}')
    
            # TODO determine feedback

            # update screen
            updated_rects = self._grid.redraw()
            pygame.display.update(updated_rects)
        
            # calculate processing time and amount of delay needed for desired framerate
            tick_clock.tick_delay()

    ############################################################################
    #                                 Graphics                                 #
    ############################################################################
    
    def resize(self, new_size: (int, int) = None):
        if new_size is not None:
            self._screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
        
        grid_size = self._screen.get_width() // self.config.cell_size[0], \
                    self._screen.get_height() // self.config.cell_size[1]
        grid_screen_size = grid_size[0] * self.config.cell_size[0], \
                           grid_size[1] * self.config.cell_size[1]
        grid_screen_rect = Rect((0, 0), grid_screen_size)
        
        self._screen.fill(self.config.bg_color)
        self._grid = Grid(self._screen, grid_screen_rect, self.config)
        
        self._grid.redraw(force=True)
        pygame.display.update()

    ############################################################################
    #                              Events & Input                              #
    ############################################################################
    
    def _primary_clicked(self, event: pygame.event.Event):
        return event.type == MOUSEBUTTONUP and event.button == 1
    
    def _secondary_clicked(self, event: pygame.event.Event):
        return event.type == MOUSEBUTTONUP and event.button == 3

    # noinspection PyDefaultArgument
    def _primary_double_clicked(self, event: pygame.event.Event,
                                _last_clicked_cell=[(-1, -1)], clock=pygame.time.Clock()):
        valid_dbl_click = False
        
        if event.type == MOUSEBUTTONUP and event.button == 1:
            if clock.tick() <= self.config.double_click_time and \
                    self._grid.pos_of(event.pos) == _last_clicked_cell[0]:
                valid_dbl_click = True
                
            _last_clicked_cell[0] = self._grid.pos_of(event.pos)
            
        return valid_dbl_click
        # TODO: maybe implement a multi-click feature
