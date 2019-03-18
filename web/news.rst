====
News
====

PySAT is being developed with the *rolling release* model, which means we do
not deliver major releases from time to time. Instead, many small (sometimes
tiny) and frequent updates are provided. As a result, `upgrading
<installation.html>`_ your installation of the toolkit every now to keep it up
to date and then is good idea.

Changelog and more
------------------

17.03.2019 (*0.1.4.dev2*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added three solvers of the Maple family: Maplesat (i.e. MapleCOMSPS_LRB),
  MapleCM, and MapleChrono (i.e. MapleLCMDistChronoBT).
- A few minor fixes.

13.03.2019 (*0.1.4.dev1*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added :mod:`pysat.pb` providing access to a few PB constraints with the use
  of PyPBLib.
- A number of small fixes.

28.12.2018 (*0.1.3.dev25*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed model enumerator in :mod:`pysat.examples.rc2`.
- Documented :mod:`pysat.examples.rc2`.

01.11.2018 (*0.1.3.dev24*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Documented a few example modules including :mod:`pysat.examples.lbx`,
  :mod:`pysat.examples.mcsls`, and :mod:`pysat.examples.lsu`.

22.09.2018 (*0.1.3.dev23*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added the image of the FLOC medals to the webpage.
- Added the news section to the webpage.
- Removed unused source code.

20.09.2018 (*0.1.3.dev22*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added better support for iterables in :mod:`pysat.card` and
  :mod:`pysat.solvers`.
- Added documentation for ``examples/fm.py``, ``examples/genhard.py``,
  ``examples/hitman.py`` and ``examples/musx.py``.

06.09.2018 (*0.1.3.dev21*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a typo in the project description on `PyPI
  <https://pypi.org/project/python-sat/>`_.

30.08.2018 (*0.1.3.dev20*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added an implementation of the LSU algorithm for MaxSAT.
- Fixed a bug in :mod:`pysat._fileio` appearing when LZMA is not present.

25.08.2018 (*0.1.3.dev19*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Solvers can receive ``iterables`` as clauses (besides ``lists``).
- Fixed a minor issue in ``examples/hitman.py``.

25.08.2018 (*0.1.3.dev18*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Cosmetic changes in the documentation.

25.08.2018 (*0.1.3.dev17*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- More incremental functionality in RC2, LBX, and MCSls.
- Added a minimal hitting set enumerator as another example.

20.08.2018 (*0.1.3.dev16*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a problem appearing when no model exists.

19.08.2018 (*0.1.3.dev15*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added support for reading and writing with \*zipped files.
- Added the corresponding capabilities to the examples.

17.08.2018 (*0.1.3.dev14*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a couple of minor issues related to Python 3 (in RC2 and iterative
  totalizer).

27.07.2018 (*0.1.3.dev13*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added support for setting variable *phases* (*user-preferred polarities*).

16.07.2018 (*0.1.3.dev12*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added incremetal model enumeration to RC2.
- Fixed a couple of minor issues in LBX and MCSls.
- Added mutilated chessboard princimple formulas for ``examples/genhard.py``.

12.07.2018 (RC2)
~~~~~~~~~~~~~~~~

MaxSAT solver RC2 won both *unweighted* and *weighted* categories of the main
track of `MaxSAT Evaluation 2018
<https://maxsat-evaluations.github.io/2018/rankings.html>`_ and got two medals
at `FLOC 2018 Olympic Games <https://www.floc2018.org/floc-olympic-games/>`_!

.. image:: medals.svg
   :width: 270 px
   :align: left

20.06.2018 (*0.1.3.dev11*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Added the webpage for the toolkit.
- The first draft of the documentation.

07.06.2018 (*0.1.3.dev10*)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a minor bug in iterative totalizer.
- Added modes A and B to RC2 for MaxSAT evaluation 2018.

28.05.2018 (*0.1.3.dev9*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added a way to manually set off a previously set budget on the number of
  clauses or propagations.
- Added an optional core minimization in RC2.

25.05.2018 (*0.1.3.dev8*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed *long_description* of the project. Corrected the GitHub reference.
- Implemented hidden AtMost1 constraint detection in RC2.
- Improved support for Python 3 in RC2.
- A few more minor issues in RC2 got fixed.

23.05.2018 (*0.1.3.dev7*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added optional *phase saving* in literal propagation.
- Fixed a bug in literal propagation.

22.05.2018 (*0.1.3.dev6*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- More fixes in literal propagation and its interface.

21.05.2018 (*0.1.3.dev5*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- A minor modification of literal propagation.

21.05.2018 (*0.1.3.dev4*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added *literal propagation* in MiniSat-like solvers, i.e. ``Minisat22``,
  ``MinisatGH``, ``Minicard``, ``Glucose3``, and ``Glucose41``.

15.05.2018 (*0.1.3.dev3*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Another attempt to fix installation. Mirrored GitHub-hosted solvers.

02.05.2018 (*0.1.3.dev2*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Modified signal handling in ``pysolvers`` and ``pycard``.
- Fixed a couple of minor issues in iterative totalizer.
- Reimplemented ``examples/genhard.py``. Each family of formulas is not a
  class.

10.04.2018 (*0.1.3.dev1*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a bug in *limited* SAT solving, i.e. in solving within a given
  *budget* on the number of conflicts or the number of propagations.

09.04.2018 (*0.1.3.dev0*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Improved ``README.rst``.
- Minor modifications in ``examples/genhard.py``.
- Added example scripts installation as executables.

08.04.2018 (*0.1.2.dev9*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a couple of minor bugs in :mod:`pysat.card` and :mod:`pysat.formula`.

06.04.2018 (*0.1.2.dev8*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added a couple of optimizations to ``examples/rc2.py`` including
  *unsatisfiable core trimming* and *core exhaustion*.
- Added :class:`SolverNames` to simplify a solver selection.
- An attempt to make the installation process less fragile.

03.04.2018 (*0.1.2.dev7*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed incremental mode of Glucose 4.1.
- Added support for Minicard's native cardinality constraints in
  ``examples/fm.py``.
- Added RC2 as an example of a MaxSAT solver.
- Fixed a minor issue in iterative totalizer.

29.03.2018 (*0.1.2.dev6*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a bug in iterative totalizer, which led to clause duplication.

28.03.2018 (*0.1.2.dev5*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added iterative totalizer to :mod:`pysat.card`.
- Added solver download caching (i.e. a solver is not downloaded more than once).

25.03.2018 (*0.1.2.dev4*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added support for Glucose 4.1.

06.03.2018 (*0.1.2.dev3*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Added ``examples/genhard.py`` illustrating the work with the
  :mod:`pysat.formula` module.
- Added :class:`pysat.formula.IDPool`, a simple manager of *variable
  identifiers*.

04.03.2018 (*0.1.2.dev2*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a bug related to SAT oracle's timer.

02.03.2018 (*0.1.2.dev1*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Fixed a number of issues in ``examples/fm.py``, ``examples/lbx.py``, and
  ``examples/musx.py`` for a better support of Python 3.

01.03.2018 (*0.1.1.dev9*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Minor fixes in ``README.rst``.

22.02.2018 (*0.1.1.dev8*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Minor changes in :mod:`pysat.card`.
- A few typos in :mod:`pysat.examples.fm`.
- Fixed *author_email* in ``setup.py``.

11.02.2018 (*0.1.1.dev7*)
~~~~~~~~~~~~~~~~~~~~~~~~~

- Initial commit accompanying the `corresponding SAT submission
  <citation.html>`_.
