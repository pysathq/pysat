import pytest
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

@pytest.mark.parametrize('solver_name', ['m22', 'mgh', 'mep'])
def test_atmost1(solver_name):
    encs = list(filter(lambda name: not name.startswith('__') and name != 'native', dir(EncType)))
    for l in range(10, 20):
        for e in encs:
            cnf = CardEnc.atmost(lits=list(range(1, l + 1)), bound=1, encoding=getattr(EncType, e))

            # enumerating all models
            with Solver(name=solver_name, bootstrap_with=cnf) as solver:
                for num, model in enumerate(solver.enum_models(), 1):
                    solver.add_clause([-l for l in model[:l]])

            assert num == l + 1, 'wrong number of models for AtMost-1-of-{0} ({1}) using {2}'.format(l, e, solver_name)
