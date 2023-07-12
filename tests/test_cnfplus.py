from pysat.card import *
from pysat.formula import CNFPlus
from pysat.solvers import Solver, SolverNames

# all available solvers
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
           'mergesat3',
           'minicard',
           'minisat22',
           'minisat-gh']

# CNF+ formula with native atmost1 constraint
cnf1 = CardEnc.atmost(lits=range(1, 6), bound=1, encoding=EncType.native)
cnf1.append(range(1, 6))  # at least 1

# just a normal CNF formula
cnf2 = CardEnc.atmost(lits=range(1, 6), bound=1, encoding=EncType.seqcounter)
cnf2.append(range(1, 6))  # at least 1

def test_cnfplus():
    # testing cnf1:
    for name in solvers:
        if name not in ('minicard', 'gluecard30', 'gluecard41'):
            try:
                with Solver(name=name, bootstrap_with=cnf1) as s:
                    s.solve()
                assert False, 'we should not get here'
            except NotImplementedError:
                pass
        else:
            with Solver(name=name, bootstrap_with=cnf1) as s:
                for i, model in enumerate(s.enum_models(), 1):
                    pass
            assert i == 5, 'there should be 5 models'

    for name in solvers:
        if name not in ('minicard', 'gluecard30', 'gluecard41'):
            try:
                with Solver(name=name) as s:
                    s.append_formula(cnf1)
                    s.solve()
                assert False, 'we should not get here'
            except NotImplementedError:
                pass
        else:
            with Solver(name=name) as s:
                s.append_formula(cnf1)
                for i, model in enumerate(s.enum_models(), 1):
                    pass
            assert i == 5, 'there should be 5 models'

def test_cnf():
    # testing cnf2
    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf2) as s:
            for i, model in enumerate(s.enum_models(), 1):
                pass
        assert i == 5, 'there should be 5 models'

    for name in solvers:
        with Solver(name=name) as s:
            s.append_formula(cnf2)
            for i, model in enumerate(s.enum_models(), 1):
                pass
        assert i == 5, 'there should be 5 models'
