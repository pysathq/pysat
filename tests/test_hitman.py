import random

import pytest

from pysat.examples.hitman import Atom, Hitman


def generate_instance(
    seed, num_sets, range_nums, min_size_sets, max_size_sets
):
    rng = random.Random(seed)
    collection_of_sets = []
    for _ in range(num_sets):
        collection_of_sets.append(
            rng.sample(range(range_nums), rng.randint(min_size_sets, max_size_sets))
        )
    return collection_of_sets


def is_minimal_hs(hs, hit_sets, blocked_sets):
    for blocked in blocked_sets:
        if blocked.issubset(hs):
            return False

    in_minimal = set()

    for s in hit_sets:
        overlap = s.intersection(hs)

        if not overlap:
            return False

        if len(overlap) == 1:
            in_minimal.update(overlap)

    return in_minimal == hs


def test_add_hard_registers_new_object_with_mcs_enumerators():
    for htype in ('lbx', 'mcsls'):
        with Hitman(bootstrap_with=[['first']], htype=htype) as hitman:
            hitman.add_hard([Atom('second')])

            assert sorted(hitman.get()) == ['first', 'second']


def test_add_hard_registers_weighted_new_objects_with_rc2():
    weights = {'base': 1, 'expensive': 10, 'cheap': 1}

    with Hitman(bootstrap_with=[['base']], weights=weights,
            htype='sorted') as hitman:
        hitman.add_hard([Atom('expensive'), Atom('cheap')], weights=weights)

        assert sorted(hitman.get()) == ['base', 'cheap']


def test_add_hard_registers_new_objects_with_sat():
    with Hitman(bootstrap_with=[['base']], htype='sat',
            solver='mgh') as hitman:
        hitman.add_hard([Atom('left'), Atom('right')])

        result = hitman.get()

        assert 'base' in result
        assert len(set(result) & {'left', 'right'}) == 1
        assert set(hitman.oracle.vmap.e2i) == {1, 2, 3}


@pytest.mark.parametrize('solver', ['minisat-gh', 'cadical153', 'cadical195', 'cadical300'])
@pytest.mark.parametrize('seed', [0, 1, 2])
def test_sat_enumerates_minimal_hitting_sets(solver, seed):
    max_num_hitting_sets = 5_000

    num_sets = 100
    range_nums = 200
    min_size_sets = 3
    max_size_sets = 10

    sets = generate_instance(
            seed, num_sets, range_nums, min_size_sets, max_size_sets
    )

    to_hit = [frozenset(s) for s in sets]
    blocked = []

    with Hitman(bootstrap_with=sets, htype="sat", solver=solver) as hitman:

        for _ in range(max_num_hitting_sets):
            hs = hitman.get()
            if hs is None:
                break

            hs = frozenset(hs)
            assert is_minimal_hs(hs, to_hit, blocked), \
                    'Error: The hitting set is non-minimal'

            blocked.append(hs)
            hitman.block(hs)

