import math
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import MinisatGH

encs = ['seqcounter', 'sortnetwrk', 'cardnetwrk', 'totalizer', 'mtotalizer',
        'kmtotalizer']


def bincoeff(n, k):
    n_fac = math.factorial(n)
    k_fac = math.factorial(k)
    n_minus_k_fac = math.factorial(n - k)
    return int(n_fac / (k_fac * n_minus_k_fac))


def test_atmostk():
    for l in range(5, 10):
        for k in range(2, l):
            for e in encs:
                cnf = CardEnc.atmost(lits=list(range(1, l + 1)), bound=k, encoding=getattr(EncType, e))

                # enumerating all models
                with MinisatGH(bootstrap_with=cnf) as solver:
                    for num, model in enumerate(solver.enum_models(), 1):
                        solver.add_clause([-l for l in model[:l]])

                assert num == sum([bincoeff(l, o + 1) for o in range(k)]) + 1, 'wrong number of models for AtMost-{0}-of-{1} ({2})'.format(k, l, e)
