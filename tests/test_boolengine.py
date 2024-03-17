from pysat.card import *
from pysat.engines import *
from pysat.formula import CNF
from pysat.solvers import Solver

def test_propagate():
        cnf = CNF()
        leq1 = CardEnc.atmost(list(range(1, 6)), bound=2, encoding=EncType.native)
        leq1 = [leq1.atmosts[0][0], leq1.atmosts[0][1]]

        leq2 = CardEnc.atleast(list(range(1, 6)), bound=1, encoding=EncType.native)
        leq2 = [leq2.atmosts[0][0], leq2.atmosts[0][1]]

        with Solver(name='cadical195', bootstrap_with=cnf) as solver:
            engine = BooleanEngine([('linear', leq1), ('linear', leq2)], adaptive=True)
            solver.connect_propagator(engine)
            engine.setup_observe(solver)
            n1 = 0
            for model in solver.enum_models():
                n1 += 1

        vpool = IDPool()
        cnf = CardEnc.atmost(list(range(1, 6)), bound=2, vpool=vpool, encoding=EncType.kmtotalizer)
        cnf.extend(CardEnc.atleast(list(range(1, 6)), bound=1, vpool=vpool, encoding=EncType.kmtotalizer))

        with Solver(name='cadical195', bootstrap_with=cnf) as solver:
            n2 = 0
            for model in solver.enum_models():
                solver.add_clause([-l for l in model[:5]])
                n2 += 1

        assert n1 == n2, 'Wrong number of models from the propagator'
