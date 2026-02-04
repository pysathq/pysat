import pytest
try:
    import pysat.pb
except Exception:
    pytest.skip('pypblib is required for integer module tests', allow_module_level=True)

from decimal import Decimal
from pysat.integer import Integer, IntegerEngine, LinearExpr
from pysat.solvers import Solver


def _enum_models_engine(eng, vars):
    models = set()
    with Solver(name='cadical195') as solver:
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


def test_engine_models_match():
    x = Integer('x', 0, 2, encoding='direct')
    y = Integer('y', 0, 2, encoding='order')
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x + y <= 2)
    eng.add_linear(x >= y)
    eng.add_linear(x + y != x)

    vars = [x, y]
    m1 = _enum_models_engine(eng, vars)
    m2 = _enum_models_cnf(eng, vars)

    assert m1 == m2, 'Model sets from engine and solver do not match'


def test_engine_unsat():
    a = Integer('a', 0, 2)
    b = Integer('b', 0, 2)
    eng = IntegerEngine([a, b], adaptive=False)

    eng.add_linear(a + b <= 1)
    eng.add_linear(a - b >= 2)

    with Solver(name='cadical195') as solver:
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


def test_decode_assignment_conflicts_and_fixes():
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

    vals = eng.decode_assignment(lits)

    assert vals[x] == [1, 2], 'Conflicting equalities should return all values'
    assert vals[y] == [], 'Contradictory bounds should return an empty list'
    assert vals[z] == 2, 'Consistent bounds should yield a single value'
    assert vals[w] == [2, 3], 'Non-fixed bounds should return all values in range'

    with pytest.raises(ValueError):
        eng.decode_assignment([0])


def test_operator_constraints():
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(x + y == 2)
    eng.add_linear(x != y)
    eng.add_linear(x < y)

    vars = [x, y]
    expected = {(0, 2)}
    assert _enum_models_engine(eng, vars) == expected, 'Operator constraints mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Operator constraints mismatch [solver]'


def test_linear_expr_not_equal():
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    # 2x + y != x + 1
    eng.add_linear(2 * x + y != x + 1)

    vars = [x, y]
    expected = {(0, 0), (0, 2), (1, 1), (1, 2),
                (2, 0), (2, 1), (2, 2)}
    assert _enum_models_engine(eng, vars) == expected, 'Linear != expr mismatch [engine]'
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

    found = sum([1 if key[1] == '_reif' else 0 for key in vpool.obj2id])
    assert found == 2, 'Wrong reification (expected two selectors)'


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


def test_decimal_constraints():
    d = Integer('d', 0, 2, numeric='decimal')
    e = Integer('e', 0, 2, numeric='decimal')
    eng = IntegerEngine([d, e], adaptive=False)

    eng.add_linear(Decimal('1') * d + Decimal('1') * e == Decimal('2'))

    vars = [d, e]
    expected = {(0, 2), (1, 1), (2, 0)}
    assert _enum_models_engine(eng, vars) == expected, 'Decimal constraints mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Decimal constraints mismatch [solver]'


def test_integral_with_decimal_coeffs_ok():
    d = Integer('d', 0, 2, numeric='decimal')
    e = Integer('e', 0, 2, numeric='decimal')
    eng = IntegerEngine([d, e], adaptive=False)

    eng.add_linear(Decimal('1') * d + 2 * e == Decimal('2'))

    vars = [d, e]
    expected = {(0, 1), (2, 0)}
    assert _enum_models_engine(eng, vars) == expected, 'Integral+decimal coeffs mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Integral+decimal coeffs mismatch [solver]'


def test_integral_with_float_coeffs_ok():
    x = Integer('x', 0, 2)
    y = Integer('y', 0, 2)
    eng = IntegerEngine([x, y], adaptive=False)

    eng.add_linear(1.0 * x + 2 * y == 2.0)

    vars = [x, y]
    expected = {(0, 1), (2, 0)}
    assert _enum_models_engine(eng, vars) == expected, 'Integral+float coeffs mismatch [engine]'
    assert _enum_models_cnf(eng, vars) == expected, 'Integral+float coeffs mismatch [solver]'


def test_coupled_channeling():
    x = Integer('x', 0, 2, encoding='coupled')
    eng = IntegerEngine([x], adaptive=False)
    cnf = eng.clausify()

    # with propagator (no clausification)
    with Solver(name='cadical195') as solver:
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
