import pytest

from pysat.card import *
from pysat.formula import IDPool
from pysat.solvers import Solver
from pysat.solvers import ergo_present
from pysat.solvers import Cadical195
from pysat.solvers import Cadical300
from pysat.solvers import Ergo
from pysat.solvers import MinisatEP
from pysat.engines import Propagator

solvers = ['cadical153',
           'cadical195',
           'cadical300',
           'ergo',
           'gluecard30',
           'gluecard41',
           'glucose30',
           'glucose41',
           'glucose42',
           'maplechrono',
           'maplecm',
           'maplesat',
           'minicard',
           'mergesat3',
           'minisat22',
           'minisat-gh',
           'minisatep']

if not ergo_present:  # not built on every platform
    solvers.remove('ergo')

def test_solvers():
    cnf = CardEnc.atmost(lits=range(1, 6), bound=1, encoding=EncType.pairwise)

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf) as solver:
            for l in range(1, 6):
                st, lits = solver.propagate(assumptions=[l], phase_saving=1)
                assert st, 'wrong status of {0} after propagate()'.format(name)
                assert [lits[0]] + sorted(lits[1:], key=lambda l: abs(l)) == [l] + [-l2 for l2 in range(1, 6) if l2 != l], 'wrong list of propagated literals: {0}'.format(lits)

                solver.solve(assumptions=[3])

            solver.solve()

            solver.add_clause([2])
            st, lits = solver.propagate(assumptions=[1])
            assert not st, 'wrong status of {0} after propagate()'.format(name)
            assert not lits, 'wrong list of propagated literals: {0}'.format(lits)


@pytest.mark.parametrize('solver_class', [Cadical195, Cadical300, MinisatEP])
@pytest.mark.parametrize('bootstrap, action, failing_method, message', [
    ([[1]], lambda solver: solver.observe(1), 'on_assignment', 'boom in on_assignment'),
    ([[1]], lambda solver: solver.solve(), 'propagate', 'boom in propagate'),
    ([], lambda solver: solver.propagate(assumptions=[1]), 'propagate', 'boom in propagate'),
])
def test_cadical_callback_exceptions(solver_class, bootstrap, action, failing_method, message):
    class BoomPropagator(Propagator):
        def setup_observe(self, solver):
            solver.observe(1)

        def on_assignment(self, lit, fixed=False):
            if failing_method == 'on_assignment':
                raise AssertionError('boom in on_assignment')

        def propagate(self):
            if failing_method == 'propagate':
                raise AssertionError('boom in propagate')
            return []

        def decide(self):
            return 0

    with solver_class(bootstrap_with=bootstrap) as solver:
        prop = BoomPropagator()
        solver.connect_propagator(prop)

        if failing_method != 'on_assignment':
            prop.setup_observe(solver)

        with pytest.raises(AssertionError, match=message):
            action(solver)


@pytest.mark.skipif(not ergo_present, reason='ergo is not built on this platform')
@pytest.mark.parametrize('failing_method', ['on_assignment', 'propagate'])
def test_ergo_callback_exceptions(failing_method):
    class BoomPropagator(Propagator):
        def on_assignment(self, lit, fixed=False):
            if failing_method == 'on_assignment':
                raise AssertionError('boom in on_assignment')

        def propagate(self):
            if failing_method == 'propagate':
                raise AssertionError('boom in propagate')
            return []

        def check_model(self, model):
            return True

        def add_clause(self):
            return []

    with Ergo(bootstrap_with=[[1, 2]]) as solver:
        solver.connect_propagator(BoomPropagator())
        solver.observe(1)
        solver.observe(2)

        with pytest.raises(AssertionError, match='boom in {0}'.format(failing_method)):
            solver.solve()


@pytest.mark.parametrize('solver_class', [MinisatEP] +
                         ([Ergo] if ergo_present else []))
def test_interruptible_solve_with_propagator(solver_class):
    with solver_class() as solver:
        solver.connect_propagator(Propagator())

        with pytest.raises(NotImplementedError, match='external propagator'):
            solver.solve_limited(expect_interrupt=True)


@pytest.mark.parametrize('solver_class', [Cadical300] +
                         ([Ergo] if ergo_present else []))
def test_sync_with_idpool(solver_class):
    pool1 = IDPool()
    pool2 = IDPool()

    with solver_class(bootstrap_with=[[5]], sync_with=pool1) as solver:
        assert solver.nof_vars() == 5
        assert pool1.top == 5
        assert pool1.id() == 6

    with solver_class(bootstrap_with=[[5]]) as solver:
        solver.attach_vpool(pool2)

        assert solver.nof_vars() == 5
        assert pool2.top == 5
        assert pool2.id() == 6


@pytest.mark.parametrize('name', solvers)
def test_solver_kwargs_compatibility(name):
    pool = IDPool()

    with Solver(name=name, bootstrap_with=[[1]], sync_with=pool, native_card=True) as solver:
        assert solver.solve() is True

        if name in ('cadical300', 'ergo'):
            assert pool.top >= 1
        else:
            assert pool.top == 0
