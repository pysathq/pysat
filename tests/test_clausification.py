from pysat.formula import Atom, Formula, And, Or, Neg, XOr


def compare(a, b):
    assert tuple(map(tuple, a)) == tuple(map(tuple, b)), f'{a} != {b}'


def test_clausification():
    # reset vpool
    Formula.cleanup()

    # Atom outermost
    compare(list(Atom('1')), [[1]])

    # Neg outermost clauses
    compare(list(Neg(Atom('1'))), [[-1]])

    compare(list(Neg(And(Atom('1'), Atom('2')))), [[1, -3], [2, -3], [3, -1, -2], [-3]])

    # Neg inner clauses
    compare(list(Or(Neg(And(Atom('1'), Atom('2'))), Atom('3'))),
            [[1, -3], [2, -3], [3, -1, -2], [-3, 4]])
    compare(list(Or(Atom('1'), Neg(Atom('2')), Neg(Atom('2')))), [[1, -2, -2]])

    # XOr outermost
    compare(list(XOr(Atom('1'), Atom('2'))), [[-1, -2], [1, 2]])
    compare(list(XOr(Atom('1'), Atom('2'), Atom('3'))), [[-2, -4, -5], [2, 4, -5], [5, -2, 4], [5, 2, -4],
                                                         [-1, -5], [1, 5]])

    # XOr inner
    compare(list(And(XOr(Atom('1'), Atom('2'), Atom('3')), Atom('4'))), [[-2, -4, -5], [2, 4, -5],
                                                                         [5, -2, 4], [5, 2, -4], [-1, -5, -6],
                                                                         [1, 5, -6], [6, -1, 5], [6, 1, -5], [6], [7]])

    # multiple successive inner/outermost clausification
    f = And(Atom('1'), Atom('2'))
    g = And(f, Atom('3'))
    compare(list(f), [[1], [2]])
    compare(list(g), [[1, -3], [2, -3], [3, -1, -2], [3], [4]])
    compare(list(f), [[1], [2]])
    compare(list(g), [[1, -3], [2, -3], [3, -1, -2], [3], [4]])
