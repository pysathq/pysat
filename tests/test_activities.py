import math

import pysolvers
import pytest

from pysat.examples.genhard import PHP
from pysat.solvers import Solver, ergo_present

solvers = ['gluecard30',
           'gluecard41',
           'glucose30',
           'glucose41',
           'glucose421',
           'minicard',
           'minisat22',
           'minisat-gh',
           'minisatep'] + (['ergo'] if ergo_present else [])


@pytest.mark.parametrize('name', solvers)
def test_set_get_roundtrip(name):
    with Solver(name=name, bootstrap_with=[[1, 2], [-2, 3]]) as s:
        s.set_activities({1: 3.0, 2: 0.5, 5: 7.0})
        # unlisted 3 drops to 0, unknown 100 reports 0
        assert s.get_activities([5, 1, 2, 3, 100]) == {5: 7.0, 1: 3.0, 2: 0.5, 3: 0.0, 100: 0.0}
        assert s.get_activities([]) == {}
        assert s.solve()


@pytest.mark.parametrize('name', solvers)
def test_unlisted_drop_to_zero(name):
    with Solver(name=name, bootstrap_with=PHP(5).clauses) as s:
        assert not s.solve()
        nv = s.nof_vars()
        assert any(a > 0 for a in s.get_activities(range(1, nv + 1)).values())

        s.set_activities({1: 1.0})
        acts = s.get_activities(range(1, nv + 1))
        assert acts[1] == 1.0 and all(a == 0.0 for v, a in acts.items() if v != 1)

        # the search goes on from the new ordering
        assert not s.solve()


@pytest.mark.parametrize('name', solvers)
def test_order_drives_decisions(name):
    with Solver(name=name, bootstrap_with=[[-1, 2], [-3, -2]]) as s:
        s.set_phases([1, 2, 3])
        s.set_activities({1: 2.0, 3: 1.0})
        assert s.solve() and s.get_model() == [1, 2, -3]

        s.set_phases([1, 2, 3])  # undo phase saving
        s.set_activities({3: 2.0, 1: 1.0})
        assert s.solve() and s.get_model() == [-1, -2, 3]


@pytest.mark.parametrize('name', solvers)
def test_bad_input(name):
    with Solver(name=name, bootstrap_with=[[1, 2]]) as s:
        for bad in ({-1: 1.0}, {0: 1.0}, {1: math.nan}, {1: 1e101}):
            with pytest.raises(pysolvers.error):
                s.set_activities(bad)
        with pytest.raises(pysolvers.error):
            s.get_activities([-1])
        with pytest.raises(ValueError):
            s.get_activities([0])

        # nothing changed
        assert s.get_activities([1, 2]) == {1: 0.0, 2: 0.0}


def test_unsupported_solver():
    with Solver(name='cadical195', bootstrap_with=[[1, 2]]) as s:
        with pytest.raises(NotImplementedError):
            s.set_activities({1: 1.0})
        with pytest.raises(NotImplementedError):
            s.get_activities([1])
