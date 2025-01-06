from pysat.formula import *
from itertools import permutations

def test_atom_uniqueness():
    x1, x2 = Atom('x'), Atom('x')  # same atom
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
