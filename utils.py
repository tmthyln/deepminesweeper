from collections import namedtuple, deque

import pygame

from typing import Deque, Literal


################################################################################
#                               Data Structures                                #
################################################################################

class TimeMovingAverage:
    """
    Computes a moving average over a time series, producing a windowed average (can be either unweighted or weighted
    by duration).
    
    All times are assumed to be in milliseconds.
    
    Example:
        Time  |  5  |  2  |  4  |  4
        ------+-----+-----+-----+-----NOW
        Value |  1  |  0  |  0  |  1
        
        If using a window >= 15, the unweighted average returned is 0.50 and the weighted average returned is 0.60.
        If using a window of 12, the unweighted average returned is 0.33 and the weighted average returned is 0.40.
        
        Note that the window excludes any elements that "cross the boundary," i.e. will not include any elements that
        make the total amount of time exceed the window size.
    """
    TimeValue = namedtuple('TimeValue', ['time', 'value'])
    
    def __init__(self, time_window_ms: int = 20_000, method: Literal['weighted', 'unweighted'] = 'unweighted'):
        """
        :param time_window_ms: size (in ms) of the averaging window
        :param method: averaging method, either 'weighted' or 'unweighted' (default: 'unweighted')
        """
        
        self._method = method
        
        self._time_window_ms = time_window_ms
        self._timeline: Deque[TimeMovingAverage.TimeValue] = deque()
        self._time_stored = 0
        self._value_stored = 0
        self._time_value_stored = 0
        self._saturated = False
        
    def add_next(self, time_ms, value):
        """
        Adds a new element into the moving average.
        
        :param time_ms: duration of the value
        :param value: value to be averaged
        """
        
        # store new value
        self._timeline.append(TimeMovingAverage.TimeValue(time_ms, value))
        self._time_stored += time_ms
        self._value_stored += value
        self._time_value_stored += time_ms * value
        
        # remove earliest values until invariants satisfied
        while len(self._timeline) > 0 and self._time_stored > self._time_window_ms:
            self._saturated = True
            
            next_earliest = self._timeline.popleft()
            self._time_stored -= next_earliest.time
            self._value_stored -= next_earliest.value
            self._time_value_stored -= next_earliest.time * next_earliest.value

    @property
    def saturated(self):
        """
        The moving average is saturated once the full moving average window is filled; otherwise not saturated.
        
        :return: whether the moving average is saturated
        """
        return self._saturated

    @property
    def average(self):
        """
        :return: current (moving) average.
        """
        if self._method == 'weighted':
            return self._time_value_stored / self._time_stored if self._time_stored != 0 else 0.
        else:
            return self._value_stored / len(self._timeline) if len(self._timeline) != 0 else 0.


################################################################################
#                           Timers, Clocks, Tracking                           #
################################################################################

class Delayer:
    """
    A class that manages a consistent tick rate, delaying or slowing the overall tick rate as necessary.
    """
    
    def __init__(self, initial_fps=30):
        self._clock = pygame.time.Clock()
        self._fps = initial_fps
        self._ticks = TimeMovingAverage()
    
    def tick_start(self):
        """Mark the start of the timing cycle."""
        self._clock.tick()
        
    def tick_delay(self, delay=True):
        """
        Ticks once and delays as needed to maintain a consistent tick rate.
        
        :param delay: whether to actually delay the process
        :return: amount of delay time needed
        """
        
        tick_time = self._clock.tick()
        delay_time = max(0, 1000 // self._fps - tick_time)

        self._ticks.add_next(delay_time, 1. if delay_time == 0 else 0.)
        if self._ticks.saturated and delay_time == 0:
            print(f'A tick overloaded, lagging... ({100 * self.lag_ratio:.2f}% of ticks lagging)')
        
        # TODO: adaptive framerate? (lagging in no more than 10% of ticks) to prevent backlogs
        if delay:
            pygame.time.delay(delay_time)
        
        return delay_time
        
    @property
    def lag_ratio(self):
        """
        :return: average proportion of ticks lagging
        """
        
        return self._ticks.average


class TickRepeater:
    """
    A simple class to manage periodic events based on the number of cycles/ticks passed.
    
    Typical Code Usage:
        ticker = TickRepeater(20)
        
        while <condition>:
            if ticker.tick():
                <do periodic work>
    """
    def __init__(self, repeat: int, initial_delay: int = 0):
        """
        Sets up a tick counter with a specific periodicity and initial delay.
        
        :param repeat: number of ticks to wait between executions
        :param initial_delay: initial number of ticks to wait before the first execution
        """
        self._repeat_interval = repeat
        self._wait_ticks = initial_delay
        
    def tick(self) -> bool:
        """
        Tick once.
        
        :return: if an execution should occur
        """
        self._wait_ticks -= 1
        
        if self._wait_ticks <= 0:
            self._wait_ticks = self._repeat_interval
            return True
        else:
            return False
