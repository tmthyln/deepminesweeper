from typing import Sequence

import pygame

from minesweeper.board import OnScreen


class StatusBar(OnScreen):
    height_per_line = 30
    
    def __init__(self, screen: pygame.Surface, rect: pygame.Rect, config):
        self._screen = screen
        self._rect = rect
        self._config = config
        
        self._values = {None: ''}
        self._font = pygame.font.Font(pygame.font.match_font('courier'), 14)
        
        self.redraw()
    
    def realign(self, screen, rect):
        self._screen = screen
        self._rect = rect
    
    def resize(self, screen, rect):
        self._screen = screen
        self._rect = rect
    
    def redraw(self) -> Sequence[pygame.Rect]:
        # redraw background
        self._screen.fill(self._config.bg_color, rect=self._rect)
        
        def render_status(text, left):
            text = self._font.render(text, True, (255, 0, 0))
            text_rect = text.get_rect()
            text_rect.centery = self._rect.centery
            text_rect.left = self._rect.left + left + abs(self._rect.h - text_rect.h) // 2
            self._screen.blit(text, text_rect)
        
        # render main text
        render_status(self._values[None], 0)
        
        # render auxiliary statuses
        others = [val for key, val in self._values.items() if key is not None]
        for i, other_text in enumerate(others):
            render_status(other_text, self._rect.w // 3 + 2 * self._rect.w // 3 * i // len(others))
        
        return [self._rect]
    
    def update(self, val, key=None):
        self._values[key] = val
    
    @property
    def rect(self):
        return self._rect
    
    @classmethod
    def get_preferred_rect(cls, available_space: pygame.Rect, lines: int):
        status_rect = available_space.copy()
        status_rect.h = cls.height_per_line * lines
        status_rect.bottom = available_space.bottom
        return status_rect
