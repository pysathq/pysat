from pysat.formula import IDPool

def test_idpool_neg():
    pool = IDPool(with_neg=True)

    pool.id('hello')
    pool.id(+25)
    pool.id(-42)
    pool.id('world')

    assert pool.id('hello') == 1
    assert pool.id(25) == -pool.id(-25) == +2
    assert pool.id(42) == -pool.id(-42) == -3
    assert pool.id('world') == 4

def test_idpool_occupied():
    pool = IDPool(start_from=5, occupied=[[2, 10], [12, 20], [22, 30]], with_neg=True)

    pool.id('hello')
    pool.id(+25)
    pool.id(-42)
    pool.id('world')

    assert pool.id('hello') == 11
    assert pool.id(25) == -pool.id(-25) == +21
    assert pool.id(42) == -pool.id(-42) == -31
    assert pool.id('world') == 32
