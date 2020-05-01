from collections import deque

import numpy as np
import os
import pygame
from pygame import Rect

from scipy.signal import convolve2d

from minesweeper import register_board
from minesweeper.board import Board, Grid, adjacents
from minesweeper.seeders import Seeder


################################################################################
#                                    Square                                    #
################################################################################

class SquareGrid(Grid):
    
    def __init__(self, screen: pygame.Surface, available_rect: pygame.Rect, config):
        # save parameters and pre-load assets/resources
        self._screen = screen
        self._config = config
        self._load_cells()

        self.resize(screen, available_rect)
    
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
    
    def realign(self, screen, available_rect: Rect):
        self._screen = screen
        self._available_rect = available_rect
        self._used_rect.center = available_rect.center

        ref_x, ref_y = self._used_rect.topleft
        cell_x, cell_y = self.cell_size
        
        for x, y in np.ndindex(self._size):
            self._subrects[x, y] = Rect(ref_x + x * cell_x, ref_y + y * cell_y, cell_x, cell_y)

        self._changelist.extend(np.ndindex(self._size))
    
    def resize(self, screen, available_rect: Rect):
        self._screen = screen
        self._available_rect = available_rect
        
        self._changelist = []

        cell_x, cell_y = self.cell_size
    
        # calculate used area of available screen real estate
        self._size = grid_size = available_rect.w // cell_x, \
                                 available_rect.h // cell_y
        grid_screen_size = grid_size[0] * cell_x, grid_size[1] * cell_y
        self._used_rect = Rect((0, 0), grid_screen_size)
        self._used_rect.center = available_rect.center
    
        ref_x, ref_y = self._used_rect.topleft
    
        # initialize all board state arrays
        self.flags = np.zeros(grid_size, dtype=bool)
        self.open = np.zeros(grid_size, dtype=bool)
        self._proximity = np.zeros(grid_size, dtype=np.int8)
        self._subrects = np.empty(grid_size, dtype=pygame.Rect)
        for x, y in np.ndindex(grid_size):
            self._subrects[x, y] = Rect(ref_x + x * cell_x, ref_y + y * cell_y, cell_x, cell_y)
    
        # force an initial draw of the grid
        self._changelist.extend(np.ndindex(self._size))
    
    def refill(self, proximity: np.ndarray, open_layout: np.ndarray = None):
        assert proximity.shape == self._proximity.shape
        
        self._proximity = proximity
        
        self.flags.fill(False)
        
        self.open.fill(False)
        if open_layout is not None:
            self.open[open_layout] = True
        
        self._changelist.extend(np.ndindex(self._size))
    
    def shift(self, dx, dy):
        pass
    
    ############################################################################
    #                                 Queries                                  #
    ############################################################################
    
    @property
    def size(self):
        return self._size
    
    def pos_of(self, coords):
        return (coords[0] - self._used_rect.left) // self.cell_size[0], (coords[1] - self._used_rect.top) // self.cell_size[1]
    
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
    
    def redraw(self):
        if len(self._changelist) > 0:
            for pos in self._changelist:
                self._screen.blit(self._cell_image(pos), self._subrects[pos])
        
        updated_rectangles = [self._subrects[pos] for pos in self._changelist]
        self._changelist = []
        return updated_rectangles


@register_board('square', SquareGrid)
class SquareBoard(Board):

    def __init__(self, grid: SquareGrid, seeder: Seeder, config, open_layout: np.ndarray = None):
        self._grid = grid
        self._seeder = seeder
        self._config = config
        
        self._mine_layout = seeder(grid.size)
        self._proximity = SquareBoard.add_neighbors(self._mine_layout)
        
        self._grid.refill(self._proximity, open_layout)
    
    def first_select(self, pos):
        self._mine_layout[pos] = False
        for adj_pos in self.adjacents(*pos):
            self._mine_layout[adj_pos] = False
            
        self._proximity = SquareBoard.add_neighbors(self._mine_layout)
        self._grid.refill(self._proximity)
        # FIXME: when clicking on edge, two sides are opened
        self.select(pos)
    
    def select(self, pos, propagate=True):
        if propagate and self._proximity[pos] == 0:
            candidates = deque([pos])
            
            while len(candidates) != 0:
                next_empty = candidates.popleft()
                
                if self._proximity[next_empty] == 0 and not self._grid.is_open(next_empty):
                    for adj_cell in self.adjacents(*next_empty):
                        candidates.append(adj_cell)
                
                self._grid.select(next_empty)
        
        self._grid.select(pos)
    
    def toggle_flag(self, pos):
        return self._grid.toggle_flag(pos)
    
    def chord(self, pos):
        if not self._grid.is_open(pos):
            return
        
        flagged_cells = 0
        for adj_pos in self.adjacents(*pos):
            if self._grid.is_flagged(adj_pos) or (self._grid.is_open(adj_pos) and self._mine_layout[adj_pos]):
                flagged_cells += 1
        
        if flagged_cells == self._proximity[pos]:
            for adj_pos in self.adjacents(*pos):
                self.select(adj_pos)
    
    def superchord(self):
        """Selects all cells that can reasonably be selected."""
        
        while True:
            # keep track of the number of open cells from before
            open_cells = self.open_cells
            
            # cells where flagged or are open mines
            known_mine_layout = self.flag_layout | (self.mine_layout & self.open_layout)
            
            # number of adjacent known mines for each cell
            known_neighbors = SquareBoard.add_neighbors(known_mine_layout)
            
            # positions for which it is okay to open all adjacent cells
            openable_adjacent_cells = (known_neighbors == self._proximity) & self.open_layout
            
            # cells that are adjacent to at least one cell that is "complete" (has known neighbors == neighbors)
            openable_cells = SquareBoard.add_neighbors(openable_adjacent_cells) > 0
            
            # open cells
            for pos in np.argwhere(openable_cells):
                self.select(tuple(pos))
            
            # stop superchording if no change
            if open_cells == self.open_cells:
                break
    
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
    def cells(self) -> int:
        return self._proximity.size
    
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
        return self.open_mines > self._config.forgiveness
    
    def adjacents(self, x, y):
        return adjacents((x, y), self._grid.size)
    
    @staticmethod
    def add_neighbors(mines: np.ndarray) -> np.ndarray:
        neighbors = convolve2d(mines, np.array([[1, 1, 1],
                                                [1, 0, 1],
                                                [1, 1, 1]]),
                               mode='same', boundary='fill')
        
        return neighbors * (1 - mines) - mines
