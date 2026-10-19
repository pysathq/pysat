from pysat.formula import IDPool
from pysat.card import CardEnc
import itertools
import pytest
from pysat.solvers import Solver

pytest.importorskip("pindakaas")

def test_pbenc_conditional():
    from pysat.pb import PBEnc, EncType
    L = 3
    LITS = list(range(1, L + 1))  # Variables x1, x2, x3, x4
    WEIGHTS = [2, 1, 1]        # Coefficients: 2*x1 + 3*x2 + 5*x3 + 8*x4
    bound = 10                 # Constraint: ... <= 10

    CONDS = [L+1]

    # We need a vpool even if we don't use it, to handle PySAT internal structure
    vpool = IDPool()

    # Generate the CNF clauses
    cnf = PBEnc.atleast(
        lits=LITS,
        weights=WEIGHTS,
        bound=bound,
        vpool=vpool,
        conditionals=CONDS
    )

    assert cnf.clauses == [[-4]]

    bound = 2

    # Generate the CNF clauses
    cnf = PBEnc.atleast(
        lits=LITS,
        weights=WEIGHTS,
        bound=bound,
        vpool=vpool,
        conditionals=CONDS
    )

    # the constraint must hold whenever the condition is true
    with Solver(bootstrap_with=cnf.clauses) as solver:
        for vals in itertools.product([False, True], repeat=L + 1):
            assumps = [l if v else -l for l, v in zip(LITS + CONDS, vals)]
            holds = sum(w for w, v in zip(WEIGHTS, vals) if v) >= bound
            assert solver.solve(assumptions=assumps) == (holds or not vals[-1])

    bound = 0

    # Generate the CNF clauses
    cnf = PBEnc.atleast(
        lits=LITS,
        weights=WEIGHTS,
        bound=bound,
        vpool=vpool,
        conditionals=CONDS
    )

    assert cnf.clauses == []

