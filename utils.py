from collections import namedtuple, deque

import numpy as np
import pygame

from typing import Deque


################################################################################
#                               Data Structures                                #
################################################################################

class TimeMovingAverage:
    TimeValue = namedtuple('TimeValue', ['time', 'value'])
    
    def __init__(self, time_window_ms: int = 20_000, method: str = 'weighted'):
        if method not in ('weighted', 'unweighted'):
            raise ValueError('Invalid averaging method for time-based moving average')
        
        self._method = method
        
        self._time_window_ms = time_window_ms
        self._timeline: Deque[TimeMovingAverage.TimeValue] = deque()
        self._time_stored = 0
        self._value_stored = 0
        
    def add_next(self, time_ms, value):
        self._timeline.append(TimeMovingAverage.TimeValue(time_ms, value))
        self._time_stored += time_ms
        self._value_stored += value
        
        while len(self._timeline) > 0 and self._time_stored > self._time_window_ms:
            next_earliest = self._timeline.popleft()
            self._time_stored -= next_earliest.time
            self._value_stored -= next_earliest.value

    @property
    def average(self):
        if self._method == 'weighted':
            return self._value_stored / self._time_stored if self._time_stored != 0 else 0.
        else:
            return self._value_stored / len(self._timeline) if len(self._timeline) != 0 else 0.


################################################################################
#                           Timers, Clocks, Tracking                           #
################################################################################

class Delayer:
    
    def __init__(self, initial_fps=30):
        self._clock = pygame.time.Clock()
        self._fps = initial_fps
        self._ticks = TimeMovingAverage()
    
    def tick_start(self):
        self._clock.tick()
        
    def tick_delay(self, delay=True):
        tick_time = self._clock.tick()
        delay_time = max(0, 1000 // self._fps - tick_time)

        self._ticks.add_next(delay_time, 1. if delay_time == 0 else 0.)
        if delay_time == 0:
            print(f'A tick overloaded, lagging... ({100 * self.lag_ratio:.2f}% of ticks lagging)')
        
        # TODO: adaptive framerate? (lagging in no more than 10% of ticks) to prevent backlogs
        if delay:
            pygame.time.delay(delay_time)
        
    @property
    def lag_ratio(self):
        return self._ticks.average
