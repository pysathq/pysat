#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## models.py
##
##  Created on: Mar 4, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        enumerate_models

    ==================
    Module description
    ==================

    The module implements a simple iterative enumeration of a given number of
    models of :class:`.CNF` or :class:`CNFPlus` formula. In the latter case,
    only :class:`.Minicard` can be used as a SAT solver. The module aims at
    illustrating how one can work with model computation and enumeration.

    The implementation facilitates the simplest use of a SAT oracle from the
    *command line*. If one deals with the enumeration task from a Python
    script, it is more convenient to exploit the internal model enumeration of
    the :mod:`pysat.solvers` module. Concretely, see
    :meth:`pysat.solvers.Solver.enum_models()`.

    ::

        $ cat formula.cnf
        p cnf 4 4
        -1 2 0
        -1 3 0
        -2 4 0
        3 -4 0

        $ models.py -e all -s glucose3 formula.cnf
        v -1 -2 +3 -4 0
        v +1 +2 -3 +4 0
        c nof models: 2
        c accum time: 0.00s
        c mean  time: 0.00s

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.formula import CNFPlus
from pysat.solvers import Solver, SolverNames
import sys


#
#==============================================================================
def enumerate_models(formula, to_enum, solver):
    """

        Enumeration procedure. It represents a loop iterating over satisfying
        assignment for a given formula until either all or a given number of
        them is enumerated.

        :param formula: input WCNF formula
        :param to_enum: number of models to compute
        :param solver: name of SAT solver

        :type formula: :class:`.CNFPlus`
        :type to_enum: int or 'all'
        :type solver: str
    """

    with Solver(name=solver, bootstrap_with=formula.clauses, use_timer=True) as s:
        # adding native cardinality constraints if needed
        if formula.atmosts:
            assert solver_name in SolverNames.minicard or \
                    solver_name in SolverNames.gluecard3 or \
                    solver_name in SolverNames.gluecard4, \
                    '{0} does not support native cardinality constraints'.format(solver_name)

            for atm in formula.atmosts:
                s.add_atmost(*atm)

        # model enumeration and printing is done here
        computed = 0
        for i, model in enumerate(s.enum_models(), 1):
            print('v {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in model])))

            computed = i
            if i == to_enum:
                break

        # some final statistics
        print('c nof models: {0}'.format(computed))
        print('c accum time: {0:.2f}s'.format(s.time()))

        if computed:
            print('c mean  time: {0:.2f}s'.format(s.time() / computed))


#
#==============================================================================
def parse_options():
    """
        Parses command-line options:
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'e:h:s:',
                                   ['enum=',
                                    'help',
                                    'solver='])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    to_enum = 1
    solver = 'g3'

    for opt, arg in opts:
        if opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum == 'all':
                to_enum = -1
            else:
                to_enum = int(to_enum)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return to_enum, solver, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -e, --enum=<int>         Compute at most this number of models')
    print('                                 Available values: [1 .. INT_MAX], all (default: 1)')
    print('        -h, --help               Show this message')
    print('        -s, --solver=<string>    SAT solver to use')
    print('                                 Available values: cd, g3, g4, lgl, mcb, mcm, mpl, m22, mc, mgh (default = g3)')


#
#==============================================================================
if __name__ == '__main__':
    # parsing command-line options
    to_enum, solver, files = parse_options()

    # reading an input formula either from a file or from stdin
    if files:
        formula = CNFPlus(from_file=files[0])
    else:
        formula = CNFPlus(from_fp=sys.stdin)

    enumerate_models(formula, to_enum, solver)
