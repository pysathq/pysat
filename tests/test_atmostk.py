import math
import pytest
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

encs = ['seqcounter', 'sortnetwrk', 'cardnetwrk', 'totalizer', 'mtotalizer',
        'kmtotalizer']


def bincoeff(n, k):
    n_fac = math.factorial(n)
    k_fac = math.factorial(k)
    n_minus_k_fac = math.factorial(n - k)
    return int(n_fac / (k_fac * n_minus_k_fac))


@pytest.mark.parametrize('solver_name', ['m22', 'mgh', 'mep'])
def test_atmostk(solver_name):
    for l in range(5, 10):
        for k in range(2, l):
            for e in encs:
                cnf = CardEnc.atmost(lits=list(range(1, l + 1)), bound=k, encoding=getattr(EncType, e))

                # enumerating all models
                with Solver(name=solver_name, bootstrap_with=cnf) as solver:
                    for num, model in enumerate(solver.enum_models(), 1):
                        solver.add_clause([-l for l in model[:l]])

                assert num == sum([bincoeff(l, o + 1) for o in range(k)]) + 1, 'wrong number of models for AtMost-{0}-of-{1} ({2}) using {3}'.format(k, l, e, solver_name)


def test_atmostk_vpool_occupied():
    for e in encs:
        pool = IDPool(occupied=[[1, 3], [5, 20]])
        cnf = CardEnc.atmost(lits=[1, 2, 3], bound=1, vpool=pool, encoding=getattr(EncType, e))
        aux = set(abs(l) for cl in cnf.clauses for l in cl) - set([1, 2, 3])
        assert not any(5 <= v <= 20 for v in aux), 'occupied ids used by {0}'.format(e)

        with Solver(bootstrap_with=cnf) as solver:
            for num, model in enumerate(solver.enum_models(), 1):
                solver.add_clause([-l for l in model[:3]])
        assert num == 4, 'wrong number of models for AtMost-1-of-3 using {0}'.format(e)

    # an encoding without auxiliary variables still moves the pool past the range
    pool = IDPool(occupied=[[1, 10]])
    assert CardEnc.atleast(lits=[1, 2, 3], bound=1, vpool=pool).clauses == [[1, 2, 3]]
    assert pool.top >= 10
