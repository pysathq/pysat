#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## rc2.py
##
##      Python-based implementation of the OLLITI algorithm described in:
##      1. A. Morgado, J. Marques-Silva. CP 2014
##      2. A. Morgado, A. Ignatiev, J. Marques-Silva. JSAT 2015
##      This implementation roughly follows the one of MSCG15.
##
##  Created on: Dec 2, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import gzip
import itertools
import os
from pysat.formula import CNF, WCNF
from pysat.card import ITotalizer
from pysat.solvers import Solver
import six
from six.moves import range
import sys


#
#==============================================================================
class RC2(object):
    """
        MaxSAT algorithm based on relaxable cardinality constraints (RC2/OLL).
    """

    def __init__(self, formula, solver='m22', incr=False, verbose=0):
        """
            Constructor.
        """

        # saving verbosity level
        self.verbose = verbose
        self.solver = solver

        # clause selectors and mapping from selectors to clause ids
        self.sels, self.vmap = [], {}

        # other MaxSAT related stuff
        self.topv = self.orig_nv = formula.nv
        self.wght = {}  # weights of soft clauses
        self.sums = []  # totalizer sum assumptions
        self.bnds = {}  # a mapping from sum assumptions to totalizer bounds
        self.tobj = {}  # a mapping from sum assumptions to totalizer objects
        self.cost = 0

        # initialize SAT oracle with hard clauses only
        self.init(formula, incr=incr)

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
            Initialize the SAT solver.
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
                self.vmap[selv] = i
            else:
                # selector is not new; increment its weight
                self.wght[selv] += formula.wght[i]

        self.sels_set = set(self.sels)

    def delete(self):
        """
            Explicit destructor.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

            for t in six.itervalues(self.tobj):
                t.delete()

    def compute(self):
        """
            Compute and return a solution.
        """

        while not self.oracle.solve(assumptions=self.sels + self.sums):
            self.get_core()

            if not self.core:
                # core is empty, i.e. hard part is unsatisfiable
                print('s UNSATISFIABLE')
                return

            self.process_core()

            if self.verbose:
                print('c cost: {0}; core sz: {1}; soft sz: {2}'.format(self.cost,
                    len(self.core), len(self.sels) + len(self.sums)))

        print('s OPTIMUM FOUND')
        print('o {0}'.format(self.cost))

        if self.verbose > 1:
            model = self.oracle.get_model()
            model = filter(lambda l: abs(l) <= self.orig_nv, model)
            print('v', ' '.join([str(l) for l in model]), '0')

    def get_core(self):
        """
            Extract unsatisfiable core.
        """

        # extracting the core
        self.core = self.oracle.get_core()
        self.minw = min(map(lambda l: self.wght[l], self.core))

        # dividing the core into two parts
        iter1, iter2 = itertools.tee(self.core)
        self.core_sels = list(l for l in iter1 if l in self.sels_set)
        self.core_sums = list(l for l in iter2 if l not in self.sels_set)

    def process_core(self):
        """
            Deal with a core found in the main loop.
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

            # create a new cardunality constraint
            if len(self.rels) > 1:
                self.create_sum()
        else:
            # unit cores are treated differently
            # (their negation is added to the hard part)
            self.oracle.add_clause([-self.core_sels[0]])
            self.garbage.add(self.core_sels[0])

        # remove unnecessary assumptions
        self.filter_assumps()

    def process_sels(self):
        """
            Process soft clause selectors participating in a new core.
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
                    self.sums.append(lnew)
                    self.wght[lnew] = self.minw
                    self.tobj[lnew] = t
                    self.bnds[lnew] = b
                else:
                    self.wght[lnew] += self.minw

            # put this assumption to relaxation vars
            self.rels.append(-l)

    def create_sum(self):
        """
            Create a totalizer object encoding a new cardinality constraint.
        """

        # new totalizer sum
        t = ITotalizer(lits=self.rels, top_id=self.topv)

        # updating top variable id
        self.topv = t.top_id

        # adding a new assumption to force the sum to be at most 1
        self.sums.append(-t.rhs[1])

        # saving the totalizer object in a mapping and its weight
        self.tobj[-t.rhs[1]] = t
        self.bnds[-t.rhs[1]] = 1
        self.wght[-t.rhs[1]] = self.minw

        # adding its clauses to oracle
        for cl in t.cnf.clauses:
            self.oracle.add_clause(cl)

        return t

    def update_sum(self, assump):
        """
            Increase the bound for a given totalizer object.
        """

        # getting a totalizer object corresponding to assumption
        t = self.tobj[assump]

        # increment the current bound
        b = self.bnds[assump] + 1

        # increasing its bound
        t.increase(ubound=b, top_id=self.topv)

        # updating top variable id
        self.topv = t.top_id

        # adding its clauses to oracle
        if t.nof_new:
            for cl in t.cnf.clauses[-t.nof_new:]:
                self.oracle.add_clause(cl)

        return t, b

    def filter_assumps(self):
        """
            Filter out both unnecessary selectors and sums.
        """

        self.sels = filter(lambda x: x not in self.garbage, self.sels)
        self.sums = filter(lambda x: x not in self.garbage, self.sums)

        self.bnds = {l: b for l, b in six.iteritems(self.bnds) if l not in self.garbage}
        self.wght = {l: w for l, w in six.iteritems(self.wght) if l not in self.garbage}

        self.garbage.clear()

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'his:v',
                ['help', 'incr', 'solver=', 'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    incr = False
    solver = 'm22'
    verbose = 0

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-i', '--incr'):
            incr = True
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return incr, solver, verbose, args


#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -h, --help')
    print('        -i, --incr       Use SAT solver incrementally (only for g3 and g4)')
    print('        -s, --solver     SAT solver to use')
    print('                         Available values: g3, g4, lgl, m22, mgh (default = m22)')
    print('        -v, --verbose    Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    incr, solver, verbose, files = parse_options()

    if files:
        if files[0].endswith('.gz'):
            fp = gzip.open(files[0], 'rt')
            ftype = 'WCNF' if files[0].endswith('.wcnf.gz') else 'CNF'
        else:
            fp = open(files[0], 'r')
            ftype = 'WCNF' if files[0].endswith('.wcnf') else 'CNF'

        if ftype == 'WCNF':
            formula = WCNF(from_fp=fp)
        else:  # expecting '*.cnf'
            formula = CNF(from_fp=fp).weighted()

        fp.close()

        with RC2(formula, solver=solver, incr=incr, verbose=verbose) as rc2:
            rc2.compute()

            print('c oracle time: {0:.4f}'.format(rc2.oracle_time()))
