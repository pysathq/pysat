"""Correctness and variable numbering checks for the vector encodings."""
from itertools import product
import operator

import pytest

from pysat.formula import IDPool
from pysat.solvers import Solver
from pysat.vector import VecEnc


# both encodings, for the tests that apply to each of them
ENCODINGS = [pytest.param(VecEnc.lex_leq, id='lex_leq'),
             pytest.param(VecEnc.lex_lt, id='lex_lt')]

# each encoding, together with the comparison of tuples it should match
METHODS = [pytest.param(VecEnc.lex_leq, operator.le, id='lex_leq'),
           pytest.param(VecEnc.lex_lt, operator.lt, id='lex_lt')]

# vectors containing something other than a literal
NOT_LITERALS = [pytest.param([0, 1], [2, 3], id='zero'),
                pytest.param([1, 2], [3, 1.5], id='float'),
                pytest.param([1, 'x'], [2, 3], id='string'),
                pytest.param([True, 2], [3, 4], id='bool')]

# vectors given as other iterables than lists
ITERABLES = [pytest.param((1, -2), (3, 4), id='tuples'),
             pytest.param((1, -2), [3, 4], id='tuple_and_list'),
             pytest.param(range(1, 3), range(3, 5), id='ranges')]

# vectors that share variables or repeat a literal
SHARED = [pytest.param([1, 2, -3], [2, 1, 3], id='swapped'),
          pytest.param([1, 1], [1, -1], id='repeated'),
          pytest.param([1, -2], [1, -2], id='identical'),
          pytest.param([-1, 2, 1], [1], id='longer')]

# empty vectors, with the clauses expected from lex_leq and from lex_lt: an
# empty vector is smaller than any other one, and an empty clause makes the
# formula unsatisfiable
EMPTY = [pytest.param([], [], [], [[]], id='both_empty'),
         pytest.param([], [1, 2], [], [], id='a_empty'),
         pytest.param([1, 2], [], [[]], [[]], id='b_empty')]

# vectors of different lengths, with the number of clauses expected from
# either encoding: 3k - 2 if a is shorter, and 3k - 1 if a is longer, where
# k is the shorter length
UNEQUAL = [pytest.param(2, 4, 4, id='a_shorter'),
           pytest.param(4, 2, 5, id='a_longer'),
           pytest.param(1, 3, 1, id='a_single'),
           pytest.param(3, 1, 2, id='b_single')]


def vectors(n, m):
    """
        Two vectors of lengths ``n`` and ``m`` over distinct variables, with
        literals of both signs.
    """

    a = [i if i % 2 else -i for i in range(1, n + 1)]
    b = [-i if i % 2 else i for i in range(n + 1, n + m + 1)]

    return a, b


def check(method, compare, a, b, **kwargs):
    """
        Check that the encoding is satisfiable under exactly those
        assignments of the input variables under which ``compare`` holds for
        the values of the two vectors.
    """

    cnf = method(a, b, **kwargs)
    inputs = sorted(set(abs(lit) for lit in a + b))

    with Solver(name='g3', bootstrap_with=cnf.clauses) as solver:
        for bits in product((False, True), repeat=len(inputs)):
            value = dict(zip(inputs, bits))
            assumptions = [v if value[v] else -v for v in inputs]
            left = tuple(value[abs(lit)] == (lit > 0) for lit in a)
            right = tuple(value[abs(lit)] == (lit > 0) for lit in b)
            expected = compare(left, right)

            assert solver.solve(assumptions=assumptions) == expected, (
                'wrong result for {0} and {1}'.format(left, right))

    return cnf


def helper_vars(cnf, a, b):
    """
        The variables of the encoding that do not occur in the vectors.
    """

    inputs = set(abs(lit) for lit in a + b)

    return sorted(set(abs(lit) for cl in cnf.clauses for lit in cl) - inputs)


def test_lex_leq_example():
    # the example from the docstring of lex_leq
    cnf = VecEnc.lex_leq([1, 2], [3, 4])
    assert cnf.clauses == [[-1, 3], [-1, 5], [3, 5], [-5, -2, 4]]
    assert cnf.nv == 5


def test_lex_lt_example():
    # the example from the docstring of lex_lt
    cnf = VecEnc.lex_lt([1, 2], [3, 4])
    assert cnf.clauses == [[-1, 3], [-1, 5], [3, 5], [-5, -2], [-5, 4]]
    assert cnf.nv == 5


def test_vecenc_example():
    # the example from the docstring of VecEnc
    vpool = IDPool(occupied=[[5, 10]])
    cnf = VecEnc.lex_leq([1, 2], [3, 4], vpool=vpool)
    assert cnf.clauses == [[-1, 3], [-1, 11], [3, 11], [-11, -2, 4]]
    assert cnf.nv == vpool.top == 11


@pytest.mark.parametrize('method', ENCODINGS)
@pytest.mark.parametrize('a, b', NOT_LITERALS)
def test_lex_not_literals(method, a, b):
    with pytest.raises(ValueError):
        method(a, b)


@pytest.mark.parametrize('method', ENCODINGS)
def test_lex_top_id_and_vpool(method):
    with pytest.raises(AssertionError):
        method([1], [2], top_id=5, vpool=IDPool())


@pytest.mark.parametrize('method', ENCODINGS)
def test_lex_inputs_unchanged(method):
    a, b = [1, -2, 3], [4, 5]
    method(a, b)
    assert a == [1, -2, 3] and b == [4, 5]


@pytest.mark.parametrize('method', ENCODINGS)
@pytest.mark.parametrize('a, b', ITERABLES)
def test_lex_iterables(method, a, b):
    # other iterables give the same encoding as lists
    assert method(a, b).clauses == method(list(a), list(b)).clauses


@pytest.mark.parametrize('method', ENCODINGS)
def test_lex_numpy(method):
    numpy = pytest.importorskip('numpy')

    a, b = numpy.array([1, -2]), numpy.array([3, 4])
    cnf = method(a, b)
    assert cnf.clauses == method([1, -2], [3, 4]).clauses

    # the clauses contain plain ints, not numpy integers
    assert all(type(lit) is int for cl in cnf.clauses for lit in cl)


@pytest.mark.parametrize('method, compare', METHODS)
@pytest.mark.parametrize('n, m', list(product(range(5), repeat=2)))
def test_lex_lengths(method, compare, n, m):
    a, b = vectors(n, m)
    check(method, compare, a, b)


@pytest.mark.parametrize('method, compare', METHODS)
@pytest.mark.parametrize('a, b', SHARED)
def test_lex_shared_variables(method, compare, a, b):
    check(method, compare, a, b)


@pytest.mark.parametrize('a, b, leq, lt', EMPTY)
def test_lex_empty(a, b, leq, lt):
    assert VecEnc.lex_leq(a, b).clauses == leq
    assert VecEnc.lex_lt(a, b).clauses == lt


@pytest.mark.parametrize('method', ENCODINGS)
def test_lex_empty_numbering(method):
    # no helper variables, so nv is the largest input variable or top_id
    assert method([], []).nv == 0
    assert method([], [], top_id=7).nv == 7
    assert method([1, 2], []).nv == 2

    # the pool is not moved if there is nothing to number
    pool = IDPool(start_from=4)
    assert method([], [], vpool=pool).nv == pool.top == 3

    # but it is still raised past inputs that did not come from it
    pool = IDPool()
    assert method([1, 2], [], vpool=pool).nv == pool.top == 2


@pytest.mark.parametrize('n', range(1, 6))
def test_lex_size(n):
    a, b = vectors(n, n)

    cnf = VecEnc.lex_leq(a, b)
    assert len(helper_vars(cnf, a, b)) == n - 1
    assert len(cnf.clauses) == 3 * n - 2

    cnf = VecEnc.lex_lt(a, b)
    assert len(helper_vars(cnf, a, b)) == n - 1
    assert len(cnf.clauses) == 3 * n - 1


@pytest.mark.parametrize('n, m, nof_clauses', UNEQUAL)
def test_lex_size_unequal(n, m, nof_clauses):
    # if the lengths differ, they decide the strictness, so both encodings
    # produce the same clauses, and only the shorter length counts
    a, b = vectors(n, m)

    for method in (VecEnc.lex_leq, VecEnc.lex_lt):
        cnf = method(a, b)
        assert len(helper_vars(cnf, a, b)) == min(n, m) - 1
        assert len(cnf.clauses) == nof_clauses


@pytest.mark.parametrize('method, compare', METHODS)
def test_lex_top_id(method, compare):
    a, b = vectors(4, 4)

    # the helper variables come right after top_id
    cnf = check(method, compare, a, b, top_id=20)
    assert helper_vars(cnf, a, b) == [21, 22, 23]
    assert cnf.nv == 23

    # a top_id below the input variables is raised above them
    cnf = check(method, compare, a, b, top_id=3)
    assert helper_vars(cnf, a, b) == [9, 10, 11]
    assert cnf.nv == 11

    # without helper variables, nv still covers top_id
    cnf = method([1], [2], top_id=20)
    assert cnf.nv == 20

    # with different lengths, only the shorter vector gets helper variables
    for n, m in ((4, 2), (2, 4)):
        a, b = vectors(n, m)
        cnf = check(method, compare, a, b, top_id=20)
        assert helper_vars(cnf, a, b) == [21]
        assert cnf.nv == 21


@pytest.mark.parametrize('method, compare', METHODS)
def test_lex_vpool(method, compare):
    # inputs taken from the pool: the pool moves past the helper variables
    pool = IDPool()

    a = [pool.id(('a', i)) for i in range(3)]
    b = [pool.id(('b', i)) for i in range(3)]
    cnf = check(method, compare, a, b, vpool=pool)
    assert helper_vars(cnf, a, b) == [7, 8]
    assert cnf.nv == pool.top == 8
    assert pool.id('next') == 9

    # occupied ranges are skipped, even when an input reaches into one
    pool = IDPool(occupied=[[5, 10]])
    a, b = [1, 2, 3], [4, 7, 8]
    cnf = check(method, compare, a, b, vpool=pool)
    assert helper_vars(cnf, a, b) == [11, 12]
    assert cnf.nv == pool.top == 12

    # inputs not taken from the pool are not handed out again
    pool = IDPool()
    a, b = [1, 2], [3, 4]
    cnf = check(method, compare, a, b, vpool=pool)
    assert helper_vars(cnf, a, b) == [5]
    assert cnf.nv == pool.top == 5

    # with different lengths, only the shorter vector gets helper variables
    pool = IDPool()
    a = [pool.id(('a', i)) for i in range(4)]
    b = [pool.id(('b', i)) for i in range(2)]
    cnf = check(method, compare, a, b, vpool=pool)
    assert helper_vars(cnf, a, b) == [7]
    assert cnf.nv == pool.top == 7
