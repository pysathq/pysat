from pysat.engines import Propagator
from pysat.solvers import Solver
import pytest


class EmptyClausePropagator(Propagator):
    def __init__(self):
        super().__init__()
        self.need_clause = False

    def on_assignment(self, lit, fixed=False):
        pass

    def on_new_level(self):
        pass

    def on_backtrack(self, to):
        pass

    def check_model(self, model):
        self.need_clause = True
        return False

    def decide(self):
        return 0

    def propagate(self):
        return []

    def provide_reason(self, lit):
        return [lit]

    def has_clause(self):
        return self.need_clause

    def add_clause(self):
        self.need_clause = False
        return []


@pytest.mark.parametrize('solver_name', ['cadical195', 'cadical300', 'minisatep'])
def test_empty_external_clause(solver_name):
    with Solver(name=solver_name) as solver:
        solver.connect_propagator(EmptyClausePropagator())
        assert solver.solve() is False
