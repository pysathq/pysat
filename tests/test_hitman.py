from pysat.examples.hitman import Atom, Hitman


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
