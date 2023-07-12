from pysat.solvers import Solver
from pysat.formula import CNF

solvers = ['cadical103',
           'cadical153',
           'gluecard30',
           'gluecard41',
           'glucose30',
           'glucose42',
           'lingeling',
           'maplechrono',
           'maplecm',
           'maplesat',
           'mergesat3',
           'minicard',
           'minisat22',
           'minisat-gh']

def test_solvers():
    cnf = CNF(from_clauses=[[1, 2, 3], [-1, 2], [-2]])

    for name in solvers:
        print("Name = {}".format(name))
        with Solver(name=name, bootstrap_with=cnf) as solver:
            solver.solve()
            stats = solver.accum_stats()
            assert 'conflicts' in stats, 'No conflicts for {0}'.format(name)
            assert 'decisions' in stats, 'No decisions for {0}'.format(name)
            assert 'propagations' in stats, 'No propagations for {0}'.format(name)
            assert 'restarts' in stats, 'No restarts for {0}'.format(name)
