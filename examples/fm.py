#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## fm.py
##
##  Created on: Feb 5, 2018
##      Author: Antonio Morgado, Alexey Ignatiev
##      E-mail: {ajmorgado, aignatiev}@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        FM

    ==================
    Module description
    ==================

    This module implements a variant of the seminal core-guided MaxSAT
    algorithm originally proposed by [1]_ and then improved and modified
    further in [2]_ [3]_ [4]_ [5]_. Namely, the implementation follows the
    WMSU1 variant [5]_ of the algorithm extended to the case of *weighted
    partial* formulas.

    .. [1] Zhaohui Fu, Sharad Malik. *On Solving the Partial MAX-SAT Problem*.
        SAT 2006. pp. 252-265

    .. [2] Joao Marques-Silva, Jordi Planes. *On Using Unsatisfiability for
        Solving Maximum Satisfiability*. CoRR abs/0712.1097. 2007

    .. [3] Joao Marques-Silva, Vasco M. Manquinho. *Towards More Effective
        Unsatisfiability-Based Maximum Satisfiability Algorithms*. SAT 2008.
        pp. 225-230

    .. [4] Carlos Ansótegui, Maria Luisa Bonet, Jordi Levy. *Solving
        (Weighted) Partial MaxSAT through Satisfiability Testing*. SAT 2009.
        pp. 427-440

    .. [5] Vasco M. Manquinho, Joao Marques Silva, Jordi Planes. *Algorithms
        for Weighted Boolean Optimization*. SAT 2009. pp. 495-508

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``fm.py -h``) in the following way:

    ::

        $ xzcat formula.wcnf.xz
        p wcnf 3 6 4
        1 1 0
        1 2 0
        1 3 0
        4 -1 -2 0
        4 -1 -3 0
        4 -2 -3 0

        $ fm.py -c cardn -s glucose3 -vv formula.wcnf.xz
        c cost: 1; core sz: 2
        c cost: 2; core sz: 3
        s OPTIMUM FOUND
        o 2
        v -1 -2 3 0
        c oracle time: 0.0001

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.fm import FM
        >>> from pysat.formula import WCNF
        >>>
        >>> wcnf = WCNF(from_file='formula.wcnf.xz')
        >>>
        >>> fm = FM(wcnf, verbose=0)
        >>> fm.compute()  # set of hard clauses should be satisfiable
        True
        >>> print(fm.cost) # cost of MaxSAT solution should be 2
        >>> 2
        >>> print(fm.model)
        [-1, -2, 3]

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import copy
import getopt
import gzip
import os
from pysat.formula import CNFPlus, WCNFPlus
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver, SolverNames
import re
from six.moves import range
import sys


# cardinality encodings
#==============================================================================
encmap = {
    'pw': EncType.pairwise,
    'bw': EncType.bitwise,
    'seqc': EncType.seqcounter,
    'cardn': EncType.cardnetwrk,
    'sortn': EncType.sortnetwrk,
    'ladder': EncType.ladder,
    'tot': EncType.totalizer,
    'mtot': EncType.mtotalizer,
    'kmtot': EncType.kmtotalizer,
    'native': EncType.native
}


#
#==============================================================================
class FM(object):
    """
        A non-incremental implementation of the FM (Fu&Malik, or WMSU1)
        algorithm. The algorithm (see details in [5]_) is *core-guided*, i.e.
        it solves maximum satisfiability with a series of unsatisfiability
        oracle calls, each producing an unsatisfiable core. The clauses
        involved in an unsatisfiable core are *relaxed* and a new
        :math:`\\textsf{AtMost1}` constraint on the corresponding *relaxation
        variables* is added to the formula. The process gets a bit more
        sophisticated in the case of weighted formulas because of the *clause
        weight splitting* technique.

        The constructor of :class:`FM` objects receives a target :class:`.WCNF`
        MaxSAT formula, an identifier of the cardinality encoding to use, a SAT
        solver name, and a verbosity level. Note that the algorithm uses the
        ``pairwise`` (see :class:`.card.EncType`) cardinality encoding by
        default, while the default SAT solver is MiniSat22 (referred to as
        ``'m22'``, see :class:`.SolverNames` for details). The default
        verbosity level is ``1``.

        :param formula: input MaxSAT formula
        :param enc: cardinality encoding to use
        :param solver: name of SAT solver
        :param verbose: verbosity level

        :type formula: :class:`.WCNF`
        :type enc: int
        :type solver: str
        :type verbose: int
    """

    def __init__(self, formula, enc=EncType.pairwise, solver='m22', verbose=1):
        """
            Constructor.
        """

        # saving verbosity level
        self.verbose = verbose
        self.solver = solver
        self.time = 0.0

        # MaxSAT related stuff
        self.topv = self.orig_nv = formula.nv
        self.hard = copy.deepcopy(formula.hard)
        self.soft = copy.deepcopy(formula.soft)
        self.atm1 = copy.deepcopy(formula.atms)
        self.wght = formula.wght[:]
        self.cenc = enc
        self.cost = 0

        # initialize SAT oracle with hard clauses only
        self.init(with_soft=False)

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

    def init(self, with_soft=True):
        """
            The method for the SAT oracle initialization. Since the oracle is
            is used non-incrementally, it is reinitialized at every iteration
            of the MaxSAT algorithm (see :func:`reinit`). An input parameter
            ``with_soft`` (``False`` by default) regulates whether or not the
            formula's soft clauses are copied to the oracle.

            :param with_soft: copy formula's soft clauses to the oracle or not
            :type with_soft: bool
        """

        self.oracle = Solver(name=self.solver, bootstrap_with=self.hard, use_timer=True)

        if self.atm1:  # this check is needed at the beggining (before iteration 1)
            assert self.solver in SolverNames.minicard, \
                    'Only Minicard supports native cardinality constraints. Make sure you use the right type of formula.'

            # self.atm1 is not empty only in case of minicard
            for am in self.atm1:
                self.oracle.add_atmost(*am)

        if with_soft:
            for cl, cpy in zip(self.soft, self.scpy):
                if cpy:
                    self.oracle.add_clause(cl)

    def delete(self):
        """
            Explicit destructor of the internal SAT oracle.
        """

        if self.oracle:
            self.time += self.oracle.time_accum()  # keep SAT solving time

            self.oracle.delete()
            self.oracle = None

    def reinit(self):
        """
            This method calls :func:`delete` and :func:`init` to reinitialize
            the internal SAT oracle. This is done at every iteration of the
            MaxSAT algorithm.
        """

        self.delete()
        self.init();

    def compute(self):
        """
            Compute a MaxSAT solution. First, the method checks whether or
            not the set of hard clauses is satisfiable. If not, the method
            returns ``False``. Otherwise, add soft clauses to the oracle and
            call the MaxSAT algorithm (see :func:`_compute`).

            Note that the soft clauses are added to the oracles after being
            augmented with additional *selector* literals. The selectors
            literals are then used as *assumptions* when calling the SAT oracle
            and are needed for extracting unsatisfiable cores.
        """

        if self.oracle.solve():
            # hard part is satisfiable
            # create selectors and a mapping from selectors to clause ids
            self.sels, self.vmap = [], {}
            self.scpy = [True for cl in self.soft]

            # adding soft clauses to oracle
            for i in range(len(self.soft)):
                self.topv += 1

                self.soft[i].append(-self.topv)
                self.sels.append(self.topv)
                self.oracle.add_clause(self.soft[i])

                self.vmap[self.topv] = i

            self._compute()
            return True
        else:
            return False

    def _compute(self):
        """
            This method implements WMSU1 algorithm. The method is essentially a
            loop, which at each iteration calls the SAT oracle to decide
            whether the working formula is satisfiable. If it is, the method
            derives a model (stored in variable ``self.model``) and returns.
            Otherwise, a new unsatisfiable core of the formula is extracted
            and processed (see :func:`treat_core`), and the algorithm proceeds.
        """

        while True:
            if self.oracle.solve(assumptions=self.sels):
                self.model = self.oracle.get_model()
                self.model = filter(lambda l: abs(l) <= self.orig_nv, self.model)
                return
            else:
                self.treat_core()

                if self.verbose > 1:
                    print('c cost: {0}; core sz: {1}'.format(self.cost, len(self.core)))

                self.reinit()

    def treat_core(self):
        """
            Now that the previous SAT call returned UNSAT, a new unsatisfiable
            core should be extracted and relaxed. Core extraction is done
            through a call to the :func:`pysat.solvers.Solver.get_core` method,
            which returns a subset of the selector literals deemed responsible
            for unsatisfiability.

            After the core is extracted, its *minimum weight* ``minw`` is
            computed, i.e. it is the minimum weight among the weights of all
            soft clauses involved in the core (see [5]_). Note that the cost of
            the MaxSAT solution is incremented by ``minw``.

            Clauses that have weight larger than ``minw`` are split (see
            :func:`split_core`). Afterwards, all clauses of the unsatisfiable
            core are relaxed (see :func:`relax_core`).
        """

        # extracting the core
        self.core = [self.vmap[sel] for sel in self.oracle.get_core()]
        minw = min(map(lambda i: self.wght[i], self.core))

        # updating the cost
        self.cost += minw

        # splitting clauses in the core if necessary
        self.split_core(minw)

        # relaxing clauses in the core and adding a new atmost1 constraint
        self.relax_core()

    def split_core(self, minw):
        """
            Split clauses in the core whenever necessary.

            Given a list of soft clauses in an unsatisfiable core, the method
            is used for splitting clauses whose weights are greater than the
            minimum weight of the core, i.e. the ``minw`` value computed in
            :func:`treat_core`. Each clause :math:`(c\\vee\\neg{s},w)`, s.t.
            :math:`w>minw` and :math:`s` is its selector literal, is split into
            clauses (1) clause :math:`(c\\vee\\neg{s}, minw)` and (2) a
            residual clause :math:`(c\\vee\\neg{s}',w-minw)`. Note that the
            residual clause has a fresh selector literal :math:`s'` different
            from :math:`s`.

            :param minw: minimum weight of the core
            :type minw: int
        """

        for clid in self.core:
            sel = self.sels[clid]

            if self.wght[clid] > minw:
                self.topv += 1

                cl_new = []
                for l in self.soft[clid]:
                    if l != -sel:
                        cl_new.append(l)
                    else:
                        cl_new.append(-self.topv)

                self.sels.append(self.topv)
                self.vmap[self.topv] = len(self.soft)

                self.soft.append(cl_new)
                self.wght.append(self.wght[clid] - minw)
                self.wght[clid] = minw

                self.scpy.append(True)

    def relax_core(self):
        """
            Relax and bound the core.

            After unsatisfiable core splitting, this method is called. If the
            core contains only one clause, i.e. this clause cannot be satisfied
            together with the hard clauses of the formula, the formula gets
            augmented with the negation of the clause (see
            :func:`remove_unit_core`).

            Otherwise (if the core contains more than one clause), every clause
            :math:`c` of the core is *relaxed*. This means a new *relaxation
            literal* is added to the clause, i.e. :math:`c\gets c\\vee r`,
            where :math:`r` is a fresh (unused) relaxation variable. After the
            clauses get relaxed, a new cardinality encoding is added to the
            formula enforcing the sum of the new relaxation variables to be not
            greater than 1, :math:`\sum_{c\in\phi}{r\leq 1}`, where
            :math:`\phi` denotes the unsatisfiable core.
        """

        if len(self.core) > 1:
            # relaxing
            rels = []

            for clid in self.core:
                self.topv += 1
                rels.append(self.topv)
                self.soft[clid].append(self.topv)

            # creating a new cardinality constraint
            am1 = CardEnc.atmost(lits=rels, top_id=self.topv, encoding=self.cenc)

            for cl in am1.clauses:
                self.hard.append(cl)

            # only if minicard
            # (for other solvers am1.atmosts should be empty)
            for am in am1.atmosts:
                self.atm1.append(am)

            self.topv = am1.nv

        elif len(self.core) == 1:  # unit core => simply negate the clause
            self.remove_unit_core()

    def remove_unit_core(self):
        """
            If an unsatisfiable core contains only one clause :math:`c`, this
            method is invoked to add a bunch of new unit size hard clauses. As
            a result, the SAT oracle gets unit clauses :math:`(\\neg{l})` for
            all literals :math:`l` in clause :math:`c`.
        """

        self.scpy[self.core[0]] = False

        for l in self.soft[self.core[0]]:
            self.hard.append([-l])

    def oracle_time(self):
        """
            Method for calculating and reporting the total SAT solving time.
        """

        self.time += self.oracle.time_accum()  # include time of the last SAT call
        return self.time


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hs:c:v', ['help','solver=','cardenc=','verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    solver = 'm22'
    cardenc = 'seqc'
    verbose = 1

    for opt, arg in opts:
        if opt in ('-c', '--cardenc'):
            cardenc = str(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    cardenc = encmap[cardenc]

    # using minicard's native implementation of AtMost1 constraints
    if solver in SolverNames.minicard:
        cardenc = encmap['native']
    else:
        assert cardenc != encmap['native'], 'Only Minicard can handle cardinality constraints natively'

    return solver, cardenc, verbose, args


#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -c, --cardenc    Cardinality encoding to use:')
    print('                         Available values: bw, cardn, kmtot, ladder, mtot, pw, seqc, sortn, tot (default = seqc)')
    print('        -h, --help')
    print('        -s, --solver     SAT solver to use')
    print('                         Available values: g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = m22)')
    print('        -v, --verbose    Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    solver, cardenc, verbose, files = parse_options()

    if files:
        # parsing the input formula
        if re.search('\.wcnf[p|+]?(\.(gz|bz2|lzma|xz))?$', files[0]):
            formula = WCNFPlus(from_file=files[0])
        else:  # expecting '*.cnf[,p,+].*'
            formula = CNFPlus(from_file=files[0]).weighted()

        with FM(formula, solver=solver, enc=cardenc, verbose=verbose) as fm:
            res = fm.compute()

            if res:
                print('s OPTIMUM FOUND')
                print('o {0}'.format(fm.cost))

                if verbose > 2:
                    print('v', ' '.join([str(l) for l in fm.model]), '0')
            else:
                print('s UNSATISFIABLE')

            if verbose > 1:
                print('c oracle time: {0:.4f}'.format(fm.oracle_time()))
