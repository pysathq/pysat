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
    with Solver(bootstrap_with=[[1]]) as solver:
        assert list(solver.enum_models(assumptions=[-1], projection=[])) == []
        assert list(solver.enum_models(projection=[])) == [[]]
        assert not solver.solve()


def test_projected_model_is_blocked_before_yield():
    with Solver(bootstrap_with=[[1, 2]]) as solver:
        first = next(solver.enum_models(projection=[2]))
        assert not solver.solve(assumptions=first)
        assert list(solver.enum_models(projection=[2])) == [[-first[0]]]


@pytest.mark.parametrize('projection,error', [([0], ValueError), ([-1], ValueError),
                                               ([1, 1], ValueError), ([2], ValueError),
                                               ([1.5], TypeError)])
def test_bad_projection_does_not_block(projection, error):
    with Solver(bootstrap_with=[[1]]) as solver:
        with pytest.raises(error):
            list(solver.enum_models(projection=projection))
        assert solver.solve()


def test_nonincremental_solver_rejects_projection():
    with Solver(name='kissat404', bootstrap_with=[[1]]) as solver:
        with pytest.raises(NotImplementedError):
            list(solver.enum_models(projection=[1]))
