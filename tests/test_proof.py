from pysat.solvers import Solver
from pysat.formula import CNF

solvers = [
    "gluecard30",
    "gluecard41",
    "glucose30",
    "glucose41",
    "glucose42",
    "kissat4",
    "lingeling",
    "maplechrono",
    "maplecm",
    "maplesat",
]


def test_solver_proofs():
    cnf = CNF(from_clauses=[[1, 2], [-1, -2], [1, -2], [-1, 2]])

    for name in solvers:
        with Solver(name=name, bootstrap_with=cnf, with_proof=True) as solver:
            assert not solver.solve(), "wrong outcome by {0}".format(name)

            proof = solver.get_proof()
            assert len(proof) > 0, "wrong proof by {0}".format(name)
