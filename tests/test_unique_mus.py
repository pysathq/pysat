import itertools
from pysat.examples.optux import OptUx
from pysat.formula import CNF, WCNF

def test_unique_mus():
    cnf = CNF(from_clauses=[[-1, 2], [1, -2], [-1, -2], [1, 2]])
    wcnf = cnf.weighted()

    # considering various parameter combinations
    for booleans in itertools.product([False, True], repeat=3):
        for trim in [0, 5]:

            with OptUx(wcnf, solver='g3', adapt=booleans[0],
                    exhaust=booleans[1], minz=booleans[2],
                    trim=trim, verbose=0) as optux:

                muses = []
                for mus in optux.enumerate():
                    muses.append(mus)

                assert len(muses) == 1, 'There should be a single MUS!'
