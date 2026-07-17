"""
Regression test for https://github.com/pysathq/pysat/issues/224.

Minisat-family solvers allocate through ``mtl/XAlloc.h``, which throws a C++
``OutOfMemoryException`` when its int32 region/vector allocator overflows.  The
C extension now catches that exception at every allocating entry point and
re-raises it as a Python ``MemoryError`` instead of letting it unwind through
CPython and crash the interpreter.

Triggering the real overflow would need gigabytes, so the test caps the child
process' address space with ``resource.RLIMIT_AS`` and then asks a solver to
declare an enormous number of variables: the allocator fails almost immediately
and must surface as ``MemoryError`` (child exits 0) rather than aborting the
process (negative/non-zero exit code).

The trigger is run in a subprocess so the address-space limit cannot disturb the
pytest process, and the whole module is skipped where ``RLIMIT_AS`` is not
available/reliable (Windows has no ``resource`` module; only Linux enforces
``RLIMIT_AS`` dependably).  The project's test CI runs on Linux, so it executes
there.
"""

import subprocess
import sys
import textwrap

import pytest

pytest.importorskip("resource")  # not available on Windows

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="resource.RLIMIT_AS is reliably enforced only on Linux",
)

# Run in a child so the address-space cap stays isolated from pytest.  Map the
# interpreter + solver first, then cap address space to the current size plus a
# small headroom, then force a ~1e9-variable vector growth so the solver's
# xrealloc fails.  With the fix that failure is a MemoryError (exit 0); without
# it the uncaught C++ exception aborts the process (exit code != 0).
_CHILD = textwrap.dedent(
    """
    import resource, sys
    from pysat.solvers import Solver

    s = Solver(name=sys.argv[1])

    with open("/proc/self/statm") as fp:
        vsz = int(fp.read().split()[0]) * resource.getpagesize()
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (vsz + (256 << 20), hard))

    try:
        s.add_clause([2 ** 30])      # ~1.07e9 vars -> blows past the headroom
        sys.exit(2)                  # no exception raised -> wrong
    except MemoryError:
        sys.exit(0)                  # correct: OOM surfaced as MemoryError
    except BaseException:
        sys.exit(3)                  # some other exception -> wrong
    """
)


@pytest.mark.parametrize("name", ["minisat22", "glucose3", "mergesat3", "minicard"])
def test_oom_raises_memoryerror(name):
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD, name],
        capture_output=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        "expected MemoryError for %s, got returncode=%r\nstdout=%r\nstderr=%r"
        % (name, proc.returncode, proc.stdout, proc.stderr)
    )
