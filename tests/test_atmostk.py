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
