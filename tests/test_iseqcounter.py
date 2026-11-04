"""Correctness and lifetime checks for Jesse Looney's iterative counter."""
from itertools import product

import pytest

from pysat.card import ISeqCounter
from pysat.solvers import Solver


@pytest.mark.parametrize('size', range(1, 7))
@pytest.mark.parametrize('ubound', [0, 1, 10])
def test_iseqcounter_prefixes(size, ubound):
    lits = [i if i % 2 else -i for i in range(1, size + 1)]
    with ISeqCounter(lits=lits, ubound=ubound, top_id=20) as counter:
        assert counter.top_id > 20
        assert len(counter.rhs) == min(ubound + 1, size)
        assert counter.nof_new == len(counter.cnf.clauses)
        with Solver(name='g3', bootstrap_with=counter.cnf.clauses) as solver:
            for bits in product((False, True), repeat=size):
                assumptions = [i if bit else -i
                               for i, bit in enumerate(bits, 1)]
                values = [bit if lit > 0 else not bit
                          for bit, lit in zip(bits, lits)]
                assert solver.solve(assumptions=assumptions)
                for prefix in range(1, size + 1):
                    for bound in range(min(prefix, len(counter.rhs))):
                        lit = counter.get_constraint(prefix, bound)
                        if prefix == size:
                            assert lit == counter.rhs[bound]
                        assert solver.solve(assumptions=assumptions + [-lit]) == (
                            sum(values[:prefix]) <= bound)


def test_iseqcounter_increase():
    lits = [1, -2, 3, -4, 5, -6]
    with ISeqCounter(lits=lits, ubound=0) as counter:
        with Solver(name='g3', bootstrap_with=counter.cnf.clauses) as solver:
            for bound in range(1, len(lits)):
                previous_rhs = counter.rhs[:]
                previous_size = len(counter.cnf.clauses)
                previous_top = counter.top_id
                reserved_top = previous_top + 10
                counter.increase(ubound=bound, top_id=reserved_top)
                assert counter.rhs[:-1] == previous_rhs
                assert counter.nof_new == len(counter.cnf.clauses) - previous_size
                added = counter.cnf.clauses[previous_size:]
                assert all(abs(lit) <= previous_top or abs(lit) > reserved_top
                           for clause in added for lit in clause)
                assert counter.cnf.nv == counter.top_id
                solver.append_formula(added)
                for bits in product((False, True), repeat=len(lits)):
                    assumptions = [i if bit else -i
                                   for i, bit in enumerate(bits, 1)]
                    count = sum(bit if lit > 0 else not bit
                                for bit, lit in zip(bits, lits))
                    for old_bound, rhs in enumerate(counter.rhs):
                        assert solver.solve(assumptions=assumptions + [-rhs]) == (
                            count <= old_bound)
            counter.increase(ubound=len(lits) + 5)
            assert len(counter.rhs) == len(lits)
            assert counter.nof_new == 0
            counter.increase(ubound=0)
            assert counter.nof_new == 0


@pytest.mark.parametrize('lits', [[1, 1, 2], [1, -1, 2]])
def test_iseqcounter_repeated_literals(lits):
    with ISeqCounter(lits=lits, ubound=2) as counter:
        with Solver(name='g3', bootstrap_with=counter.cnf.clauses) as solver:
            for first, second in product((False, True), repeat=2):
                values = {1: first, 2: second}
                count = sum(values[abs(lit)] if lit > 0 else not values[abs(lit)]
                            for lit in lits)
                assumptions = [1 if first else -1, 2 if second else -2]
                for bound, rhs in enumerate(counter.rhs):
                    assert solver.solve(assumptions=assumptions + [-rhs]) == (
                        count <= bound)


def test_iseqcounter_empty_and_delete():
    with ISeqCounter() as counter:
        assert counter.tobj is None
        assert counter.rhs == []
        assert counter.cnf.clauses == []
        counter.increase(ubound=5)
        assert counter.nof_new == 0
        assert counter.get_constraint(0, 0) is None
    counter.delete()
    with ISeqCounter(lits=[1, 2, 3]) as counter:
        assert counter.tobj is not None
    assert counter.tobj is None
    assert counter.rhs == []
    assert counter.cnf.clauses == []
    counter.delete()
    assert counter.get_constraint(1, 0) is None


def test_iseqcounter_invalid_bounds():
    with pytest.raises(ValueError):
        ISeqCounter(lits=[1, 2], ubound=-1)
    with ISeqCounter(lits=[1, 2, 3], ubound=0) as counter:
        for prefix, bound in [(0, 0), (4, 0), (1, 1), (1, -1), (3, 1)]:
            assert counter.get_constraint(prefix, bound) is None
