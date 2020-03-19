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
    height_per_line = 30
    
    def __init__(self, screen: pygame.Surface, rect: pygame.Rect, config):
        self._screen = screen
        self._rect = rect
        self._config = config
        
        self._values = {None: ''}
        self._font = pygame.font.Font(pygame.font.match_font('courier'), 14)
    
    def redraw(self) -> Sequence[pygame.Rect]:
        # redraw background
        self._screen.fill(self._config.bg_color, rect=self._rect)

        # render the main text
        text = self._font.render(self._values[None], True, (255, 0, 0))
        text_rect = text.get_rect()
        text_rect.centery = self._rect.centery
        text_rect.left = abs(self._rect.h - text_rect.h) // 2
        
        self._screen.blit(text, text_rect)
        
        return [self._rect]
    
    def update(self, val, key=None):
        self._values[key] = val
    
    @classmethod
    def get_preferred_rect(cls, available_space: pygame.Rect, lines: int):
        status_rect = available_space.copy()
        status_rect.h = cls.height_per_line * lines
        status_rect.bottom = available_space.bottom
        return status_rect


class GameWindow:
    def __init__(self, config: Config.__class__):
        self.config: Config.__class__ = config

        pygame.init()
        pygame.display.set_caption(config.window_title)
        pygame.display.set_icon(pygame.image.load(os.path.join(config.res_dir, config.favicon_file)))
        
        self._resize(config.window_size)
        self._new_game()

    def _resize(self, new_size: (int, int) = None):
        if new_size is not None:
            self._screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
    
        self._screen.fill(self.config.bg_color)
        
        # status bar
        status_rect = StatusBar.get_preferred_rect(self._screen.get_rect(), 1)
        self._status_bar = StatusBar(self._screen, status_rect, self.config)
        self._status_bar.redraw()
        
        # grid
        grid_rect = self._screen.get_rect()
        grid_rect.h -= status_rect.h
        grid_rect.top = self._screen.get_rect().top
        self._grid = SquareGrid(self._screen, grid_rect, self.config)
        self._grid.redraw(force=True)
        
        pygame.display.update()
        
    def _new_game(self):
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
                    self._resize(new_size=(event.w, event.h))
                    self._new_game()
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
                    self._status_bar.update('Game completed.')
                elif self._board.failed:
                    game_log.info('GAME FAILED.')
                    self._status_bar.update('Game failed.')
                
            if self._board.completed or self._board.failed:
                logutils.save_board(f'game_user_{games_finished}.npz',
                                    self._board.mine_layout,
                                    self._board.open_layout,
                                    self._board.flag_layout)
                games_finished += 1
                self._new_game()
            
            # TODO determine feedback

            # update screen
            updated_rects = []
            updated_rects.extend(self._grid.redraw())
            updated_rects.extend(self._status_bar.redraw())
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
