import pytest
from pytest import approx

from utils import TimeMovingAverage


class TestTimeMovingAverage:
    
    @pytest.fixture
    def window(self):
        return 15
    
    @pytest.fixture(params=['weighted', 'unweighted'])
    def avg(self, request, window):
        return TimeMovingAverage(window, method=request.param)
    
    @pytest.mark.parametrize('window', [20])
    def test_single_item(self, avg):
        avg.add_next(20, 5)
        assert avg.average == 5

    @pytest.mark.parametrize('window', list(range(1, 100)))
    def test_saturation_with_units(self, avg, window):
        for val in range(1, window):
            avg.add_next(1, val)
            assert not avg.saturated
        
        avg.add_next(1, window)
        assert avg.saturated

    @pytest.mark.parametrize('unit', list(range(1, 20, 3)))
    @pytest.mark.parametrize('end', list(range(2, 100)))
    def test_equal_times(self, unit, end):
        """Having equal time steps must imply weighted and unweighted are approximately the same."""
        weighted = TimeMovingAverage(end // 2, method='weighted')
        unweighted = TimeMovingAverage(end // 2, method='unweighted')
        
        for val in range(end):
            weighted.add_next(unit, val)
            unweighted.add_next(unit, val)
        
        assert weighted.average == approx(unweighted.average)

    @pytest.mark.parametrize('window', [15])
    def test_docs_example1(self, avg):
        avg.add_next(5, 1)
        avg.add_next(2, 0)
        avg.add_next(4, 0)
        avg.add_next(4, 1)

        if avg.method == 'unweighted':
            assert avg.average == 0.50
        else:
            assert avg.average == 0.60

    @pytest.mark.parametrize('window', [12])
    def test_docs_example2(self, avg):
        avg.add_next(5, 1)
        avg.add_next(2, 0)
        avg.add_next(4, 0)
        avg.add_next(4, 1)
        
        if avg.method == 'unweighted':
            assert avg.average == approx(1/3)
        else:
            assert avg.average == 0.40
