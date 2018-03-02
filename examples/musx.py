#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## musx.py
##
##  Created on: Jan 25, 2018
##      Author: Antonio Morgado, Alexey Ignatiev
##      E-mail: {ajmorgado, aignatiev}@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.formula import CNF, WCNF
from pysat.solvers import Solver
import sys


#
#==============================================================================
class MUSX(object):
    """
        MUS eXctractor using the deletion based algorithm.
    """

    def __init__(self, formula, solver='m22', verbosity=1):
        """
            Constructor.
        """

        topv, self.verbose = formula.nv, verbosity

        # clause selectors and a mapping from selectors to clause ids
        self.sels, self.vmap = [], {}

        # constructing the oracle
        self.oracle = Solver(name=solver, use_timer=True)

        # relaxing clauses and adding them to the oracle
        for i, cl in enumerate(formula.clauses):
            topv += 1

            self.sels.append(topv)
            self.vmap[topv] = i

            self.oracle.add_clause(cl + [-topv])

    def __enter__(self):
        """
            'with' constructor.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
            'with' destructor.
        """

        self.oracle.delete()
        self.oracle = None

    def delete(self):
        """
            Explicit destructor.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

    def compute(self):
        """
            Compute and return a solution.
        """

        # cheking whether or not the formula is unsatisfiable
        if not self.oracle.solve(assumptions=self.sels):
            # get an overapproximation of an MUS
            approx = sorted(self.oracle.get_core())

            if self.verbose:
                print('c MUS approx:', ' '.join([str(self.vmap[sel] + 1) for sel in approx]), '0')

            # iterate over clauses in the approximation and try to delete them
            self._compute(approx)

            # return an MUS
            return list(map(lambda x: self.vmap[x] + 1, approx))

    def _compute(self, approx):
        """
            Deletion-based MUS extraction.
            (Try to delete clauses in the given approximation one by one.)
        """

        i = 0

        while i < len(approx):
            to_test = approx[:i] + approx[(i + 1):]
            sel, clid = approx[i], self.vmap[approx[i]]

            if self.verbose > 1:
                print('c testing clid: {0}'.format(clid), end='')

            if self.oracle.solve(assumptions=to_test):
                if self.verbose > 1:
                    print(' -> sat (keeping {0})'.format(clid))

                i += 1
            else:
                if self.verbose > 1:
                    print(' -> unsat (removing {0})'.format(clid))

                approx = to_test

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
        opts, args = getopt.getopt(sys.argv[1:], 'hs:v', ['help', 'solver=', 'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    solver = 'm22'
    verbose = 0

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return solver, verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -h, --help')
    print('        -s, --solver     SAT solver to use')
    print('                         Available values: g3, lgl, m22, mc, mgh (default: m22)')
    print('        -v, --verbose    Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    solver, verbose, files = parse_options()

    if files:
        formula = CNF(from_file=files[0])

        with MUSX(formula, solver=solver, verbosity=verbose) as musx:
            mus = musx.compute()

            if mus:
                if verbose:
                    print('c CNF size: {0}'.format(len(formula.clauses)))
                    print('c MUS size: {0}'.format(len(mus)))

                print('v', ' '.join([str(clid) for clid in mus]), '0')
                print('c oracle time: {0:.4f}'.format(musx.oracle_time()))
