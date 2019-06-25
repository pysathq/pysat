#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## rc2.py
##
##  Created on: Dec 2, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        RC2
        RC2Stratified

    ==================
    Module description
    ==================

    An implementation of the RC2 algorithm for solving maximum
    satisfiability. RC2 stands for *relaxable cardinality constraints*
    (alternatively, *soft cardinality constraints*) and represents an
    improved version of the OLLITI algorithm, which was described in
    [1]_ and [2]_ and originally implemented in the `MSCG MaxSAT
    solver <https://reason.di.fc.ul.pt/wiki/doku.php?id=mscg>`_.

    Initially, this solver was supposed to serve as an example of a
    possible PySAT usage illustrating how a state-of-the-art MaxSAT
    algorithm could be implemented in Python and still be efficient.
    It participated in the `MaxSAT Evaluation 2018
    <https://maxsat-evaluations.github.io/2018/>`_ where,
    surprisingly, it `was ranked first
    <https://maxsat-evaluations.github.io/2018/rankings.html>`_ in two
    complete categories: *unweighted* and *weighted*. A brief solver
    description can be found in [3]_.

    .. [1] António Morgado, Carmine Dodaro, Joao Marques-Silva.
        *Core-Guided MaxSAT with Soft Cardinality Constraints*. CP
        2014. pp. 564-573

    .. [2] António Morgado, Alexey Ignatiev, Joao Marques-Silva.
        *MSCG: Robust Core-Guided MaxSAT Solving*. JSAT 9. 2014.
        pp. 129-134

    .. [3] Alexey Ignatiev, António Morgado, Joao Marques-Silva.
        *RC2: a Python-based MaxSAT Solver*. MaxSAT Evaluation 2018.
        p. 22

    The file implements two classes: :class:`RC2` and
    :class:`RC2Stratified`. The former class is the basic
    implementation of the algorithm, which can be applied to a MaxSAT
    formula in the :class:`.WCNF` format. The latter class
    additionally implements Boolean lexicographic optimization (BLO)
    [4]_ and stratification [5]_ on top of :class:`RC2`.

    .. [4] Joao Marques-Silva, Josep Argelich, Ana Graça, Inês Lynce.
        *Boolean lexicographic optimization: algorithms &
        applications*. Ann. Math. Artif. Intell. 62(3-4). 2011.
        pp. 317-343

    .. [5] Carlos Ansótegui, Maria Luisa Bonet, Joel Gabàs, Jordi
        Levy. *Improving WPM2 for (Weighted) Partial MaxSAT*. CP
        2013. pp. 117-132

    The implementation can be used as an executable (the list of
    available command-line options can be shown using ``rc2.py -h``)
    in the following way:

    ::

        $ xzcat formula.wcnf.xz
        p wcnf 3 6 4
        1 1 0
        1 2 0
        1 3 0
        4 -1 -2 0
        4 -1 -3 0
        4 -2 -3 0

        $ rc2.py -vv formula.wcnf.xz
        c formula: 3 vars, 3 hard, 3 soft
        c cost: 1; core sz: 2; soft sz: 2
        c cost: 2; core sz: 2; soft sz: 1
        s OPTIMUM FOUND
        o 2
        v -1 -2 3
        c oracle time: 0.0001

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.rc2 import RC2
        >>> from pysat.formula import WCNF
        >>>
        >>> wcnf = WCNF(from_file='formula.wcnf.xz')
        >>>
        >>> with RC2(wcnf) as rc2:
        ...     for m in rc2.enumerate():
        ...         print 'model {0} has cost {1}'.format(m, rc2.cost)
        model [-1, -2, 3] has cost 2
        model [1, -2, -3] has cost 2
        model [-1, 2, -3] has cost 2
        model [-1, -2, -3] has cost 3

    As can be seen in the example above, the solver can be instructed
    either to compute one MaxSAT solution of an input formula, or to
    enumerate a given number (or *all*) of its top MaxSAT solutions.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import collections
import getopt
import itertools
from math import copysign
import os
from pysat.formula import CNF, WCNF
from pysat.card import ITotalizer
from pysat.solvers import Solver
import re
import six
from six.moves import range
import sys


#
#==============================================================================
class RC2(object):
    """
        Implementation of the basic RC2 algorithm. Given a (weighted)
        (partial) CNF formula, i.e. formula in the :class:`.WCNF`
        format, this class can be used to compute a given number of
        MaxSAT solutions for the input formula. :class:`RC2` roughly
        follows the implementation of algorithm OLLITI [1]_ [2]_ of
        MSCG and applies a few heuristics on top of it. These include

        - *unsatisfiable core exhaustion* (see method :func:`exhaust_core`),
        - *unsatisfiable core reduction* (see method :func:`minimize_core`),
        - *intrinsic AtMost1 constraints* (see method :func:`adapt_am1`).

        :class:`RC2` can use any SAT solver available in PySAT. The
        default SAT solver to use is ``g3`` (see
        :class:`.SolverNames`). Additionally, if Glucose is chosen,
        the ``incr`` parameter controls whether to use the incremental
        mode of Glucose [6]_ (turned off by default). Boolean
        parameters ``adapt``, ``exhaust``, and ``minz`` control
        whether or to apply detection and adaptation of intrinsic
        AtMost1 constraints, core exhaustion, and core reduction.
        Unsatisfiable cores can be trimmed if the ``trim`` parameter
        is set to a non-zero integer. Finally, verbosity level can be
        set using the ``verbose`` parameter.

        .. [6] Gilles Audemard, Jean-Marie Lagniez, Laurent Simon.
            *Improving Glucose for Incremental SAT Solving with
            Assumptions: Application to MUS Extraction*. SAT 2013.
            pp. 309-317

        :param formula: (weighted) (partial) CNF formula
        :param solver: SAT oracle name
        :param adapt: detect and adapt intrinsic AtMost1 constraints
        :param exhaust: do core exhaustion
        :param incr: use incremental mode of Glucose
        :param minz: do heuristic core reduction
        :param trim: do core trimming at most this number of times
        :param verbose: verbosity level

        :type formula: :class:`.WCNF`
        :type solver: str
        :type adapt: bool
        :type exhaust: bool
        :type incr: bool
        :type minz: bool
        :type trim: int
        :type verbose: int
    """

    def __init__(self, formula, solver='g3', adapt=False, exhaust=False,
            incr=False, minz=False, trim=0, verbose=0):
        """
            Constructor.
        """

        # saving verbosity level and other options
        self.verbose = verbose
        self.exhaust = exhaust
        self.solver = solver
        self.adapt = adapt
        self.minz = minz
        self.trim = trim

        # clause selectors and mapping from selectors to clause ids
        self.sels, self.smap = [], {}

        # other MaxSAT related stuff
        self.topv = formula.nv
        self.wght = {}  # weights of soft clauses
        self.sums = []  # totalizer sum assumptions
        self.bnds = {}  # a mapping from sum assumptions to totalizer bounds
        self.tobj = {}  # a mapping from sum assumptions to totalizer objects
        self.cost = 0

        # mappings between internal and external variables
        VariableMap = collections.namedtuple('VariableMap', ['e2i', 'i2e'])
        self.vmap = VariableMap(e2i={}, i2e={})

        # initialize SAT oracle with hard clauses only
        self.init(formula, incr=incr)

        # core minimization is going to be extremely expensive
        # for large plain formulas, and so we turn it off here
        wght = self.wght.values()
        if not formula.hard and len(self.sels) > 100000 and min(wght) == max(wght):
            self.minz = False

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

    def init(self, formula, incr=False):
        """
            Initialize the internal SAT oracle. The oracle is used
            incrementally and so it is initialized only once when
            constructing an object of class :class:`RC2`. Given an
            input :class:`.WCNF` formula, the method bootstraps the
            oracle with its hard clauses. It also augments the soft
            clauses with "fresh" selectors and adds them to the oracle
            afterwards.

            Optional input parameter ``incr`` (``False`` by default)
            regulates whether or not Glucose's incremental mode [6]_
            is turned on.

            :param formula: input formula
            :param incr: apply incremental mode of Glucose

            :type formula: :class:`.WCNF`
            :type incr: bool
        """

        # creating a solver object
        self.oracle = Solver(name=self.solver, bootstrap_with=formula.hard,
                incr=incr, use_timer=True)

        # adding soft clauses to oracle
        for i, cl in enumerate(formula.soft):
            selv = cl[0]  # if clause is unit, selector variable is its literal

            if len(cl) > 1:
                self.topv += 1
                selv = self.topv

                cl.append(-self.topv)
                self.oracle.add_clause(cl)

            if selv not in self.wght:
                # record selector and its weight
                self.sels.append(selv)
                self.wght[selv] = formula.wght[i]
                self.smap[selv] = i
            else:
                # selector is not new; increment its weight
                self.wght[selv] += formula.wght[i]

        # storing the set of selectors
        self.sels_set = set(self.sels)

        # at this point internal and external variables are the same
        for v in range(1, formula.nv + 1):
            self.vmap.e2i[v] = v
            self.vmap.i2e[v] = v

        if self.verbose > 1:
            print('c formula: {0} vars, {1} hard, {2} soft'.format(formula.nv,
                len(formula.hard), len(formula.soft)))

    def add_clause(self, clause, weight=None):
        """
            The method for adding a new hard of soft clause to the
            problem formula. Although the input formula is to be
            specified as an argument of the constructor of
            :class:`RC2`, adding clauses may be helpful when
            *enumerating* MaxSAT solutions of the formula. This way,
            the clauses are added incrementally, i.e. *on the fly*.

            The clause to add can be any iterable over integer
            literals. The additional integer parameter ``weight`` can
            be set to meaning the the clause being added is soft
            having the corresponding weight (note that parameter
            ``weight`` is set to ``None`` by default meaning that the
            clause is hard).

            :param clause: a clause to add
            :param weight: weight of the clause (if any)

            :type clause: iterable(int)
            :type weight: int

            .. code-block:: python

                >>> from pysat.examples.rc2 import RC2
                >>> from pysat.formula import WCNF
                >>>
                >>> wcnf = WCNF()
                >>> wcnf.append([-1, -2])  # adding hard clauses
                >>> wcnf.append([-1, -3])
                >>>
                >>> wcnf.append([1], weight=1)  # adding soft clauses
                >>> wcnf.append([2], weight=1)
                >>> wcnf.append([3], weight=1)
                >>>
                >>> with RC2(wcnf) as rc2:
                ...     rc2.compute()  # solving the MaxSAT problem
                [-1, 2, 3]
                ...     print rc2.cost
                1
                ...     rc2.add_clause([-2, -3])  # adding one more hard clause
                ...     rc2.compute()  # computing another model
                [-1, -2, 3]
                ...     print rc2.cost
                2
        """

        # first, map external literals to internal literals
        # introduce new variables if necessary
        cl = list(map(lambda l: self._map_extlit(l), clause))

        if not weight:
            # the clause is hard, and so we simply add it to the SAT oracle
            self.oracle.add_clause(cl)
        else:
            # soft clauses should be augmented with a selector
            selv = cl[0]  # for a unit clause, no selector is needed

            if len(cl) > 1:
                self.topv += 1
                selv = self.topv

                cl.append(-self.topv)
                self.oracle.add_clause(cl)

            if selv not in self.wght:
                # record selector and its weight
                self.sels.append(selv)
                self.wght[selv] = weight
                self.smap[selv] = len(self.sels) - 1
            else:
                # selector is not new; increment its weight
                self.wght[selv] += weight

            self.sels_set.add(selv)

    def delete(self):
        """
            Explicit destructor of the internal SAT oracle and all the
            totalizer objects creating during the solving process.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

            if self.solver != 'mc':  # for minicard, there is nothing to free
                for t in six.itervalues(self.tobj):
                    t.delete()

    def compute(self):
        """
            This method can be used for computing one MaxSAT solution,
            i.e. for computing an assignment satisfying all hard
            clauses of the input formula and maximizing the sum of
            weights of satisfied soft clauses. It is a wrapper for the
            internal :func:`compute_` method, which does the job,
            followed by the model extraction.

            Note that the method returns ``None`` if no MaxSAT model
            exists. The method can be called multiple times, each
            being followed by blocking the last model. This way one
            can enumerate top-:math:`k` MaxSAT solutions (this can
            also be done by calling :meth:`enumerate()`).

            :returns: a MaxSAT model
            :rtype: list(int)

            .. code-block:: python

                >>> from pysat.examples.rc2 import RC2
                >>> from pysat.formula import WCNF
                >>>
                >>> rc2 = RC2(WCNF())  # passing an empty WCNF() formula
                >>> rc2.add_clause([-1, -2])
                >>> rc2.add_clause([-1, -3])
                >>> rc2.add_clause([-2, -3])
                >>>
                >>> rc2.add_clause([1], weight=1)
                >>> rc2.add_clause([2], weight=1)
                >>> rc2.add_clause([3], weight=1)
                >>>
                >>> model = rc2.compute()
                >>> print model
                [-1, -2, 3]
                >>> print rc2.cost
                2
                >>> rc2.delete()
        """

        # simply apply MaxSAT only once
        res = self.compute_()

        if res:
            # extracting a model
            self.model = self.oracle.get_model()
            self.model = filter(lambda l: abs(l) in self.vmap.i2e, self.model)
            self.model = map(lambda l: int(copysign(self.vmap.i2e[abs(l)], l)), self.model)
            self.model = sorted(self.model, key=lambda l: abs(l))

            return self.model

    def enumerate(self):
        """
            Enumerate top MaxSAT solutions (from best to worst). The
            method works as a generator, which iteratively calls
            :meth:`compute` to compute a MaxSAT model, blocks it
            internally and returns it.

            :returns: a MaxSAT model
            :rtype: list(int)

            .. code-block:: python

                >>> from pysat.examples.rc2 import RC2
                >>> from pysat.formula import WCNF
                >>>
                >>> rc2 = RC2(WCNF())  # passing an empty WCNF() formula
                >>> rc2.add_clause([-1, -2])  # adding clauses "on the fly"
                >>> rc2.add_clause([-1, -3])
                >>> rc2.add_clause([-2, -3])
                >>>
                >>> rc2.add_clause([1], weight=1)
                >>> rc2.add_clause([2], weight=1)
                >>> rc2.add_clause([3], weight=1)
                >>>
                >>> for model in rc2.enumerate():
                ...     print model, rc2.cost
                [-1, -2, 3] 2
                [1, -2, -3] 2
                [-1, 2, -3] 2
                [-1, -2, -3] 3
                >>> rc2.delete()
        """

        done = False
        while not done:
            model = self.compute()

            if model != None:
                self.add_clause([-l for l in model])
                yield model
            else:
                done = True

    def compute_(self):
        """
            Main core-guided loop, which iteratively calls a SAT
            oracle, extracts a new unsatisfiable core and processes
            it. The loop finishes as soon as a satisfiable formula is
            obtained. If specified in the command line, the method
            additionally calls :meth:`adapt_am1` to detect and adapt
            intrinsic AtMost1 constraints before executing the loop.

            :rtype: bool
        """

        # trying to adapt (simplify) the formula
        # by detecting and using atmost1 constraints
        if self.adapt:
            self.adapt_am1()

        # main solving loop
        while not self.oracle.solve(assumptions=self.sels + self.sums):
            self.get_core()

            if not self.core:
                # core is empty, i.e. hard part is unsatisfiable
                return False

            self.process_core()

            if self.verbose > 1:
                print('c cost: {0}; core sz: {1}; soft sz: {2}'.format(self.cost,
                    len(self.core), len(self.sels) + len(self.sums)))

        return True

    def get_core(self):
        """
            Extract unsatisfiable core. The result of the procedure is
            stored in variable ``self.core``. If necessary, core
            trimming and also heuristic core reduction is applied
            depending on the command-line options. A *minimum weight*
            of the core is computed and stored in ``self.minw``.
            Finally, the core is divided into two parts:

            1. clause selectors (``self.core_sels``),
            2. sum assumptions (``self.core_sums``).
        """

        # extracting the core
        self.core = self.oracle.get_core()

        if self.core:
            # try to reduce the core by trimming
            self.trim_core()

            # and by heuristic minimization
            self.minimize_core()

            # core weight
            self.minw = min(map(lambda l: self.wght[l], self.core))

            # dividing the core into two parts
            iter1, iter2 = itertools.tee(self.core)
            self.core_sels = list(l for l in iter1 if l in self.sels_set)
            self.core_sums = list(l for l in iter2 if l not in self.sels_set)

    def process_core(self):
        """
            The method deals with a core found previously in
            :func:`get_core`. Clause selectors ``self.core_sels`` and
            sum assumptions involved in the core are treated
            separately of each other. This is handled by calling
            methods :func:`process_sels` and :func:`process_sums`,
            respectively. Whenever necessary, both methods relax the
            core literals, which is followed by creating a new
            totalizer object encoding the sum of the new relaxation
            variables. The totalizer object can be "exhausted"
            depending on the option.
        """

        # updating the cost
        self.cost += self.minw

        # assumptions to remove
        self.garbage = set()

        if len(self.core_sels) != 1 or len(self.core_sums) > 0:
            # process selectors in the core
            self.process_sels()

            # process previously introducded sums in the core
            self.process_sums()

            if len(self.rels) > 1:
                # create a new cardunality constraint
                t = self.create_sum()

                # apply core exhaustion if required
                b = self.exhaust_core(t) if self.exhaust else 1

                if b:
                    # save the info about this sum and
                    # add its assumption literal
                    self.set_bound(t, b)
                else:
                    # impossible to satisfy any of these clauses
                    # they must become hard
                    for relv in self.rels:
                        self.oracle.add_clause([relv])
        else:
            # unit cores are treated differently
            # (their negation is added to the hard part)
            self.oracle.add_clause([-self.core_sels[0]])
            self.garbage.add(self.core_sels[0])

        # remove unnecessary assumptions
        self.filter_assumps()

    def adapt_am1(self):
        """
            Detect and adapt intrinsic AtMost1 constraints. Assume
            there is a subset of soft clauses
            :math:`\\mathcal{S}'\subseteq \\mathcal{S}` s.t.
            :math:`\sum_{c\in\\mathcal{S}'}{c\leq 1}`, i.e. at most
            one of the clauses of :math:`\\mathcal{S}'` can be
            satisfied.

            Each AtMost1 relationship between the soft clauses can be
            detected in the following way. The method traverses all
            soft clauses of the formula one by one, sets one
            respective selector literal to true and checks whether
            some other soft clauses are forced to be false. This is
            checked by testing if selectors for other soft clauses are
            unit-propagated to be false. Note that this method for
            detection of AtMost1 constraints is *incomplete*, because
            in general unit propagation does not suffice to test
            whether or not :math:`\\mathcal{F}\wedge l_i\\models
            \\neg{l_j}`.

            Each intrinsic AtMost1 constraint detected this way is
            handled by calling :func:`process_am1`.
        """

        # literal connections
        conns = collections.defaultdict(lambda: set([]))
        confl = []

        # prepare connections
        for l1 in self.sels:
            st, props = self.oracle.propagate(assumptions=[l1], phase_saving=2)
            if st:
                for l2 in props:
                    if -l2 in self.sels_set:
                        conns[l1].add(-l2)
                        conns[-l2].add(l1)
            else:
                # propagating this literal results in a conflict
                confl.append(l1)

        if confl:  # filtering out unnecessary connections
            ccopy = {}
            confl = set(confl)

            for l in conns:
                if l not in confl:
                    cc = conns[l].difference(confl)
                    if cc:
                        ccopy[l] = cc

            conns = ccopy
            confl = list(confl)

            # processing unit size cores
            for l in confl:
                self.core, self.minw = [l], self.wght[l]
                self.core_sels, self.core_sums = [l], []
                self.process_core()

            if self.verbose > 1:
                print('c unit cores found: {0}; cost: {1}'.format(len(confl),
                    self.cost))

        nof_am1 = 0
        len_am1 = []
        lits = set(conns.keys())
        while lits:
            am1 = [min(lits, key=lambda l: len(conns[l]))]

            for l in sorted(conns[am1[0]], key=lambda l: len(conns[l])):
                if l in lits:
                    for l_added in am1[1:]:
                        if l_added not in conns[l]:
                            break
                    else:
                        am1.append(l)

            # updating remaining lits and connections
            lits.difference_update(set(am1))
            for l in conns:
                conns[l] = conns[l].difference(set(am1))

            if len(am1) > 1:
                # treat the new atmost1 relation
                self.process_am1(am1)
                nof_am1 += 1
                len_am1.append(len(am1))

        # updating the set of selectors
        self.sels_set = set(self.sels)

        if self.verbose > 1 and nof_am1:
            print('c am1s found: {0}; avgsz: {1:.1f}; cost: {2}'.format(nof_am1,
                sum(len_am1) / float(nof_am1), self.cost))

    def process_am1(self, am1):
        """
            Process an AtMost1 relation detected by :func:`adapt_am1`.
            Note that given a set of soft clauses
            :math:`\\mathcal{S}'` at most one of which can be
            satisfied, one can immediately conclude that the formula
            has cost at least :math:`|\\mathcal{S}'|-1` (assuming
            *unweighted* MaxSAT). Furthermore, it is safe to replace
            all clauses of :math:`\\mathcal{S}'` with a single soft
            clause :math:`\sum_{c\in\\mathcal{S}'}{c}`.

            Here, input parameter ``am1`` plays the role of subset
            :math:`\\mathcal{S}'` mentioned above. The procedure bumps
            the MaxSAT cost by ``self.minw * (len(am1) - 1)``.

            All soft clauses involved in ``am1`` are replaced by a
            single soft clause, which is a disjunction of the
            selectors of clauses in ``am1``. The weight of the new
            soft clause is set to ``self.minw``.

            :param am1: a list of selectors connected by an AtMost1 constraint

            :type am1: list(int)
        """

        # computing am1's weight
        self.minw = min(map(lambda l: self.wght[l], am1))

        # pretending am1 to be a core, and the bound is its size - 1
        self.core_sels, b = am1, len(am1) - 1

        # incrementing the cost
        self.cost += b * self.minw

        # assumptions to remove
        self.garbage = set()

        # splitting and relaxing if needed
        self.process_sels()

        # new selector
        self.topv += 1
        selv = self.topv

        self.oracle.add_clause([-l for l in self.rels] + [-selv])

        # integrating the new selector
        self.sels.append(selv)
        self.wght[selv] = self.minw
        self.smap[selv] = len(self.wght) - 1

        # removing unnecessary assumptions
        self.filter_assumps()

    def trim_core(self):
        """
            This method trims a previously extracted unsatisfiable
            core at most a given number of times. If a fixed point is
            reached before that, the method returns.
        """

        for i in range(self.trim):
            # call solver with core assumption only
            # it must return 'unsatisfiable'
            self.oracle.solve(assumptions=self.core)

            # extract a new core
            new_core = self.oracle.get_core()

            if len(new_core) == len(self.core):
                # stop if new core is not better than the previous one
                break

            # otherwise, update core
            self.core = new_core

    def minimize_core(self):
        """
            Reduce a previously extracted core and compute an
            over-approximation of an MUS. This is done using the
            simple deletion-based MUS extraction algorithm.

            The idea is to try to deactivate soft clauses of the
            unsatisfiable core one by one while checking if the
            remaining soft clauses together with the hard part of the
            formula are unsatisfiable. Clauses that are necessary for
            preserving unsatisfiability comprise an MUS of the input
            formula (it is contained in the given unsatisfiable core)
            and are reported as a result of the procedure.

            During this core minimization procedure, all SAT calls are
            dropped after obtaining 1000 conflicts.
        """

        if self.minz and len(self.core) > 1:
            self.core = sorted(self.core, key=lambda l: self.wght[l])
            self.oracle.conf_budget(1000)

            i = 0
            while i < len(self.core):
                to_test = self.core[:i] + self.core[(i + 1):]

                if self.oracle.solve_limited(assumptions=to_test) == False:
                    self.core = to_test
                else:
                    i += 1

    def exhaust_core(self, tobj):
        """
            Exhaust core by increasing its bound as much as possible.
            Core exhaustion was originally referred to as *cover
            optimization* in [5]_.

            Given a totalizer object ``tobj`` representing a sum of
            some *relaxation* variables :math:`r\in R` that augment
            soft clauses :math:`\\mathcal{C}_r`, the idea is to
            increase the right-hand side of the sum (which is equal to
            1 by default) as much as possible, reaching a value
            :math:`k` s.t. formula
            :math:`\\mathcal{H}\wedge\\mathcal{C}_r\wedge(\sum_{r\in
            R}{r\leq k})` is still unsatisfiable while increasing it
            further makes the formula satisfiable (here
            :math:`\\mathcal{H}` denotes the hard part of the
            formula).

            The rationale is that calling an oracle incrementally on a
            series of slightly modified formulas focusing only on the
            recently computed unsatisfiable core and disregarding the
            rest of the formula may be practically effective.
        """

        # the first case is simpler
        if self.oracle.solve(assumptions=[-tobj.rhs[1]]):
            return 1
        else:
            self.cost += self.minw

        for i in range(2, len(self.rels)):
            # saving the previous bound
            self.tobj[-tobj.rhs[i - 1]] = tobj
            self.bnds[-tobj.rhs[i - 1]] = i - 1

            # increasing the bound
            self.update_sum(-tobj.rhs[i - 1])

            if self.oracle.solve(assumptions=[-tobj.rhs[i]]):
                # the bound should be equal to i
                return i

            # the cost should increase further
            self.cost += self.minw

        return None

    def process_sels(self):
        """
            Process soft clause selectors participating in a new core.
            The negation :math:`\\neg{s}` of each selector literal
            :math:`s` participating in the unsatisfiable core is added
            to the list of relaxation literals, which will be later
            used to create a new totalizer object in
            :func:`create_sum`.

            If the weight associated with a selector is equal to the
            minimal weight of the core, e.g. ``self.minw``, the
            selector is marked as garbage and will be removed in
            :func:`filter_assumps`. Otherwise, the clause is split as
            described in [1]_.
        """

        # new relaxation variables
        self.rels = []

        for l in self.core_sels:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)

                # reuse assumption variable as relaxation
                self.rels.append(-l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # it is an unrelaxed soft clause,
                # a new relaxed copy of which we add to the solver
                self.topv += 1
                self.oracle.add_clause([l, self.topv])
                self.rels.append(self.topv)

    def process_sums(self):
        """
            Process cardinality sums participating in a new core.
            Whenever necessary, some of the sum assumptions are
            removed or split (depending on the value of
            ``self.minw``). Deleted sums are marked as garbage and are
            dealt with in :func:`filter_assumps`.

            In some cases, the process involves updating the
            right-hand sides of the existing cardinality sums (see the
            call to :func:`update_sum`). The overall procedure is
            detailed in [1]_.
        """

        for l in self.core_sums:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

            # increase bound for the sum
            t, b = self.update_sum(l)

            # updating bounds and weights
            if b < len(t.rhs):
                lnew = -t.rhs[b]
                if lnew in self.garbage:
                    self.garbage.remove(lnew)
                    self.wght[lnew] = 0

                if lnew not in self.wght:
                    self.set_bound(t, b)
                else:
                    self.wght[lnew] += self.minw

            # put this assumption to relaxation vars
            self.rels.append(-l)

    def create_sum(self, bound=1):
        """
            Create a totalizer object encoding a cardinality
            constraint on the new list of relaxation literals obtained
            in :func:`process_sels` and :func:`process_sums`. The
            clauses encoding the sum of the relaxation literals are
            added to the SAT oracle. The sum of the totalizer object
            is encoded up to the value of the input parameter
            ``bound``, which is set to ``1`` by default.

            :param bound: right-hand side for the sum to be created
            :type bound: int

            :rtype: :class:`.ITotalizer`

            Note that if Minicard is used as a SAT oracle, native
            cardinality constraints are used instead of
            :class:`.ITotalizer`.
        """

        if self.solver != 'mc':  # standard totalizer-based encoding
            # new totalizer sum
            t = ITotalizer(lits=self.rels, ubound=bound, top_id=self.topv)

            # updating top variable id
            self.topv = t.top_id

            # adding its clauses to oracle
            for cl in t.cnf.clauses:
                self.oracle.add_clause(cl)
        else:
            # for minicard, use native cardinality constraints instead of the
            # standard totalizer, i.e. create a new (empty) totalizer sum and
            # fill it with the necessary data supported by minicard
            t = ITotalizer()
            t.lits = self.rels

            self.topv += 1  # a new variable will represent the bound

            # proper initial bound
            t.rhs = [None] * (len(t.lits))
            t.rhs[bound] = self.topv

            # new atmostb constraint instrumented with
            # an implication and represented natively
            rhs = len(t.lits)
            amb = [[-self.topv] * (rhs - bound) + t.lits, rhs]

            # add constraint to the solver
            self.oracle.add_atmost(*amb)

        return t

    def update_sum(self, assump):
        """
            The method is used to increase the bound for a given
            totalizer sum. The totalizer object is identified by the
            input parameter ``assump``, which is an assumption literal
            associated with the totalizer object.

            The method increases the bound for the totalizer sum,
            which involves adding the corresponding new clauses to the
            internal SAT oracle.

            The method returns the totalizer object followed by the
            new bound obtained.

            :param assump: assumption literal associated with the sum
            :type assump: int

            :rtype: :class:`.ITotalizer`, int

            Note that if Minicard is used as a SAT oracle, native
            cardinality constraints are used instead of
            :class:`.ITotalizer`.
        """

        # getting a totalizer object corresponding to assumption
        t = self.tobj[assump]

        # increment the current bound
        b = self.bnds[assump] + 1

        if self.solver != 'mc':  # the case of standard totalizer encoding
            # increasing its bound
            t.increase(ubound=b, top_id=self.topv)

            # updating top variable id
            self.topv = t.top_id

            # adding its clauses to oracle
            if t.nof_new:
                for cl in t.cnf.clauses[-t.nof_new:]:
                    self.oracle.add_clause(cl)
        else:  # the case of cardinality constraints represented natively
            # right-hand side is always equal to the number of input literals
            rhs = len(t.lits)

            if b < rhs:
                # creating an additional bound
                if not t.rhs[b]:
                    self.topv += 1
                    t.rhs[b] = self.topv

                # a new at-most-b constraint
                amb = [[-t.rhs[b]] * (rhs - b) + t.lits, rhs]
                self.oracle.add_atmost(*amb)

        return t, b

    def set_bound(self, tobj, rhs):
        """
            Given a totalizer sum and its right-hand side to be
            enforced, the method creates a new sum assumption literal,
            which will be used in the following SAT oracle calls.

            :param tobj: totalizer sum
            :param rhs: right-hand side

            :type tobj: :class:`.ITotalizer`
            :type rhs: int
        """

        # saving the sum and its weight in a mapping
        self.tobj[-tobj.rhs[rhs]] = tobj
        self.bnds[-tobj.rhs[rhs]] = rhs
        self.wght[-tobj.rhs[rhs]] = self.minw

        # adding a new assumption to force the sum to be at most rhs
        self.sums.append(-tobj.rhs[rhs])

    def filter_assumps(self):
        """
            Filter out unnecessary selectors and sums from the list of
            assumption literals. The corresponding values are also
            removed from the dictionaries of bounds and weights.

            Note that assumptions marked as garbage are collected in
            the core processing methods, i.e. in :func:`process_core`,
            :func:`process_sels`, and :func:`process_sums`.
        """

        self.sels = list(filter(lambda x: x not in self.garbage, self.sels))
        self.sums = list(filter(lambda x: x not in self.garbage, self.sums))

        self.bnds = {l: b for l, b in six.iteritems(self.bnds) if l not in self.garbage}
        self.wght = {l: w for l, w in six.iteritems(self.wght) if l not in self.garbage}

        self.garbage.clear()

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()

    def _map_extlit(self, l):
        """
            Map an external variable to an internal one if necessary.

            This method is used when new clauses are added to the
            formula incrementally, which may result in introducing new
            variables clashing with the previously used *clause
            selectors*. The method makes sure no clash occurs, i.e. it
            maps the original variables used in the new problem
            clauses to the newly introduced auxiliary variables (see
            :func:`add_clause`).

            Given an integer literal, a fresh literal is returned. The
            returned integer has the same sign as the input literal.

            :param l: literal to map
            :type l: int

            :rtype: int
        """

        v = abs(l)

        if v in self.vmap.e2i:
            return int(copysign(self.vmap.e2i[v], l))
        else:
            self.topv += 1

            self.vmap.e2i[v] = self.topv
            self.vmap.i2e[self.topv] = v

            return int(copysign(self.topv, l))


#
#==============================================================================
class RC2Stratified(RC2, object):
    """
        RC2 augmented with BLO and stratification techniques. Although
        class :class:`RC2` can deal with weighted formulas, there are
        situations when it is necessary to apply additional heuristics
        to improve the performance of the solver on weighted MaxSAT
        formulas. This class extends capabilities of :class:`RC2` with
        two heuristics, namely

        1. Boolean lexicographic optimization (BLO) [4]_
        2. stratification [5]_

        There is no way to enable only one of them -- both heuristics
        are applied at the same time. Except for the aforementioned
        additional techniques, every other component of the solver
        remains as in the base class :class:`RC2`. Therefore, a user
        is referred to the documentation of :class:`RC2` for details.
    """

    def __init__(self, formula, solver='g3', adapt=False, exhaust=False,
            incr=False, minz=False, trim=0, verbose=0):
        """
            Constructor.
        """

        # calling the constructor for the basic version
        super(RC2Stratified, self).__init__(formula, solver=solver,
                adapt=adapt, exhaust=exhaust, incr=incr, minz=minz, trim=trim,
                verbose=verbose)

        self.levl = 0   # initial optimization level
        self.blop = []  # a list of blo levels

        # backing up selectors
        self.bckp, self.bckp_set = self.sels, self.sels_set
        self.sels = []

        # initialize Boolean lexicographic optimization
        if sum(self.wght.values()) > len(self.bckp):
            self.init_wstr()

    def init_wstr(self):
        """
            Compute and initialize optimization levels for BLO and
            stratification. This method is invoked once, from the
            constructor of an object of :class:`RC2Stratified`. Given
            the weights of the soft clauses, the method divides the
            MaxSAT problem into several optimization levels.
        """

        # a mapping for stratified problem solving,
        # i.e. from a weight to a list of selectors
        self.wstr = collections.defaultdict(lambda: [])

        for s, w in six.iteritems(self.wght):
            self.wstr[w].append(s)

        # sorted list of distinct weight levels
        self.blop = sorted([w for w in self.wstr], reverse=True)

        # diversity parameter for stratification
        self.sdiv = len(self.blop) / 2.0

    def compute(self):
        """
            This method solves the MaxSAT problem iteratively. Each
            optimization level is tackled the standard way, i.e. by
            calling :func:`compute_`. A new level is started by
            calling :func:`next_level` and finished by calling
            :func:`finish_level`. Each new optimization level
            activates more soft clauses by invoking
            :func:`activate_clauses`.
        """

        done = 0  # levels done

        # first attempt to get an optimization level
        self.next_level()

        while self.levl != None and done < len(self.blop):
            # add more clauses
            done = self.activate_clauses(done)

            if self.verbose > 1:
                print('c wght str:', self.blop[self.levl])

            # call RC2
            if self.compute_() == False:
                return

            # updating the list of distinct weight levels
            self.blop = sorted([w for w in self.wstr], reverse=True)

            if done < len(self.blop):
                if self.verbose > 1:
                    print('c curr opt:', self.cost)

                # done with this level
                self.finish_level()

                self.levl += 1

                # get another level
                self.next_level()

                if self.verbose > 1:
                    print('c')

        # extracting a model
        self.model = self.oracle.get_model()
        self.model = filter(lambda l: abs(l) in self.vmap.i2e, self.model)
        self.model = map(lambda l: int(copysign(self.vmap.i2e[abs(l)], l)), self.model)
        self.model = sorted(self.model, key=lambda l: abs(l))

        return self.model

    def next_level(self):
        """
            Compute the next optimization level (starting from the
            current one). The procedure represents a loop, each
            iteration of which checks whether or not one of the
            conditions holds:

            - partial BLO condition
            - stratification condition

            If any of these holds, the loop stops.
        """

        if self.levl >= len(self.blop):
            self.levl = None

        while self.levl < len(self.blop) - 1:
            # number of selectors with weight less than current weight
            numc = sum([len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

            # sum of their weights
            sumw = sum([w * len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

            # partial BLO
            if self.blop[self.levl] > sumw and sumw != 0:
                break

            # stratification
            if numc / float(len(self.blop) - self.levl - 1) > self.sdiv:
                break

            self.levl += 1

    def activate_clauses(self, beg):
        """
            This method is used for activating the clauses that belong
            to optimization levels up to the newly computed level. It
            also reactivates previously deactivated clauses (see
            :func:`process_sels` and :func:`process_sums` for
            details).
        """

        end = min(self.levl + 1, len(self.blop))

        for l in range(beg, end):
            for sel in self.wstr[self.blop[l]]:
                if sel in self.bckp_set:
                    self.sels.append(sel)
                else:
                    self.sums.append(sel)

        # updating set of selectors
        self.sels_set = set(self.sels)

        return end

    def finish_level(self):
        """
            This method does postprocessing of the current
            optimization level after it is solved. This includes
            *hardening* some of the soft clauses (depending on their
            remaining weights) and also garbage collection.
        """

        # assumptions to remove
        self.garbage = set()

        # sum of weights of the remaining levels
        sumw = sum([w * len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

        # trying to harden selectors and sums
        for s in self.sels + self.sums:
            if self.wght[s] > sumw:
                self.oracle.add_clause([s])
                self.garbage.add(s)

        if self.verbose > 1:
            print('c hardened:', len(self.garbage))

        # remove unnecessary assumptions
        self.filter_assumps()

    def process_am1(self, am1):
        """
            Due to the solving process involving multiple optimization
            levels to be treated individually, new soft clauses for
            the detected intrinsic AtMost1 constraints should be
            remembered. The method is a slightly modified version of
            the base method :func:`RC2.process_am1` taking care of
            this.
        """

        # computing am1's weight
        self.minw = min(map(lambda l: self.wght[l], am1))

        # pretending am1 to be a core, and the bound is its size - 1
        self.core_sels, b = am1, len(am1) - 1

        # incrementing the cost
        self.cost += b * self.minw

        # assumptions to remove
        self.garbage = set()

        # splitting and relaxing if needed
        self.process_sels()

        # new selector
        self.topv += 1
        selv = self.topv

        self.oracle.add_clause([-l for l in self.rels] + [-selv])

        # integrating the new selector
        self.sels.append(selv)
        self.wght[selv] = self.minw
        self.smap[selv] = len(self.wght) - 1

        # do not forget this newly selector!
        self.bckp_set.add(selv)

        # removing unnecessary assumptions
        self.filter_assumps()

    def process_sels(self):
        """
            A redefined version of :func:`RC2.process_sels`. The only
            modification affects the clauses whose weight after
            splitting becomes less than the weight of the current
            optimization level. Such clauses are deactivated and to be
            reactivated at a later stage.
        """

        # new relaxation variables
        self.rels = []

        # selectors that should be deactivated (but not removed completely)
        to_deactivate = set([])

        for l in self.core_sels:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)

                # reuse assumption variable as relaxation
                self.rels.append(-l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # deactivate this assumption and put at a lower level
                if self.wght[l] < self.blop[self.levl]:
                    self.wstr[self.wght[l]].append(l)
                    to_deactivate.add(l)

                # it is an unrelaxed soft clause,
                # a new relaxed copy of which we add to the solver
                self.topv += 1
                self.oracle.add_clause([l, self.topv])
                self.rels.append(self.topv)

        # deactivating unnecessary selectors
        self.sels = list(filter(lambda x: x not in to_deactivate, self.sels))

    def process_sums(self):
        """
            A redefined version of :func:`RC2.process_sums`. The only
            modification affects the clauses whose weight after
            splitting becomes less than the weight of the current
            optimization level. Such clauses are deactivated and to be
            reactivated at a later stage.
        """

        # sums that should be deactivated (but not removed completely)
        to_deactivate = set([])

        for l in self.core_sums:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # deactivate this assumption and put at a lower level
                if self.wght[l] < self.blop[self.levl]:
                    self.wstr[self.wght[l]].append(l)
                    to_deactivate.add(l)

            # increase bound for the sum
            t, b = self.update_sum(l)

            # updating bounds and weights
            if b < len(t.rhs):
                lnew = -t.rhs[b]
                if lnew in self.garbage:
                    self.garbage.remove(lnew)
                    self.wght[lnew] = 0

                if lnew not in self.wght:
                    self.set_bound(t, b)
                else:
                    self.wght[lnew] += self.minw

            # put this assumption to relaxation vars
            self.rels.append(-l)

        # deactivating unnecessary sums
        self.sums = list(filter(lambda x: x not in to_deactivate, self.sums))


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ac:e:hilms:t:vx',
                ['adapt', 'comp=', 'enum=', 'exhaust', 'help', 'incr', 'blo',
                    'minimize', 'solver=', 'trim=', 'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    adapt = False
    exhaust = False
    cmode = None
    to_enum = 1
    incr = False
    blo = False
    minz = False
    solver = 'g3'
    trim = 0
    verbose = 1

    for opt, arg in opts:
        if opt in ('-a', '--adapt'):
            adapt = True
        elif opt in ('-c', '--comp'):
            cmode = str(arg)
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
            else:
                to_enum = 0
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-i', '--incr'):
            incr = True
        elif opt in ('-l', '--blo'):
            blo = True
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

    return adapt, blo, cmode, to_enum, exhaust, incr, minz, solver, trim, \
            verbose, args


#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -a, --adapt              Try to adapt (simplify) input formula')
    print('        -c, --comp=<string>      Enable one of the MSE18 configurations')
    print('                                 Available values: a, b, none (default = none)')
    print('        -e, --enum=<int>         Number of MaxSAT models to compute')
    print('                                 Available values: [1 .. INT_MAX], all (default = 1)')
    print('        -h, --help               Show this message')
    print('        -i, --incr               Use SAT solver incrementally (only for g3 and g4)')
    print('        -l, --blo                Use BLO and stratification')
    print('        -m, --minimize           Use a heuristic unsatisfiable core minimizer')
    print('        -s, --solver=<string>    SAT solver to use')
    print('                                 Available values: g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = g3)')
    print('        -t, --trim=<int>         How many times to trim unsatisfiable cores')
    print('                                 Available values: [0 .. INT_MAX] (default = 0)')
    print('        -v, --verbose            Be verbose')
    print('        -x, --exhaust            Exhaust new unsatisfiable cores')


#
#==============================================================================
if __name__ == '__main__':
    adapt, blo, cmode, to_enum, exhaust, incr, minz, solver, trim, verbose, \
            files = parse_options()

    if files:
        # parsing the input formula
        if re.search('\.wcnf(\.(gz|bz2|lzma|xz))?$', files[0]):
            formula = WCNF(from_file=files[0])
        else:  # expecting '*.cnf'
            formula = CNF(from_file=files[0]).weighted()

        # enabling the competition mode
        if cmode:
            assert cmode in ('a', 'b'), 'Wrong MSE18 mode chosen: {0}'.format(cmode)
            adapt, blo, exhaust, solver, verbose = True, True, True, 'g3', 3

            if cmode == 'a':
                trim = 5 if max(formula.wght) > min(formula.wght) else 0
                minz = False
            else:
                trim, minz = 0, True

            # trying to use unbuffered standard output
            if sys.version_info.major == 2:
                sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

        # deciding whether or not to stratify
        if blo and max(formula.wght) > min(formula.wght):
            assert to_enum == 1, 'Stratified solving is incompatible with model enumeration'
            MXS = RC2Stratified
        else:
            MXS = RC2

        # starting the solver
        with MXS(formula, solver=solver, adapt=adapt, exhaust=exhaust,
                incr=incr, minz=minz, trim=trim, verbose=verbose) as rc2:

            optimum_found = False
            for i, model in enumerate(rc2.enumerate(), 1):
                optimum_found = True

                if verbose:
                    if i == 1:
                        print('s OPTIMUM FOUND')
                        print('o {0}'.format(rc2.cost))

                    if verbose > 2:
                        print('v', ' '.join([str(l) for l in model]))

                if i == to_enum:
                    break

            if verbose:
                if not optimum_found:
                    print('s UNSATISFIABLE')
                elif to_enum != 1:
                    print('c models found:', i)

                if verbose > 1:
                    print('c oracle time: {0:.4f}'.format(rc2.oracle_time()))
