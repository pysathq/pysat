#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## lbx.py
##
##  Created on: Jan 9, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        LBX
        LBXPlus

    ==================
    Module description
    ==================

    This module implements a prototype of the LBX algorithm for the computation
    of a *minimal correction subset* (MCS) and/or MCS enumeration. The LBX
    abbreviation stands for *literal-based MCS extraction* algorithm, which was
    proposed in [1]_. Note that this prototype does not follow the original
    low-level implementation of the corresponding MCS extractor available
    `online <https://reason.di.fc.ul.pt/wiki/doku.php?id=lbx>`_ (compared to
    our prototype, the low-level implementation has a number of additional
    heuristics used). However, it implements the LBX algorithm for partial
    MaxSAT formulas, as described in [1]_.

    .. [1] Carlos Mencia, Alessandro Previti, Joao Marques-Silva.
        *Literal-Based MCS Extraction*. IJCAI 2015. pp. 1973-1979

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``lbx.py -h``) in the following
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

        $ lbx.py -d -e all -s glucose3 -vv formula.wcnf.xz
        c MCS: 1 3 0
        c cost: 2
        c MCS: 2 3 0
        c cost: 2
        c MCS: 1 2 0
        c cost: 2
        c oracle time: 0.0002

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.lbx import LBX
        >>> from pysat.formula import WCNF
        >>>
        >>> wcnf = WCNF(from_file='formula.wcnf.xz')
        >>>
        >>> lbx = LBX(wcnf, use_cld=True, solver_name='g3')
        >>> for mcs in lbx.enumerate():
        ...     lbx.block(mcs)
        ...     print mcs
        [1, 3]
        [2, 3]
        [1, 2]

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import collections
import getopt
from math import copysign
import os
from pysat.formula import CNF, WCNF, WCNFPlus
from pysat.solvers import Solver
import re
from six.moves import range
import sys


#
#==============================================================================
class LBX(object):
    """
        LBX-like algorithm for computing MCSes. Given an unsatisfiable partial
        CNF formula, i.e. formula in the :class:`.WCNF` format, this class can
        be used to compute a given number of MCSes of the formula. The
        implementation follows the LBX algorithm description in [1]_. It can
        use any SAT solver available in PySAT. Additionally, the "clause
        :math:`D`" heuristic can be used when enumerating MCSes.

        The default SAT solver to use is ``m22`` (see :class:`.SolverNames`).
        The "clause :math:`D`" heuristic is disabled by default, i.e.
        ``use_cld`` is set to ``False``. Internal SAT solver's timer is also
        disabled by default, i.e. ``use_timer`` is ``False``.

        :param formula: unsatisfiable partial CNF formula
        :param use_cld: whether or not to use "clause :math:`D`"
        :param solver_name: SAT oracle name
        :param use_timer: whether or not to use SAT solver's timer

        :type formula: :class:`.WCNF`
        :type use_cld: bool
        :type solver_name: str
        :type use_timer: bool
    """

    def __init__(self, formula, use_cld=False, solver_name='m22', use_timer=False):
        """
            Constructor.
        """

        # bootstrapping the solver with hard clauses
        self.oracle = Solver(name=solver_name, bootstrap_with=formula.hard,
                use_timer=use_timer)

        self.topv = formula.nv  # top variable id
        self.soft = formula.soft
        self.sels = []
        self.ucld = use_cld

        # mappings between internal and external variables
        VariableMap = collections.namedtuple('VariableMap', ['e2i', 'i2e'])
        self.vmap = VariableMap(e2i={}, i2e={})

        # at this point internal and external variables are the same
        for v in range(1, formula.nv + 1):
            self.vmap.e2i[v] = v
            self.vmap.i2e[v] = v

        for cl in self.soft:
            sel = cl[0]
            if len(cl) > 1 or cl[0] < 0:
                self.topv += 1
                sel = self.topv

                self.oracle.add_clause(cl + [-sel])

            self.sels.append(sel)

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

    def add_clause(self, clause, soft=False):
        """
            The method for adding a new hard of soft clause to the problem
            formula. Although the input formula is to be specified as an
            argument of the constructor of :class:`LBX`, adding clauses may be
            helpful when *enumerating* MCSes of the formula. This way, the
            clauses are added incrementally, i.e. *on the fly*.

            The clause to add can be any iterable over integer literals. The
            additional Boolean parameter ``soft`` can be set to ``True``
            meaning the the clause being added is soft (note that parameter
            ``soft`` is set to ``False`` by default).

            :param clause: a clause to add
            :param soft: whether or not the clause is soft

            :type clause: iterable(int)
            :type soft: bool
        """

        # first, map external literals to internal literals
        # introduce new variables if necessary
        cl = list(map(lambda l: self._map_extlit(l), clause))

        if not soft:
            # the clause is hard, and so we simply add it to the SAT oracle
            self.oracle.add_clause(cl)
        else:
            self.soft.append(cl)

            # soft clauses should be augmented with a selector
            sel = cl[0]
            if len(cl) > 1 or cl[0] < 0:
                self.topv += 1
                sel = self.topv

                self.oracle.add_clause(cl + [-sel])

            self.sels.append(sel)

    def compute(self):
        """
            Compute and return one solution. This method checks whether the
            hard part of the formula is satisfiable, i.e. an MCS can be
            extracted. If the formula is satisfiable, the model computed by the
            SAT call is used as an *over-approximation* of the MCS in the
            method :func:`_compute` invoked here, which implements the LBX
            algorithm.

            An MCS is reported as a list of integers, each representing a soft
            clause index (the smallest index is ``1``).

            :rtype: list(int)
        """

        self.setd = []
        self.satc = [False for cl in self.soft]  # satisfied clauses
        self.solution = None
        self.bb_assumps = []  # backbone assumptions
        self.ss_assumps = []  # satisfied soft clause assumptions

        if self.oracle.solve():
            # hard part is satisfiable => there is a solution
            self._filter_satisfied(update_setd=True)
            self._compute()

            self.solution = list(map(lambda i: i + 1, filter(lambda i: not self.satc[i], range(len(self.soft)))))

        return self.solution

    def enumerate(self):
        """
            This method iterates through MCSes enumerating them until the
            formula has no more MCSes. The method iteratively invokes
            :func:`compute`. Note that the method does not block the MCSes
            computed - this should be explicitly done by a user.
        """

        done = False
        while not done:
            mcs = self.compute()

            if mcs != None:
                yield mcs
            else:
                done = True

    def block(self, mcs):
        """
            Block a (previously computed) MCS. The MCS should be given as an
            iterable of integers. Note that this method is not automatically
            invoked from :func:`enumerate` because a user may want to block
            some of the MCSes conditionally depending on the needs. For
            example, one may want to compute disjoint MCSes only in which case
            this standard blocking is not appropriate.

            :param mcs: an MCS to block
            :type mcs: iterable(int)
        """

        self.oracle.add_clause([self.sels[cl_id - 1] for cl_id in mcs])

    def _satisfied(self, cl, model):
        """
            Given a clause (as an iterable of integers) and an assignment (as a
            list of integers), this method checks whether or not the assignment
            satisfies the clause. This is done by a simple clause traversal.
            The method is invoked from :func:`_filter_satisfied`.

            :param cl: a clause to check
            :param model: an assignment

            :type cl: iterable(int)
            :type model: list(int)

            :rtype: bool
        """

        for l in cl:
            if len(model) < abs(l) or model[abs(l) - 1] == l:
                # either literal is unassigned or satisfied by the model
                return True

        return False

    def _filter_satisfied(self, update_setd=False):
        """
            This method extracts a model provided by the previous call to a SAT
            oracle and iterates over all soft clauses checking if each of is
            satisfied by the model. Satisfied clauses are marked accordingly
            while the literals of the unsatisfied clauses are kept in a list
            called ``setd``, which is then used to refine the correction set
            (see :func:`_compute`, and :func:`do_cld_check`).

            Optional Boolean parameter ``update_setd`` enforces the method to
            update variable ``self.setd``. If this parameter is set to
            ``False``, the method only updates the list of satisfied clauses,
            which is an under-approximation of a *maximal satisfiable subset*
            (MSS).

            :param update_setd: whether or not to update setd
            :type update_setd: bool
        """

        model = self.oracle.get_model()
        setd = set()

        for i, cl in enumerate(self.soft):
            if not self.satc[i]:
                if self._satisfied(cl, model):
                    self.satc[i] = True
                    self.ss_assumps.append(self.sels[i])
                else:
                    setd = setd.union(set(cl))

        if update_setd:
            self.setd = list(setd)

    def _compute(self):
        """
            The main method of the class, which computes an MCS given its
            over-approximation. The over-approximation is defined by a model
            for the hard part of the formula obtained in :func:`compute`.

            The method is essentially a simple loop going over all literals
            unsatisfied by the previous model, i.e. the literals of
            ``self.setd`` and checking which literals can be satisfied. This
            process can be seen a refinement of the over-approximation of the
            MCS. The algorithm follows the pseudo-code of the LBX algorithm
            presented in [1]_.

            Additionally, if :class:`LBX` was constructed with the requirement
            to make "clause :math:`D`" calls, the method calls
            :func:`do_cld_check` at every iteration of the loop using the
            literals of ``self.setd`` not yet checked, as the contents of
            "clause :math:`D`".
        """

        # unless clause D checks are used, test one literal at a time
        # and add it either to satisfied of backbone assumptions
        i = 0
        while i < len(self.setd):
            if self.ucld:
                self.do_cld_check(self.setd[i:])
                i = 0

            if self.setd:  # if may be empty after the clause D check
                if self.oracle.solve(assumptions=self.ss_assumps + self.bb_assumps + [self.setd[i]]):
                    # filtering satisfied clauses
                    self._filter_satisfied()
                else:
                    # current literal is backbone
                    self.bb_assumps.append(-self.setd[i])

            i += 1

    def do_cld_check(self, cld):
        """
            Do the "clause :math:`D`" check. This method receives a list of
            literals, which serves a "clause :math:`D`" [2]_, and checks
            whether the formula conjoined with :math:`D` is satisfiable.

            .. [2] Joao Marques-Silva, Federico Heras, Mikolas Janota,
                Alessandro Previti, Anton Belov. *On Computing Minimal
                Correction Subsets*. IJCAI 2013. pp. 615-622

            If clause :math:`D` cannot be satisfied together with the formula,
            then negations of all of its literals are backbones of the formula
            and the LBX algorithm can stop. Otherwise, the literals satisfied
            by the new model refine the MCS further.

            Every time the method is called, a new fresh selector variable
            :math:`s` is introduced, which augments the current clause
            :math:`D`. The SAT oracle then checks if clause :math:`(D \\vee
            \\neg{s})` can be satisfied together with the internal formula.
            The :math:`D` clause is then disabled by adding a hard clause
            :math:`(\\neg{s})`.

            :param cld: clause :math:`D` to check
            :type cld: list(int)
        """

        # adding a selector literal to clause D
        # selector literals for clauses D currently
        # cannot be reused, but this may change later
        self.topv += 1
        sel = self.topv
        cld.append(-sel)

        # adding clause D
        self.oracle.add_clause(cld)

        if self.oracle.solve(assumptions=self.ss_assumps + self.bb_assumps + [sel]):
            # filtering satisfied
            self._filter_satisfied(update_setd=True)
        else:
            # clause D is unsatisfiable => all literals are backbones
            self.bb_assumps.extend([-l for l in cld[:-1]])
            self.setd = []

        # deactivating clause D
        self.oracle.add_clause([-sel])

    def _map_extlit(self, l):
        """
            Map an external variable to an internal one if necessary.

            This method is used when new clauses are added to the formula
            incrementally, which may result in introducing new variables
            clashing with the previously used *clause selectors*. The method
            makes sure no clash occurs, i.e. it maps the original variables
            used in the new problem clauses to the newly introduced auxiliary
            variables (see :func:`add_clause`).

            Given an integer literal, a fresh literal is returned. The returned
            integer has the same sign as the input literal.

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

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()


#
#==============================================================================
class LBXPlus(LBX, object):
    """
        LBX-like algorithm extended for :class:`.WCNFPlus` formulas (using
        Minicard).
    """

    def __init__(self, formula, use_cld=False, solver_name=None, use_timer=False):
        """
            Constructor.
        """

        super(LBXPlus, self).__init__(formula, use_cld=use_cld,
                solver_name='mc', use_timer=use_timer)

        # adding atmost constraints
        for am in formula.atms:
            self.oracle.add_atmost(*am)


#
#==============================================================================
def parse_options():
    """
        Parses command-line options.
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'de:hs:v',
                                   ['dcalls',
                                    'enum=',
                                    'help',
                                    'solver=',
                                    'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize() + '\n')
        usage()
        sys.exit(1)

    dcalls = False
    to_enum = 1
    solver = 'm22'
    verbose = 0

    for opt, arg in opts:
        if opt in ('-d', '--dcalls'):
            dcalls = True
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return dcalls, to_enum, solver, verbose, args


#
#==============================================================================
def usage():
    """
        Prints help message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] file')
    print('Options:')
    print('        -d, --dcalls           Try to bootstrap algorithm')
    print('        -e, --enum=<string>    How many solutions to compute')
    print('                               Available values: [1 .. all] (default: 1)')
    print('        -h, --help')
    print('        -s, --solver           SAT solver to use')
    print('                               Available values: g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = m22)')
    print('        -v, --verbose          Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    dcalls, to_enum, solver, verbose, files = parse_options()

    if type(to_enum) == str:
        to_enum = 0

    if files:
        # reading standard CNF or WCNF
        if re.search('cnf(\.(gz|bz2|lzma|xz))?$', files[0]):
            if re.search('\.wcnf(\.(gz|bz2|lzma|xz))?$', files[0]):
                formula = WCNF(from_file=files[0])
            else:  # expecting '*.cnf'
                formula = CNF(from_file=files[0]).weighted()

            MCSEnum = LBX

        # reading WCNF+
        elif re.search('\.wcnf[p,+](\.(gz|bz2|lzma|xz))?$', files[0]):
            formula = WCNFPlus(from_file=files[0])
            MCSEnum = LBXPlus

        with MCSEnum(formula, use_cld=dcalls, solver_name=solver, use_timer=True) as mcsls:
            for i, mcs in enumerate(mcsls.enumerate()):
                if verbose:
                    print('c MCS:', ' '.join([str(cl_id) for cl_id in mcs]), '0')

                    if verbose > 1:
                        cost = sum([formula.wght[cl_id - 1] for cl_id in mcs])
                        print('c cost:', cost)

                if to_enum and i + 1 == to_enum:
                    break

                mcsls.block(mcs)

            print('c oracle time: {0:.4f}'.format(mcsls.oracle_time()))
