#!/usr/bin/env python3
"""
    Enumerate non-isomorphic graphs on n vertices using SAT + IPASIR-UP.

    This example uses the CaDiCaL 1.9.5 solver with an external propagator
    (via the IPASIR-UP interface) to enforce canonical form (colex-minimal
    adjacency matrix under vertex permutations). The propagator detects
    symmetry violations during search and prunes them with reason clauses.

    Usage:
        python ipasirup_graphs.py <n>

    Expected counts (OEIS A000088):
        n=0: 1, n=1: 1, n=2: 2, n=3: 4, n=4: 11, n=5: 34, n=6: 156

    Based on the graph enumeration example from the sat-examples repository,
    adapted for pysat's single-literal on_assignment API.
"""

from pysat.formula import CNF
from pysat.solvers import Solver
from pysat.engines import Propagator
from itertools import combinations
from sys import argv

n = int(argv[1])

# Map edge variables (1-indexed) to vertex pairs and back
vars_ids = {i: I for (i, I) in enumerate(combinations(range(n), 2), 1)}
rev_vars = {I: i for (i, I) in enumerate(combinations(range(n), 2), 1)}
for i, j in combinations(range(n), 2):
    rev_vars[j, i] = rev_vars[i, j]

assert all(rev_vars[vars_ids[i]] == i for i in vars_ids)

cnf = CNF()

check_model_calls = 0
propagate_calls = 0


def is_symmetric(A):
    n_ = len(A)
    return all(A[r][c] == A[c][r] for c in range(n_) for r in range(n_))


def permute(A, perm):
    assert all(x in range(len(A)) for x in perm)
    return [[A[r][c] for c in perm] for r in perm]


def combinations_colex_ordered(L, r):
    return list(reversed([tuple(reversed(I)) for I in combinations(reversed(L), r)]))


def fingerprint(A):
    return [A[i][j] for i, j in combinations_colex_ordered(range(len(A)), 2)]


def replace(L, oldvalue, newvalue):
    return [(newvalue if x == oldvalue else x) for x in L]


def minCheck(A, perm=tuple()):
    if not perm:
        assert is_symmetric(A)
    k = len(perm)
    n_ = len(A)
    A_ = permute(A, range(k))
    B_ = permute(A, perm)
    A_fp = replace(fingerprint(A_), None, 0)
    B_fp = replace(fingerprint(B_), None, 1)
    assert len(A_fp) == len(B_fp)

    if B_fp > A_fp:
        return

    if k == n_:
        if B_fp < A_fp:
            order_A = combinations_colex_ordered(range(k), 2)
            order_B = combinations_colex_ordered(perm, 2)
            assert all(y == (perm[x[0]], perm[x[1]]) for x, y in zip(order_A, order_B))

            must_be_positive = set()
            must_be_negative = set()
            found = False
            for l in range(len(B_fp)):
                if B_fp[l] == 0:
                    must_be_positive.add(rev_vars[order_B[l]])
                if A_fp[l] == 1:
                    must_be_negative.add(rev_vars[order_A[l]])
                if B_fp[l] != A_fp[l]:
                    assert B_fp[l] == 0 and A_fp[l] == 1
                    yield perm, must_be_positive, must_be_negative
                    found = True
                    break
            assert found
    else:
        assert k < n_
        for v in range(n_):
            if v not in perm:
                yield from minCheck(A, perm + (v,))


class GraphPropagator(Propagator):
    def __init__(self, n):
        super().__init__()
        self.n = n
        self.level = 0

        self.assigned_at_level = [set()]
        self.assigned_positive = set()
        self.assigned_negative = set()

        self.reason = {}
        self.reason_at_level = [set()]
        self.queue = []
        self.pending = []

    def adjMatrix(self):
        A = [[0 for c in range(self.n)] for r in range(self.n)]
        for i in vars_ids.keys():
            r, c = vars_ids[i]
            if i in self.assigned_positive:
                A[r][c] = A[c][r] = 1
            elif i in self.assigned_negative:
                A[r][c] = A[c][r] = 0
            else:
                A[r][c] = A[c][r] = None
        return A

    def setup_observe(self, s):
        for v in vars_ids:
            s.observe(v)

    def on_new_level(self):
        self.level += 1
        self.assigned_at_level.append(set())
        self.reason_at_level.append(set())
        assert len(self.assigned_at_level) == self.level + 1
        assert len(self.reason_at_level) == self.level + 1

    def on_backtrack(self, to):
        while self.level > to:
            for lit in self.assigned_at_level[self.level]:
                if lit > 0:
                    self.assigned_positive.discard(lit)
                else:
                    self.assigned_negative.discard(-lit)
            self.assigned_at_level.pop()

            for lit in self.reason_at_level[self.level]:
                self.reason.pop(lit, None)
            self.reason_at_level.pop()

            self.level -= 1

        # CaDiCaL may backtrack before propagate() is called, so the queue
        # can still have entries. Clear it instead of asserting it's empty.
        self.queue.clear()

    def on_assignment(self, lit, fixed=False):
        self.assigned_at_level[self.level].add(lit)
        if lit > 0:
            self.assigned_positive.add(lit)
        else:
            self.assigned_negative.add(-lit)

        for better_perm, must_be_positive, must_be_negative in minCheck(self.adjMatrix()):
            assert must_be_negative.issubset(self.assigned_positive)
            assert must_be_positive.issubset(self.assigned_negative)
            conflict_clause = [+x for x in must_be_positive] + [-x for x in must_be_negative]
            impl = conflict_clause[0]
            self.queue.append(impl)
            self.reason[impl] = conflict_clause
            # Track which reason entries were added at this level so
            # on_backtrack can clean them up and avoid stale reasons.
            self.reason_at_level[self.level].add(impl)
            return

    def propagate(self):
        if not self.queue:
            return []
        global propagate_calls
        propagate_calls += 1
        lits = self.queue
        self.queue = []
        return lits

    def provide_reason(self, lit):
        r = self.reason.pop(lit)
        for s in self.reason_at_level:
            s.discard(lit)
        return r

    def check_model(self, model):
        global check_model_calls
        check_model_calls += 1

        for _ in minCheck(self.adjMatrix()):
            print("this should never happen! on_assignment should filter all invalid configurations!")
            self.pending = [-l for l in model]
            return False

        return True

    def add_clause(self):
        cls = self.pending
        self.pending = []
        return cls

    def decide(self):
        return 0


solutions = []
with Solver(name="cadical195", bootstrap_with=cnf.clauses) as s:
    p = GraphPropagator(n)
    s.connect_propagator(p)
    p.setup_observe(s)

    while s.solve():
        model = s.get_model()
        A = [[0 for c in range(n)] for r in range(n)]
        for i in vars_ids:
            r, c = vars_ids[i]
            if model[i - 1] > 0:
                A[r][c] = A[c][r] = 1
        solutions.append(A)
        s.add_clause([-l for l in model])

print(f"{len(solutions)} solutions")

expected_count = [1, 1, 2, 4, 11, 34, 156, 1044, 12346, 274668, 12005168, 1018997864, 165091172592]
assert len(solutions) == expected_count[n], f"expected {expected_count[n]}, got {len(solutions)}"

print(f"check_model_calls: {check_model_calls}")
print(f"propagate_calls: {propagate_calls}")
