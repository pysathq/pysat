from pysat.examples.optux import OptUx
from pysat.formula import CNF, WCNF, IDPool
from pysat.process import Processor
from pysat.solvers import Solver

def test_processor():
    cnf1 = CNF(from_clauses=[[-1, 2], [-2, 3], [-3, 4], [1, -5], [1, 5], [-4, 6], [-4, -6]])
    cnf2 = CNF(from_clauses=[[-1, 2], [-2, 3], [-3, 4], [1, -5], [1, 5], [-4, 6]])

    # must be unsatisfiable
    with Processor(cnf1) as processor:
        result = processor.process()

        with Solver(bootstrap_with=result) as solver:
            assert solver.solve() == False, 'CNF1 must be unsatisfiable'

    # must be satisfiable
    with Processor(cnf2) as processor:
        result = processor.process()

        with Solver(bootstrap_with=result) as solver:
            assert solver.solve() == True, 'CNF2 must be satisfiable'
            model = solver.get_model()
            restored = processor.restore(model)

            with Solver(bootstrap_with=cnf2) as checker:
                assert checker.solve(assumptions=restored) == True, 'Wrong model after reconstruction'

def test_frozen():
    pool = IDPool()
    xvar = lambda i: pool.id(f'x{i}')
    rvar = lambda i: pool.id(f'r{i}')

    hard = CNF(from_clauses=[
                             [+xvar(6), +xvar(2), +rvar(1)],
                             [-xvar(6), +xvar(2), +rvar(2)],
                             [-xvar(2), +xvar(1), +rvar(3)],
                             [-xvar(6), +xvar(8), +rvar(4)],
                             [+xvar(6), -xvar(8), +rvar(5)],
                             [+xvar(2), +xvar(4), +rvar(6)],
                             [-xvar(4), +xvar(5), +rvar(7)],
                             [+xvar(7), +xvar(5), +rvar(8)],
                             [-xvar(7), +xvar(5), +rvar(9)],
                             [-xvar(5), +xvar(3), rvar(10)],
                            ])

    soft = [-rvar(i) for i in range(1, 11)] + [-xvar(1), -xvar(3)]

    # we should be able to compute all the MUSes
    with Processor(hard) as processor:
        result = processor.process(freeze=soft)

        wcnf = WCNF()
        wcnf.hard = result.clauses
        wcnf.soft = [[l] for l in soft]
        wcnf.wght = [1 for l in soft]
        wcnf.topw = len(wcnf.soft) + 1
        wcnf.nv = max([abs(lit) for lit in soft] + [result.nv])

        # enumerating all MUSes
        with OptUx(wcnf) as optux:
            muses = []
            for i, mus in enumerate(optux.enumerate(), 1):
                muses.append(mus)

            muses.sort()
            assert muses == [[1, 2, 3, 11], [3, 6, 7, 10, 11, 12], [8, 9, 10, 12]], 'Wrong MUSes'
