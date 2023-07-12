from pysat.card import CardEnc
from pysat.solvers import Solver

def test_warmstart():
    n, b = 5, 3

    cnf = CardEnc.atmost(range(1, n + 1), b)

    for name in ['m22', 'mgh', 'mpl', 'mcm', 'mc', 'g30', 'g41', 'gc30', 'gc41', 'g42']:
        models1 = []
        with Solver(name=name, bootstrap_with=cnf, warm_start=False) as solver:
            models1 = [model for model in solver.enum_models()]

        with Solver(name=name, bootstrap_with=cnf, warm_start=True) as solver:
            models2 = [model for model in solver.enum_models()]

        assert sorted(models1) == sorted(models2), 'Wrong set/number of models for {0}'.format(name)
