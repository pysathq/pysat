PySAT: SAT technology in Python
===============================

PySAT is a Python (2.7, 3.4+) toolkit, which aims at providing a simple and
unified interface to a number of state-of-art `Boolean satisfiability (SAT)
<https://en.wikipedia.org/wiki/Boolean_satisfiability_problem>`__ solvers as
well as to a variety of cardinality and pseudo-Boolean encodings. The purpose
of PySAT is to enable researchers working on SAT and its applications and
generalizations to easily prototype with SAT oracles in Python while
exploiting incrementally the power of the original low-level implementations
of modern SAT solvers.

PySAT can be helpful when solving problems in `NP
<https://en.wikipedia.org/wiki/NP_(complexity)>`__ but also `beyond NP
<http://beyondnp.org/>`__. For instance, PySAT is handy when one needs to
quickly implement a MaxSAT solver, an MUS/MCS extractor or enumerator, an
abstraction-based QBF solver, or any other kind of tool solving an application
problem with the (potentially *multiple* and/or *incremental*) use of a SAT
oracle.

PySAT is licensed under `MIT
<https://raw.githubusercontent.com/pysathq/pysat/master/LICENSE.txt>`__.

.. image:: medals.svg
   :width: 270 px
   :align: right

.. toctree::
   :hidden:

   news
   features
   usage
   installation
   citation
   todo
