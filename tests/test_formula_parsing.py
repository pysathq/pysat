from io import StringIO
from decimal import Decimal

import pytest
import pysat.formula as formula_mod
from pysat.formula import CNF, WCNF, CNFPlus, WCNFPlus


def test_cnf_parser_comments_and_clauses():
    s = 'c hello\np cnf 3 2\n-1 2 0\n3 0\n'
    cnf = CNF(from_string=s)

    assert cnf.comments == ['c hello']
    assert cnf.clauses == [[-1, 2], [3]]
    assert cnf.nv == 3


def test_cnf_parser_from_fp():
    fp = StringIO('c note\np cnf 2 1\n1 -2 0\n')
    cnf = CNF(from_fp=fp)

    assert cnf.comments == ['c note']
    assert cnf.clauses == [[1, -2]]
    assert cnf.nv == 2


def test_wcnf_parser_decimal_and_negative_weights():
    s = 'c weighted\np wcnf 3 3 10\n10 -1 2 0\n3.5 1 0\n-2 -3 0\n'
    wcnf = WCNF(from_string=s)

    assert wcnf.comments == ['c weighted']
    assert wcnf.hard == [[-1, 2]]
    assert wcnf.soft == [[1], [3]]
    assert wcnf.wght == [Decimal('3.5'), 2]
    assert wcnf.topw == 10
    assert wcnf.nv == 3


def test_cnfplus_parser_pb_and_cardinality():
    s = 'c plus\np cnf+ 5 3\n1 -2 3 0\n1 2 3 <= 1\nw 2*1 3*-4 1*5 >= 3\n'
    cnf = CNFPlus(from_string=s)

    assert cnf.comments == ['c plus']
    assert cnf.clauses == [[1, -2, 3]]
    assert cnf.atmosts == [
        [[1, 2, 3], 1],
        [[-1, 4, -5], 3, [2, 3, 1]],
    ]
    assert cnf.nv == 5


def test_wcnfplus_parser_hard_soft_and_pb():
    s = (
        'c wplus\n'
        'p wcnf+ 5 4 10\n'
        '10 1 -2 0\n'
        '2.5 3 0\n'
        'h 1 2 3 <= 1\n'
        'h w 2*1 3*-4 1*5 >= 3\n'
    )
    wcnf = WCNFPlus(from_string=s)

    assert wcnf.comments == ['c wplus']
    assert wcnf.hard == [[1, -2]]
    assert wcnf.soft == [[3]]
    assert wcnf.wght == [Decimal('2.5')]
    assert wcnf.atms == [
        [[1, 2, 3], 1],
        [[-1, 4, -5], 3, [2, 3, 1]],
    ]
    assert wcnf.topw == 10
    assert wcnf.nv == 5


def test_cnfplus_parser_accepts_plain_cnf_preamble():
    s = 'c plain\np cnf 3 2\n1 0\n-2 3 0\n'
    cnf = CNFPlus(from_string=s)

    assert cnf.comments == ['c plain']
    assert cnf.clauses == [[1], [-2, 3]]
    assert cnf.atmosts == []
    assert cnf.nv == 3


def test_wcnfplus_parser_accepts_plain_wcnf_preamble():
    s = 'c plain\np wcnf 3 3 5\n5 1 0\n1 -2 0\n2 3 0\n'
    wcnf = WCNFPlus(from_string=s)

    assert wcnf.comments == ['c plain']
    assert wcnf.hard == [[1]]
    assert wcnf.soft == [[-2], [3]]
    assert wcnf.wght == [1, 2]
    assert wcnf.atms == []
    assert wcnf.topw == 5
    assert wcnf.nv == 3


def test_invalid_preamble_lines_raise_errors():
    with pytest.raises(ValueError, match='invalid CNF/CNF\\+ preamble'):
        CNFPlus(from_string='c x\np bullshit\np cnf 2 1\n1 0\n')

    with pytest.raises(ValueError, match='invalid CNF/CNF\\+ preamble'):
        CNFPlus(from_string='p cnfxyz\np cnf 2 1\n1 0\n')

    with pytest.raises(ValueError, match='invalid WCNF/WCNF\\+ preamble'):
        WCNFPlus(from_string='c y\np nonsense\np wcnf 2 1 5\n5 1 0\n')

    with pytest.raises(ValueError, match='invalid WCNF/WCNF\\+ preamble'):
        WCNFPlus(from_string='p wcnfxyz\np wcnf 2 1 5\n5 1 0\n')


def test_python_wcnfplus_negative_normalization_keeps_nv():
    old = formula_mod.pyformula_present
    formula_mod.pyformula_present = False

    try:
        s = 'p wcnf 4 3 10\n10 1 0\n3.5 -2 0\n-2 3 0\n'
        wcnf = WCNFPlus(from_string=s)
    finally:
        formula_mod.pyformula_present = old

    assert wcnf.hard == [[1]]
    assert wcnf.soft == [[-2], [-3]]
    assert wcnf.wght == [Decimal('3.5'), 2]
    assert wcnf.topw == 10
    assert wcnf.nv == 3


def test_python_wcnf_negative_normalization_counts_aux_var():
    old = formula_mod.pyformula_present
    formula_mod.pyformula_present = False

    try:
        s = 'p wcnf 5 2 10\n10 1 0\n-2 4 5 0\n'
        wcnf = WCNF(from_string=s)
    finally:
        formula_mod.pyformula_present = old

    assert wcnf.soft == [[-6]]
    assert wcnf.wght == [2]
    assert sorted(wcnf.hard) == sorted([[1], [6, -4], [6, -5], [-6, 4, 5]])
    assert wcnf.topw == 10
    assert wcnf.nv == 6
