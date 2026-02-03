=================================
Welcome to PySAT's documentation!
=================================

This site covers the usage and API documentation of the PySAT toolkit. For the
basic information on what PySAT is, please, see `the main project website
<https://pysathq.github.io>`__.

API documentation
=================

The PySAT toolkit has seven core modules: :mod:`.card`, :mod:`.engines`,
:mod:`.formula`, :mod:`.integer`, :mod:`.pb`, :mod:`.process` and
:mod:`.solvers`. The four of them (:mod:`.card`, :mod:`.pb`, :mod:`.process`
and :mod:`.solvers`) are Python wrappers for the code originally implemented
in the C/C++ languages while the :mod:`.engines`, :mod:`.formula` and
:mod:`.integer` modules are *pure* Python modules. Version
*0.1.4.dev0* of PySAT brings a new module called :mod:`.pb`, which is a wrapper
for the basic functionality of a third-party library `PyPBLib
<https://pypi.org/project/pypblib/>`__ developed by the `Logic Optimization
Group <http://ulog.udl.cat/>`__ of the University of Lleida.

A supplementary sixth module :mod:`.examples` presents a list of scripts,
which are supposed to demonstrate how the toolkit can be used for practical
problem solving. The module includes a formula generator, several MaxSAT
solvers including an award-winning RC2, a few (S)MUS extractors and
enumerators as well as MCS enumerators, among other scripts.

Finally, an additional seventh module :mod:`.allies` brought by version
*0.1.8.dev3* is meant to provide access to a number of third-party tools
important for practical SAT-based problem solving.

Core PySAT modules
------------------

.. toctree::
    :maxdepth: 1

    api/card
    api/engines
    api/formula
    api/integer
    api/pb
    api/process
    api/solvers

Supplementary :mod:`.examples` package
--------------------------------------

.. toctree::
    :maxdepth: 1

    api/examples/bbscan
    api/examples/bica
    api/examples/fm
    api/examples/genhard
    api/examples/hitman
    api/examples/lbx
    api/examples/lsu
    api/examples/mcsls
    api/examples/models
    api/examples/musx
    api/examples/optux
    api/examples/primer
    api/examples/rc2

Supplementary :mod:`.allies` package
------------------------------------

This module provides interface to a list of external tools useful in practical
SAT-based problem solving. Although only ApproxMCv4 is currently present here,
the list of tools will grow.

.. toctree::
    :maxdepth: 1

    api/allies/approxmc
    api/allies/unigen
