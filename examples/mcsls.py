#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## mcsls.py
##
##  Created on: Jan 9, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.formula import CNF, WCNF, WCNFPlus
from pysat.solvers import Solver
import sys


#
#==============================================================================
class MCSls(object):
    """
        Algorithm LS of MCSls augmented with D calls.
    """

    def __init__(self, formula, use_cld=False, solver_name='m22', use_timer=False):
        """
            Constructor.
        """

        # bootstrapping the solver with hard clauses
        self.oracle = Solver(name=solver_name, bootstrap_with=formula.hard, use_timer=use_timer)

        self.topv = formula.nv  # top variable id
        self.soft = []
        self.ucld = use_cld
        self.vmap_dir = {}
        self.vmap_opp = {}

        for cl in formula.soft:
            new_cl = cl[:]
            if len(cl) > 1 or cl[0] < 0:
                self.topv += 1
                sel = self.topv

                new_cl.append(-sel)  # creating a new selector
                self.oracle.add_clause(new_cl)
            else:
                sel = cl[0]

            self.soft.append([sel])
            self.vmap_dir[sel] = len(self.soft)
            self.vmap_opp[len(self.soft)] = sel

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
            Compute and return one solution.
        """

        self.setd = []
        self.solution = None
        self.bb_assumps = []  # backbone assumptions
        self.ss_assumps = []  # satisfied soft clause assumptions

        if self.oracle.solve():
            # hard part is satisfiable => there is a solution
            self._overapprox()
            self._compute()

            self.solution = [self.vmap_dir[-l] for l in self.bb_assumps]

        return self.solution

    def enumerate(self):
        """
            Enumerate all MCSes and report them one by one.
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
            Block a (previously computed) MCS.
        """

        self.oracle.add_clause([self.vmap_opp[cl_id] for cl_id in mcs])

    def _overapprox(self):
        """
            Over-approximates the solution.
        """

        model = self.oracle.get_model()

        for cl in self.soft:
            sel = cl[0]
            if len(model) < sel or model[sel - 1] > 0:
                # soft clauses contain positive literals
                # so if var is true then the clause is satisfied
                self.ss_assumps.append(sel)
            else:
                self.setd.append(sel)

    def _compute(self):
        """
            Compute an MCS.
        """

        # unless clause D checks are used, test one literal at a time
        # and add it either to satisfied of backbone assumptions
        i = 0
        while i < len(self.setd):
            if self.ucld:
                self.do_cld_check(self.setd[i:])
                i = 0

            if self.setd:
                # if may be empty after the clause D check

                self.ss_assumps.append(self.setd[i])
                if not self.oracle.solve(assumptions=self.ss_assumps + self.bb_assumps):
                    self.ss_assumps.pop()
                    self.bb_assumps.append(-self.setd[i])

            i += 1

    def do_cld_check(self, cld):
        """
            Do clause D check.
        """

        # adding a selector literal to clause D
        # selector literals for clauses D currently
        # cannot be reused, but this may change later
        self.topv += 1
        sel = self.topv
        cld.append(-sel)

        # adding clause D
        self.oracle.add_clause(cld)
        self.ss_assumps.append(sel)

        self.setd = []
        self.oracle.solve(assumptions=self.ss_assumps + self.bb_assumps)

        self.ss_assumps.pop()  # removing clause D assumption
        if self.oracle.get_status() == True:
            model = self.oracle.get_model()

            for l in cld[:-1]:
                # filtering all satisfied literals
                if model[abs(l) - 1] > 0:
                    self.ss_assumps.append(l)
                else:
                    self.setd.append(l)
        else:
            # clause D is unsatisfiable => all literals are backbones
            self.bb_assumps.extend([-l for l in cld[:-1]])

        # deactivating clause D
        self.oracle.add_clause([-sel])

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()


#
#==============================================================================
class MCSlsPlus(MCSls, object):
    """
        Algorithm LS of MCSls for CNF+/WCNF+ formulas.
    """

    def __init__(self, formula, use_cld=False, use_timer=False):
        """
            Constructor.
        """

        super(MCSlsPlus, self).__init__(formula, use_cld=use_cld, solver_name='mc', use_timer=use_timer)

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
    print('                               Available values: g3, lgl, m22, mc, mgh (default: m22)')
    print('        -v, --verbose          Be verbose')


#
#==============================================================================
if __name__ == '__main__':
    dcalls, to_enum, solver, verbose, files = parse_options()

    if type(to_enum) == str:
        to_enum = 0

    if files:
        if files[0].endswith('cnf'):
            if files[0].endswith('.wcnf'):
                formula = WCNF(from_file=files[0])
            else:  # expecting '*.cnf'
                formula = CNF(from_file=files[0]).weighted()

            with MCSls(formula, use_cld=dcalls, solver_name=solver, use_timer=True) as mcsls:
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
        elif files[0].endswith('.wcnf+'):
            formula = WCNFPlus(from_file=files[0])

            with MCSlsPlus(formula, use_cld=dcalls, use_timer=True) as mcsls:
                for i, mcs in enumerate(mcsls.enumerate()):
                    if verbose:
                        print('c MCS:', ' '.join([str(cl_id) for cl_id in mcs]), '0')

                    if to_enum and i + 1 == to_enum:
                        break

                    mcsls.block(mcs)

                print('c oracle time: {0:.4f}'.format(mcsls.oracle_time()))
