#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## usage.py
##
##  Created on: Nov 27, 2016
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
from pysat.solvers import Solver  # standard way to import the library
from pysat.solvers import Minisat22, Glucose3  # more direct way

#
#==============================================================================
if __name__ == '__main__':
    print('simple infrastructure (add_clause, solve):')
    s1 = Solver(name='g3')
    s1.add_clause([-1, 2])
    s1.add_clause([-2, 3])
    s1.add_clause([-3, 4])

    if s1.solve() == True:
        print(s1.get_model())

    print('blocking models:')
    m = s1.get_model()
    s1.add_clause([-l for l in m])  # actual blocking

    if s1.solve() == True:
        print(s1.get_model())  # should compute another model
    s1.delete()  # this is needed if used not within the 'with' context

    print('model enumeration + bootstrapping the solver:')
    s2 = Minisat22(bootstrap_with=[[-1, 2], [-2, 3], [-3, 4]])  # also working with MiniSat22 directly
    for m in s2.enum_models():  # implemented as a generator
        print(m)
    s2.delete()

    print('\'with\' constructor + assumptions:')
    with Solver(name='mgh', bootstrap_with=[[-1, 2], [-2, 3], [-3, 4]]) as s3:
        for m in s3.enum_models(assumptions=[5]):
            print(m)

        # no s3.delete() is needed -- it is called automatically if used in the 'with' environment

    print('appending formula and extracting an unsat core:')
    with Glucose3(bootstrap_with=[[-1, 2], [-2, 3]]) as s4:
        s4.append_formula([[-3, 4], [-4, 5]])

        if s4.solve(assumptions=[1, -5]) == False:
            print(s4.get_core())

        # no s4.delete() is needed -- it is called automatically if used in the 'with' environment

    print('extracting a proof:')  # supported by glucose and lingeling only
    with Glucose3(bootstrap_with=[[-1, 2], [1, -2], [-1, -2], [1, 2]], with_proof=True) as s5:

        if s5.solve() == False:
            print(s5.get_proof())
