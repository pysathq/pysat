from pysat.formula import *
from itertools import permutations

def test_atom_uniqueness():
    x1, x2 = Atom('x'), Atom(object='x')  # same atom
    z = Atom('z')                  # a different atom

    assert x1 is x2, 'Atoms should be the same object'
    assert x1 is not z, 'Atoms should be different objects'

def test_2and_uniqueness():
    x1, x2 = Atom('x'), Atom('x')  # same atom
    y = Atom('y')                  # a different atom

    a = And(x1, y)
    b = And(y, x1)
    c = And(x2, y)
    d = And(y, x2)

    assert id(a) == id(b) == id(c) == id(d), 'All 2-and\'s should be the same object'

def test_3and_uniqueness():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    a = And(x, y, z)

    for comb in permutations([x, y, z]):
        assert And(*comb) is a, 'All 3-and\'s should be the same object'
        assert And(comb) is a, 'All 3-and\'s should be the same object'

def test_3or_uniqueness():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    a = Or(x, y, z)

    for comb in permutations([x, y, z]):
        assert Or(*comb) is a, 'All 3-and\'s should be the same object'
        assert Or(comb) is a, 'All 3-and\'s should be the same object'

def test_impl_uniqueness():
    x, y = Atom('x'), Atom('y')

    a = x >> y
    b = y >> x

    a2 = Implies(x, y)

    assert a is a2, 'Non-unique implication is detected'
    assert a is not b, 'Implication is not commutative'

def test_ite_uniqueness():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    a = ITE(x, y, z)

    for comb in permutations([x, y, z]):
        if comb == (x, y, z):
            continue

        assert ITE(*comb) is not a, 'ITE is not commutative'

def test_xor_uniqueness():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    a = XOr(x, y, z, merge=True)
    b = XOr(x, y, z, merge=False)

    for comb in permutations([x, y, z]):
        assert XOr(*comb, merge=True) is a, 'All 3-xor\'s should be the same object'

    for comb in permutations([x, y, z]):
        assert XOr(*comb, merge=False) is b, 'All 3-xor\'s should be the same object'
        assert XOr(*comb) is b, 'All 3-xor\'s should be the same object'

def test_equals_uniqueness():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    a = Equals(x, y, z, merge=True)
    b = Equals(x, y, z, merge=False)

    for comb in permutations([x, y, z]):
        assert Equals(*comb, merge=True) is a, 'All 3-equality\'s should be the same object'

    for comb in permutations([x, y, z]):
        assert Equals(*comb, merge=False) is b, 'All 3-equality\'s should be the same object'
        assert Equals(*comb) is b, 'All 3-equality\'s should be the same object'

def test_complex():
    x, y, z = Atom('x'), Atom('y'), Atom('z')

    f1 = XOr(x, y, z, merge=False)
    g1 = Or(f1, z, x, merge=True)
    h1 = And(y, g1, x, merge=True)

    f2 = XOr(z, y, x, merge=False)
    g2 = Or(x, f2, z, merge=True)
    h2 = And(x, g2, y, merge=True)

    assert f1 is f2, 'Complex uniqueness fail: step 1'
    assert g1 is g2, 'Complex uniqueness fail: step 2'
    assert h1 is h2, 'Complex uniqueness fail: step 3'
