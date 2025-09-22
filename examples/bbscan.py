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
        >>> with BBScan(cnf, solver='g3', lift=False, rotate=True) as bbscan:
        ...     bbone = bbscan.compute(algorithm='core')
        ...
        ...     # outputting the results
        ...     if bbone:
        ...         print(bbone)
        [1, -3]

    Each of the available algorithms can be augmented with two simple
    heuristics aiming at reducing satisfying assignments and, thus, filtering
    out unnecessary literals: literal lifting and filtering rotatable
    literals. Both are described in the aforementioned paper.

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
        in [1]_ augmented with two simple heuristics that can be speed up the
        process.

        Note that the input formula can be a :class:`.CNF` object but also any
        object of class :class:`.Formula`, thus the tool can used for
        computing backbone literals of non-clausal formulas.

        A user can select one of the SAT solvers available at hand
        (``'glucose3'`` is used by default). The optional two heuristics can
        be also specified as Boolean input arguments ``lift``, and ``rotate``
        (turned off by default).

        The list of initialiser's arguments is as follows:

        :param formula: input formula whose backbone is sought
        :param solver: SAT oracle name
        :param lift: apply literal lifting heuristic
        :param rotate: apply rotatable literal filtering
        :param verbose: verbosity level

        :type formula: :class:`.Formula` or :class:`.CNF`
        :type solver: str
        :type lift: bool
        :type rotate: bool
        :type verbose: int
    """

    def __init__(self, formula, solver='g3', lift=False, rotate=False, verbose=0):
        """
            Constructor.
        """

        self.formula = formula
        self.verbose = verbose
        self.oracle  = None

        # implicant reduction heuristics
        self.lift, self.rotate = lift, rotate

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
            which is set to 100 by default.

            Finally, one may opt for computing backbone literals out of a
            particular subset of literals / variables, which may run faster
            than computing the entire formula's backbone. To focus on a
            particular set of variables / literals, the user should use the
            parameter ``focus_on``, which is set to ``None`` by default.

            .. note::

                The method raises ``ValueError`` if the input formula is
                unsatisfiable.

            :param algorithm: backbone computation algorithm
            :param chunk_size: number of literals in the chunk (for chunking algorithms)
            :param focus_on: a list of literals to focus on

            :type algorithm: str
            :type chunk_size: int
            :type focus_on: iterable(int)
        """

        self.calls += 1

        if self.oracle.solve():
            self.model = self.oracle.get_model()
            if focus_on is not None:
                model = set(self.model)
                self.model = [l for l in focus_on if l in model]
        else:
            raise ValueError('Unsatisfiable formula')

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

        return sorted(result, key=lambda l: abs(l))

    def _get_implicant(self, model):
        """
            Simple literal lifting used to reduce a given model.
        """

        res, model = set(), set(model)

        # traversing the clauses and collecting all literals
        # that satisfy at least one clause of the formula
        for cl in self.formula:
            res |= set([l for l in cl if l in model])

        return list(res)

    def _filter_rotatable(self, model):
        """
            Filter out rotatable literals.
        """

        units, model = set([]), set(model)

        # determining unit literals
        for cl in self.formula:
            satisfied = [l for l in cl if l in model]
            if len(satisfied) == 1:
                units.add(satisfied[0])

        self.filtered += len(model) - len(units)
        return list(units)

    def _process_model(self, model):
        """
            Heuristically reduce a model.
        """

        if self.lift:
            model = self._get_implicant(model)

        if self.rotate:
            model = self._filter_rotatable(model)

        return model

    def _compute_enum(self, focus_on=None):
        """
            Enumeration-based backbone computation.
        """

        if self.verbose:
            print('c using enumeration-based algorithm')

        # initial backbone estimate contains all literals
        bbone = set(self.model) if focus_on is None else set(focus_on)

        while bbone:
            # counting the number of calls
            self.calls += 1

            # stop if there are no more models
            if not self.oracle.solve():
                break

            self.model = self.oracle.get_model()
            # if self.lift:
            #     self.model = self._get_implicant(self.model)

            self.model = self._process_model(self.model)

            # updating backbone estimate - intersection
            bbone &= set(self.model)

            # blocking the previously found implicant
            self.oracle.add_clause([-l for l in self.model])

        return list(bbone)

    def _compute_iter(self, focus_on=None):
        """
            Iterative algorithm with one test per variable.
        """

        if self.verbose:
            print('c using iterative algorithm')

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
                coex = set(self.oracle.get_model())
                model = [l for l in model if l in coex]
                model = self._process_model(model)

        return bbone

    def _compute_compl(self, focus_on=None):
        """
            Iterative algorithm with complement of backbone estimate.
        """

        if self.verbose:
            print('c using complement of backbone estimate algorithm')

        # initial estimate
        bbone = set(self.model) if focus_on is None else set(focus_on)

        # iterating until we find the backbone or determine there is none
        while bbone:
            self.calls += 1

            # first, adding a new D-clause
            self.oracle.add_clause([-l for l in bbone])

            # testing for unsatisfiability
            if self.oracle.solve() == False:
                break
            else:
                model = self._process_model(self.oracle.get_model())
                model = self._process_model(model)
                bbone &= set(model)

        return list(bbone)

    def _compute_chunking(self, chunk_size=100, focus_on=None):
        """
            Algorithm 5: Chunking algorithm.
        """

        if self.verbose:
            print('c using chunking algorithm, with chunk size:', chunk_size)

        # initial estimate
        bbone, model = [], self.model if focus_on is None else focus_on

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
                model = self._process_model(model)

        return bbone

    def _compute_core_based(self, focus_on=None):
        """
            Core-based algorithm.
        """

        if self.verbose:
            print('c using core-based algorithm')

        # initial estimate
        bbone, model = [], self.model if focus_on is None else focus_on

        # iterating until we find the backbone or determine there is none
        while model:
            # flipping all the literals
            assumps = [-l for l in model]

            # getting unsatisfiable cores with them
            while True:
                self.calls += 1

                if self.oracle.solve(assumptions=assumps):
                    coex = set(self.oracle.get_model())
                    model = [l for l in model if l in coex]
                    model = self._process_model(model)
                    break

                else:
                    core = self.oracle.get_core()
                    if len(core) == 1:
                        bbone.append(-core[0])
                        self.oracle.add_clause([-core[0]])

                        # remove from the working model
                        indx = model.index(-core[0])  # may be slow
                        if indx < len(model) - 1:
                            model[indx] = model.pop()
                        else:
                            model.pop()

                    # filtering out unnecessary flipped literals
                    core = set(core)
                    assumps = [l for l in assumps if l not in core]

                    if not assumps:
                        # resorting to the iterative traversal algorithm
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
        bbone, model = [], self.model if focus_on is None else focus_on

        # we are going to use clause selectors
        vpool = IDPool(start_from=self.formula.nv + 1)

        # iterating until we find the backbone or determine there is none
        while model:
            # preparing the chunking
            size = min(chunk_size, len(model))

            # flipping all the literals
            assumps, skipped = [-model.pop() for i in range(size)], []

            # getting unsatisfiable cores with them
            while True:
                self.calls += 1

                if self.oracle.solve(assumptions=assumps):
                    coex = set(self.oracle.get_model())
                    model = [l for l in model if l in coex]
                    model = self._process_model(model)

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
                        skipped += [-l for l in core]

                    # filtering out unnecessary flipped literals
                    core = set(core)
                    assumps = [l for l in assumps if l not in core]

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
                                   'a:c:hlrs:v',
                                   ['algo=',
                                    'chunk=',
                                    'help',
                                    'lift',
                                    'rotate',
                                    'solver=',
                                    'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        usage()
        sys.exit(1)

    algo = 'iter'
    chunk = 100
    lift = False
    rotate = False
    solver = 'g3'
    verbose = 0

    for opt, arg in opts:
        if opt in ('-a', '--algo'):
            algo = str(arg)
            assert algo in ('enum', 'iter', 'compl', 'chunk', 'core', 'corechunk'), 'Unknown algorithm'
        elif opt in ('-c', '--chunk'):
            chunk = int(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-l', '--lift'):
            lift = True
        elif opt in ('-r', '--rotate'):
            rotate = True
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return algo, chunk, lift, rotate, solver, verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] file')
    print('Options:')
    print('        -a, --algo=<string>      Algorithm to use')
    print('                                 Available values: enum, iter, compl, chunk, core, corechunk (default: iter)')
    print('        -c, --chunk=<int>        Chunk size for chunking algorithms')
    print('                                 Available values: [1 .. INT_MAX] (default: 100)')
    print('        -h, --help               Show this message')
    print('        -l, --lift               Apply literal lifting for heuristic model reduction')
    print('        -r, --rotate             Heuristically filter out rotatable literals')
    print('        -s, --solver=<string>    SAT solver to use')
    print('                                 Available values: cd15, cd19, g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default: g3)')
    print('        -v, --verbose            Be verbose (can be used multiple times)')


#
#==============================================================================
if __name__ == '__main__':
    algo, chunk, lift, rotate, solver, verbose, files = parse_options()

    if files:
        # read CNF from file
        assert re.search(r'cnf(\.(gz|bz2|lzma|xz|zst))?$', files[0]), \
                'Unknown input file extension'
        formula = CNF(from_file=files[0])

        if verbose:
            print('c formula: {0} vars, {1} clauses'.format(formula.nv,
                                                            len(formula.clauses)))

        # computing the backbone
        with BBScan(formula, solver=solver, lift=lift, rotate=rotate,
                    verbose=verbose) as bbscan:
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
                print('c filtered: {0}; ({1:.2f})'.format(bbscan.filtered, 100. * bbscan.filtered / formula.nv))

            print('c oracle time: {0:.4f}'.format(bbscan.oracle_time()))
            print('c oracle calls: {0}'.format(bbscan.calls))
