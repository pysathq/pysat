#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## optux.py
##
##  Created on: Mar 22, 2021
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        OptUx

    ==================
    Module description
    ==================

    An implementation of an extractor of a smallest size minimal unsatisfiable
    subset (smallest MUS, or SMUS) [1]_ [2]_ [3]_ [4]_ and enumerator of
    SMUSes based on *implicit hitting set enumeration* [1]_. This
    implementation tries to replicate the well-known SMUS extractor Forqes
    [1]_. In contrast to Forqes, this implementation supports not only plain
    DIMACS :class:`.CNF` formulas but also weighted :class:`.WCNF` formulas.
    As a result, the tool is able to compute and enumerate *optimal* MUSes in
    case of weighted formulas. On the other hand, this prototype lacks a
    number of command-line options used in Forqes and so it may be less
    efficient compared to Forqes but the performance difference should not be
    significant.

    .. [1] Alexey Ignatiev, Alessandro Previti, Mark H. Liffiton, Joao
        Marques-Silva. *Smallest MUS Extraction with Minimal Hitting Set
        Dualization*. CP 2015. pp. 173-182

    .. [2] Mark H. Liffiton, Maher N. Mneimneh, Ines Lynce, Zaher S. Andraus,
        Joao Marques-Silva, Karem A. Sakallah. *A branch and bound algorithm
        for extracting smallest minimal unsatisfiable subformulas*.
        Constraints An Int. J. 14(4). 2009. pp. 415-442

    .. [3] Alexey Ignatiev, Mikolas Janota, Joao Marques-Silva. *Quantified
        Maximum Satisfiability: A Core-Guided Approach*. SAT 2013.
        pp. 250-266

    .. [4] Alexey Ignatiev, Mikolas Janota, Joao Marques-Silva. *Quantified
        maximum satisfiability*. Constraints An Int. J. 21(2). 2016.
        pp. 277-302

    The file provides a class :class:`OptUx`, which is the basic
    implementation of the algorithm. It can be applied to any formula in the
    :class:`.CNF` or :class:`.WCNF` format.

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``optux.py -h``) in the following
    way:

    ::

        $ xzcat formula.wcnf.xz
        p wcnf 3 6 4
        1 1 0
        1 2 0
        1 3 0
        4 -1 -2 0
        4 -1 -3 0
        4 -2 -3 0

        $ optux.py -vvv formula.wcnf.xz
        c mcs: 1 2 0
        c mcses: 0 unit, 1 disj
        c mus: 1 2 0
        c cost: 2
        c oracle time: 0.0001

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.optux import OptUx
        >>> from pysat.formula import WCNF
        >>>
        >>> wcnf = WCNF(from_file='formula.wcnf.xz')
        >>>
        >>> with OptUx(wcnf) as optux:
        ...     for mus in optux.enumerate():
        ...         print('mus {0} has cost {1}'.format(mus, optux.cost))
        mus [1, 2] has cost 2
        mus [1, 3] has cost 2
        mus [2, 3] has cost 2

    As can be seen in the example above, the solver can be instructed either
    to compute one optimal MUS of an input formula, or to enumerate a given
    number (or *all*) of its top optimal MUSes.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.examples.hitman import Hitman
from pysat.examples.rc2 import RC2
from pysat.formula import CNFPlus, WCNFPlus
from pysat.solvers import Solver
import re
import sys


#
#==============================================================================
class OptUx(object):
    """
        A simple Python version of the implicit hitting set based optimal MUS
        extractor and enumerator. Given a (weighted) (partial) CNF formula,
        i.e. formula in the :class:`.WCNF` format, this class can be used to
        compute a given number of optimal MUS (starting from the *best* one)
        of the input formula. :class:`OptUx` roughly follows the
        implementation of Forqes [1]_ but lacks a few additional heuristics,
        which however aren't applied in Forqes by default.

        As a result, OptUx applies exhaustive *disjoint* minimal correction
        subset (MCS) enumeration [1]_, [2]_, [3]_, [4]_ with the incremental
        use of RC2 [5]_ as an underlying MaxSAT solver. Once disjoint MCSes
        are enumerated, they are used to bootstrap a hitting set solver. This
        implementation uses :class:`.Hitman` as a hitting set solver, which is
        again based on RC2.

        Note that in the main implicit hitting enumeration loop of the
        algorithm, OptUx follows Forqes in that it does not reduce correction
        subsets detected to minimal correction subsets. As a result,
        correction subsets computed in the main loop are added to
        :class:`Hitman` *unreduced*.

        :class:`OptUx` can use any SAT solver available in PySAT. The default
        SAT solver to use is ``g3``, which stands for Glucose 3 [6]_ (see
        :class:`.SolverNames`). Boolean parameters ``adapt``, ``exhaust``, and
        ``minz`` control whether or not the underlying :class:`.RC2` oracles
        should apply detection and adaptation of intrinsic AtMost1
        constraints, core exhaustion, and core reduction. Also, unsatisfiable
        cores can be trimmed if the ``trim`` parameter is set to a non-zero
        integer. Finally, verbosity level can be set using the ``verbose``
        parameter.

        .. [5] Alexey Ignatiev, Antonio Morgado, Joao Marques-Silva. *RC2: an
            Efficient MaxSAT Solver*. J. Satisf. Boolean Model. Comput. 11(1).
            2019. pp. 53-64

        .. [6] Gilles Audemard, Jean-Marie Lagniez, Laurent Simon.
            *Improving Glucose for Incremental SAT Solving with
            Assumptions: Application to MUS Extraction*. SAT 2013.
            pp. 309-317

        :param formula: (weighted) (partial) CNF formula
        :param solver: SAT oracle name
        :param adapt: detect and adapt intrinsic AtMost1 constraints
        :param exhaust: do core exhaustion
        :param minz: do heuristic core reduction
        :param trim: do core trimming at most this number of times
        :param verbose: verbosity level

        :type formula: :class:`.WCNF`
        :type solver: str
        :type adapt: bool
        :type exhaust: bool
        :type minz: bool
        :type trim: int
        :type verbose: int
    """

    def __init__(self, formula, solver='g3', adapt=False, exhaust=False,
            minz=False, trim=False, verbose=0):
        """
            Constructor.
        """

        # verbosity level
        self.verbose = verbose

        # constructing a local copy of the formula
        self.formula = WCNFPlus()
        self.formula.hard = formula.hard[:]
        self.formula.wght = formula.wght[:]
        self.formula.topw = formula.topw
        self.formula.nv = formula.nv

        # top variable identifier
        self.topv = formula.nv

        # processing soft clauses
        self._process_soft(formula)
        self.formula.nv = self.topv

        # creating an unweighted copy
        unweighted = self.formula.copy()
        unweighted.wght = [1 for w in unweighted.wght]

        # enumerating disjoint MCSes (including unit-size MCSes)
        to_hit, self.units = self._disjoint(unweighted, solver, adapt, exhaust,
                minz, trim)

        if self.verbose > 2:
            print('c mcses: {0} unit, {1} disj'.format(len(self.units),
                len(to_hit) + len(self.units)))

        # hitting set enumerator
        self.hitman = Hitman(bootstrap_with=to_hit, weights=self.weights,
                solver=solver, htype='sorted', mxs_adapt=adapt,
                mxs_exhaust=exhaust, mxs_minz=minz, mxs_trim=trim)

        # SAT oracle bootstrapped with the hard clauses; note that
        # clauses of the unit-size MCSes are enforced to be enabled
        self.oracle = Solver(name=solver, bootstrap_with=unweighted.hard +
                [[mcs] for mcs in self.units])

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
            Explicit destructor of the internal hitting set and SAT oracles.
        """

        if self.hitman:
            self.hitman.delete()
            self.hitman = None

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

    def _process_soft(self, formula):
        """
            The method is for processing the soft clauses of the input
            formula. Concretely, it checks which soft clauses must be relaxed
            by a unique selector literal and applies the relaxation.

            :param formula: input formula
            :type formula: :class:`.WCNF`
        """

        # list of selectors
        self.sels = []

        # mapping from selectors to clause ids
        self.smap = {}

        # duplicate unit clauses
        processed_dups = set()

        # processing the soft clauses
        for cl in formula.soft:
            # if the clause is unit-size, its sole literal acts a selector
            selv = cl[0]

            # if clause is not unit, we relax it
            if len(cl) > 1:
                self.topv += 1
                selv = self.topv
                self.formula.hard.append(cl + [-selv])
            elif selv in self.smap:
                # the clause is unit but a there is a previously seen
                # duplicate of this clause; this means we have to
                # reprocess the previous clause again and relax it
                if selv not in processed_dups:
                    self.topv += 1
                    nsel = self.topv
                    self.sels[self.smap[selv] - 1] = nsel
                    self.formula.hard.append(self.formula.soft[self.smap[selv] - 1] + [-nsel])
                    self.formula.soft[self.smap[selv] - 1] = [nsel]
                    self.smap[nsel] = self.smap[selv]
                    processed_dups.add(selv)

                # processing the current clause
                self.topv += 1
                selv = self.topv
                self.formula.hard.append(cl + [-selv])

            self.sels.append(selv)
            self.formula.soft.append([selv])
            self.smap[selv] = len(self.sels)

        # garbage-collecting the duplicates
        for selv in processed_dups:
            del self.smap[selv]

        # these numbers should be equal after the processing
        assert len(self.sels) == len(self.smap) == len(self.formula.wght)

        # creating a dictionary of weights
        self.weights = {l: w for l, w in zip(self.sels, self.formula.wght)}

    def _disjoint(self, formula, solver, adapt, exhaust, minz, trim):
        """
            This method constitutes the preliminary step of the implicit
            hitting set paradigm of Forqes. Namely, it enumerates all the
            disjoint *minimal correction subsets* (MCSes) of the formula,
            which will be later used to bootstrap the hitting set solver.

            Note that the MaxSAT solver in use is :class:`.RC2`. As a result,
            all the input parameters of the method, namely, ``formula``,
            ``solver``, ``adapt``, `exhaust``, ``minz``, and ``trim`` -
            represent the input and the options for the RC2 solver.

            :param formula: input formula
            :param solver: SAT solver name
            :param adapt: detect and adapt AtMost1 constraints
            :param exhaust: exhaust unsatisfiable cores
            :param minz: apply heuristic core minimization
            :param trim: trim unsatisfiable cores at most this number of times

            :type formula: :class:`.WCNF`
            :type solver: str
            :type adapt: bool
            :type exhaust: bool
            :type minz: bool
            :type trim: int
        """

        # these will store disjoint MCSes
        # (unit-size MCSes are stored separately)
        to_hit, units = [], []

        with RC2(formula, solver=solver, adapt=adapt, exhaust=exhaust,
                minz=minz, trim=trim, verbose=0) as oracle:

            # iterating over MaxSAT solutions
            while True:
                # a new MaxSAT model
                model = oracle.compute()

                if model is None:
                    # no model => no more disjoint MCSes
                    break

                # extracting the MCS corresponding to the model
                falsified = list(filter(lambda l: model[abs(l) - 1] == -l, self.sels))

                # unit size or not?
                if len(falsified) > 1:
                    to_hit.append(falsified)
                else:
                    units.append(falsified[0])

                # blocking the MCS;
                # next time, all these clauses will be satisfied
                for l in falsified:
                    oracle.add_clause([l])

                # reporting the MCS
                if self.verbose > 3:
                    print('c mcs: {0} 0'.format(' '.join([str(self.smap[s]) for s in falsified])))

            # RC2 will be destroyed next; let's keep the oracle time
            self.disj_time = oracle.oracle_time()

        return to_hit, units

    def compute(self):
        """
            This method implements the main look of the implicit hitting set
            paradigm of Forqes to compute a best-cost MUS. The result MUS is
            returned as a list of integers, each representing a soft clause
            index.

            :rtype: list(int)
        """

        while True:
            # computing a new optimal hitting set
            hs = self.hitman.get()

            if hs is None:
                # no more hitting sets exist
                break

            # setting all the selector polarities to true
            self.oracle.set_phases(self.sels)

            # testing satisfiability of the {self.units + hs} subset
            res = self.oracle.solve(assumptions=hs)

            if res == False:
                # the candidate subset of clauses is unsatisfiable,
                # i.e. it is an optimal MUS we are searching for;
                # therefore, blocking it and returning
                self.hitman.block(hs)
                self.cost = self.hitman.oracle.cost + len(self.units)
                return sorted(map(lambda s: self.smap[s], self.units + hs))
            else:
                # the candidate subset is satisfiable,
                # thus extracting a correction subset
                model = self.oracle.get_model()
                cs = list(filter(lambda l: model[abs(l) - 1] == -l, self.sels))

                # hitting the new correction subset
                self.hitman.hit(cs, weights=self.weights)

    def enumerate(self):
        """
            This is generator method iterating through MUSes and enumerating
            them until the formula has no more MUSes, or a user decides to
            stop the process.

            :rtype: list(int)
        """

        done = False

        while not done:
            mus = self.compute()

            if mus != None:
                yield mus
            else:
                done = True

    def oracle_time(self):
        """
            This method computes and returns the total SAT solving time
            involved.

            :rtype: float
        """

        return self.disj_time + self.hitman.oracle_time() + self.oracle.time_accum()


#
#==============================================================================
def parse_options():
    """
        Parses command-line options.
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ae:hms:t:vx',
                ['adapt', 'enum=', 'exhaust', 'help', 'minimize', 'solver=',
                    'trim=', 'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        usage()
        sys.exit(1)

    adapt = False
    exhaust = False
    minz = False
    to_enum = 1
    solver = 'm22'
    trim = 0
    verbose = 1

    for opt, arg in opts:
        if opt in ('-a', '--adapt'):
            adapt = True
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-m', '--minimize'):
            minz = True
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-t', '--trim'):
            trim = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-x', '--exhaust'):
            exhaust = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return adapt, exhaust, minz, trim, to_enum, solver, verbose, args


#
#==============================================================================
def usage():
    """
        Prints help message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] file')
    print('Options:')
    print('        -a, --adapt            Try to adapt (simplify) input formula')
    print('        -e, --enum=<string>    Enumerate top-k solutions')
    print('                               Available values: [1 .. INT_MAX], all (default: 1)')
    print('        -h, --help             Show this message')
    print('        -m, --minimize         Use a heuristic unsatisfiable core minimizer')
    print('        -s, --solver           SAT solver to use')
    print('                               Available values: g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = m22)')
    print('        -t, --trim=<int>       How many times to trim unsatisfiable cores')
    print('                               Available values: [0 .. INT_MAX] (default = 0)')
    print('        -v, --verbose          Be verbose')
    print('        -x, --exhaust          Exhaust new unsatisfiable cores')


#
#==============================================================================
if __name__ == '__main__':
    adapt, exhaust, minz, trim, to_enum, solver, verbose, files = parse_options()

    if files:
        # reading standard CNF, WCNF, or (W)CNF+
        if re.search('cnf[p|+]?(\.(gz|bz2|lzma|xz))?$', files[0]):
            if re.search('\.wcnf[p|+]?(\.(gz|bz2|lzma|xz))?$', files[0]):
                formula = WCNFPlus(from_file=files[0])
            else:  # expecting '*.cnf[,p,+].*'
                formula = CNFPlus(from_file=files[0]).weighted()

        # creating an object of OptUx
        with OptUx(formula, solver=solver, adapt=adapt, exhaust=exhaust,
                minz=minz, trim=trim, verbose=verbose) as optux:

            # iterating over the necessary number of optimal MUSes
            for i, mus in enumerate(optux.enumerate()):
                # reporting the current solution
                if verbose:
                    print('c mus:', ' '.join([str(cl_id) for cl_id in mus]), '0')

                    if verbose > 1:
                        print('c cost:', optux.cost)

                # checking if we are done
                if to_enum and i + 1 == to_enum:
                    break

            # reporting the total oracle time
            if verbose > 1:
                print('c oracle time: {0:.4f}'.format(optux.oracle_time()))
