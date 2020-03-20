import os
import re
import sys
from abc import ABC
from collections import namedtuple
from dataclasses import dataclass
from typing import List, Sequence, Type

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


def primary_clicked(event: pygame.event.Event):
    return event.type == MOUSEBUTTONUP and event.button == 1


def secondary_clicked(event: pygame.event.Event):
    return event.type == MOUSEBUTTONUP and event.button == 3


class StatusBar:
    height_per_line = 30
    
    def __init__(self, screen: pygame.Surface, rect: pygame.Rect, config):
        self._screen = screen
        self._rect = rect
        self._config = config
        
        self._values = {None: ''}
        self._font = pygame.font.Font(pygame.font.match_font('courier'), 14)
        
        self.redraw()
    
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


@dataclass(eq=False)
class GameWindow:
    config: Type[Config]
    
    def __post_init__(self):
        pygame.init()
        pygame.display.set_caption(self.config.window_title)
        pygame.display.set_icon(pygame.image.load(os.path.join(self.config.res_dir, self.config.favicon_file)))
        
        self._resize(self.config.window_size)

    def _resize(self, new_size: (int, int)):
        self.screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
    
        self.screen.fill(self.config.bg_color)
    
        # status bar
        status_rect = StatusBar.get_preferred_rect(self.screen.get_rect(), 1)
        self.status_bar = StatusBar(self.screen, status_rect, self.config)
    
        # grid
        grid_rect = self.screen.get_rect().copy()
        grid_rect.h -= status_rect.h
        grid_rect.top = self.screen.get_rect().top
        self.grid = SquareGrid(self.screen, grid_rect, self.config)
        
        pygame.display.update()
        
    def redraw(self):
        updated_rects = []
        
        updated_rects.extend(self.status_bar.redraw())
        updated_rects.extend(self.grid.redraw())
        
        pygame.display.update(updated_rects)
        
    def events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                game_log.info('Closing Minesweeper')
                sys.exit(0)
            elif self._primary_double_clicked(event):
                game_log.debug(f'double clicked at {event.pos}')
                yield event
            elif primary_clicked(event):
                game_log.debug(f'primary clicked at {event.pos}')
                yield event
            elif secondary_clicked(event):
                game_log.debug(f'secondary key clicked at {event.pos}')
                yield event
            elif event.type == VIDEORESIZE:
                game_log.debug(f'window resized')
                self._resize(new_size=(event.w, event.h))
                yield event
            else:
                yield event

    # noinspection PyDefaultArgument
    def _primary_double_clicked(self, event: pygame.event.Event,
                                _last_clicked_cell=[(-1, -1)], clock=pygame.time.Clock()):
        valid_dbl_click = False

        if event.type == MOUSEBUTTONUP and event.button == 1:
            if clock.tick() <= self.config.double_click_time and \
                    self.grid.pos_of(event.pos) == _last_clicked_cell[0]:
                valid_dbl_click = True

            _last_clicked_cell[0] = self.grid.pos_of(event.pos)

        return valid_dbl_click
        # TODO: maybe implement a multi-click feature


class Game:
    def __init__(self, config: Type[Config]):
        self.config = config
        
        self.game_window = GameWindow(config)
        self.board = SquareBoard(self.game_window.grid, uniform_random(0.2), config)
        self.curr_state = self._new_game
        self.games_finished = 0
        self.games_completed = 0
    
    @property
    def playing(self):
        return self.curr_state in [self._first_select, self._playing]
    
    ############################################################################
    #                             State Functions                              #
    ############################################################################
    
    def _new_game(self, *args):
        self.board = SquareBoard(self.game_window.grid, uniform_random(0.2), self.config)
        self._last_reward = 0.
        
        if self.config.good_first_select:
            game_log.debug('Changing state: new_game --> first_select')
            return self._first_select
        else:
            game_log.debug('Changing state: new_game --> playing')
            return self._playing

    def _first_select(self, *args):
        
        game_log.debug('Changing state: first_select --> playing')
        return self._playing

    def _playing(self, actions, *args):
        add_action = actions.append
        cell_pos = self.game_window.grid.pos_of
    
        # handle user events
        for event in self.game_window.events():
            if self._primary_double_clicked(event):  # TODO: add back in intersection checks
                add_action(Action.chord(cell_pos(event.pos)))
            elif primary_clicked(event):
                pos = cell_pos(event.pos)
                add_action(Action.flag(pos) if self.config.click_to_flag else Action.select(pos))
            elif secondary_clicked(event):
                pos = cell_pos(event.pos)
                add_action(Action.select(pos) if self.config.click_to_flag else Action.flag(pos))
            elif event.type == KEYUP:
                if event.key == K_q:
                    add_action(Action.surrender())
                if self.config.superchord == 'keyup':
                    add_action(Action.superchord())
            elif event.type == VIDEORESIZE:
                return self._new_game
    
        if self.config.superchord == 'auto' and len(actions) > 0:
            add_action(Action.superchord())

        if any(map(lambda a: a.type == ActionType.SURRENDER, actions)):
            game_log.debug('Changing state: playing --> game_end')
            return self._game_end
    
        # process all actions and determine next reward
        for action in actions:
            if action.type == ActionType.SELECT:
                self.board.select(action.pos)
            elif action.type == ActionType.FLAG:
                self.board.toggle_flag(action.pos)
            elif action.type == ActionType.CHORD:
                self.board.chord(action.pos)
            elif action.type == ActionType.SUPERCHORD:
                self.board.superchord()
            else:
                game_log.warning(f'Unknown action: {action}, skipping processing')
    
        # TODO determine feedback
        
        if self.board.failed or self.board.completed:
            game_log.debug('Changing state: playing --> game_end')
            return self._game_end
        else:
            return self._playing
    
    def _game_end(self, *args):
        if self.board.completed:
            game_log.info('GAME COMPLETED.')
            self.game_window.status_bar.update('Game completed.')
        elif self.board.failed:
            game_log.info('GAME FAILED.')
            self.game_window.status_bar.update('Game failed.')

        # TODO add game end callbacks/hooks
        
        logutils.save_board(f'game_user_{self.games_finished}.npz',
                            self.board.mine_layout,
                            self.board.open_layout,
                            self.board.flag_layout)
        self.games_finished += 1
        
        game_log.debug('Changing state: game_end --> new_game')
        return self._new_game

    ############################################################################
    #                                Game Loop                                 #
    ############################################################################
    
    def run(self):
        tick_clock = Delayer(initial_fps=self.config.fps)
        
        # TODO automake directory (maybe put into logutils)
        _, _, files = next(os.walk('runs/'))
        save_filename_pattern = re.compile(r'^game_user_(\d+).npz$')
        for filename in files:
            match = save_filename_pattern.match(filename)
            self.games_finished = max(self.games_finished, int(match[1]))
        self.games_finished += 1
        
        agent_actions = []
        self.game_window.redraw()
        
        tick_clock.tick_start()
        
        while True:
            self.curr_state = self.curr_state(agent_actions)
            self.game_window.redraw()
            
            if self.playing:
                masked_proximity = self.board.proximity_matrix.copy()
                masked_proximity[~self.board.open_layout] = 0
                next_board_state = HiddenBoardState(
                        openable_layout=~self.board.open_layout & ~self.board.flag_layout,
                        flag_layout=self.board.flag_layout,
                        proximity_matrix=masked_proximity)
    
                next_input = (yield next_board_state, self._last_reward)
                agent_actions = next_input if next_input is not None else []  # TODO change reward to a status
                
            # calculate processing time and amount of delay needed for desired framerate
            tick_clock.tick_delay()

    # noinspection PyDefaultArgument
    def _primary_double_clicked(self, event: pygame.event.Event,
                                _last_clicked_cell=[(-1, -1)], clock=pygame.time.Clock()):
        valid_dbl_click = False

        if event.type == MOUSEBUTTONUP and event.button == 1:
            if clock.tick() <= self.config.double_click_time and \
                    self.game_window.grid.pos_of(event.pos) == _last_clicked_cell[0]:
                valid_dbl_click = True

            _last_clicked_cell[0] = self.game_window.grid.pos_of(event.pos)

        return valid_dbl_click
        # TODO: maybe implement a multi-click feature

