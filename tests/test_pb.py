import itertools
import random

import pytest

from pysat.formula import IDPool
from pysat.solvers import Solver

pytest.importorskip("pindakaas")

from pysat.pb import PBEnc, EncType

ENCODINGS = [EncType.best, EncType.bdd, EncType.seqcounter,
             EncType.sortnetwrk, EncType.adder, EncType.binmerge,
             EncType.watchdog, EncType.totalizer, EncType.mixedradix]

COMPARATORS = {
    'leq': lambda s, k: s <= k,
    'geq': lambda s, k: s >= k,
    'equals': lambda s, k: s == k,
}


def check(cnf, lits, weights, bound, holds):
    """Every assignment of the inputs extends to a model iff the constraint holds."""
    with Solver(bootstrap_with=cnf.clauses) as solver:
        for vals in itertools.product([False, True], repeat=len(lits)):
            total = sum(w for l, w, v in zip(lits, weights, vals) if (l > 0) == v)
            assumps = [abs(l) if v else -abs(l) for l, v in zip(lits, vals)]
            assert solver.solve(assumptions=assumps) == holds(total, bound)


@pytest.mark.parametrize('encoding', ENCODINGS)
@pytest.mark.parametrize('cmp', COMPARATORS)
def test_semantics(encoding, cmp):
    rng = random.Random(encoding * 10 + len(cmp))
    for _ in range(10):
        n = rng.randint(1, 5)
        lits = [v if rng.random() < 0.7 else -v for v in range(1, n + 1)]
        weights = [rng.randint(1, 6) for _ in lits]
        bound = rng.randint(0, sum(weights) + 1)

        cnf = getattr(PBEnc, cmp)(lits=lits, weights=weights, bound=bound,
                                  encoding=encoding)
        assert all(abs(l) <= cnf.nv for cl in cnf.clauses for l in cl)
        check(cnf, lits, weights, bound, COMPARATORS[cmp])


def test_pairs_input():
    cnf = PBEnc.atleast([(-1, 2), (2, 3)], bound=3)
    check(cnf, [-1, 2], [2, 3], 3, COMPARATORS['geq'])


def test_vpool():
    # auxiliary variables start after the top id or the pool
    for kwargs in ({'top_id': 7}, {'vpool': IDPool(start_from=8)}):
        cnf = PBEnc.leq([1, 2, 3], [2, 3, 4], bound=5, **kwargs)
        aux = {abs(l) for cl in cnf.clauses for l in cl} - {1, 2, 3}
        assert aux and min(aux) > 7 and cnf.nv >= max(aux)

    # occupied ranges are skipped, and conditionals above the pool are kept
    vpool = IDPool(start_from=11, occupied=[[5, 9], [12, 15]])
    cnf = PBEnc.atmost([1, 2, 3], [2, 3, 4], bound=5, vpool=vpool, conditionals=[14])
    aux = {abs(l) for cl in cnf.clauses for l in cl} - {1, 2, 3, 14}
    assert aux and not any(5 <= v <= 9 or 12 <= v <= 15 for v in aux)
    assert vpool.top == cnf.nv >= max(aux)
    check(cnf, [1, 2, 3, 14], [2, 3, 4, 9], 14, COMPARATORS['leq'])  # 14 -> sum <= 5


def test_native():
    cnf = PBEnc.equals([1, 2, 3], [2, 3, 4], bound=5, encoding=EncType.native)
    assert cnf.atmosts == [([1, 2, 3], 5, [2, 3, 4]), ([-1, -2, -3], 4, [2, 3, 4])]
