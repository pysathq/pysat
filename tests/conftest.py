import pytest
from pysat.solvers import ergo_present


def pytest_collection_modifyitems(config, items):
    """
        Ergo is not built on every platform (MSVC cannot compile it), so
        skip whatever names it rather than failing to import or construct.
    """

    if ergo_present:
        return

    skip = pytest.mark.skip(reason='ergo is not built on this platform')

    for item in items:
        if 'ergo' in item.nodeid.lower():
            item.add_marker(skip)
