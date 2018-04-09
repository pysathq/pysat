#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## genhard.py
##
##  Created on: Mar 6, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import collections
import getopt
import itertools
import os
from pysat.formula import IDPool, CNF
from six.moves import range
import sys


#
#==============================================================================
def generate_php(size, kval=1, verb=False):
    """
        Generates PHP formula for (kval * size) pigeons and (size - 1) holes.
    """

    # result formula
    cnf = CNF()

    vpool = IDPool(start_from=1)
    var = lambda i, j: vpool.id('v_{0}_{1}'.format(i, j))

    # placing all pigeons into holes
    for i in range(1, kval * (size - 1) + 2):
        cnf.append([var(i, j) for j in range(1, size)])

    # there cannot be more than 1 pigeon in 1 hole
    pigeons = range(1, kval * (size - 1) + 2)
    for j in range(1, size):
        for comb in itertools.combinations(pigeons, kval + 1):
            cnf.append([-var(i, j) for i in comb])

    if verb:
        head = 'c {0}PHP formula for'.format('' if kval == 1 else str(kval) + '-')
        head += ' {0} pigeons and {1} holes'.format(kval * (size - 1) + 1, size - 1)
        cnf.comments.append(head)

        for i in range(1, kval * (size - 1) + 2):
            for j in range(1, size):
                cnf.comments.append('c (pigeon, hole) pair: ({0}, {1}); bool var: {2}'.format(i, j, var(i, j)))

    return cnf


#
#==============================================================================
def generate_gt(size, verb=False):
    """
        Generates GT principle formula for a given size.
    """

    # result formula
    cnf = CNF()

    vpool = IDPool(start_from=1)
    var = lambda i, j: vpool.id('v_{0}_{1}'.format(i, j))

    # anti-symmetric relation clauses
    for i in range(1, size):
        for j in range(i + 1, size + 1):
            cnf.append([-var(i, j), -var(j, i)])

    # transitive relation clauses
    for i in range(1, size + 1):
        for j in range(1, size + 1):
            if j != i:
                for k in range(1, size + 1):
                    if k != i and k != j:
                        cnf.append([-var(i, j), -var(j, k), var(i, k)])

    # successor clauses
    for j in range(1, size + 1):
        cnf.append([var(k, j) for k in range(1, size + 1) if k != j])

    if verb:
        cnf.comments.append('c GT formula for {0} elements'.format(size))
        for i in range(1, size + 1):
            for j in range(1, size + 1):
                if i != j:
                    cnf.comments.append('c orig pair: {0}; bool var: {1}'.format((i, j), var(i, j)))

    return cnf


#
#==============================================================================
def generate_parity(size, verb=False):
    """
        Generate parity principle formula for a given size.
    """

    # result formula
    cnf = CNF()

    vpool = IDPool(start_from=1)
    var = lambda i, j: vpool.id('v_{0}_{1}'.format(min(i, j), max(i, j)))

    for i in range(1, 2 * size + 2):
        cnf.append([var(i, j) for j in range(1, 2 * size + 2) if j != i])

    for j in range(1, 2 * size + 2):
        for i, k in itertools.combinations(range(1, 2 * size + 2), 2):
            if i == j or k == j:
                continue

            cnf.append([-var(i, j), -var(k, j)])

    if verb:
        cnf.comments.append('c Parity formula for m == {0} ({1} vertices)'.format(size, 2 * size + 1))
        for i in range(1, 2 * size + 2):
            for j in range(i + 1, 2 * size + 2):
                cnf.comments.append('c edge: {0}; bool var: {1}'.format((i, j), var(i, j)))

    return cnf


#
#==============================================================================
def parse_options():
    """
        Parses command-line options:
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'k:n:ht:v',
                                   ['kval=',
                                    'size=',
                                    'help',
                                    'type=',
                                    'verb'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    kval = 1
    size = 8
    ftype = 'php'
    verb = False

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-k', '--kval'):
            kval = int(arg)
        elif opt in ('-n', '--size'):
            size = int(arg)
        elif opt in ('-t', '--type'):
            ftype = str(arg)
        elif opt in ('-v', '--verb'):
            verb = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return ftype, kval, size, verb


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options]')
    print('Options:')
    print('        -k, --kval=<int>       Value k for generating k-PHP')
    print('                               Available values: [1 .. INT_MAX] (default = 1)')
    print('        -n, --size=<int>       Integer parameter of formula (its size)')
    print('                               Available values: [0 .. INT_MAX] (default = 8)')
    print('        -h, --help')
    print('        -t, --type=<string>    Formula type')
    print('                               Available values: gt, php, parity (default = php)')
    print('        -v, --verb             Be verbose (show comments)')

#
#==============================================================================
if __name__ == '__main__':
    # parse command-line options
    ftype, kval, size, verb = parse_options()

    # generate formula
    if ftype == 'php':
        cnf = generate_php(size, kval=kval, verb=verb)
    elif ftype == 'gt':  # gt
        cnf = generate_gt(size, verb=verb)
    else:  # parity
        cnf = generate_parity(size, verb=verb)

    # print formula in DIMACS to stdout
    cnf.to_fp(sys.stdout)
