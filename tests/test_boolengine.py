from pysat.card import *
from pysat.engines import *
from pysat.formula import CNF, CNFPlus
from pysat.solvers import Solver, ergo_present
import pytest


def native_plus(lits):
    """
        An AtMost2 and an AtLeast1 over the same literals, kept native.
    """

    plus = CNFPlus()
    plus.atmosts = CardEnc.atmost(lits, bound=2, encoding=EncType.native).atmosts
    plus.atmosts += CardEnc.atleast(lits, bound=1, encoding=EncType.native).atmosts
    plus.nv = len(lits)

    return plus


def encoded_count(solver_name, lits):
    """
        How many models the same two constraints have once encoded to CNF.
        This is the oracle every native route below is measured against.
    """

    vpool = IDPool()
    cnf = CardEnc.atmost(lits, bound=2, vpool=vpool, encoding=EncType.kmtotalizer)
    cnf.extend(CardEnc.atleast(lits, bound=1, vpool=vpool, encoding=EncType.kmtotalizer))

    with Solver(name=solver_name, bootstrap_with=cnf) as solver:
        nof_models = 0
        for model in solver.enum_models():
            solver.add_clause([-l for l in model[:len(lits)]])
            nof_models += 1

    return nof_models


def engine_by_hand(solver, lits):
    """
        The engine built and attached by the caller, bypassing the solver's
        own AtMost interface entirely.
    """

    engine = BooleanEngine([('linear', [am[0], am[1]])
                            for am in native_plus(lits).atmosts], adaptive=True)
    solver.connect_propagator(engine)
    engine.setup_observe(solver)


def by_activation(solver, lits):
    """
        The engine activated by the solver, constraints handed over one by
        one through its AtMost interface.
    """

    solver.activate_atmost()

    for am in native_plus(lits).atmosts:
        solver.add_atmost(am[0], am[1])


@pytest.mark.parametrize('solver_name', ['cadical195', 'cadical300', 'minisatep'] +
                         (['ergo'] if ergo_present else []))
@pytest.mark.parametrize('setup', [engine_by_hand, by_activation])
def test_native_card(solver_name, setup):
    """
        Native linear constraints, however the engine gets hold of them,
        have to admit exactly the models their CNF encoding does.
    """

    with Solver(name=solver_name, bootstrap_with=CNF()) as solver:
        assert not solver.supports_atmost()

        setup(solver, list(range(1, 6)))
        assert solver.supports_atmost()

        nof_models = sum(1 for model in solver.enum_models())

    assert nof_models == encoded_count(solver_name, list(range(1, 6)))


@pytest.mark.parametrize('solver_name', ['cadical195', 'cadical300', 'minisatep'] +
                         (['ergo'] if ergo_present else []))
def test_native_card_bootstrap(solver_name):
    """
        The same constraints given at construction time, which is the one
        route that cannot be taken after the solver exists.
    """

    with Solver(name=solver_name, bootstrap_with=native_plus(list(range(1, 6))),
                native_card=True) as solver:
        assert solver.supports_atmost()
        nof_models = sum(1 for model in solver.enum_models())

    assert nof_models == encoded_count(solver_name, list(range(1, 6)))
