from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import MinisatGH

def test_equals1():
    encs = list(filter(lambda name: not name.startswith('__') and name != 'native', dir(EncType)))
    for l in range(10, 20):
        for e in encs:
            for b in (1, l - 1):
                cnf = CardEnc.equals(lits=list(range(1, l + 1)), bound=b,
                        encoding=getattr(EncType, e))

                # enumerating all models
                with MinisatGH(bootstrap_with=cnf) as solver:
                    for num, model in enumerate(solver.enum_models(), 1):
                        solver.add_clause([-l for l in model[:l]])

                assert num == l, 'wrong number of models for Equals-1-of-{0} ({1})'.format(l, e)
