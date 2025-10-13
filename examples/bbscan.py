#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## bbscan.py
##
##  Created on: Sep 21, 2025
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        BBScan

    ==================
    Module description
    ==================

    A simple implementation of a few backbone extraction algorithms described
    in [1]_. Given a Boolean formula :math:`\\varphi`, a backbone literal is a
    literal that holds true in every satisfying assignment of
    :math:`\\varphi`. The backbone of formula :math:`\\varphi` is the set of
    all backbone literals. This implementation includes the following
    algorithms from [1]_:

    * implicant enumeration algorithm,
    * iterative algorithm (with one test per variable),
    * complement of backbone estimate algorithm,
    * chunking algorithm,
    * core-based algorithm,
    * core-based algorithm with chunking.

    .. [1] Mikolás Janota, Inês Lynce, Joao Marques-Silva. *Algorithms for
        computing backbones of propositional formulae*. AI Commun. 28(2).
        2015. pp. 161-177

    The implementation can be used as an executable (the list of
    available command-line options can be shown using ``bbscan.py -h``)
    in the following way:

    ::

        $ xzcat formula.cnf.xz
        p cnf 3 4
        1 2 0
        1 -2 0
        2 -3 0
        -2 -3 0

        $ bbscan.py -v formula.cnf.xz
        c formula: 3 vars, 4 clauses
        c using iterative algorithm
        v +1 -3 0
        c backbone size: 2 (66.67% of all variables)
        c oracle time: 0.0000
        c oracle calls: 4

    Alternatively, the algorithms can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.bbscan import BBScan
        >>> from pysat.formula import CNF
        >>>
        >>> # reading a formula from file
        >>> cnf = CNF(from_file='formula.wcnf.xz')
        >>>
        >>> # creating BBScan and running it
        >>> with BBScan(cnf, solver='g3', rotate=True) as bbscan:
        ...     bbone = bbscan.compute(algorithm='core')
        ...
        ...     # outputting the results
        ...     if bbone:
        ...         print(bbone)
        [1, -3]

    Each of the available algorithms can be augmented with a simple heuristic
    aiming at reducing satisfying assignments and, thus, filtering out
    unnecessary literals: namely, filtering rotatable literals. The heuristic
    is described in the aforementioned paper.

    Note that most of the methods of the class :class:`BBScan` are made
    private. Therefore, the tool provides a minimalistic interface via which a
    user can specify all the necessary parameters.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import getopt
import itertools
import os
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver, SolverNames
import sys
import re
import time


#
#==============================================================================
class BBScan:
    """
        A solver for computing all backbone literals of a given Boolean
        formula. It implements 6 algorithms for backbone computation described
        in [1]_ augmented with a heuristic that can be speed up the process.

        Note that the input formula can be a :class:`.CNF` object but also any
        object of class :class:`.Formula`, thus the tool can used for
        computing backbone literals of non-clausal formulas.

        A user can select one of the SAT solvers available at hand
        (``'glucose3'`` is used by default). The optional heuristic can be
        also specified as a Boolean input arguments ``rotate`` (turned off by
        default).

        The list of initialiser's arguments is as follows:

        :param formula: input formula whose backbone is sought
        :param solver: SAT oracle name
        :param rotate: apply rotatable literal filtering
        :param verbose: verbosity level

        :type formula: :class:`.Formula` or :class:`.CNF`
        :type solver: str
        :type rotate: bool
        :type verbose: int
    """

    def __init__(self, formula, solver='g3', rotate=False, verbose=0):
        """
            Constructor.
        """

        self.formula = formula
        self.focuscl = list(range(len(formula.clauses))) if rotate else []
        self.verbose = verbose
        self.oracle  = None

        # implicant reduction heuristics
        self.rotate = rotate

        # basic stats
        self.calls, self.filtered = 0, 0

        # this is going to be our workhorse
        self.oracle = Solver(name=solver, bootstrap_with=formula, use_timer=True)

    def __del__(self):
        """
            Destructor.
        """

        self.delete()

    def __enter__(self):
        """
            'with' constructor.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
            'with' destructor.
        """

        self.delete()

    def delete(self):
        """
            Explicit destructor of the internal SAT oracle.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

    def compute(self, algorithm='iter', chunk_size=100, focus_on=None):
        """
            Main solving method. A user is supposed to specify which backbone
            computation algorithm they want to use:

            * ``'enum'`` (implicant enumeration algorithm),
            * ``'iter'`` (iterative algorithm, with one test per variable),
            * ``'compl'`` (complement of backbone estimate algorithm),
            * ``'chunk'`` (chunking algorithm),
            * ``'core'`` (core-based algorithm),
            * ``'corechunk'`` (core-based algorithm with chunking).

            By default, :class:`.BBScan` opts for ``'iter'``.

            If the chunking algorithm is selected (either ``'chunk'`` or
            ``'corechunk'``), the user may specify the size of the chunk,
            which is set to 100 by default. Note that the chunk_size can be a
            floating-point number in the interval (0, 1], which will set the
            actual chunk_size relative to the total number of literals of
            interest.

            Finally, one may opt for computing backbone literals out of a
            particular subset of literals, which may run faster than computing
            the entire formula's backbone. To focus on a particular set of
            literals, the user should use the parameter ``focus_on``, which is
            set to ``None`` by default.

            .. note::

                The method raises ``ValueError`` if the input formula is
                unsatisfiable.

            :param algorithm: backbone computation algorithm
            :param chunk_size: number of literals in the chunk (for chunking algorithms)
            :param focus_on: a list of literals to focus on

            :type algorithm: str
            :type chunk_size: int or float
            :type focus_on: iterable(int)
        """

        self.calls += 1
        trivial = []

        if self.oracle.solve():
            self.model = set(self.oracle.get_model())
            if focus_on is not None:
                self.model &= set(focus_on)

                # if filtering rotatable literals is requested then
                # we should be clever about the clauses to traverse
                if self.rotate:
                    self.focuscl = []
                    for i, cl in enumerate(self.formula):
                        for l in cl:
                            if l in self.model:
                                if len(cl) == 1:
                                    trivial.append(l)
                                    self.model.remove(l)
                                else:
                                    self.focuscl.append(i)
                                break
        else:
            raise ValueError('Unsatisfiable formula')

        if isinstance(chunk_size, float):
            assert 0 < chunk_size <= 1, f'Wrong chunk proportion {chunk_size}'
            chunk_size = int(min(self.formula.nv, len(self.model)) * chunk_size)

        if algorithm == 'enum':
            result = self._compute_enum()
        elif algorithm == 'iter':
            result = self._compute_iter()
        elif algorithm == 'compl':
            result = self._compute_compl()
        elif algorithm == 'chunk':
            result = self._compute_chunking(chunk_size)
        elif algorithm == 'core':
            result = self._compute_core_based()
        elif algorithm == 'corechunk':
            result = self._compute_core_chunking(chunk_size)
        else:
            assert 0, f'Unknown algorithm: {algorithm}'

        return sorted(trivial + result, key=lambda l: abs(l))

    def _filter_rotatable(self, model):
        """
            Filter out rotatable literals.
        """

        def get_unit(cl):
            # this is supposed to be a faster alternative to the
            # complete clause traversal with a conditional inside
            unit = None
            for l in cl:
                if l in model:
                    if unit:
                        return
                    else:
                        unit = l
            return unit

        # result of this procedure
        units = set([])

        # determining unit literals
        for i in self.focuscl:
            unit = get_unit(self.formula.clauses[i])
            if unit:
                units.add(unit)

        self.filtered += len(model) - len(units)
        return units

    def _compute_enum(self, focus_on=None):
        """
            Enumeration-based backbone computation.
        """

        if self.verbose:
            print('c using enumeration-based algorithm')

        # initial backbone estimate contains all literals
        bbone = self.model if focus_on is None else focus_on

        while bbone:
            # counting the number of calls
            self.calls += 1

            # stop if there are no more models
            if not self.oracle.solve():
                break

            # updating backbone estimate - intersection
            bbone &= set(self.oracle.get_model())

            if self.rotate:
                bbone = self._filter_rotatable(bbone)

            # blocking the previously found implicant
            self.oracle.add_clause([-l for l in bbone])

        return list(bbone)

    def _compute_iter(self, focus_on=None):
        """
            Iterative algorithm with one test per variable.
        """

        if self.verbose:
            print('c using iterative algorithm')

        # initial estimate
        # using sets for model and assumps to save filtering time
        bbone, model = [], self.model if focus_on is None else focus_on

        while model:
            # counting the number of oracle calls
            self.calls += 1

            # checking this literal
            lit = model.pop()

            if self.oracle.solve(assumptions=[-lit]) == False:
                # it is a backbone literal
                bbone.append(lit)
            else:
                # it isn't and we've got a counterexample
                # => using it to filter out more literals
                model &= set(self.oracle.get_model())

                if self.rotate:
                    model = self._filter_rotatable(model)

        return bbone

    def _compute_compl(self, focus_on=None):
        """
            Iterative algorithm with complement of backbone estimate.
        """

        if self.verbose:
            print('c using complement of backbone estimate algorithm')

        # initial estimate
        bbone = self.model if focus_on is None else focus_on

        # iterating until we find the backbone or determine there is none
        while bbone:
            self.calls += 1

            # first, adding a new D-clause
            self.oracle.add_clause([-l for l in bbone])

            # testing for unsatisfiability
            if self.oracle.solve() == False:
                break
            else:
                bbone &= set(self.oracle.get_model())

                if self.rotate:
                    bbone = self._filter_rotatable(bbone)

        return list(bbone)

    def _compute_chunking(self, chunk_size=100, focus_on=None):
        """
            Chunking algorithm.
        """

        if self.verbose:
            print('c using chunking algorithm, with chunk size:', chunk_size)

        # initial estimate
        bbone, model = [], list(self.model if focus_on is None else focus_on)

        # we are going to use clause selectors
        vpool = IDPool(start_from=self.formula.nv + 1)

        # iterating until we find the backbone or determine there is none
        while model:
            self.calls += 1

            # preparing the call
            size = min(chunk_size, len(model))
            selv = vpool.id()

            # first, adding a new D-clause for the selected chunk
            self.oracle.add_clause([-model[-i] for i in range(1, size + 1)] + [-selv])

            # testing for unsatisfiability
            if self.oracle.solve(assumptions=[selv]) == False:
                # all literals in the chunk are in the backbone
                for _ in range(size):
                    lit = model.pop()
                    bbone.append(lit)
                    self.oracle.add_clause([lit])
            else:
                coex = set(self.oracle.get_model())
                model = [l for l in model if l in coex]

                if self.rotate:
                    model = list(self._filter_rotatable(set(model)))

        return bbone

    def _compute_core_based(self, focus_on=None):
        """
            Core-based algorithm.
        """

        if self.verbose:
            print('c using core-based algorithm')

        # initial estimate
        # using sets for model and assumps to save filtering time
        bbone, model = [], self.model if focus_on is None else focus_on

        # iterating until we find the backbone or determine there is none
        while model:
            # flipping all the literals
            assumps = {-l for l in model}

            # getting unsatisfiable cores with them
            while True:
                self.calls += 1

                if self.oracle.solve(assumptions=assumps):
                    model &= set(self.oracle.get_model())

                    if self.rotate:
                        model  = self._filter_rotatable(model)

                    break

                else:
                    core = self.oracle.get_core()
                    if len(core) == 1:
                        bbone.append(-core[0])
                        self.oracle.add_clause([-core[0]])

                        # remove from the working model
                        model.remove(-core[0])

                    # filtering out unnecessary flipped literals
                    assumps -= set(core)

                    if not assumps:
                        self.model = model
                        return bbone + self._compute_iter()

        return bbone

    def _compute_core_chunking(self, chunk_size=100, focus_on=None):
        """
            Core-based algorithm with chunking.
        """

        if self.verbose:
            print('c using core-based chunking, with chunk size:', chunk_size)

        # initial estimate
        bbone, model = [], list(self.model if focus_on is None else focus_on)

        # we are going to use clause selectors
        vpool = IDPool(start_from=self.formula.nv + 1)

        # iterating until we find the backbone or determine there is none
        while model:
            # preparing the chunking
            size = min(chunk_size, len(model))

            # flipping all the literals
            assumps, skipped = {-model.pop() for i in range(size)}, set()

            # getting unsatisfiable cores with them
            while True:
                self.calls += 1

                if self.oracle.solve(assumptions=assumps):
                    coex = set(self.oracle.get_model())
                    model = [l for l in model if l in coex]

                    if self.rotate:
                        model = list(self._filter_rotatable(set(model)))

                    if skipped:
                        bbone += self._compute_iter(focus_on=skipped)

                    break

                else:
                    core = self.oracle.get_core()

                    if len(core) == 1:
                        # a unit-size core must contain a backbone literal
                        bbone.append(-core[0])
                        self.oracle.add_clause([-core[0]])
                    else:
                        # all removed literals are going to be tested later
                        skipped |= {-l for l in core}

                    # filtering out unnecessary flipped literals
                    assumps -= set(core)

                    if not assumps:
                        # resorting to the iterative traversal algorithm
                        # in order to test all the removed literals
                        bbone += self._compute_iter(focus_on=skipped)
                        break

        return bbone

    def oracle_time(self):
        """
            This method computes and returns the total SAT solving time
            involved, including the time spent by the hitting set enumerator
            and the two SAT oracles.

            :rtype: float
        """

        return self.oracle.time_accum()


#
#==============================================================================
def parse_options():
    """
        Parses command-line options.
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'a:c:hrs:v',
                                   ['algo=',
                                    'chunk=',
                                    'help',
                                    'rotate',
                                    'solver=',
                                    'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        usage()
        sys.exit(1)

    algo = 'iter'
    chunk = 100
    rotate = False
    solver = 'g3'
    verbose = 0

    for opt, arg in opts:
        if opt in ('-a', '--algo'):
            algo = str(arg)
            assert algo in ('enum', 'iter', 'compl', 'chunk', 'core', 'corechunk'), 'Unknown algorithm'
        elif opt in ('-c', '--chunk'):
            chunk = float(arg)
            if chunk.is_integer():
                chunk = int(chunk)
            else:
                assert 0 < chunk <= 1, f'Wrong chunk proportion {chunk_size}'
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-r', '--rotate'):
            rotate = True
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return algo, chunk, rotate, solver, verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] file')
    print('Options:')
    print('        -a, --algo=<string>        Algorithm to use')
    print('                                   Available values: enum, iter, compl, chunk, core, corechunk (default: iter)')
    print('        -c, --chunk=<int,float>    Chunk size for chunking algorithms')
    print('                                   Available values: [1 .. INT_MAX] or (0 .. 1] (default: 100)')
    print('        -h, --help                 Show this message')
    print('        -r, --rotate               Heuristically filter out rotatable literals')
    print('        -s, --solver=<string>      SAT solver to use')
    print('                                   Available values: cd15, cd19, g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default: g3)')
    print('        -v, --verbose              Be verbose (can be used multiple times)')


#
#==============================================================================
if __name__ == '__main__':
    algo, chunk, rotate, solver, verbose, files = parse_options()

    if files:
        # read CNF from file
        assert re.search(r'cnf(\.(gz|bz2|lzma|xz|zst))?$', files[0]), \
                'Unknown input file extension'
        formula = CNF(from_file=files[0])

        if verbose:
            print('c formula: {0} vars, {1} clauses'.format(formula.nv,
                                                            len(formula.clauses)))

        # computing the backbone
        with BBScan(formula, solver=solver, rotate=rotate, verbose=verbose) as bbscan:
            try:
                bbone = bbscan.compute(algorithm=algo, chunk_size=chunk)

            except ValueError as e:
                print('s UNSATISFIABLE')
                print('c', str(e))
                sys.exit(1)

            # outputting the results
            if bbone:
                print('v {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in bbone])))
                print('c backbone size: {0} ({1:.2f}% of all variables)'.format(len(bbone), 100. * len(bbone) / formula.nv))
            else:
                print('v 0')

            if verbose > 1:
                print('c filtered: {0} ({1:.2f})'.format(bbscan.filtered, 100. * bbscan.filtered / formula.nv))

            print('c oracle time: {0:.4f}'.format(bbscan.oracle_time()))
            print('c oracle calls: {0}'.format(bbscan.calls))
