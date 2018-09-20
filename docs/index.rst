=================================
Welcome to PySAT's documentation!
=================================

This site covers the usage and API documentation of the PySAT toolkit. For the
basic information on what PySAT is, please, see `the main project website
<https://pysathq.github.io>`__.

API documentation
=================

The PySAT toolkit has three core modules: :mod:`.card`, :mod:`.formula`, and
:mod:`.solvers`.  The two of them (:mod:`.card` and :mod:`.solvers`) are Python
wrappers for the code originally implemented in the C/C++ languages while the
:mod:`.formula` module is a *pure* Python module.

Core PySAT modules
------------------

.. toctree::
    :maxdepth: 3

    api/card
    api/formula
    api/solvers

Supplementary :mod:`.examples` package (partially documented)
-------------------------------------------------------------

.. toctree::
    api/examples/fm
    api/examples/genhard
    api/examples/hitman
    api/examples/lbx
    api/examples/lsu
    api/examples/mcsls
    api/examples/musx
    api/examples/rc2
