#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## unigen.py
##
##  Created on: Oct 16, 2023
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Sampler

    ==================
    Module description
    ==================

    This module provides interface to `UniGen3
    <https://github.com/meelgroup/unigen/>`_, a state-of-the-art
    almost-uniform sampler utilising an improved version of CryptoMiniSat to
    handle problems of size and complexity that were not possible before. .
    The original work on UniGen3 has been published in [1]_, [2]_, and [3]_.

    .. [1] Supratik Chakraborty, Kuldeep S. Meel, Moshe Y. Vardi. *Balancing
        Scalability and Uniformity in SAT Witness Generator*. DAC 2014.
        pp. 60:1-60:6

    .. [2] Supratik Chakraborty, Daniel J. Fremont, Kuldeep S. Meel, Sanjit A.
        Seshia, Moshe Y. Vardi. *On Parallel Scalable Uniform SAT Witness
        Generation*. TACAS 2015. pp. 304-319

    .. [3] Mate Soos, Stephan Gocht, Kuldeep S. Meel. *Tinted, Detached, and
        Lazy CNF-XOR Solving and Its Applications to Counting and Sampling*.
        CAV 2020. pp. 463-484

    Note that to be functional, the module requires package ``pyunigen`` to be
    installed:

    ::

        $ pip install pyunigen

    The interface gives access to :class:`Sampler`, which expects a formula in
    :class:`.CNF` as input. Given a few additional (optional) arguments,
    including a random seed, *tolerance factor* :math:`\\varepsilon`,
    *confidence* :math:`\delta` (to be used by ApproxMC), and *uniformity
    parameter* :math:`\kappa`, the class can be used to get apply
    almost-uniform sampling and to obtain a requested number of samples as a
    result, subject to the given tolerance factor and confidence parameter.

    Namely, given a CNF formula :math:`\mathcal{F}` with the set of satisfying
    assignments (or models) denoted by :math:`sol(\mathcal{F})` and parameter
    :math:`\\varepsilon\in(0,1]`, a uniform sampler outputs a model
    :math:`y\in sol(\mathcal{F})` such that :math:`\\textrm{Pr}\left[y
    \\textrm{ is output}\\right]=\\frac{1}{|sol(\mathcal{F})|}`.
    Almost-uniform sampling relaxes the uniformity guarantee and ensures that
    :math:`\\frac{1}{(1+\\varepsilon)|sol(\mathcal{F})|} \leq
    \\textrm{Pr}\left[y \\textrm{ is output}\\right] \leq
    \\frac{1+\\varepsilon}{|sol(\mathcal{F})|}`.

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``unigen.py -h``) in the
    following way:

    ::

        $ xzcat formula.cnf.xz
        p cnf 6 2
        1 5 0
        1 6 0

        $ unigen.py -n 4 formula.cnf.xz
        v +1 -2 +3 -4 -5 -6 0
        v +1 +2 +3 -4 +5 +6 0
        v +1 -2 -3 -4 +5 -6 0
        v -1 -2 -3 -4 +5 +6 0

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.allies.unigen import Sampler
        >>> from pysat.formula import CNF
        >>>
        >>> cnf = CNF(from_file='formula.cnf.xz')
        >>>
        >>> with Sampler(cnf) as sampler:
        ...     print(sampler.sample(nof_samples=4, sample_over=[1, 2, 3])
        [[1, 2, 3, 4, 5], [1, -2, -3, -4, -5], [1, -2, -3, -4, 5], [1, 2, -3, 4, 5]]

    As can be seen in the above example, sampling can be done over a
    user-defined set of variables (rather than the complete set of variables).

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

# we need pyunigen to be installed:
pyunigen_present = True
try:
    import pyunigen
except ImportError:
    pyunigen_present = False


#
#==============================================================================
class Sampler(object):
    """
        A wrapper for UniGen3, a state-of-the-art almost-uniform sampler.
        Given a formula in :class:`.CNF`, this class can be used to apply
        almost-uniform sampling of the formula's models, subject to a few
        input parameters.

        The class initialiser receives a number of input arguments. The
        ``formula`` argument can be left unspecified at this stage. In this
        case, a user is expected to add all the relevant clauses using
        :meth:`add_clause`.

        Additional parameters a user may want to specify include integer
        ``seed`` (used by ApproxMC), tolerance factor ``epsilon`` (used in the
        probabilistic guarantees of almost-uniformity), confidence parameter
        ``delta`` (used by ApproxMC), and uniformity parameter ``kappa`` (see
        [2]_).

        :param formula: CNF formula
        :param seed: seed value
        :param epsilon: tolerance factor
        :param delta: confidence parameter (used by ApproxMC)
        :param kappa: uniformity parameter
        :param verbose: verbosity level

        :type formula: :class:`.CNF`
        :type seed: int
        :type epsilon: float
        :type delta: float
        :type kappa: float
        :type verbose: int

        .. code-block:: python

            >>> from pysat.allies.unigen import Sampler
            >>> from pysat.formula import CNF
            >>>
            >>> cnf = CNF(from_file='some-formula.cnf')
            >>> with Sampler(formula=cnf, epsilon=0.1, delta=0.9) as sampler:
            ...     for model in sampler.sample(nof_samples=100):
            ...         print(model)  # printing 100 result samples
    """

    def __init__(self, formula=None, seed=1, epsilon=0.8, delta=0.2,
                 kappa=0.638, verbose=0):
        """
            Constructor.
        """

        assert pyunigen_present, 'Package \'pyunigen\' is unavailable. Check your installation.'

        # there are no initial values
        self.cellc, self.hashc, self.samples = None, None, []

        # creating the Sampler object
        self.sampler = pyunigen.Sampler(verbosity=verbose, seed=seed,
                                        delta=delta, epsilon=epsilon,
                                        kappa=kappa)

        # adding clauses to the sampler
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
            constructor of :class:`Sampler`, adding clauses may also be
            helpful afterwards, *on the fly*.

            The clause to add can be any iterable over integer literals.

            :param clause: a clause to add
            :type clause: iterable(int)

            .. code-block:: python

                >>> from pysat.allies.unigen import Sampler
                >>>
                >>> with Sampler() as sampler:
                ...     sampler.add_clause(range(1, 4))
                ...     sampler.add_clause([3, 4])
                ...
                ...     print(sampler.sample(nof_samples=4))
                [[1, 2, -3, 4], [-1, 2, -3, 4], [1, 2, 3, -4], [-1, 2, 3, 4]]
        """

        self.sampler.add_clause(clause)

    def sample(self, nof_samples, sample_over=None, counts=None):
        """
            Given the formula provided by the user either in the constructor
            of :class:`Sampler` or through a series of calls to
            :meth:`add_clause`, this method runs the UniGen3 sampler with the
            specified values of tolerance :math:`\\varepsilon`, confidence
            :math:`\delta` parameters, and uniformity parameter :math:`kappa`
            as well as the random ``seed`` value, and outputs a requested
            number of samples.

            A user may specify an argument ``sample_over``, which is a list of
            integers specifying the variables with respect to which sampling
            should be performed. If ``sample_over`` is left as ``None``,
            almost-uniform sampling  is done wrt. all the variables of the
            input formula.

            Finally, argument ``counts`` can be specified as a pair of integer
            values: *cell count* and *hash count* (in this order) used during
            sampling. If left undefined (``None``), the values are determined
            by ApproxMC.

            :param nof_samples: number of samples to output
            :param sample_over: variables to sample over
            :param counts: cell count and hash count values

            :type nof_samples: int
            :type sample_over: list(int)
            :type counts: [int, int]

            :return: a list of samples

            .. code-block:: python

                >>> from pysat.allies.unigen import Sampler
                >>> from pysat.card import CardEnc, EncType
                >>>
                >>> # cardinality constraint with auxiliary variables
                >>> # there are exactly 6 models for the constraint
                >>> # over the 6 original variables
                >>> cnf = CardEnc.equals(lits=range(1, 5), bound=2, encoding=EncType.totalizer)
                >>>
                >>> with Sampler(formula=cnf, epsilon=0.05, delta=0.95) as sampler:
                ...     for model in sampler.sample(nof_samples=3):
                ...         print(model)
                [1, -2, 3, -4, 5, 6, -7, -8, 9, -10, 11, -12, 13, 14, -15, 16, 17, -18, 19, -20]
                [1, -2, -3, 4, 5, 6, -7, -8, 9, -10, 11, -12, 13, 14, -15, 16, 17, -18, 19, -20]
                [1, 2, -3, -4, 5, 6, -7, 8, -9, -10, 11, 12, 13, 14, -15, 16, 17, 18, -19, -20]
                >>>
                >>> # now, sampling over the original variables
                >>> with Sampler(formula=cnf, epsilon=0.05, delta=0.95) as sampler:
                ...     for model in sampler.sample(nof_samples=3, sample_over=range(1, 5)):
                ...         print(model)
                [1, 2, -3, -4]
                [1, -2, 3, -4]
                [-1, 2, 3, -4]
        """

        # we cannot pass None as arguments, hence these if-elif branches
        if sample_over is None and counts is None:
            self.cellc, self.hashc, self.samples = self.sampler.sample(num=nof_samples)
        elif counts is None:
            self.cellc, self.hashc, self.samples = self.sampler.sample(num=nof_samples,
                                                                       sampling_set=sample_over)
        elif sample_over is None:
            self.cellc, self.hashc, self.samples = self.sampler.sample(num=nof_samples,
                                                                       cell_hash_count=tuple(counts))
        else:
            self.cellc, self.hashc, self.samples = self.sampler.sample(num=nof_samples,
                                                                       sampling_set=sample_over,
                                                                       cell_hash_count=tuple(counts))

        return self.samples

    def delete(self):
        """
            Explicit destructor of the internal Sampler oracle.
            Delete the actual sampler object and sets it to ``None``.
        """

        if self.sampler:
            del self.sampler
            self.sampler = None


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:d:e:hk:n:S:s:v:',
                ['counts=', 'delta=', 'epsilon=', 'help', 'kappa=',
                 'nof-samples=' 'sample-over=', 'seed=', 'verbose='])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    counts = None
    delta = 0.2
    epsilon = 0.8
    kappa = 0.638
    nof_samples = 4
    sample_over = None
    seed = 1
    verbose = 0

    for opt, arg in opts:
        if opt in ('-c', '--counts'):
            counts = tuple([int(v) for v in str(arg).split(',')])
        elif opt in ('-d', '--delta'):
            delta = float(arg)
        elif opt in ('-e', '--epsilon'):
            epsilon = float(arg)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-k', '--kappa'):
            kappa = float(arg)
        elif opt in ('-n', '--nof-samples'):
            nof_samples = int(arg)
        elif opt in ('-S', '--sample-over'):
            # parsing the list of variables
            sample_over, values = [], str(arg).split(',')

            # checking if there are intervals
            for value in values:
                if value.isnumeric():
                    sample_over.append(int(value))
                elif '-' in value:
                    lb, ub = value.split('-')
                    assert int(lb) < int(ub)
                    sample_over.extend(list(range(int(lb), int(ub) + 1)))

            # removing duplicates, if any
            sample_over = sorted(set(sample_over))
        elif opt in ('-s', '--seed'):
            seed = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose = int(arg)
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return nof_samples, counts, delta, epsilon, kappa, sample_over, seed, \
            verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -c, --counts=<float>        A comma-separated pair of integer values representing cell count and hash count parameters (if any)')
    print('                                    Note: if omitted, there values are computed by ApproxMC')
    print('                                    Default: none')
    print('        -d, --delta=<float>         Confidence parameter as per PAC guarantees')
    print('                                    Available values: [0, 1) (default = 0.2)')
    print('        -e, --epsilon=<float>       Tolerance factor as per PAC guarantees')
    print('                                    Available values: (0 .. 1], all (default = 0.8)')
    print('        -k, --kappa=<float>         Uniformity parameter')
    print('                                    Available values: (0 .. 1], all (default = 0.638)')
    print('        -n, --nof-samples=<int>     Number of required samples')
    print('                                    Available values: [1 .. INT_MAX] (default = 4)')
    print('        -S, --sample-over=<list>    If provided, solutions are almost uniformly sampled over this set of variables')
    print('                                    Available values: comma-separated-list, none (default = none)')
    print('        -s, --seed=<int>            Random seed')
    print('                                    Available values: [0 .. INT_MAX] (default = 1)')
    print('        -v, --verbose=<int>         Verbosity level')
    print('                                    Available values: [0 .. 15] (default = 0)')


#
#==============================================================================
if __name__ == '__main__':
    nof_samples, counts, delta, epsilon, kappa, sample_over, seed, verbose, \
            files = parse_options()

    # parsing the input formula
    if files and re.search('\.cnf(\.(gz|bz2|lzma|xz))?$', files[0]):
        formula = CNF(from_file=files[0])

        # creating the sampler object
        with Sampler(formula, seed=seed, epsilon=epsilon, delta=delta,
                     kappa=kappa, verbose=verbose) as sampler:

            # almost uniform sampling
            samples = sampler.sample(nof_samples, sample_over=sample_over,
                                     counts=counts)

            # printing the result
            for sample in samples:
                print('v {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in sample])))
