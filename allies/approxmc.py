#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## approxmc.py
##
##  Created on: Apr 14, 2023
##      Author: Mate Soos
##      E-mail: soos.mate@gmail.com
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Counter

    ==================
    Module description
    ==================

    Some description. Consult examples/*.py to see how this could be done. :-)

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import getopt
import os
from pysat.formula import CNF
import re
import sys

# we need pyapproxmc to be installed:
pyapproxmc_present = True
try:
    import pyapproxmc
except ImportError:
    pyapproxmc_present = False


#
#==============================================================================
class Counter(object):
    """
        Class doc-string.
    """

    def __init__(self, formula=None, seed=1, epsilon=0.8, delta=0.2, verbose=0):
        """
            Constructor.
        """

        assert pyapproxmc_present, 'Package \'pyapproxmc\' is unavailable. Check your installation.'

        # there are no initial counts
        self.cellc, self.hashc = None, None

        # creating the Counter object
        self.counter = pyapproxmc.Counter(verbosity=verbose, seed=seed,
                                          epsilon=epsilon, delta=delta)

        # adding clauses to the counter
        for clause in formula:
            self.add_clause(clause)

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

    def add_clause(self, clause):
        """
            The method for adding a clause to the problem formula. Although
            the input formula is to be specified as an argument of the
            constructor of :class:`Counter`, adding clauses may also be
            helpful afterwards, *on the fly*.

            The clause to add can be any iterable over integer literals.

            :param clause: a clause to add
            :type clause: iterable(int)
        """

        self.counter.add_clause(clause)

    def count(self, projection=None):
        """
            .
        """

        if projection is not None:
            self.cellc, self.hashc = self.counter.count(projection=projection)
        else:
            self.cellc, self.hashc = self.counter.count()

        return self.cellc * (2 ** self.hashc)

    def delete(self):
        """
            Explicit destructor of the internal Counter oracle.
        """

        if self.counter:
            del self.counter
            self.counter = None


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:e:hp:s:v:',
                ['delta=', 'epsilon=', 'help', 'projection=', 'seed=', 'verbose='])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    delta = 0.2
    epsilon = 0.8
    projection = None
    seed = 1
    verbose = 0

    for opt, arg in opts:
        if opt in ('-d', '--delta'):
            delta = float(arg)
        elif opt in ('-e', '--epsilon'):
            epsilon = float(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-p', '--projection'):
            # parsing the list of variables
            projection, values = [], str(arg).split(',')

            # checking if there are intervals
            for value in values:
                if value.isnumeric():
                    projection.append(int(value))
                elif '-' in value:
                    lb, ub = value.split('-')
                    assert int(lb) < int(ub)
                    projection.extend(list(range(int(lb), int(ub) + 1)))

            # removing duplicates, if any
            projection = sorted(set(projection))
        elif opt in ('-s', '--seed'):
            seed = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose = int(arg)
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return delta, epsilon, projection, seed, verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -d, --delta=<float>        Delta parameter as per PAC guarantees')
    print('                                   Available values: [0, 1] (default = 0.2)')
    print('        -e, --epsilon=<float>      Epsilon parameter as per PAC guarantees')
    print('                                   Available values: [1 .. INT_MAX], all (default = 0.8)')
    print('        -p, --projection=<list>    Do model counting projected on this set of variables')
    print('                                   Available values: comma-separated-list, none (default = none)')
    print('        -s, --seed=<int>           Random seed')
    print('                                   Available values: [0 .. INT_MAX] (default = 1)')
    print('        -v, --verbose=<int>        Verbosity level')
    print('                                   Available values: [0 .. 15] (default = 0)')


#
#==============================================================================
if __name__ == '__main__':
    delta, epsilon, projection, seed, verbose, files = parse_options()

    # parsing the input formula
    if files and re.search('\.cnf(\.(gz|bz2|lzma|xz))?$', files[0]):
        formula = CNF(from_file=files[0])

        # creating the counter object
        with Counter(formula, seed=seed, epsilon=epsilon, delta=delta,
                        verbose=verbose) as counter:

            # approximate model counting
            count = counter.count(projection=projection)

            # printing the result
            print('s mc', count)
