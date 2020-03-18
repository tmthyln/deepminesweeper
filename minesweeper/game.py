import os
import re
import sys
from typing import List, Sequence

import pygame
from pygame.locals import *

import minesweeper.logutils as logutils
from board import HiddenBoardState
from config import Config
from minesweeper.actions import Action, ActionType
from minesweeper.boards import SquareBoard, SquareGrid
from minesweeper.seeders import uniform_random
from minesweeper.utils import Delayer

game_log = logutils.get_logger('game')


class StatusBar:
    
    def __init__(self, screen: pygame.Surface, rect: pygame.Rect):
        pass
    
    def redraw(self) -> Sequence[pygame.Rect]:
        # redraw background
        
        pass
    
    pass


class GameWindow:
    def __init__(self, config: Config.__class__):
        self.config: Config.__class__ = config
        self._screen = None
        self._board = None
        self._grid = None
        self._last_reward = None

        pygame.init()
        pygame.display.set_caption(config.window_title)
        pygame.display.set_icon(pygame.image.load(os.path.join(config.res_dir, config.favicon_file)))
        
        self.resize(config.window_size)
        self.new_game()

    def resize(self, new_size: (int, int) = None):
        if new_size is not None:
            self._screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
    
        self._screen.fill(self.config.bg_color)
        self._grid = SquareGrid(self._screen, self._screen.get_rect(), self.config)
    
        self._grid.redraw(force=True)
        pygame.display.update()
        
    def new_game(self):
        self._board = SquareBoard(self._grid, uniform_random(0.2), self.config)
        self._last_reward = 0.
        self._grid.redraw(force=True)
        pygame.display.update()

    def run(self):
        tick_clock = Delayer(initial_fps=self.config.fps)
        games_finished = 0
        
        # TODO automake directory (maybe put into logutils)
        _, _, files = next(os.walk('runs/'))
        save_filename_pattern = re.compile(r'^game_user_(\d+).npz$')
        for filename in files:
            match = save_filename_pattern.match(filename)
            games_finished = max(games_finished, int(match[1]))
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
                    game_log.info('Closing Minesweeper')
                    sys.exit(0)
                elif self._primary_double_clicked(event):  # TODO: add back in intersection checks
                    game_log.debug(f'double clicked at {event.pos}')
                    add_action(Action.chord(cell_pos(event.pos)))
                elif self._primary_clicked(event):
                    game_log.debug(f'primary key clicked at {event.pos}')
                    pos = cell_pos(event.pos)
                    add_action(Action.flag(pos) if self.config.click_to_flag else Action.select(pos))
                elif self._secondary_clicked(event):
                    game_log.debug(f'secondary key clicked at {event.pos}')
                    pos = cell_pos(event.pos)
                    add_action(Action.select(pos) if self.config.click_to_flag else Action.flag(pos))
                elif event.type == VIDEORESIZE:
                    game_log.debug(f'window resized')
                    self.resize(new_size=(event.w, event.h))
                    self.new_game()
                elif event.type == KEYUP:
                    if event.key == K_q:
                        add_action(Action.surrender())
                    if self.config.superchord == 'keyup':
                        add_action(Action.superchord())
        
            # yield to caller
            masked_proximity = self._board.proximity_matrix.copy()
            masked_proximity[~self._board.open_layout] = 0
            next_board_state = HiddenBoardState(
                    openable_layout=~self._board.open_layout & ~self._board.flag_layout,
                    flag_layout=self._board.flag_layout,
                    proximity_matrix=masked_proximity)
            
            agent_actions = (yield next_board_state, self._last_reward)  # TODO change reward to a status
            if agent_actions is not None:
                actions.extend(agent_actions)
            
            # TODO process surrendering separately
            
            if self.config.superchord == 'auto' and len(actions) > 0:
                add_action(Action.superchord())
            
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
                    game_log.warning(f'Unknown action: {action}, skipping processing')
            
            # TODO add game end callbacks/hooks
            if len(actions) > 0:
                if self._board.completed:
                    game_log.info('GAME COMPLETED.')
                elif self._board.failed and self._board.open_mines > self.config.forgiveness:
                    game_log.info('GAME FAILED.')
                
            if self._board.completed or self._board.failed:
                logutils.save_board(f'game_user_{games_finished}.npz',
                                    self._board.mine_layout,
                                    self._board.open_layout,
                                    self._board.flag_layout)
                games_finished += 1
                self.new_game()
            
            # TODO determine feedback

            # update screen
            updated_rects = self._grid.redraw()
            pygame.display.update(updated_rects)
        
            # calculate processing time and amount of delay needed for desired framerate
            tick_clock.tick_delay()

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
