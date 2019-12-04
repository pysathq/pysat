=================================
Welcome to PySAT's documentation!
=================================

This site covers the usage and API documentation of the PySAT toolkit. For the
basic information on what PySAT is, please, see `the main project website
<https://pysathq.github.io>`__.

API documentation
=================

The PySAT toolkit has four core modules: :mod:`.card`, :mod:`.formula`,
:mod:`.pb` and :mod:`.solvers`. The three of them (:mod:`.card`, :mod:`.pb`
and :mod:`.solvers`) are Python wrappers for the code originally implemented
in the C/C++ languages while the :mod:`.formula` module is a *pure* Python
module. Version *0.1.4.dev0* of PySAT brings a new module called :mod:`pb`,
which is a wrapper for the basic functionality of a third-party library
`PyPBLib <https://pypi.org/project/pypblib/>`__ developed by the `Logic
Optimization Group <http://ulog.udl.cat/>`__ of the University of Lleida.

Core PySAT modules
------------------

.. toctree::
    :maxdepth: 3

    api/card
    api/formula
    api/pb
    api/solvers

Supplementary :mod:`.examples` package
--------------------------------------

.. toctree::
    api/examples/fm
    api/examples/genhard
    api/examples/hitman
    api/examples/lbx
    api/examples/lsu
    api/examples/mcsls
    api/examples/models
    api/examples/musx
    api/examples/rc2
