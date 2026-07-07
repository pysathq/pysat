"""Test that solver OOM raises RuntimeError instead of crashing the process.

Uses a subprocess with RLIMIT_AS to cap address space. This makes realloc()
return NULL (triggering OutOfMemoryException) instead of letting the Linux
OOM killer terminate the process.
"""

import subprocess
import sys

import pytest

# fmt: off
MINISAT_SOLVERS = [
    "glucose3", "glucose41", "glucose421",
    "gluecard3", "gluecard41",
    "minisat22", "minisat-gh",
    "maplesat", "maplecm", "maplechrono",
    "minicard", "mergesat3",
]
# fmt: on

_SUBPROCESS_SCRIPT = """\
import resource, sys

GB = 1024**3
resource.setrlimit(resource.RLIMIT_AS, (4 * GB, 4 * GB))

from pysat.solvers import Solver

solver_name = sys.argv[1]
s = Solver(name=solver_name)
var = 1
try:
    while True:
        s.add_clause(list(range(var, var + 1000)))
        var += 1000
except RuntimeError as e:
    if "allocator limit" in str(e):
        print(f"OK: {e}")
        s.delete()
        sys.exit(0)
    print(f"WRONG RuntimeError: {e}", file=sys.stderr)
    s.delete()
    sys.exit(1)
except BaseException as e:
    print(f"UNEXPECTED {type(e).__name__}: {e}", file=sys.stderr)
    s.delete()
    sys.exit(2)

print("ERROR: loop ended without exception", file=sys.stderr)
s.delete()
sys.exit(3)
"""


@pytest.mark.parametrize("solver_name", MINISAT_SOLVERS)
def test_oom_raises_runtime_error(solver_name):
    """Solver's internal allocator overflow raises RuntimeError, not process crash.

    Runs in a subprocess with 4 GB address-space limit so that realloc()
    fails before the Linux OOM killer can intervene. Before this fix, the
    uncaught C++ OutOfMemoryException would cross the FFI boundary and
    std::terminate() the process.
    """
    result = subprocess.run(
        [sys.executable, "-c", _SUBPROCESS_SCRIPT, solver_name],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"Solver {solver_name}: expected RuntimeError, got rc={result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
