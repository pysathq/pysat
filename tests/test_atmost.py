from pysat.formula import IDPool
from pysat.card import CardEnc

def test_atmost():
    vp = IDPool()
    n = 20
    b = 50
    assert n <= b

    lits = [vp.id(v) for v in range(1, n + 1)]
    top = vp.top

    G = CardEnc.atmost(lits, b, vpool=vp)

    assert len(G.clauses) == 0

    try:
        assert vp.top >= top
    except AssertionError as e:
        print(f"\nvp.top = {vp.top} (expected >= {top})\n")
        raise e
