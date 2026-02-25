---
title: Updates
---

PySAT is being developed with the *rolling release* model, which means we do
not deliver major releases from time to time. Instead, many small (sometimes
tiny) and frequent updates are provided. As a result,
[upgrading](../installation) your installation of the toolkit every now and
then to keep it up-to-date is good idea.

<!-- # Changelog and more -->

## 25.02.2026 (*1.9.dev1*)

-   Added Kissat 4.0.4 (thanks to Hosein Hadipour). Kissat's wrapper supports
    no incrementality.
-   Fixed a minor issue in conflict budgetting in CryptoMiniSat (thanks to
    Julien Drapeau).

## 04.02.2026 (*1.8.dev30*)

-   Corrected a bug in Cadical195's propagation when an external engine is
    attached.
-   Added :meth:`decode_assignment()`.

## 03.02.2026 (*1.8.dev29*)

-   Added experimental support for rudimentary modelling with integer
    variables.

## 27.01.2026 (*1.8.dev28*)

-   Added support for MSE22 WCNF format.

## 21.01.2026 (*1.8.dev27*)

-   Fixed a bug in the initialiser of RC2.

## 20.12.2025 (*1.8.dev26*)

-   Added asynchronous interruption in RC2.

## 15.12.2025 (*1.8.dev25*)

-   Added automatic negation handling in IDPool.

## 13.10.2025 (*1.8.dev24*)

-   A few impovements in BBScan.
-   Fixed an issue in ztsd compression for Python 3.14.

## 26.09.2025 (*1.8.dev23*)

-   A few corrections in BBScan.

## 22.09.2025 (*1.8.dev22*)

-   Minor fixes in the example scripts accepting input (W)CNF files.
-   Added BBScan, a tool for computing backbones literals of a formula.

## 14.09.2025 (*1.8.dev21*)

-   Added literal freezing in the ``process`` module. This will allow one to
    apply preprocessing in the context of MaxSAT solving as well as MUS and
    MCS enumeration.
-   Added rudimentary support of formula preprocessing to RC2, LBX, MCSls, and
    OptUx.
-   Replaced the compiler for Glucose 4.2.1 (thanks to Christoph Jabs).
-   Fixed Glucose 4.2.1 compilation on systems with musl libc.
-   Fixed further muslinux compilation issues related to external propagation.

## 26.08.2025 (*1.8.dev20*)

-   Removed clause duplicates when accessing clauses of a clausified formula.
-   Added support for Zstandard compression in formula I/O. (Requires Python
    3.14, so not yet tested.)

## 07.08.2025 (*1.8.dev19*)

-   Numerous bug fixes in non-clausal formula handling.

## 03.08.2025 (*1.8.dev18*)

-   Added Bica, a formula simplifier.
-   Added Primer, a prime enumerator.
-   Minor updates in RC2.

## 30.05.2025 (*1.8.dev17*)

-   Fixed a typo in variable spelling (thanks to
    [aditya95sriram](https://github.com/aditya95sriram)).

## 15.03.2025 (*1.8.dev16*)

-   Another (minor) issue fixed, related to constant clausification.

## 15.03.2025 (*1.8.dev15*)

-   Fixed an issue related to clausifying formulas with true/false constants.
-   Glucose 4.2.1 random mode is now supported.

## 07.01.2025 (*1.8.dev14*)

-   Fixed an issue in (fresh) empty formula copying (thanks to
    [gavinp](https://github.com/gavinp)).
-   Fixed a bug of formula non-uniqueness (when the arguments are reordered).
-   Fixed a few issues in the generic solver's initialiser.
-   Fixed most if not all the escape sequences in the docstrings.

## 12.05.2024 (*1.8.dev13*)

-   Fixed a few minor issues in MUSx (thanks to
    [brossignol](https://github.com/brossignol)).

## 18.04.2024 (*1.8.dev12*)

-   Made minor tweaks in updating CNF formulas, related to updating the
    default vpool (the methods affected are ``append`` and ``extend``).

## 17.04.2024 (*1.8.dev11*)

-   Fixed an issue in formula clausification. Now, depending on whether the
    formula is outermost or not, the clauses will be either raw or
    tseitin-encoded (thanks to [brossignol](https://github.com/brossignol)).
-   Changed the way ``PYSAT_FALSE`` and ``PYSAT_TRUE`` constants are treated.
    They are now global constants stored in a special context (thanks to
    [brossignol](https://github.com/brossignol)).

## 11.04.2024 (*1.8.dev10*)

-   Fixed a bug in ``simplified()`` method for XOr terms.

## 07.04.2024 (*1.8.dev9*)

-   Fixed implementation of ``propagate()`` for CaDiCaL 1.9.5.

## 05.04.2024 (*1.8.dev8*)

-   Added support for CaDiCaL 1.9.5 with linear engine in example scripts.

## 31.03.2024 (*1.8.dev7*)

-   Fixed a bug in formula key flattening.
-   Added support for *empty* conjunctions and disjunctions representing
    ``PYSAT_TRUE`` and ``PYSAT_FALSE`` respectively.

## 27.03.2024 (*1.8.dev6*)

-   A few minor issues in the toolkit setup.

## 20.03.2024 (*1.8.dev5*)

-   Fixed a few issues in formula simplification.

## 17.03.2024 (*1.8.dev4*)

-   Fixed a bug in the PB encoder.
-   Added support for CaDiCaL 1.9.5.
-   Added module ``engines`` supporting external propagators.

## 29.02.2024 (*1.8.dev3*)

-   Minor corrections.

## 29.02.2024 (*1.8.dev2*)

-   Fixed a bug/typo in implication clausification.
-   Added checks for the number of arguments in And, Or, Equals, and XOR
    constraints.

## 25.02.2024 (*1.8.dev1*)

-   Changed versioning scheme.
-   Added functionality to manipulate arbitrary Boolean formulas.

## 20.02.2024 (*0.1.8.dev17*)

-   Fixed a minor bug once in a while manifesting itself in the solvers'
    destructors.

## 18.02.2024 (*0.1.8.dev16*)

-   Added an option in ``CNF`` constructor to copy clauses by reference
    instead of deep-copying them (if the ``CNF`` is constructed from clauses).

## 07.02.2024 (*0.1.8.dev15*)

-   Corrected polarities of core literals if extracted from CryptoMiniSat.

## 31.01.2024 (*0.1.8.dev14*)

-   Added a standard Python destructor for each solver so that the garbage
    collector manages to destroy the objects, if this is not done by the user
    explicitly.

## 09.01.2024 (*0.1.8.dev13*)

-   Fixed the issue of a missing variable in CaDiCaL's unsatisfiable core
    handling after a limited SAT call.

## 28.11.2023 (*0.1.8.dev12*)

-   Added (rudimentary) support of CryptoMiniSat5 by means of the
    ``pycryptosat`` package's interface.

## 24.11.2023 (*0.1.8.dev11*)

-   Added another external tool (UniGen3) to the module ``pysat.allies``.

## 13.10.2023 (*0.1.8.dev10*)

-   Added assumption-based propagation functionality to CaDiCaL 1.5.3 (thanks
    to Zi Li Tan).

## 12.07.2023 (*0.1.8.dev9*)

-   Updated proof logging in Glucose 4.2.1 (thanks to Marco Marino).

## 12.07.2023 (*0.1.8.dev8*)

-   Added Glucose 4.2.1 (thanks to Marco Marino).

## 09.06.2023 (*0.1.8.dev7*)

-   Minor fix in RC2 making the new version backward compatible with the old
    API.

## 04.06.2023 (*0.1.8.dev6*)

-   Added parameter setting for CaDiCaL 153.
-   Added an interface for preferred polarity setting in CaDiCaL 153.
-   Added CaDiCaL 153 as a possible oracle to Hitman.
-   Added phase switching in Hitman when pure SAT-based enumeration is used.
-   Added an option to use pure SAT-based hitting set enumeration in OptUx.

## 03.06.2023 (*0.1.8.dev5*)

-   Exposed cadical's limited solving capability.
-   Added pure SAT-based minimal hitting set enumeration through the use of
    phase preferences.

## 25.05.2023 (*0.1.8.dev4*)

-   Another attempt to fix the bug in RC2 related to stratification and weight
    splitting (thanks to Bart Bogaerts, Andy Oertel, Jeremias Berg, Jakob
    Nordström, and Dieter Vandesande).
-   Multiple slight amendments in the formula API (thanks to Rex Yuan).

## 21.04.2023 (*0.1.8.dev3*)

-   Added a new module called ``pysat.allies``, which is meant to contain
    external tools callable from PySAT. The first tool added is ApproxMCv4.

## 19.03.2023 (*0.1.8.dev2*)

-   Fixed a subtle bug in RC2Stratified (thanks to the feedback of Jeremias
    Berg, Jakob Nordström, Bart Bogaerts, Andy Oertel, and Dieter Vandesande).
    The bug led to erroneous hardening of some of the sum literals due to an
    incorrect estimation of the sum of the weights in lower strata.

## 05.03.2023 (*0.1.8.dev1*)

-   Added CaDiCaL 1.5.3 (thanks to Christos Karamanos).
-   Added the ``process`` module (thanks to Christos Karamanos).
-   Added a build for Python 3.11 on Win64.

## xx.02.2023 (*0.1.7.dev27*)

-   Fixed the list of auxiliary variables reported as a result of formula
    negation. Added a list of literals involved in the encoding of clauses.

## 23.01.2023 (*0.1.7.dev26*)

-   Added a few more warning messages for various solvers, related to missing
    keyword arguments.

## 17.01.2023 (*0.1.7.dev25*)

-   Fixed a bug related to missing keyword arguments for Minisat22, MinisatGH,
    and Minicard.
-   Updated documentation of methods `solve()`, `solve_limited()`,
    `propagate()`, and `enum_models()` saying that duplicate assumption
    literals are forbidden.

## 15.01.2023 (*0.1.7.dev24*)

-   Added warm start mode to MapleCM.

## 13.01.2023 (*0.1.7.dev23*)

-   Fixed a typo in `examples/models.py`.

## 13.01.2023 (*0.1.7.dev22*)

-   Fixed a time computation bug in `examples/models.py`.
-   Added warm start mode to 'm22', 'mgh', 'mc', 'mpl', 'g30', 'g41', 'gc30',
    'gc41'.

## 22.11.2022 (*0.1.7.dev21*)

-   Made a number of minor tweaks in formula parsing.

## 18.11.2022 (*0.1.7.dev20*)

-   Fixed the patch issue on macOS Ventura.

## 06.07.2022 (*0.1.7.dev19*)

-   An attempt to fix statistics report when running in WebAssembly (type cast
    to `Py_ssize_t`).

## 18.06.2022 (*0.1.7.dev18*)

-   Fixed a couple of minor bugs in `pysat.card` and `pysat.pb` related to
    variable ID update.

## 03.06.2022 (*0.1.7.dev17*)

-   Addition of AtMostK constraints on the fly is added to RC2, LBX and
    MCSls.
-   Added support for additional hard constraints in Hitman, both in the
    form of clauses and AtMostK constraints.
-   Added the eMUS mode to OptUx, i.e. it can enumerate subset-minimal
    MUSes.
-   Added support for additional formula to be used in OptUx for
    stopping MUS enumeration as soon as the additional formula is
    covered by the set of MUSes.

## 22.02.2022 (*0.1.7.dev16*)

-   Fixed a minor issue in RC2 related to making useless iterations in
    core minimization.
-   Added support for WCNF+ formulas in OptUx.

## 04.12.2021 (*0.1.7.dev15*)

-   Fixed a minor bug in stratified RC2 related to model enumeration for
    empty formulas.
-   Updated Hitman so that it opts for plain RC2 if all weights are the
    same.
-   Fixed cost MUS computation in OptUx.

## 24.11.2021 (*0.1.7.dev14*)

-   Another attempt to fix the bug in topw handling if unspecified.

## 24.11.2021 (*0.1.7.dev13*)

-   Fixed a minor issue in fm.py related to handling native AM1
    constraints.
-   Fixed a bug in WCNF parser, which caused incorrect top weight
    computation if not specified in the preamble of the file explicitly.

## 09.11.2021 (*0.1.7.dev12*)

-   Fixed a bug related to handling CNF formulas and improper updating
    IDPool for PB constraints in the case of no auxiliary variables.

## 12.10.2021 (*0.1.7.dev11*)

-   Fixed a bug related to meaningless bounds in cardinality constraints
    (both AtMost and AtLeast).

## 17.08.2021 (*0.1.7.dev10*)

-   Added cluster-based stratification to `RC2`.
-   Made the selection of stratification strategy in
    `RC2` optional.

## 02.08.2021 (*0.1.7.dev9*)

-   Added proper handling of border cases when creating cardinality
    constraints. Done for all encodings, and both AtMostK and AtLeastK
    constraints.
-   Added an `UnsupportedBound` exception to be raised whenever
    *pairwise*, *bitwise*, or *ladder* encodings are created with the
    bound in $(1, N
    - 1)$.

## 30.07.2021 (*0.1.7.dev8*)

-   Fixed a bug in `IDPool` introduced
    in `0.1.7.dev7`, related to `None` handling.

## 28.07.2021 (*0.1.7.dev7*)

-   Updated `IDPool` to return a new variable ID without an object.
-   Updated `RC2` to support IDPool instead of `self.topv`.

## 17.07.2021 (*0.1.7.dev6*)

-   Modified the implemention of the am1 heuristic in
    `RC2`.

## 26.06.2021 (*0.1.7.dev5*)

-   Got rid of relaxation variables in `RC2` - minor issue, which might still
    have affected the performance.

## 11.06.2021 (*0.1.7.dev4*)

-   Fixed compilation issues occurring for cadical on macOS \>= 11.3
    with the most recent version of clang. Thanks to András Salamon.

## 24.05.2021 (*0.1.7.dev3*)

-   Added a warning in `enum_models()` regarding
    unsatisfiability of the formula after model enumeration is finished.
-   Fixed a couple of bugs in `FM`.
-   Similar changes in other example implementations.

## 20.04.2021 (*0.1.7.dev2*)

-   Improved the sequential counters encoding based on Donald Knuth\'s
    irredundant variant, following the suggestion of Alex Healy.

## 31.03.2021 (*0.1.7.dev1*)

-   An attempt to fix compilation issues of Mergesat.

## 31.03.2021 (*0.1.7.dev0*)

-   Added basic interface to `Mergesat3`.
-   Ported `Minicard`\'s native
    cardinality support to Glucose, which resulted in solvers
    `Gluecard3` and
    `Gluecard4`.
-   Added translation of `Cadical`\'s
    binary DRUP format to text-based.

## 25.03.2021 (*0.1.6.dev16*)

-   A few minor corrections in `RC2`,
    `RC2Stratified`, and
    `Hitman` addressing the issues
    related to empty formulas.

## 23.03.2021 (*0.1.6.dev15*)

-   A minor correction in `OptUx`
    related to MUS cost value.

## 23.03.2021 (*0.1.6.dev14*)

-   A minor correction in the `setup.py` script.

## 23.03.2021 (*0.1.6.dev13*)

-   Added a way to bootstrap `LBX` and
    `MCSls` for computing MCSes that
    include a specified subset of clauses.
-   Updated `Hitman` to support
    *weighted* hitting set problems.
-   Added `OptUx`, which is an
    smallest/optimal MUS extractor and enumerator that aims to replicate
    the performance of Forqes.

## 13.02.2021 (*0.1.6.dev12*)

-   Fixed formula dumping in other formats (see
    `to_alien`).

## 24.11.2020 (*0.1.6.dev11*)

-   Added formula dumping in SMT-LIB2 (see `to_alien`).

## 19.11.2020 (*0.1.6.dev10*)

-   Fixed the number of propagations ins MapleChrono.

## 27.09.2020 (*0.1.6.dev9*)

-   Fixed a bug in copying of `CNFPlus`
    and `WCNFPlus` objects.
-   Added an attempt to write down OPB and LP formats (likely to be
    buggy!).

## 26.09.2020 (*0.1.6.dev8*)

-   Fixed a bug in `solvers.py` related to the
    `CNFPlus` iterator.

## 25.09.2020 (*0.1.6.dev7*)

-   Added an example for accum_stats().
-   Fixed a minor bug in musx example.
-   A few fixes in `pysat.formula`.
-   Fixed an issue in `pysat.card` related
    to non-list literals.

## 09.08.2020 (*0.1.6.dev6*)

-   Using int64_t for accum_stats().

## 03.08.2020 (*0.1.6.dev5*)

-   Fixed the bug of wrong top_id when no cardinality encoding is
    created.

## 26.07.2020 (*0.1.6.dev4*)

-   Accumulated stats for other solvers.
-   More enumeration-related fixes in RC2Stratified.

## 07.07.2020 (*0.1.6.dev3*)

-   Fixed RC2\'s enumeration of MSSes.
-   Minor changes to the patch for CaDiCaL

## 06.07.2020 (*0.1.6.dev2*)

-   Forgot to manifest the solver archives. :)

## 06.07.2020 (*0.1.6.dev1*)

-   Solver archive files are now shipped with PySAT.
-   A bit cleaner signal handling.
-   Got rid of the segmentation faults when CTRL+C\'ing limited SAT
    calls.
-   Accumulated stats for Glucose4.1 (by Chris Jefferson)

## 04.07.2020 (*0.1.5.dev17*)

-   Removed dependency for zlib.

## 23.06.2020 (*0.1.5.dev16*)

-   Fixed a minor bug in top id handling in
    `pysat.card` reported by Pedro
    Bonilla.

## 15.06.2020 (*0.1.5.dev15*)

-   A few more minor changes in RC2 to fulfill the requirements of MSE
    2020.

## 18.05.2020 (*0.1.5.dev14*)

-   A few minor changes in RC2 addressing a new v-line format and the
    top-k track.

## 05.05.2020 (*0.1.5.dev13*)

-   A few minor issues related to non-deterministic behavior of sets in
    Python3.

## 12.04.2020 (*0.1.5.dev12*)

-   Fixed a minor bug in garbage collector of RC2.
-   Fixed an empty-core bug in RC2 appearing in solution enumeration.

## 19.03.2020 (*0.1.5.dev10*)

-   Floating point arithmetic is now done through the
    `decimal` module to avoid precision
    issues.

## 19.03.2020 (*0.1.5.dev9*)

-   Minor issue fixed in `RC2Stratified`.

## 17.03.2020 (*0.1.5.dev8*)

-   Added support of floating point weights in `WCNF` and `WCNFPlus`.
-   Added support of negative weights.

## 14.03.2020 (*0.1.5.dev7*)

-   Another minor fix in `pysat.formula`
    related to importing py-aiger-cnf.

## 24.01.2020 (*0.1.5.dev6*)

-   Fixed a minor bug related to unknown keyword arguments passed to the
    constructor of `Solver`.

## 08.01.2020 (*0.1.5.dev5*)

-   Added support of copying `CNFPlus`
    and `WCNFPlus` formulas.

## 04.12.2019 (*0.1.5.dev2*)

-   Fixed yet another issue related to
    `pysat.formula.CNFPlus` and
    `pysat.solvers.Minicard`.
-   Replaced `time.clock()` with
    `time.process_time()` for Python 3.8
    and newer.

## 04.12.2019 (*0.1.5.dev1*)

-   Added Windows support (**many** thanks to [Rüdiger
    Jungbeck](https://github.com/rjungbeck)!).
-   Fixed a few more issues related to
    `pysat.formula.CNFPlus` and
    `pysat.formula.WCNFPlus`.

## 02.12.2019 (*0.1.4.dev25*)

-   Fixed the parser of `pysat.formula.WCNFPlus` formulas.
-   Fixed a bug in method `append_formula` for `pysat.solvers.Minicard`.

## 28.11.2019 (*0.1.4.dev24*)

-   Fixed signal handling in the multithreaded use of PySAT. Multiple
    oracles can be used at a time now.

## 14.11.2019 (*0.1.4.dev23*)

-   Fixed a minor bug in `pysat.examples.lsu`.

## 07.11.2019 (*0.1.4.dev22*)

-   A minor fix in `pysat.formula` related
    to importing py-aiger-cnf.

## 30.10.2019 (*0.1.4.dev21*)

-   Marked py-aiger-cnf as an optional dependency.

## 29.10.2019 (*0.1.4.dev20*)

-   The use of py-aiger is replaced by py-aiger-cnf to incapsulate the
    internals of py-aiger.

## 09.10.2019 (*0.1.4.dev19*)

-   Added solution optimality check in
    `pysat.examples.lsu`.
-   Added a way to update the used variable identifiers using
    `pysat.formula.IDPool` when working
    with `pysat.card.CardEnc.*` and
    `pysat.pb.PBEnc.*`.
-   Minor cosmetic changes.
-   New logo.

## 30.09.2019 (*0.1.4.dev18*)

-   Fixed a bug related to using py-aiger on Python 2.

## 28.08.2019 (*0.1.4.dev17*)

-   Updated the minimum version of py-aiger required for installation.

## 28.08.2019 (*0.1.4.dev16*)

-   CNF formulas can now be bootstrapped by Tseitin-encoding AIGER
    circuits. This is done with the use of the [py-aiger
    package](https://github.com/mvcisback/py-aiger).

## 21.08.2019 (*0.1.4.dev15*)

-   Added rudimentary support of CaDiCaL.

## 04.06.2019 (*0.1.4.dev13*)

-   Fixed the wrong number of variables after calling methods of
    `CardEnc`.
-   Added clause iterator to `CNF`.
-   Calling `CardEnc.*([])` returns an
    empty CNF formula.

## 25.06.2019 (*0.1.4.dev12*)

-   Corrected a typo in the method name
    `WCNF.unweighted`.

## 17.06.2019 (*0.1.4.dev11*)

-   Added top weight update when adding soft clauses into a WCNF.

## 26.05.2019 (*0.1.4.dev10*)

-   Added support for non-deterministic interruption, e.g. based on a
    timer.

## 17.05.2019 (*0.1.4.dev9*)

-   Minor fixes related to the WCNF+ support in
    `pysat.examples.lsu`,
    `pysat.examples.lbx`, and
    `pysat.examples.mcsls`.

## 27.04.2019 (*0.1.4.dev8*)

-   Made an attempt to fix the C++ library issue on MacOS.

## 19.04.2019 (*0.1.4.dev7*)

-   Fixed a couple of minor issues in
    `pysat.examples.hitman` and
    `pysat.example.mcsls`.

## 21.03.2019 (*0.1.4.dev6*)

-   Fixed a potential bug related to \"deallocating None\".

## 19.03.2019 (*0.1.4.dev5*)

-   Fixed an issue in `propagate` for
    the MapleChrono solver.

## 18.03.2019 (*0.1.4.dev3*)

-   Some fixes in the assumption handling of the Maple\* solvers.

## 17.03.2019 (*0.1.4.dev2*)

-   Added three solvers of the Maple family: Maplesat (i.e.
    MapleCOMSPS_LRB), MapleCM, and MapleChrono (i.e.
    MapleLCMDistChronoBT).
-   A few minor fixes.

## 13.03.2019 (*0.1.4.dev1*)

-   Added `pysat.pb` providing access to a
    few PB constraints with the use of PyPBLib.
-   A number of small fixes.

## 28.12.2018 (*0.1.3.dev25*)

-   Fixed model enumerator in `pysat.examples.rc2`.
-   Documented `pysat.examples.rc2`.

## 01.11.2018 (*0.1.3.dev24*)

-   Documented a few example modules including
    `pysat.examples.lbx`,
    `pysat.examples.mcsls`, and
    `pysat.examples.lsu`.

## 22.09.2018 (*0.1.3.dev23*)

-   Added the image of the FLOC medals to the webpage.
-   Added the news section to the webpage.
-   Removed unused source code.

## 20.09.2018 (*0.1.3.dev22*)

-   Added better support for iterables in `pysat.card` and `pysat.solvers`.
-   Added documentation for `examples/fm.py`, `examples/genhard.py`,
    `examples/hitman.py` and `examples/musx.py`.

## 06.09.2018 (*0.1.3.dev21*)

-   Fixed a typo in the project description on
    [PyPI](https://pypi.org/project/python-sat/).

## 30.08.2018 (*0.1.3.dev20*)

-   Added an implementation of the LSU algorithm for MaxSAT.
-   Fixed a bug in `pysat._fileio`
    appearing when LZMA is not present.

## 25.08.2018 (*0.1.3.dev19*)

-   Solvers can receive `iterables` as clauses (besides `lists`).
-   Fixed a minor issue in `examples/hitman.py`.

## 25.08.2018 (*0.1.3.dev18*)

-   Cosmetic changes in the documentation.

## 25.08.2018 (*0.1.3.dev17*)

-   More incremental functionality in RC2, LBX, and MCSls.
-   Added a minimal hitting set enumerator as another example.

## 20.08.2018 (*0.1.3.dev16*)

-   Fixed a problem appearing when no model exists.

## 19.08.2018 (*0.1.3.dev15*)

-   Added support for reading and writing with \*zipped files.
-   Added the corresponding capabilities to the examples.

## 17.08.2018 (*0.1.3.dev14*)

-   Fixed a couple of minor issues related to Python 3 (in RC2 and
    iterative totalizer).

## 27.07.2018 (*0.1.3.dev13*)

-   Added support for setting variable *phases* (*user-preferred
    polarities*).

## 16.07.2018 (*0.1.3.dev12*)

-   Added incremetal model enumeration to RC2.
-   Fixed a couple of minor issues in LBX and MCSls.
-   Added mutilated chessboard princimple formulas for
    `examples/genhard.py`.

## 12.07.2018 (RC2)

MaxSAT solver RC2 won both *unweighted* and *weighted* categories of the
main track of [MaxSAT Evaluation
2018](https://maxsat-evaluations.github.io/2018/rankings.html) and got
two medals at [FLOC 2018 Olympic
Games](https://www.floc2018.org/floc-olympic-games/)!

![image: width=270px](../medals.svg)

## 20.06.2018 (*0.1.3.dev11*)

-   Added the webpage for the toolkit.
-   The first draft of the documentation.

## 07.06.2018 (*0.1.3.dev10*)

-   Fixed a minor bug in iterative totalizer.
-   Added modes A and B to RC2 for MaxSAT evaluation 2018.

## 28.05.2018 (*0.1.3.dev9*)

-   Added a way to manually set off a previously set budget on the
    number of clauses or propagations.
-   Added an optional core minimization in RC2.

## 25.05.2018 (*0.1.3.dev8*)

-   Fixed *long_description* of the project. Corrected the GitHub
    reference.
-   Implemented hidden AtMost1 constraint detection in RC2.
-   Improved support for Python 3 in RC2.
-   A few more minor issues in RC2 got fixed.

## 23.05.2018 (*0.1.3.dev7*)

-   Added optional *phase saving* in literal propagation.
-   Fixed a bug in literal propagation.

## 22.05.2018 (*0.1.3.dev6*)

-   More fixes in literal propagation and its interface.

## 21.05.2018 (*0.1.3.dev5*)

-   A minor modification of literal propagation.

## 21.05.2018 (*0.1.3.dev4*)

-   Added *literal propagation* in MiniSat-like solvers, i.e.
    `Minisat22`, `MinisatGH`, `Minicard`, `Glucose3`, and `Glucose41`.

## 15.05.2018 (*0.1.3.dev3*)

-   Another attempt to fix installation. Mirrored GitHub-hosted solvers.

## 02.05.2018 (*0.1.3.dev2*)

-   Modified signal handling in `pysolvers` and `pycard`.
-   Fixed a couple of minor issues in iterative totalizer.
-   Reimplemented `examples/genhard.py`. Each family of formulas is not
    a class.

## 10.04.2018 (*0.1.3.dev1*)

-   Fixed a bug in *limited* SAT solving, i.e. in solving within a given
    *budget* on the number of conflicts or the number of propagations.

## 09.04.2018 (*0.1.3.dev0*)

-   Improved `README.rst`.
-   Minor modifications in `examples/genhard.py`.
-   Added example scripts installation as executables.

## 08.04.2018 (*0.1.2.dev9*)

-   Fixed a couple of minor bugs in `pysat.card` and `pysat.formula`.

## 06.04.2018 (*0.1.2.dev8*)

-   Added a couple of optimizations to `examples/rc2.py` including
    *unsatisfiable core trimming* and *core exhaustion*.
-   Added `SolverNames` to simplify a
    solver selection.
-   An attempt to make the installation process less fragile.

## 03.04.2018 (*0.1.2.dev7*)

-   Fixed incremental mode of Glucose 4.1.
-   Added support for Minicard\'s native cardinality constraints in
    `examples/fm.py`.
-   Added RC2 as an example of a MaxSAT solver.
-   Fixed a minor issue in iterative totalizer.

## 29.03.2018 (*0.1.2.dev6*)

-   Fixed a bug in iterative totalizer, which led to clause duplication.

## 28.03.2018 (*0.1.2.dev5*)

-   Added iterative totalizer to `pysat.card`.
-   Added solver download caching (i.e. a solver is not downloaded more
    than once).

## 25.03.2018 (*0.1.2.dev4*)

-   Added support for Glucose 4.1.

## 06.03.2018 (*0.1.2.dev3*)

-   Added `examples/genhard.py` illustrating the work with the
    `pysat.formula` module.
-   Added `pysat.formula.IDPool`, a
    simple manager of *variable identifiers*.

## 04.03.2018 (*0.1.2.dev2*)

-   Fixed a bug related to SAT oracle\'s timer.

## 02.03.2018 (*0.1.2.dev1*)

-   Fixed a number of issues in `examples/fm.py`, `examples/lbx.py`, and
    `examples/musx.py` for a better support of Python 3.

## 01.03.2018 (*0.1.1.dev9*)

-   Minor fixes in `README.rst`.

## 22.02.2018 (*0.1.1.dev8*)

-   Minor changes in `pysat.card`.
-   A few typos in `pysat.examples.fm`.
-   Fixed *author_email* in `setup.py`.

## 11.02.2018 (*0.1.1.dev7*)

-   Initial commit accompanying the [corresponding SAT
    submission](../citation).
