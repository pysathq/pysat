PySAT: SAT technology in Python
===============================

PySAT is a Python (2.7, 3.4+) toolkit, which aims at providing a simple and
unified interface to a number of state-of-art `Boolean satisfiability (SAT)
<https://en.wikipedia.org/wiki/Boolean_satisfiability_problem>`__ solvers as
well as to a variety of cardinality encodings. The purpose of PySAT is to
enable researchers working on SAT and its applications and generalizations to
easily prototype with SAT oracles in Python while exploiting incrementally the
power of the original low-level implementations of modern SAT solvers.

PySAT can be helpful when solving problems in :math:`\mathbb{NP}` but also
`beyond <http://beyondnp.org/>`__ :math:`\mathbb{NP}`. For instance, PySAT is
handy when one needs to quickly implement a MaxSAT solver, an MUS/MCS extractor
or enumerator, an abstraction-based QBF solver, or any other kind of tool
solving an application problem with the (potentially *multiple* and/or
*incremental*) use of a SAT oracle.

Features
--------

PySAT integrates a number of widely used state-of-the-art SAT solvers. All the
provided solvers are the original low-level implementations installed along
with PySAT. Note that the solvers' source code *is not* a part of the project's
source tree and is downloaded and patched at every PySAT installation.

Currently, the following SAT solvers are supported (at this point, for
Minisat-based solvers only *core* versions are integrated):

-  Glucose (`3.0 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Glucose (`4.1 <http://www.labri.fr/perso/lsimon/glucose/>`__)
-  Lingeling (`bbc-9230380-160707 <http://fmv.jku.at/lingeling/>`__)
-  Minicard (`1.2 <https://github.com/liffiton/minicard>`__)
-  Minisat (`2.2 release <http://minisat.se/MiniSat.html>`__)
-  Minisat (`GitHub version <https://github.com/niklasso/minisat>`__)

In order to make SAT-based prototyping easier, PySAT integrates a variety of
cardinality encodings. All of them are implemented from scratch in C++. The
list of cardinality encodings included is the following:

-  pairwise [8]_
-  bitwise [8]_
-  sequential counters [9]_
-  sorting networks [4]_
-  cardinality networks [2]_
-  ladder/regular [1]_ [5]_
-  totalizer [3]_
-  modulo totalizer [7]_
-  iterative totalizer [6]_

.. [1] Carlos Ansótegui, Felip Manyà. *Mapping Problems with Finite-Domain
   Variables to Problems with Boolean Variables*. SAT (Selected Papers) 2004.
   pp. 1-15

.. [2] Roberto Asin, Robert Nieuwenhuis, Albert Oliveras,
   Enric Rodriguez-Carbonell. *Cardinality Networks and Their Applications*.
   SAT 2009. pp. 167-180

.. [3] Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of Boolean
   Cardinality Constraints*. CP 2003. pp. 108-122

.. [4] Kenneth E. Batcher. *Sorting Networks and Their Applications*.
   AFIPS Spring Joint Computing Conference 1968. pp. 307-314

.. [5] Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
   SAT*. In International workshop on modelling and reformulating constraint
   satisfaction problems 2004. pp. 95-110

.. [6] Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
   *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

.. [7] Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura,
   Hiroshi Fujita. *Modulo Based CNF Encoding of Cardinality Constraints and
   Its Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

.. [8] Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
   2009. pp. 75-97

.. [9] Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean
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

PySAT usage is detailed in the `provided examples
<https://github.com/pysathq/pysat/tree/master/examples>`__. For instance, one
can find simple PySAT-based implementations of

-  Fu&Malik algorithm for MaxSAT [10]_
-  RC2/OLLITI algorithm for MaxSAT [14]_ [15]_
-  CLD-like algorithm for MCS extraction and enumeration [12]_
-  LBX-like algorithm for MCS extraction and enumeration [13]_
-  Deletion-based MUS extraction [11]_

.. [10] Zhaohui Fu, Sharad Malik. *On Solving the Partial MAX-SAT Problem*.
   SAT 2006. pp. 252-265

.. [11] Joao Marques Silva. *Minimal Unsatisfiability: Models, Algorithms and
   Applications*. ISMVL 2010. pp. 9-14

.. [12] Joao Marques-Silva, Federico Heras, Mikolas Janota, Alessandro Previti,
   Anton Belov. *On Computing Minimal Correction Subsets*. IJCAI 2013. pp.
   615-622

.. [13] Carlos Mencia, Alessandro Previti, Joao Marques-Silva. *Literal-Based
   MCS Extraction*. IJCAI 2015. pp. 1973-1979

.. [14] António Morgado, Carmine Dodaro, Joao Marques-Silva. *Core-Guided
   MaxSAT with Soft Cardinality Constraints*. CP 2014. pp. 564-573

.. [15] António Morgado, Alexey Ignatiev, Joao Marques-Silva. *MSCG: Robust
   Core-Guided MaxSAT Solving. System Description*. JSAT 2015. vol. 9,
   pp. 129-134

The examples are installed with PySAT as a subpackage and, thus, they can be
accessed internally in Python:

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

   $ lbx.py -e all -d -s g4 -v another-input.wcnf

Installation
------------

There are several ways to install PySAT. At this point, either way assumes you
are using a POSIX-compliant operating system with GNU `make
<https://www.gnu.org/software/make/>`__ and `patch
<http://savannah.gnu.org/projects/patch/>`__ installed and available from the
command line. Installation also relies on a C/C++ compiler supporting C++11,
e.g. `GCC <https://gcc.gnu.org/>`__ or `Clang <https://clang.llvm.org/>`__, as
well as the ``six`` `Python package <https://pypi.org/project/six/>`__.

Note that PySAT was not tested on the Microsoft Windows platform, and so *it is
not yet supported*. We are working on resolving this issue but your input may
be needed.

Once all the prerequisites are installed, the simplest way to get and start
using PySAT is to install the latest stable release of the toolkit from `PyPI
<https://pypi.org/>`__:

::

    $ pip install python-sat

Once installed from PyPI, the toolkit at a later stage can be updated in the
following way:

::

    $ pip install -U python-sat

Alternatively, one can clone `the repository
<https://github.com/pysathq/pysat>`__ and execute the following command in the
local copy:

::

    $ python setup.py install

This will install the toolkit into the system's Python path. If another
destination directory is preferred, it can be set by

::

    $ python setup.py install --prefix=<where-to-install>

Both options (i.e. via ``pip`` or ``setup.py``) are supposed to download
and compile all the supported SAT solvers as well as prepare the
installation of PySAT.

Citation
--------

If PySAT has been significant to a project that leads to an academic
publication, please, acknowledge that fact by citing PySAT:

::

    @inproceedings{imms-sat18,
      author    = {Alexey Ignatiev and
                   Antonio Morgado and
                   Joao Marques{-}Silva},
      title     = {{PySAT:} {A} {Python} Toolkit for Prototyping
                   with {SAT} Oracles},
      booktitle = {SAT},
      pages     = {428--437},
      year      = {2018},
      url       = {https://doi.org/10.1007/978-3-319-94144-8_26},
      doi       = {10.1007/978-3-319-94144-8_26}
    }

To-Do
-----

PySAT toolkit is a work in progress. Although it can already be helpful in many
practical settings (and it **was** successfully applied by its authors for a
number of times), it would be great if some of the following additional
features were implemented:

-  more SAT solvers to support (e.g. `CryptoMiniSat
   <https://github.com/msoos/cryptominisat/>`__, `RISS
   <http://tools.computational-logic.org/content/riss.php>`__ among many
   others)

-  pseudo-Boolean constraint encodings

-  formula *(pre-)processing*

-  lower level access to some of the solvers' internal parameters
   (e.g. *variable activities*, etc.)

-  high-level support for arbitrary Boolean formulas (e.g. by Tseitin-encoding
   [16]_ them internally)

All of these will require a significant effort to be made. Therefore, we would
like to encourage the SAT community to contribute and make PySAT a tool for an
easy and comfortable day-to-day use. :)

.. [16] G. S. Tseitin. *On the complexity of derivations in the propositional
   calculus*.  Studies in Mathematics and Mathematical Logic, Part II. pp.
   115–125, 1968

License
-------

PySAT is licensed under `MIT <LICENSE.txt>`__.
