from pysat.examples.genhard import PHP
from pysat.solvers import Solver
from pysat.solvers import ergo_present

solvers = ['cadical103',
           'cadical153',
           'cadical195',
           'cadical300',
           'ergo',
           'gluecard30',
           'gluecard41',
           'glucose30',
           'glucose41',
           'glucose42',
           'lingeling',
           'maplechrono',
           'maplecm',
           'maplesat']

if not ergo_present:  # not built on every platform
    solvers.remove('ergo')


def test_solvers():
    # PHP(5) is tiny but its proof already outgrows a stdio buffer
    cnf = PHP(5)

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf, with_proof=True) as solver:
            assert solver.solve() == False, 'wrong status of {0}'.format(name)

            # the solver writes the proof through a FILE* of its own layered
            # over the descriptor python handed it; unless that stream is
            # flushed first, get_proof() reads whatever has reached the
            # descriptor so far -- a prefix, cut at a buffer boundary
            proof = solver.get_proof()

            assert proof, 'empty proof reported by {0}'.format(name)
            assert '0' in [line.strip() for line in proof], \
                    'truncated proof of {0}, no empty clause derived'.format(name)
