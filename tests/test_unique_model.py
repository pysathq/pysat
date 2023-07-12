from pysat.solvers import Solver
from pysat.formula import CNF

solvers = ['cadical103',
           'cadical153',
           'gluecard30',
           'gluecard41',
           'glucose30',
           'glucose41',
           'glucose42',
           'lingeling',
           'maplechrono',
           'maplecm',
           'maplesat',
           'minicard',
           'mergesat3',
           'minisat22',
           'minisat-gh']

def test_solvers():
    cnf = CNF(from_clauses=[[1, 2, 3], [-1, 2], [-2]])

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf) as solver:
            assert solver.solve(), 'wrong outcome by {0}'.format(name)
            assert solver.get_model() == [-1, -2, 3], 'wrong model by {0}'.format(name)

            solver.add_clause([-l for l in solver.get_model()])
            assert not solver.solve(), 'wrong outcome by {0}'.format(name)
