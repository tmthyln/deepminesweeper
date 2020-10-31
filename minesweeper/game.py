import os
import re
import sys
from dataclasses import dataclass
from typing import Type

import pygame
from pygame.locals import *

import minesweeper.logutils as logutils
from minesweeper.actions import Action, ActionType
from minesweeper.board import HiddenBoardState
from minesweeper.boards import SquareBoard, SquareGrid
from minesweeper.config import Config
from minesweeper.elements import StatusBar
from minesweeper.seeders import uniform_random
from minesweeper.utils import Delayer

game_log = logutils.get_logger('game')


def primary_clicked(event: pygame.event.Event):
    return event.type == MOUSEBUTTONUP and event.button == 1


def secondary_clicked(event: pygame.event.Event):
    return event.type == MOUSEBUTTONUP and event.button == 3


@dataclass(eq=False)
class GameWindow:
    config: Type[Config]
    
    def __post_init__(self):
        pygame.init()
        pygame.display.set_caption(self.config.window_title)
        pygame.display.set_icon(pygame.image.load(os.path.join(self.config.res_dir, self.config.favicon_file)))

        self.screen = pygame.display.set_mode(self.config.window_size, flags=pygame.RESIZABLE)

        self.screen.fill(self.config.bg_color)
        pygame.display.update()

        # status bar
        status_rect = StatusBar.get_preferred_rect(self.screen.get_rect(), 1)
        self.status_bar = StatusBar(self.screen, status_rect, self.config)

        # grid
        grid_rect = self.screen.get_rect().copy()
        grid_rect.h -= status_rect.h
        grid_rect.top = self.screen.get_rect().top
        self.grid = SquareGrid(self.screen, grid_rect, self.config)

    def realign(self, new_size: (int, int)):
        self.screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
    
        self.screen.fill(self.config.bg_color)
        pygame.display.update()
    
        # status bar
        status_rect = StatusBar.get_preferred_rect(self.screen.get_rect(), 1)
        self.status_bar.realign(self.screen, status_rect)
    
        # grid
        grid_rect = self.screen.get_rect().copy()
        grid_rect.h -= status_rect.h
        grid_rect.top = self.screen.get_rect().top
        self.grid.realign(self.screen, grid_rect)

    def resize(self, new_size: (int, int)):
        self.screen = pygame.display.set_mode(new_size, flags=pygame.RESIZABLE)
    
        self.screen.fill(self.config.bg_color)
    
        # status bar
        status_rect = StatusBar.get_preferred_rect(self.screen.get_rect(), 1)
        self.status_bar.resize(self.screen, status_rect)
    
        # grid
        grid_rect = self.screen.get_rect().copy()
        grid_rect.h -= status_rect.h
        grid_rect.top = self.screen.get_rect().top
        self.grid.resize(self.screen, grid_rect)
        
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
                self.realign(new_size=(event.w, event.h))
                yield event
            elif event.type == MOUSEMOTION:
                self.status_bar.update(f'cell: {self.grid.pos_of(event.pos)}', key='mouse_debug')
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


################################################################################
#                              Game State Machine                              #
################################################################################

# noinspection PyPep8Naming
class state(object):
    
    def __init__(self, f):
        self.func = f

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __get__(self, instance, owner):
        from functools import partial
        return partial(self.__call__, instance)


class Game:
    def __init__(self, config: Type[Config]):
        self.config = config
        
        self.game_window = GameWindow(config)
        self.board = SquareBoard(self.game_window.grid, uniform_random(0.2), config)
        self.curr_state = self._new_game
        self.games_finished = 0
        self.games_completed = 0

    ############################################################################
    #                             State Functions                              #
    ############################################################################
    
    @state
    def _new_game(self, *args):
        self.board = SquareBoard(self.game_window.grid, uniform_random(0.2), self.config)
        self._last_reward = 0.
        
        self.game_window.status_bar.update('')
        
        yield
        
        if self.config.good_first_select:
            game_log.debug('Changing state: new_game --> first_select')
            return self._first_select
        else:
            game_log.debug('Changing state: new_game --> playing')
            return self._playing
    
    @state
    def _first_select(self, *args):
        while True:
            for event in self.game_window.events():
                if primary_clicked(event) or secondary_clicked(event):
                    self.board.first_select(self.game_window.grid.pos_of(event.pos))
                    game_log.debug('Changing state: first_select --> playing')
                    return self._playing
            
            yield

    @state
    def _playing(self, *args):
        while True:
            actions = []
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
        
            if self.config.superchord == 'auto' and len(actions) > 0:
                add_action(Action.superchord())

            masked_proximity = self.board.proximity_matrix.copy()
            masked_proximity[~self.board.open_layout] = 0
            next_board_state = HiddenBoardState(
                    openable=~self.board.open_layout & ~self.board.flag_layout,
                    flagged=self.board.flag_layout,
                    proximity=masked_proximity)
            
            agent_actions = (yield next_board_state, self._last_reward)  # TODO change reward to status
            if agent_actions is not None:
                actions.extend(agent_actions)
        
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
        
            if any(map(lambda a: a.type == ActionType.SURRENDER, actions)):
                game_log.debug('Changing state: playing --> game_end')
                return self._game_end
        
            # TODO determine feedback
            
            self.game_window.status_bar.update(
                    f'{self.board.open_mines + self.board.flags}/{self.board.mines} mines',
                    key='mines')
            self.game_window.status_bar.update(
                    f'{100*self.board.open_cells/(self.board.cells - self.board.mines):.2f}% cleared',
                    key='cleared')
            
            if self.board.failed or self.board.completed:
                game_log.debug('Changing state: playing --> game_end')
                return self._game_end
    
    @state
    def _game_end(self, *args):
        self.games_finished += 1
        
        if self.board.completed:
            self.games_completed += 1
            game_log.info('GAME COMPLETED.')
            self.game_window.status_bar.update('Game completed.')
        elif self.board.failed:
            game_log.info('GAME FAILED.')
            self.game_window.status_bar.update('Game failed.')

        self.game_window.status_bar.update(f'{self.games_completed} games won of {self.games_finished}', key='wins')

        # TODO add game end callbacks/hooks
        
        #logutils.save_board(f'game_user_{self.games_finished}.npz',
        #                    self.board.mine_layout,
        #                    self.board.open_layout,
        #                    self.board.flag_layout)
        
        while True:
            for event in self.game_window.events():
                if event.type == KEYDOWN or event.type == MOUSEBUTTONUP:
                    game_log.debug('Changing state: game_end --> new_game')
                    return self._new_game
            
            yield

    ############################################################################
    #                                Game Loop                                 #
    ############################################################################
    
    def run(self, agent=None):
        tick_clock = Delayer(initial_fps=self.config.fps)
        
        # TODO automake directory (maybe put into logutils)
        _, _, files = next(os.walk('runs/'))
        save_filename_pattern = re.compile(r'^game_user_(\d+).npz$')
        for filename in files:
            match = save_filename_pattern.match(filename)
            self.games_finished = max(self.games_finished, int(match[1]))
        self.games_finished += 1

        if agent:
            agent.start(self.game_window.grid.size, self.config)
        
        self.game_window.redraw()

        game_log.info('Starting the Minesweeper game.')
        tick_clock.tick_start()
        
        while True:
            state_generator = self.curr_state()
            try:
                while True:
                    next_value = next(state_generator)
                    if agent and next_value is not None:
                        agent_actions = agent.act(next_value[0])
                        if len(agent_actions) > 0:
                            reactive_state_status = state_generator.send(agent_actions)
                            agent.react(*reactive_state_status)
                    
                    self.game_window.redraw()
                    tick_clock.tick_delay()
            except StopIteration as e:
                self.curr_state = e.value

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

