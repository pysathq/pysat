import pytest

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver


@pytest.mark.parametrize('name', ['g3', 'm22', 'cd19'])
def test_project_cardinality_encoding(name):
    formula = CardEnc.atmost([1, 2, 3, 4], bound=2, encoding=EncType.seqcounter)
    with Solver(name=name, bootstrap_with=formula) as solver:
        full = list(solver.enum_models(assumptions=[-2]))
    expected = {(m[3], m[0]) for m in full}
    assert len(full) > len(expected)
    with Solver(name=name, bootstrap_with=formula) as solver:
        models = list(solver.enum_models(assumptions=iter([-2]), projection=iter([4, 1])))
        assert len(models) == len(expected)
        assert set(map(tuple, models)) == expected
        assert not solver.solve(assumptions=[-2])


def test_empty_projection():
    with Solver(bootstrap_with=[[1, 2]]) as solver:
        assert sorted(solver.enum_models(projection=[])) == [[-1, 2], [1, -2], [1, 2]]


@pytest.mark.parametrize('projection', [[0], [-1], [1, 1], [2]])
def test_bad_projection_does_not_block(projection):
    with Solver(bootstrap_with=[[1]]) as solver:
        with pytest.raises(ValueError):
            list(solver.enum_models(projection=projection))
        assert solver.solve()


def test_nonincremental_solver_rejects_projection():
    with Solver(name='kissat404', bootstrap_with=[[1]]) as solver:
        with pytest.raises(NotImplementedError):
            list(solver.enum_models(projection=[1]))
