import pytest
from decimal import Decimal
from pysat.solvers import Solver

try:
    import pysat.pb  # noqa: F401
    pypblib_available = True
except Exception:
    pypblib_available = False

pytestmark = pytest.mark.skipif(not pypblib_available,
                                reason='pypblib is required for integer module tests')

if pypblib_available:
    from pysat.integer import Integer, IntegerEngine, LinearExpr

engine_solvers = ['cadical195', 'cadical300', 'minisatep']

def _enum_models_engine(eng, vars, solver_name):
    models = set()
    with Solver(name=solver_name) as solver:
        solver.connect_propagator(eng)
        eng.setup_observe(solver)
        while solver.solve():
            model = solver.get_model()
            vals = eng.decode_model(model, vars=vars)
            key = tuple(vals[var] for var in vars)
            models.add(key)
            blits = eng.encode_model(vals, vars=vars)
            solver.add_clause([-l for l in blits])
    return models


def _enum_models_engine_assuming(eng, vars, assumptions, solver_name):
    models = set()
    with Solver(name=solver_name) as solver:
        solver.connect_propagator(eng)
        eng.setup_observe(solver)
        while solver.solve(assumptions=assumptions):
            model = solver.get_model()
            vals = eng.decode_model(model, vars=vars)
            key = tuple(vals[var] for var in vars)
            models.add(key)
            blits = eng.encode_model(vals, vars=vars)
            solver.add_clause([-l for l in blits])
    return models


def _enum_models_cnf(eng, vars):
    models = set()
    with Solver(name='glucose30', bootstrap_with=eng.clausify()) as solver:
        while solver.solve():
            model = solver.get_model()
            vals = eng.decode_model(model, vars=vars)
            key = tuple(vals[var] for var in vars)
            models.add(key)
            blits = eng.encode_model(vals, vars=vars)
            solver.add_clause([-l for l in blits])
    return models


def _is_true(model, lit):
    return model[abs(lit) - 1] == lit


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_engine_models_match(solver_name):
    x = Integer('x', 0, 2, encoding='direct')
    y = Integer('y', 0, 2, encoding='order')
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x + y <= 2)
    eng.add_linear(x >= y)
    eng.add_linear(x + y != x)

    vars = [x, y]
    m1 = _enum_models_engine(eng, vars, solver_name)
    m2 = _enum_models_cnf(eng, vars)

    assert m1 == m2, 'Model sets from engine and solver do not match'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_engine_unsat(solver_name):
    a = Integer('a', 0, 2)
    b = Integer('b', 0, 2)
    eng = IntegerEngine([a, b], adaptive=False)

    eng.add_linear(a + b <= 1)
    eng.add_linear(a - b >= 2)

    with Solver(name=solver_name) as solver:
        solver.connect_propagator(eng)
        eng.setup_observe(solver)
        assert solver.solve() is False, 'UNSAT instance reported SAT [engine]'

    cnf = eng.clausify()
    with Solver(name='glucose30', bootstrap_with=cnf) as solver:
        assert solver.solve() is False, 'UNSAT instance reported SAT [solver]'


def test_domain_encoding():
    for enc in ('direct', 'order', 'coupled'):
        x = Integer('x', 1, 3, encoding=enc)
        eng = IntegerEngine([x], adaptive=False)
        cnf = eng.clausify()

        with Solver(name='glucose30', bootstrap_with=cnf) as solver:
            values = set()
            while solver.solve():
                model = solver.get_model()
                vals = eng.decode_model(model, vars=[x])
                values.add(vals[x])
                blits = eng.encode_model(vals, vars=[x])
                solver.add_clause([-l for l in blits])

        assert values == set(x.domain), f'Domain encoding \'{enc}\' does not produce domain values'


def test_singleton_order_encoding():
    x = Integer('x', 2, 2, encoding='order')
    eng = IntegerEngine([x], adaptive=False)
    cnf = eng.clausify()

    with Solver(name='glucose30', bootstrap_with=cnf) as solver:
        values = []
        while solver.solve():
            model = solver.get_model()
            vals = eng.decode_model(model, vars=[x])
            values.append(vals[x])
            blits = eng.encode_model(vals, vars=[x])
            solver.add_clause([-l for l in blits])

    assert values == [2], 'Singleton order domain should yield a single model'


def test_decode_conflicts_and_fixes():
    x = Integer('x', 1, 3, encoding='direct')
    y = Integer('y', 1, 3, encoding='order')
    z = Integer('z', 1, 3, encoding='order')
    w = Integer('w', 1, 3, encoding='order')
    eng = IntegerEngine([x, y, z, w], adaptive=False)

    lits = [
        x.equals(1),
        x.equals(2),       # conflicting equality values
        y.ge(2),
        -y.ge(2),          # contradictory bounds
        z.ge(2),
        -z.ge(3),          # fixes z to 2
        w.ge(2),
    ]

    vals = eng.decode(lits)

    assert vals[x] == [1, 2], 'Conflicting equalities should return all values'
    assert vals[y] == [], 'Contradictory bounds should return an empty list'
    assert vals[z] == 2, 'Consistent bounds should yield a single value'
    assert vals[w] == [2, 3], 'Non-fixed bounds should return all values in range'

    with pytest.raises(ValueError):
        eng.decode([0])


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_operator_constraints(solver_name):
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x + y == 2)
    eng.add_linear(x != y)
    eng.add_linear(x < y)

    vars = [x, y]
    expected = {(0, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Operator constraints mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Operator constraints mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_eq_constraint(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) == 1)

    vars = [x]
    expected = {(-1,), (1,)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'abs == mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'abs == mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_eq_direct_avoids_linearization(solver_name):
    x = Integer('x', -1, 1, encoding='direct')
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) == 1)

    vars = [x]
    expected = {(-1,), (1,)}
    assert eng._lcons == [], 'Direct abs == should not use PB constraints'
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Direct abs == mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Direct abs == mismatch [solver]'


def test_clausify_does_not_duplicate_domain_clauses():
    x = Integer('x', -1, 1, encoding='direct')
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) == 1)
    cnf = eng.clausify()

    expected = x.domain_clauses() + [[x.equals(-1), x.equals(1)]]
    assert [sorted(cl) for cl in cnf.clauses] == [sorted(cl) for cl in expected]


def test_abs_eq_registers_singleton_var():
    x = Integer('x', -1, 1, encoding='direct')
    eng = IntegerEngine([], adaptive=False)

    eng.add_linear(abs(x) == 1)
    cnf = eng.clausify()

    assert eng.integers == [x]
    expected = x.domain_clauses() + [[x.equals(-1), x.equals(1)]]
    assert [sorted(cl) for cl in cnf.clauses] == [sorted(cl) for cl in expected]

@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_eq_order_avoids_linearization(solver_name):
    x = Integer('x', -1, 1, encoding='order')
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) == 1)

    vars = [x]
    expected = {(-1,), (1,)}
    assert eng._lcons == [], 'Order abs == should not use PB constraints'
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Order abs == mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Order abs == mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_eq_zero_constraint(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) == 0)

    vars = [x]
    expected = {(0,)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'abs == 0 mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'abs == 0 mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_le_constraint_on_expr(solver_name):
    x = Integer('x', -2, 2)
    y = Integer('y', -2, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(abs(x - y) <= 1)

    vars = [x, y]
    expected = {(i, j) for i in range(-2, 3) for j in range(-2, 3) if abs(i - j) <= 1}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'abs <= mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'abs <= mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_ge_constraint(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) >= 2)

    vars = [x]
    expected = {(-2,), (2,)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'abs >= mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'abs >= mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_abs_le_negative_bound_is_unsat(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    eng.add_linear(abs(x) <= -1)

    vars = [x]
    expected = set()
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'abs <= negative mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'abs <= negative mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_linear_constraint(solver_name):
    x = Integer('x', 0, 1)
    y = Integer('y', 0, 1)
    eng1 = IntegerEngine([x, y], adaptive=False)
    vars1 = [x, y]
    all_models = _enum_models_engine(eng1, vars1, solver_name)
    assert len(all_models) == 4, 'Unexpected base model count'

    x2 = Integer('x', 0, 1)
    y2 = Integer('y', 0, 1)
    eng2 = IntegerEngine([x2, y2], adaptive=False)
    sel = eng2.add_linear(x2 + y2 <= 1, reified=True)

    vars2 = [x2, y2]
    expected = {(0, 0), (0, 1), (1, 0)}
    assert _enum_models_engine_assuming(eng2, vars2, [sel], solver_name) == expected


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_abs_eq_constraint(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    sel = eng.add_linear(abs(x) == 1, reified=True)

    vars = [x]
    expected = {(-1,), (1,)}
    assert _enum_models_engine_assuming(eng, vars, [sel], solver_name) == expected


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_abs_eq_order(solver_name):
    x = Integer('x', -1, 1, encoding='order')
    eng = IntegerEngine([x], adaptive=False)

    sel = eng.add_linear(abs(x) == 1, reified=True)

    vars = [x]
    expected = {(-1,), (1,)}
    assert eng._lcons == [], 'Reified order abs == should not use PB constraints'
    assert _enum_models_engine_assuming(eng, vars, [sel], solver_name) == expected


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_abs_ge_zero_is_tautological(solver_name):
    x = Integer('x', -2, 2)
    eng = IntegerEngine([x], adaptive=False)

    sel = eng.add_linear(abs(x) >= 0, reified=True)

    vars = [x]
    expected = {(-2,), (-1,), (0,), (1,), (2,)}
    assert _enum_models_engine_assuming(eng, vars, [sel], solver_name) == expected


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_equal_direct(solver_name):
    x = Integer('x', 0, 1, encoding='direct')
    y = Integer('y', 0, 1, encoding='direct')
    eng = IntegerEngine([x, y], adaptive=False)

    sel = eng.add_linear(x.as_expr() == y.as_expr(), reified=True)

    vars = [x, y]
    assert _enum_models_engine_assuming(eng, vars, [sel], solver_name) == {(0, 0), (1, 1)}


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_eq_vars_direct_domain_intersection(solver_name):
    x = Integer('x', 0, 2, encoding='direct')
    y = Integer('y', 1, 3, encoding='direct')
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x.as_expr() == y.as_expr())

    vars = [x, y]
    expected = {(1, 1), (2, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Direct eq_vars mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Direct eq_vars mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_eq_vars_order_domain_intersection(solver_name):
    x = Integer('x', 0, 2, encoding='order')
    y = Integer('y', 1, 3, encoding='order')
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x.as_expr() == y.as_expr())

    vars = [x, y]
    expected = {(1, 1), (2, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Order eq_vars mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Order eq_vars mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_eq_vars_mixed_direct_order(solver_name):
    x = Integer('x', 0, 2, encoding='direct')
    y = Integer('y', 0, 2, encoding='order', vpool=x.vpool)
    eng = IntegerEngine([x, y], adaptive=False, vpool=x.vpool)

    eng.add_linear(x.as_expr() == y.as_expr())

    vars = [x, y]
    expected = {(0, 0), (1, 1), (2, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Mixed eq_vars mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Mixed eq_vars mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_eq_vars_mixed_order_direct(solver_name):
    x = Integer('x', 0, 2, encoding='order')
    y = Integer('y', 0, 2, encoding='direct', vpool=x.vpool)
    eng = IntegerEngine([x, y], adaptive=False, vpool=x.vpool)

    eng.add_linear(x.as_expr() == y.as_expr())

    vars = [x, y]
    expected = {(0, 0), (1, 1), (2, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Mixed reverse eq_vars mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Mixed reverse eq_vars mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_reified_equal_mixed_direct_order(solver_name):
    x = Integer('x', 0, 2, encoding='direct')
    y = Integer('y', 0, 2, encoding='order', vpool=x.vpool)
    eng = IntegerEngine([x, y], adaptive=False, vpool=x.vpool)

    sel = eng.add_linear(x.as_expr() == y.as_expr(), reified=True)

    vars = [x, y]
    expected = {(0, 0), (1, 1), (2, 2)}
    assert _enum_models_engine_assuming(eng, vars, [sel], solver_name) == expected


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_linear_expr_not_equal(solver_name):
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    # 2x + y != x + 1
    eng.add_linear(2 * x + y != x + 1)

    vars = [x, y]
    expected = {(0, 0), (0, 2), (1, 1), (1, 2),
                (2, 0), (2, 1), (2, 2)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Linear != expr mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Linear != expr mismatch [solver]'


def test_linear_expr_not_equal_reif_vpool_cache():
    from pysat.formula import IDPool

    vpool = IDPool()
    x = Integer('x', 0, 2, vpool=vpool)
    y = Integer('y', 0, 2, vpool=vpool)
    eng = IntegerEngine([x, y], adaptive=False, vpool=vpool)

    # same constraint twice should reuse aux variables
    eng.add_linear(x + y != 2)
    eng.add_linear(x + y != 2)

    found = sum([1 if isinstance(key, tuple) and key and key[0] in ('lin_le', 'lin_ne')
                 else 0 for key in vpool.obj2id])
    assert found == 2, 'Wrong reification (expected two selectors)'


def test_deduplication():
    x = Integer('x', 0, 2, encoding='direct')
    eng = IntegerEngine([x])

    # non-reified linear constraint
    eng.add_linear(x <= 1)
    eng.add_linear(x <= 1)
    assert len(eng._lcons) == 1, 'Duplicate linear constraints in _lcons'

    # reified linear constraint
    eng = IntegerEngine([x])
    eng.add_linear(x <= 1, reified=True)
    eng.add_linear(x <= 1, reified=True)
    assert len(eng._lcons) == 1, 'Duplicate reified linear constraints in _lcons'

    # reified abs constraint (singleton)
    eng = IntegerEngine([x])
    c1 = eng.add_linear(abs(x) <= 1, reified=True)
    c2 = eng.add_linear(abs(x) <= 1, reified=True)
    assert c1 == c2, 'Duplicate reified abs selectors'
    # we expect 4 domain clauses + 1 abs clause = 5
    # (actually seqcounter might add more, but let's check for stability)
    cnt1 = len(eng.clauses)
    eng.add_linear(abs(x) <= 1, reified=True)
    assert len(eng.clauses) == cnt1, 'Duplicate clauses for reified abs'

    # reified equality constraint
    y = Integer('y', 0, 2, encoding='direct', vpool=x.vpool)
    eng = IntegerEngine([x, y])
    cnt1 = len(eng.clauses)
    eng.add_equal(x, y, reified=True)
    cnt2 = len(eng.clauses)
    eng.add_equal(x, y, reified=True)
    assert len(eng.clauses) == cnt2, 'Duplicate clauses for reified equality'
    assert cnt2 > cnt1


def test_zero_weight_literals_removed():
    x = Integer('x', 1, 3, encoding='direct')
    y = Integer('y', 1, 2, encoding='direct')

    constraint = LinearExpr.pb_linear_leq([(2, y), (-4, x)], 2)
    _, payload = constraint
    lits, bound, weights = payload

    assert weights[x.equals(1)] == 8
    assert weights[x.equals(2)] == 4
    assert weights[y.equals(2)] == 2

    assert x.equals(3) not in weights
    assert y.equals(1) not in weights
    assert x.equals(3) not in lits
    assert y.equals(1) not in lits


def test_mixed_numeric_raises():
    x = Integer('x', 0, 1)
    d = Integer('d', 0, 1, numeric='decimal')

    with pytest.raises(ValueError):
        _ = x + d

    with pytest.raises(ValueError):
        _ = d + x


def test_float_decimal_blend_raises():
    x = Integer('x', 0, 1)
    d = Integer('d', 0, 1, numeric='decimal')

    with pytest.raises(TypeError):
        _ = Decimal('1') * x

    with pytest.raises(TypeError):
        _ = 1.5 * d


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_decimal_constraints(solver_name):
    d = Integer('d', 0, 2, numeric='decimal')
    e = Integer('e', 0, 2, numeric='decimal')
    eng = IntegerEngine([d, e], adaptive=False)

    eng.add_linear(Decimal('1') * d + Decimal('1') * e == Decimal('2'))

    vars = [d, e]
    expected = {(0, 2), (1, 1), (2, 0)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Decimal constraints mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Decimal constraints mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_integral_with_decimal_coeffs_ok(solver_name):
    d = Integer('d', 0, 2, numeric='decimal')
    e = Integer('e', 0, 2, numeric='decimal')
    eng = IntegerEngine([d, e], adaptive=False)

    eng.add_linear(Decimal('1') * d + 2 * e == Decimal('2'))

    vars = [d, e]
    expected = {(0, 1), (2, 0)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Integral+decimal coeffs mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Integral+decimal coeffs mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_integral_with_float_coeffs_ok(solver_name):
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(1.0 * x + 2 * y == 2.0)

    vars = [x, y]
    expected = {(0, 1), (2, 0)}
    assert _enum_models_engine(eng, vars, solver_name) == expected, 'Integral+float coeffs mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Integral+float coeffs mismatch [solver]'


@pytest.mark.parametrize('solver_name', engine_solvers)
def test_coupled_channeling(solver_name):
    x = Integer('x', 0, 2, encoding='coupled')
    eng = IntegerEngine([x], adaptive=False)
    cnf = eng.clausify()

    # with propagator (no clausification)
    with Solver(name=solver_name) as solver:
        solver.connect_propagator(eng)
        eng.setup_observe(solver)

        assert solver.solve(assumptions=[x.equals(1)]) is True, 'Channeling solve failed for direct value (engine)'
        model = solver.get_model()
        assert _is_true(model, x.ge(1)), 'Channeling missing ge(1) from equals(1) (engine)'
        assert not _is_true(model, x.ge(2)), 'Channeling allowed ge(2) from equals(1) (engine)'

        assert solver.solve(assumptions=[x.ge(2)]) is True, 'Channeling solve failed for order literal (engine)'
        model = solver.get_model()
        assert _is_true(model, x.equals(2)), 'Channeling missing equals(2) from ge(2) (engine)'

    # with clausification: solve() under assumptions
    with Solver(name='glucose30', bootstrap_with=cnf) as solver:
        assert solver.solve(assumptions=[x.equals(1)]) is True, 'Channeling solve failed for direct value (CNF)'
        model = solver.get_model()
        assert _is_true(model, x.ge(1)), 'Channeling missing ge(1) from equals(1) (CNF)'
        assert not _is_true(model, x.ge(2)), 'Channeling allowed ge(2) from equals(1) (CNF)'

        assert solver.solve(assumptions=[x.ge(2)]) is True, 'Channeling solve failed for order literal (CNF)'
        model = solver.get_model()
        assert _is_true(model, x.equals(2)), 'Channeling missing equals(2) from ge(2) (CNF)'

    # with clausification: propagate() under assumptions
    with Solver(name='glucose30', bootstrap_with=cnf) as solver:
        status, lits = solver.propagate(assumptions=[x.equals(1)])
        assert status is True, 'Channeling propagate failed for equals(1)'
        assert x.ge(1) in lits, 'Channeling propagate missing ge(1) from equals(1)'
        assert -x.ge(2) in lits, 'Channeling propagate missing -ge(2) from equals(1)'

        status, lits = solver.propagate(assumptions=[x.ge(2)])
        assert status is True, 'Channeling propagate failed for ge(2)'
        assert x.equals(2) in lits, 'Channeling propagate missing equals(2) from ge(2)'
