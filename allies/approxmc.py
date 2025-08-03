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

    This module provides interface to `ApproxMCv4
    <https://github.com/meelgroup/approxmc/>`_, a state-of-the-art
    *approximate* model counter utilising an improved version of CryptoMiniSat
    to give approximate model counts to problems of size and complexity that
    are out of reach for earlier approximate model counters. The original work
    on ApproxMCv4 has been published in [1]_ and [2]_.

    .. [1] Mate Soos, Kuldeep S. Meel. *BIRD: Engineering an Efficient CNF-XOR
        SAT Solver and Its Applications to Approximate Model Counting*. AAAI
        2019. pp. 1592-1599

    .. [2] Mate Soos, Stephan Gocht, Kuldeep S. Meel. *Tinted, Detached, and
        Lazy CNF-XOR Solving and Its Applications to Counting and Sampling*.
        CAV 2020. pp. 463-484

    Note that to be functional, the module requires package ``pyapproxmc`` to
    be installed:

    ::

        $ pip install pyapproxmc

    The interface gives access to :class:`Counter`, which expects a formula in
    :class:`.CNF` as input. Given a few additional (optional) arguments,
    including a random seed, *tolerance factor* :math:`\\varepsilon`, and
    *confidence* :math:`\\delta`, the class can be used to get an approximate
    number of models of the formula, subject to the given tolerance factor and
    confidence parameter.

    Namely, given a CNF formula :math:`\\mathcal{F}` with
    :math:`\\#\\mathcal{F}` as the exact number of models, and parameters
    :math:`\\varepsilon\\in(0,1]` and :math:`\\delta\\in[0,1)`, the counter
    computes and reports a value :math:`C`, which is an approximate number of
    models of :math:`\\mathcal{F}`, such that
    :math:`\\textrm{Pr}\\left[\\frac{1}{1+\\varepsilon}\\#\\mathcal{F}\\leq
    C\\leq (1+\\varepsilon)\\#\\mathcal{F}\\right]\\geq 1-\\delta`.

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``approxmc.py -h``) in the
    following way:

    ::

        $ xzcat formula.cnf.xz
        p cnf 20 2
        1 2 3 0
        3 20 0

        $ approxmc.py -p 1,2,3-9 formula.cnf.xz
        s mc 448

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.allies.approxmc import Counter
        >>> from pysat.formula import CNF
        >>>
        >>> cnf = CNF(from_file='formula.cnf.xz')
        >>>
        >>> with Counter(cnf) as counter:
        ...     print(counter.counter(projection=range(1, 10))
        448

    As can be seen in the above example, besides model counting across all the
    variables in a given input formula, the counter supports *projected* model
    counting, i.e. when one needs to approximate the number of models with
    respect to a given list of variables rather than with respect to all
    variables appearing in the formula. This feature comes in handy when the
    formula is obtained, for example, through Tseitin transformation [3]_ with
    a number of auxiliary variables introduced.

    .. [3] G. S. Tseitin. *On the complexity of derivations in the
        propositional calculus*. Studies in Mathematics and Mathematical
        Logic, Part II. pp. 115–125, 1968

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
        A wrapper for `ApproxMC <https://github.com/meelgroup/approxmc/>`_, a
        state-of-the-art *approximate* model counter. Given a formula in
        :class:`.CNF`, this class can be used to get an approximate number of
        models of the formula, subject to *tolerance factor* ``epsilon`` and
        *confidence parameter* ``delta``.

        Namely, given a CNF formula :math:`\\mathcal{F}` and parameters
        :math:`\\varepsilon\\in(0,1]` and :math:`\\delta\\in[0,1)`, the
        counter computes and reports a value :math:`C` such that
        :math:`\\textrm{Pr}\\left[\\frac{1}{1+\\varepsilon}\\#\\mathcal{F}\\leq
        C\\leq (1+\\varepsilon)\\#\\mathcal{F}\\right]\\geq 1-\\delta`. Here,
        :math:`\\#\\mathcal{F}` denotes the exact model count for formula
        :math:`\\mathcal{F}`.

        The ``formula`` argument can be left unspecified at this stage. In
        this case, a user is expected to add all the relevant clauses using
        :meth:`add_clause`.

        An additional parameter a user may want to specify is integer ``seed``
        used by ApproxMC. The value of ``seed`` is set to ``1`` by default.

        :param formula: CNF formula
        :param seed: integer seed value
        :param epsilon: tolerance factor
        :param delta: confidence parameter
        :param verbose: verbosity level

        :type formula: :class:`.CNF`
        :type seed: int
        :type epsilon: float
        :type delta: float
        :type verbose: int

        .. code-block:: python

            >>> from pysat.allies.approxmc import Counter
            >>> from pysat.formula import CNF
            >>>
            >>> cnf = CNF(from_file='some-formula.cnf')
            >>> with Counter(formula=cnf, epsilon=0.1, delta=0.9) as counter:
            ...     num = counter.count() # an approximate number of models
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
        if formula:
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
            the input formula can be specified as an argument of the
            constructor of :class:`Counter`, adding clauses may also be
            helpful afterwards, *on the fly*.

            The clause to add can be any iterable over integer literals.

            :param clause: a clause to add
            :type clause: iterable(int)

            .. code-block:: python

                >>> from pysat.allies.approxmc import Counter
                >>>
                >>> with Counter() as counter:
                ...     counter.add_clause(range(1, 4))
                ...     counter.add_clause([3, 20])
                ...
                ...     print(counter.count())
                720896
        """

        self.counter.add_clause(clause)

    def count(self, projection=None):
        """

            Given the formula provided by the user either in the constructor
            of :class:`Counter` or through a series of calls to
            :meth:`add_clause`, this method runs the ApproxMC counter with the
            specified values of tolerance :math:`\\varepsilon` and confidence
            :math:`\\delta` parameters, as well as the random ``seed`` value,
            and returns the number of models estimated.

            A user may specify an argument ``projection``, which is a list of
            integers specifying the variables with respect to which projected
            model counting should be performed. If ``projection`` is left as
            ``None``, approximate model counting is performed wrt. all the
            variables of the input formula.

            :param projection: variables to project on
            :type projection: list(int)

            .. code-block:: python

                >>> from pysat.allies.approxmc import Counter
                >>> from pysat.card import CardEnc, EncType
                >>>
                >>> # cardinality constraint with auxiliary variables
                >>> # there are exactly 70 models for the constraint
                >>> # over the 8 original variables
                >>> cnf = CardEnc.equals(lits=range(1, 9), bound=4, encoding=EncType.cardnetwrk)
                >>>
                >>> with Counter(formula=cnf, epsilon=0.05, delta=0.95) as counter:
                ...     print(counter.count())
                123840
                >>>
                >>> with Counter(formula=cnf, epsilon=0.05, delta=0.95) as counter:
                ...     print(counter.count(projection=range(1, 8)))
                70
        """

        if projection is not None:
            self.cellc, self.hashc = self.counter.count(projection=projection)
        else:
            self.cellc, self.hashc = self.counter.count()

        return self.cellc * (2 ** self.hashc)

    def delete(self):
        """
            Explicit destructor of the internal Counter oracle.
            Delete the actual counter object and sets it to ``None``.
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
    print('        -d, --delta=<float>        Confidence parameter as per PAC guarantees')
    print('                                   Available values: [0, 1) (default = 0.2)')
    print('        -e, --epsilon=<float>      Tolerance factor as per PAC guarantees')
    print('                                   Available values: (0 .. 1], all (default = 0.8)')
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
    if files and re.search(r'\.cnf(\.(gz|bz2|lzma|xz))?$', files[0]):
        formula = CNF(from_file=files[0])

        # creating the counter object
        with Counter(formula, seed=seed, epsilon=epsilon, delta=delta,
                        verbose=verbose) as counter:

            # approximate model counting
            count = counter.count(projection=projection)

            # printing the result
            print('s mc', count)
