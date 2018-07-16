#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## lbx.py
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
from six.moves import range
import sys


#
#==============================================================================
class LBX(object):
    """
        LBX-like algorithm for computing MCSes.
    """

    def __init__(self, formula, use_cld=False, solver_name='m22', use_timer=False):
        """
            Constructor.
        """

        # bootstrapping the solver with hard clauses
        self.oracle = Solver(name=solver_name, bootstrap_with=formula.hard, use_timer=use_timer)

        self.topv = formula.nv  # top variable id
        self.soft = formula.soft
        self.sels = []
        self.ucld = use_cld
        self.vmap_dir = {}
        self.vmap_opp = {}

        for cl in self.soft:
            sel = cl[0]
            if len(cl) > 1 or cl[0] < 0:
                self.topv += 1
                sel = self.topv

                self.oracle.add_clause(cl + [-sel])

            self.sels.append(sel)
            self.vmap_dir[sel] = len(self.sels)
            self.vmap_opp[len(self.sels)] = sel

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

    def _satisfied(self, cl, model):
        """
            Checks whether or not a clause is satisfied by a model.
        """

        for l in cl:
            if len(model) < abs(l) or model[abs(l) - 1] == l:
                # either literal is unassigned or satisfied by the model
                return True

        return False

    def _filter_satisfied(self, update_setd=False):
        """
            Separates satisfied clauses and literals of unsatisfied clauses.
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
            Compute an MCS.
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

        if self.oracle.solve(assumptions=self.ss_assumps + self.bb_assumps + [sel]):
            # filtering satisfied
            self._filter_satisfied(update_setd=True)
        else:
            # clause D is unsatisfiable => all literals are backbones
            self.bb_assumps.extend([-l for l in cld[:-1]])
            self.setd = []

        # deactivating clause D
        self.oracle.add_clause([-sel])

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()


#
#==============================================================================
class LBXPlus(LBX, object):
    """
        Algorithm LBX for CNF+/WCNF+ formulas.
    """

    def __init__(self, formula, use_cld=False, use_timer=False):
        """
            Constructor.
        """

        super(LBXPlus, self).__init__(formula, use_cld=use_cld, solver_name='mc', use_timer=use_timer)

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

            with LBX(formula, use_cld=dcalls, solver_name=solver, use_timer=True) as mcsls:
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

            with LBXPlus(formula, use_cld=dcalls, use_timer=True) as mcsls:
                for i, mcs in enumerate(mcsls.enumerate()):
                    if verbose:
                        print('c MCS:', ' '.join([str(cl_id) for cl_id in mcs]), '0')

                    if to_enum and i + 1 == to_enum:
                        break

                    mcsls.block(mcs)

                print('c oracle time: {0:.4f}'.format(mcsls.oracle_time()))
