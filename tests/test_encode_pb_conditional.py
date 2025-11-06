from pysat.formula import IDPool
from pysat.card import CardEnc
import pytest

@pytest.mark.skip(reason="PBLIB not installed in CI")
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

    assert cnf.clauses == [[-4]] # without PR to pblib this will be [[3, -4], [1, -4], [2, -4], [-4]]

    bound = 2

    # Generate the CNF clauses
    cnf = PBEnc.atleast(
        lits=LITS,
        weights=WEIGHTS,
        bound=bound,
        vpool=vpool,
        conditionals=CONDS
    )

    assert cnf.clauses == [[5], [-5, 6], [3, 6], [-5, 3, 7], [2, 6], [-5, 2, 7], [3, 2, 7], [-5, 3, 2, 8], [1, 9], [-7, 9], [1, -7, 10], [-10, -4]]

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

