from collections import namedtuple
from typing import Tuple, Union

from pytest import approx

from utils import TimeMovingAverage


MovingAveragers = namedtuple('MovingAveragers', ['weighted', 'unweighted'])


class TestTimeMovingAverage:
    
    def new_averagers(self, window: Union[int, Tuple[int, int]]):
        if isinstance(window, int):
            window = (window, window)
        
        return MovingAveragers(
                TimeMovingAverage(window[0], method='weighted'),
                TimeMovingAverage(window[0], method='unweighted')
        )
    
    def test_single_item(self):
        avgs = self.new_averagers((20, 15))
        
        avgs.weighted.add_next(20, 5)
        assert avgs.weighted.average == 5
        
        avgs.unweighted.add_next(15, 7)
        assert avgs.unweighted.average == 7
    
    def test_saturation_with_units(self):
        for window in range(1, 100):
            avgs = self.new_averagers(window)
            
            for avg in avgs:
                for val in range(1, window):
                    avg.add_next(1, val)
                    assert not avg.saturated
                
                avg.add_next(1, window)
                assert avg.saturated
    
    def test_equal_times(self):
        """Having equal time steps must imply weighted and unweighted are approximately the same."""
        
        for unit in range(1, 20, 3):
            for end in range(2, 250):
                avgs = self.new_averagers(end // 2)
                
                for val in range(end):
                    for avg in avgs:
                        avg.add_next(unit, val)
                
                assert avgs.weighted.average == approx(avgs.unweighted.average)
    
    def test_docs_example1(self):
        avgs = self.new_averagers(15)
        
        for avg in avgs:
            avg.add_next(5, 1)
            avg.add_next(2, 0)
            avg.add_next(4, 0)
            avg.add_next(4, 1)

        assert avgs.unweighted.average == 0.50
        assert avgs.weighted.average == 0.60

    def test_docs_example2(self):
        avgs = self.new_averagers(12)
        
        for avg in avgs:
            avg.add_next(5, 1)
            avg.add_next(2, 0)
            avg.add_next(4, 0)
            avg.add_next(4, 1)

        assert avgs.unweighted.average == approx(1/3)
        assert avgs.weighted.average == 0.40
