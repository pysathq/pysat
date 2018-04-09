PySAT: simple SAT-based prototyping in Python
=============================================

A Python library providing a simple interface to a number of
state-of-art Boolean satisfiability (SAT) solvers and a few types of
cardinality encodings. The purpose of PySAT is to enable researchers
working on SAT and its applications and generalizations to easily
prototype with SAT oracles in Python while exploiting incrementally the
power of the original low-level implementations of modern SAT solvers.

With PySAT it should be easy for you to implement a MaxSAT solver, an
MUS/MCS extractor/enumerator, or any tool solving an application problem
with the (potentially multiple) use of a SAT oracle.

Currently, the following SAT solvers are supported (currently, for
Minisat-based solvers only *core* versions are integrated):

-  Glucose (`3.0 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Glucose (`4.1 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Lingeling (`bbc-9230380-160707 <http://fmv.jku.at/lingeling/>`__)
-  Minicard (`1.2 <https://github.com/liffiton/minicard>`__)
-  Minisat (`2.2 release <http://minisat.se/MiniSat.html>`__)
-  Minisat (`GitHub version <https://github.com/niklasso/minisat>`__)

Cardinality encodings supported are implemented in C++ and include:

-  pairwise [7]_
-  bitwise [7]_
-  sequential counters [8]_
-  sorting networks [3]_
-  cardinality networks [1]_
-  ladder [4]_
-  totalizer [2]_
-  modulo totalizer [6]_
-  iterative totalizer [5]_

.. [1] Roberto Asin, Robert Nieuwenhuis, Albert Oliveras,
   Enric Rodriguez-Carbonell. *Cardinality Networks and Their Applications*.
   SAT 2009. pp. 167-180

.. [2] Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of Boolean
   Cardinality Constraints*. CP 2003. pp. 108-122

.. [3] Kenneth E. Batcher. *Sorting Networks and Their Applications*.
   AFIPS Spring Joint Computing Conference 1968. pp. 307-314

.. [4] Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
   SAT*. In International workshop on modelling and reformulating constraint
   satisfaction problems 2004. pp. 95-110

.. [5] Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
   *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

.. [6] Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura,
   Hiroshi Fujita. *Modulo Based CNF Encoding of Cardinality Constraints and
   Its Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

.. [7] Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
   2009. pp. 75-97

.. [8] Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean
   Cardinality Constraints*. CP 2005. pp. 827-831

Usage
-----

Boolean variables in PySAT are represented as natural identifiers, e.g. numbers
from :math:`\mathbb{N}_{>0}`. A *literal* in PySAT is assumed to be an integer,
e.g. ``-1`` represents a literal :math:`\neg{x_1}` while :math:`5` represents a
literal :math:`x_5`.  A *clause* is a list of literals, e.g. ``[-3, -2]`` is a
clause :math:`(\neg{x_3} \vee \neg{x_2})`.

The following is a trivial example of PySAT usage:

.. code:: python

    >>> from pysat.solvers import Glucose3
    >>>
    >>> g = Glucose3()
    >>> g.add_clause([-1, 2])
    >>> g.add_clause([-2, 3])
    >>> print g.solve()
    >>> print g.get_model()
    ...
    True
    [-1, -2, -3]

Another example shows how to extract *unsatisfiable cores* from a SAT
solver given an unsatisfiable set of clauses:

.. code:: python

    >>> from pysat.solvers import Minisat22
    >>>
    >>> with Minisat22(bootstrap_with=[[-1, 2], [-2, 3]]) as m:
    ...     print m.solve(assumptions=[1, -3])
    ...     print m.get_core()
    ...
    False
    [-3, 1]

Finally, the following example gives an idea of how one can extract a
*proof* (supported by Glucose3, Glucose4, and Lingeling only):

.. code:: python

    >>> from pysat.formula import CNF
    >>> from pysat.solvers import Lingeling
    >>>
    >>> formula = CNF()
    >>> formula.append([-1, 2])
    >>> formula.append([1, -2])
    >>> formula.append([-1, -2])
    >>> formula.append([1, 2])
    >>>
    >>> with Lingeling(bootstrap_with=formula.clauses, with_proof=True) as l:
    ...     if l.solve() == False:
    ...         print(l.get_proof())
    ...
    ['2 0', '1 0', '0']

PySAT usage is detailed in the `provided examples <examples>`__. For
instance, one can see there simple PySAT-based implementations of

-  Fu&Malik algorithm for MaxSAT [9]_
-  RC2/OLLITI algorithm for MaxSAT [13]_
-  CLD-like algorithm for MCS extraction and enumeration [11]_
-  LBX-like algorithm for MCS extraction and enumeration [12]_
-  Deletion-based MUS extraction [10]_

.. [9] Zhaohui Fu, Sharad Malik. *On Solving the Partial MAX-SAT Problem*.
   SAT 2006. pp. 252-265

.. [10] Joao Marques Silva. *Minimal Unsatisfiability: Models, Algorithms and
   Applications*. ISMVL 2010. pp. 9-14

.. [11] Joao Marques-Silva, Federico Heras, Mikolas Janota, Alessandro Previti,
   Anton Belov. *On Computing Minimal Correction Subsets*. IJCAI 2013. pp.
   615-622

.. [12] Carlos Mencia, Alessandro Previti, Joao Marques-Silva. *Literal-Based
   MCS Extraction*. IJCAI 2015. pp. 1973-1979

.. [13] António Morgado, Carmine Dodaro, Joao Marques-Silva. *Core-Guided
   MaxSAT with Soft Cardinality Constraints*. CP 2014. pp. 564-573. CP 2014.
   pp. 564-573

The examples can also be accessed as a subpackage of PySAT:

.. code:: python

    >>> from pysat.formula import CNF
    >>> from pysat.examples.lbx import LBX
    >>>
    >>> formula = CNF(from_file='input.cnf')
    >>> mcsls = LBX(formula)
    >>>
    >>> for mcs in mcsls.enumerate():
    ...     print mcs

Alternatively, they can be used as standalone executables, e.g. like this:

::

   lbx.py -e all -d -s g4 -v another-input.wcnf

Installation
------------

The simplest way to get and start using PySAT is to install the latest
stable release of PySAT from PyPI:

::

    pip install python-sat

Alternatively, you can clone this repository and do the following with
your local copy:

::

    python setup.py install

or (if you choose a directory to install PySAT into)

::

    python setup.py install --prefix=<where-to-install>

Both options (i.e. via ``pip`` or ``setup.py``) are supposed to download
and compile all the supported SAT solvers as well as prepare the
installation of PySAT.

License
-------

This project is licensed under the MIT License - see the
`LICENSE <LICENSE.txt>`__ file for details.
