#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## lsu.py
##
##  Created on: Aug 29, 2018
##      Author: Miguel Neves
##      E-mail: neves@sat.inesc-id.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
from pysat.card import ITotalizer
from pysat.formula import CNF, WCNF
from pysat.solvers import Solver
import os
import sys
import re


# TODO: support weighted MaxSAT
#==============================================================================
class LSU:
    """
        Linear Sat-Unsat algorithm for MaxSAT.
        Only supports unweighted problems for now.
    """

    def __init__(self, formula, solver='g4', verbose=0):
        """
            Constructor.
        """

        self.verbose = verbose
        self.solver = solver
        self.formula = formula
        self.topv = formula.nv  # largest variable index
        self.sels = []          # soft clause selector variables
        self.tot = None         # totalizer encoder for the cardinality constraint
        self._init(formula)     # initiaize SAT oracle

    def _init(self, formula):
        """
            Initialize the SAT solver.
        """

        self.oracle = Solver(name=self.solver, bootstrap_with=formula.hard, incr=True, use_timer=True)

        for i, cl in enumerate(formula.soft):
            # TODO: if clause is unit, use its literal as selector
            # (ITotalizer must be extended to support PB constraints first)
            self.topv += 1
            selv = self.topv
            cl.append(self.topv)
            self.oracle.add_clause(cl)
            self.sels.append(selv)

        if self.verbose > 1:
            print('c formula: {0} vars, {1} hard, {2} soft'.format(formula.nv, len(formula.hard), len(formula.soft)))

    def solve(self):
        """
            Computes a solution to the MaxSAT problem.
            Returns ``True`` if a solution exists, ``False`` if the hard
            formula is unsatisfiable.
        """

        is_sat = False

        while self.oracle.solve():
            is_sat = True
            self.model = self.oracle.get_model()
            self.cost = self._get_model_cost(self.formula, self.model)
            if self.verbose:
                print('o {0}'.format(self.cost))
                sys.stdout.flush()
            if self.cost == 0:      # if cost is 0, then model is an optimum solution
                break
            self._assert_lt(self.cost)
            self.oracle.set_phases(self.model)  # solution-based phase saving

        if is_sat:
            self.model = filter(lambda l: abs(l) <= self.formula.nv, self.model)
            if self.verbose:
                print('s OPTIMUM FOUND')
        elif self.verbose:
            print('s UNSATISFIABLE')

        return is_sat

    def get_model(self):
        """
            Returns the internal model.
        """

        return self.model

    def _get_model_cost(self, formula, model):
        """
            Computes and returns the cost of a given model.
        """

        model_set = set(model)
        cost = 0

        for i, cl in enumerate(formula.soft):
            cost += formula.wght[i] if all(l not in model_set for l in filter(lambda l: abs(l) <= self.formula.nv, cl)) else 0

        return cost

    def _assert_lt(self, cost):
        """
            Asserts constraint forcing the next solution to have a smaller
            cost than ``cost``.
        """

        if self.tot == None:
            self.tot = ITotalizer(lits=self.sels, ubound=cost-1, top_id=self.topv)
            self.topv = self.tot.top_id

            for cl in self.tot.cnf.clauses:
                self.oracle.add_clause(cl)

        self.oracle.add_clause([-self.tot.rhs[cost-1]])

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()


#
#==============================================================================
def parse_options():
    """
        Parses command-line options.
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hvm', ['help', 'verbose', 'model'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        print_usage()
        sys.exit(1)

    verbose = 1
    print_model = False

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_usage()
            sys.exit(0)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-m', '--model'):
            print_model = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return verbose, print_model, args


#
#==============================================================================
def print_usage():
    """
        Prints usage message.
    """

    print('Usage: ' + os.path.basename(sys.argv[0]) + ' [options] dimacs-file')
    print('Options:')
    print('        -h, --help       Show this message')
    print('        -v, --verbose    Be verbose')
    print('        -m, --model      Print model')


#
#==============================================================================
def parse_formula(fml_file):
    """
        Parse and return MaxSAT formula.
    """

    if re.search('\.wcnf(\.(gz|bz2|lzma|xz))?$', fml_file):
        fml = WCNF(from_file=fml_file)
    else:  # expecting '*.cnf'
        fml = CNF(from_file=fml_file).weighted()

    return fml


#
#==============================================================================
if __name__ == '__main__':
    verbose, print_model, files = parse_options()

    if files:
        formula = parse_formula(files[0])

        lsu = LSU(formula, verbose=verbose)
        if lsu.solve():
            if print_model:
                print('v ' + ' '.join([str(l) for l in lsu.get_model()]))

        if verbose > 1:
            print('c oracle time: {0:.4f}'.format(lsu.oracle_time()))
    else:
        print_usage()
