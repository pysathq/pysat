from pysat.solvers import Solver
from pysat.formula import CNF

solvers = ['cadical',
           'glucose30',
           'glucose41',
           'lingeling',
           'maplechrono',
           'maplecm',
           'maplesat',
           'minicard',
           'minisat22',
           'minisat-gh']

def test_solvers():
    cnf = CNF(from_clauses=[[1, 2, 3], [-1, 2], [-2]])

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf) as solver:
            assert solver.solve(), 'wrong outcome by {0}'.format(name)
            assert solver.get_model() == [-1, -2, 3], 'wrong model by {0}'.format(name)
