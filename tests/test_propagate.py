from pysat.card import *
from pysat.solvers import Solver

solvers = ['cadical153',
           'cadical195',
           'gluecard30',
           'gluecard41',
           'glucose30',
           'glucose41',
           'glucose42',
           'maplechrono',
           'maplecm',
           'maplesat',
           'minicard',
           'mergesat3',
           'minisat22',
           'minisat-gh']

def test_solvers():
    cnf = CardEnc.atmost(lits=range(1, 6), bound=1, encoding=EncType.pairwise)

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf) as solver:
            for l in range(1, 6):
                st, lits = solver.propagate(assumptions=[l], phase_saving=1)
                assert st, 'wrong status of {0} after propagate()'.format(name)
                assert [lits[0]] + sorted(lits[1:], key=lambda l: abs(l)) == [l] + [-l2 for l2 in range(1, 6) if l2 != l], 'wrong list of propagated literals: {0}'.format(lits)

                solver.solve(assumptions=[3])

            solver.solve()

            solver.add_clause([2])
            st, lits = solver.propagate(assumptions=[1])
            assert not st, 'wrong status of {0} after propagate()'.format(name)
            assert not lits, 'wrong list of propagated literals: {0}'.format(lits)
