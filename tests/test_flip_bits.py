import itertools
import random
from pysat.solvers import Cadical300

def check(res, clauses, assumptions, prefs):
    model, cost = res
    if model is None:
        return False

    assert all(any(l in model for l in cl) for cl in clauses), 'Not a model'
    assert all(l in model for l in assumptions), 'Assumptions are violated'
    assert cost == sum(w for l, w in prefs.items() if l not in model), 'Wrong cost'
    return True

def test_preferences():
    clauses = [[1, 2], [3]]
    prefs = {-1: 100, -2: 3, -3: 11, 4: 7, -4: 2}

    with Cadical300(bootstrap_with=clauses) as solver:
        assert solver.flip_bits(preferences=prefs) == ([-1, 2, 3, 4], 16)
        assert solver.flip_bits() == ([-1, 2, 3, 4], 16)  # preferences are kept
        assert solver.flip_bits(preferences={}) == ([-1, 2, 3, 4], 0)
        assert solver.get_status() is None and solver.solve()

def test_assumptions():
    clauses = [[1, 2], [-1, -2]]
    prefs = {1: 4, -2: 7, 5: 3}

    with Cadical300(bootstrap_with=clauses) as solver:
        for assumptions in ([1], [-1], [5], [-5], []):
            assert check(solver.flip_bits(assumptions=assumptions, preferences=prefs),
                         clauses, assumptions, prefs)
            assert solver.solve(assumptions=[-1])  # assumptions do not leak

        assert solver.flip_bits(assumptions=[1, -1]) == (None, None)

        solver.add_clause([-1])
        solver.add_clause([-2])
        assert solver.flip_bits() == (None, None)
        assert not solver.solve()

def test_warm_start():
    # all the variables are eliminated when solving
    clauses = [[1, 2], [-1, -2], [-2, 3], [2, -3], [7, 8], [-3, 9, 10], [-9, -10]]
    prefs = {1: 5, -2: 2, 3: 3, -7: 1, -8: 4}

    with Cadical300(bootstrap_with=clauses) as solver:
        solver.set_phases([-1, 2, 3, 7, 8, 9])
        assert solver.solve()
        model = solver.get_model()

        # the search starts from the model of the solver (variables 4-6 are unused)
        res = solver.flip_bits(preferences=prefs, budget=0)
        assert check(res, clauses, [], prefs)
        assert res[0][:3] + res[0][6:] == model[:3] + model[6:]

        assert check(solver.flip_bits(), clauses, [], prefs)
        assert solver.solve()

def test_random():
    rng = random.Random(9173)

    for i in range(120):
        n = rng.randrange(2, 8)
        clauses = [[rng.choice([-1, 1]) * v for v in rng.sample(range(1, n + 1), rng.randrange(1, min(4, n) + 1))] for _ in range(rng.randrange(0, 18))]
        models = [set(v if p else -v for v, p in enumerate(bits, 1)) for bits in itertools.product([False, True], repeat=n)]
        models = [m for m in models if all(any(l in m for l in cl) for cl in clauses)]

        with Cadical300(bootstrap_with=clauses) as solver:
            if i % 3 == 0:
                solver.process(rounds=2)
            elif i % 3 == 1:
                solver.solve()

            for _ in range(4):
                prefs = {p * v: rng.randrange(0, 100) for v in range(1, n + 1) for p in [-1, 1] if rng.randrange(3)}
                assumptions = [rng.choice([-1, 1]) * v for v in rng.sample(range(1, n + 1), rng.randrange(3))]
                feasible = [m for m in models if all(l in m for l in assumptions)]

                res = solver.flip_bits(assumptions=assumptions, preferences=prefs, budget=2000)
                if check(res, clauses, assumptions, prefs):
                    assert feasible
                    assert res[1] >= min(sum(w for l, w in prefs.items() if l not in m) for m in feasible)

                assert solver.solve(assumptions=assumptions) == bool(feasible)
