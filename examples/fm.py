#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## fm.py
##
##  Created on: Feb 5, 2018
##      Author: Antonio Morgado, Alexey Ignatiev
##      E-mail: {ajmorgado, aignatiev}@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import gzip
import os
from pysat.formula import CNF, WCNF
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver
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
        Algorithm FM - FU & Malik - MSU1.
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
        self.hard = formula.hard
        self.soft = formula.soft
        self.atm1 = []
        self.wght = formula.wght
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
            Initialize the SAT solver.
        """

        self.oracle = Solver(name=self.solver, bootstrap_with=self.hard, use_timer=True)

        # self.atm1 is not empty only in case of minicard
        for am in self.atm1:
            self.oracle.add_atmost(*am)

        if with_soft:
            for cl, cpy in zip(self.soft, self.scpy):
                if cpy:
                    self.oracle.add_clause(cl)

    def delete(self):
        """
            Explicit destructor.
        """

        if self.oracle:
            self.time += self.oracle.time_accum()  # keep SAT solving time

            self.oracle.delete()
            self.oracle = None

    def reinit(self):
        """
            Delete and create a new SAT solver.
        """

        self.delete()
        self.init();

    def compute(self):
        """
            Compute and return a solution.
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
        else:
            print('s UNSATISFIABLE')

    def _compute(self):
        """
            Compute and return a solution.
        """

        while True:
            if self.oracle.solve(assumptions=self.sels):
                print('s OPTIMUM FOUND')
                print('o {0}'.format(self.cost))

                if self.verbose > 1:
                    model = self.oracle.get_model()
                    model = filter(lambda l: abs(l) <= self.orig_nv, model)
                    print('v', ' '.join([str(l) for l in model]), '0')

                return
            else:
                self.treat_core()

                if self.verbose:
                    print('c cost: {0}; core sz: {1}'.format(self.cost, len(self.core)))

                self.reinit()

    def treat_core(self):
        """
            Found core in main loop, deal with it.
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
            Remove a clause responsible for a unit core.
        """

        self.scpy[self.core[0]] = False

        for l in self.soft[self.core[0]]:
            self.hard.append([-l])

    def oracle_time(self):
        """
            Report the total SAT solving time.
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
    verbose = 0

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
    if solver in ('mc', 'minicard'):
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
    print('                         Available values: g3, lgl, m22, mc, mgh (default = m22)')
    print('        -v, --verbose    Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    solver, cardenc, verbose, files = parse_options()

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

        with FM(formula, solver=solver, enc=cardenc, verbose=verbose) as fm:
            fm.compute()

            print('c oracle time: {0:.4f}'.format(fm.oracle_time()))
