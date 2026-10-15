from pysat.solvers import Solver
from pysat.solvers import ergo_present

# every solver's name, as a clause-adding backend
solvers = ['m22', 'mgh', 'mep', 'mpl', 'mcm', 'mc', 'mcb', 'lgl',
           'g3', 'g4', 'g41', 'gc3', 'gc4',
           'cd', 'cd15', 'cd19', 'cd30', 'cdl', 'cdl15', 'cdl19', 'ergo']

if not ergo_present:  # not built on every platform
    solvers.remove('ergo')


def test_empty_clause_bootstrap():
    for name in solvers:
        with Solver(name=name, bootstrap_with=[[]]) as solver:
            assert solver.solve() == False, 'empty clause ignored by {0}'.format(name)


def test_empty_clause_first():

    for name in solvers:
        with Solver(name=name) as solver:
            solver.add_clause([])
            assert solver.solve() == False, 'empty clause ignored by {0}'.format(name)


def test_empty_clause_after():
    for name in solvers:
        with Solver(name=name) as solver:
            solver.add_clause([1, 2])
            solver.add_clause([])
            assert solver.solve() == False, 'empty clause ignored by {0}'.format(name)
