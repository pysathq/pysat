from pysat.formula import CNF
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
