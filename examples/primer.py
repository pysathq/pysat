#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## primer.py
##
##  Created on: Jul 23, 2025
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Primer

    ==================
    Module description
    ==================

    A reimplementation of the prime implicant (and implicate) enumeration
    algorithm originally called Primer-B [1]_. The algorithm exploits the
    minimal hitting duality between prime implicants and implicates of an
    input formula and hence makes extensive use of a hitting set enumerator.
    The input formula can be in a clausal or a non-clausal form, i.e. the
    input can be given as an object of either :class:`.CNF` or
    :class:`.Formula`.

    The implementation relies on :class:`.Hitman` and supports both sorted and
    unsorted hitting set enumeration. In the former case, hitting sets are
    computed from smallest to largest, which is achieved with MaxSAT-based
    hitting set enumeration, using :class:`.RC2` [2]_ [3]_ [4]_. In the latter
    case, either an LBX-like MCS enumerator :class:`.LBX` [5]_ is used or
    *pure* SAT-based minimal model enumeration [6]_.

    .. [1] Alessandro Previti, Alexey Ignatiev, António Morgado,
        Joao Marques-Silva. *Prime Compilation of Non-Clausal Formulae.*
        IJCAI 2015. pp. 1980-1988

    .. [2] António Morgado, Carmine Dodaro, Joao Marques-Silva. *Core-Guided
        MaxSAT with Soft Cardinality Constraints*. CP 2014. pp. 564-573

    .. [3] António Morgado, Alexey Ignatiev, Joao Marques-Silva. *MSCG: Robust
        Core-Guided MaxSAT Solving*. JSAT 9. 2014. pp. 129-134

    .. [4] Alexey Ignatiev, António Morgado, Joao Marques-Silva. *RC2: a
        Python-based MaxSAT Solver*. MaxSAT Evaluation 2018. p. 22

    .. [5] Carlos Mencía, Alessandro Previti, Joao Marques-Silva.
        *Literal-Based MCS Extraction*. IJCAI. 2015. pp. 1973-1979

    .. [6] Enrico Giunchiglia, Marco Maratea. *Solving Optimization Problems
        with DLL*. ECAI 2006. pp. 377-381

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``primer.py -h``) in the following
    way:

    ::

        $ xzcat formula.cnf.xz
        p cnf 4 3
        1 2 4 0
        1 -2 3 0
        -1 2 -4 0

        $ primer.py -i -e all formula.cnf.xz
        v +1 +2 0
        v +2 +3 0
        v +1 -4 0
        v -1 +3 +4 0
        v -1 -2 +4 0
        c primes: 5
        c oracle time: 0.0001
        c oracle calls: 41

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.primer import Primer
        >>> from pysat.formula import CNF
        >>>
        >>> cnf = CNF(from_file='test.cnf.xz')
        >>>
        >>> with Primer(cnf, implicates=False) as primer:
        ...     for p in primer.enumerate():
        ...         print(f'prime: {p}')
        ...
        prime: [2, 3]
        prime: [1, 2]
        prime: [1, -4]
        prime: [-1, 3, 4]
        prime: [-1, -2, 4]

    The tool can be instructed to enumerate either prime implicates or prime
    implicants (a set of the dual primes covering the formula is computed as a
    by-product of Primer's implicit hitting set algorithm). Namely, it targets
    implicate enumeration *by default*; setting the Boolean parameter
    ``implicates=False`` will force it to focus on prime implicants instead.
    (In the command line, the same effect can be achieved if using the option
    '-i'.)

    A user may also want to compute :math:`k` primes instead of enumerating
    them exhaustively. This may come in handy, for example, if the input
    formula has an exponential number of primes. Command-line option `-e NUM`
    is responsible for this. In the case of complete prime implicant
    enumeration the algorithm will essentially end up computing the input
    formula's *Blake Canonical Form* (BCF) [7]_.

    .. [7] Archie Blake. *Canonical Expressions in Boolean Algebra.*
        Dissertation. University of Chicago. 1937.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import getopt
import os
from pysat.examples.hitman import Hitman
from pysat.formula import IDPool, CNF, Neg
from pysat.solvers import Solver
import re
import sys


#
#==============================================================================
class Primer:
    """
        A simple Python-based reimplementation of the Primer-B algorithm. It
        can be used for computing either :math:`k` prime implicates or
        implicants of an input formula, or enumerating them all exhaustively
        As the algorithm is based on implicit hitting set enumeration, a set
        of dual primes (either prime implicants or implicates) covering the
        input formula is computed as a by-product.

        The input formula can be specified either in :class:`.CNF` or be a
        generic Boolean :class:`.Formula`. In the latter case, the
        implementation will clausify the formula and, importantly, report all
        the primes using the integer variable IDs introduced by the
        clausification process. As a result, a user is assumed responsible for
        translating these back to the original :class:`Atom` objects, should
        the need arise.

        Additionally, the user may additionally specify the negation of the
        formula (if not, Primer will create one in the process) and a few
        input parameters controlling the run of the algorithm. All of these in
        fact relate to the parameters of the hitting set enumerator, which is
        the key component of the tool.

        Namely, a user may specify the SAT solver of their choice to be used
        by :class:`.Hitman` and the two extra SAT oracles as well as set the
        parameters of MaxSAT/MCS/SAT-based hitting set enumeration. For
        details on these parameters and what exactly they control, please
        refer to to the description of :class:`.Hitman`.

        Finally, when the algorithm determines a hitting set *not* to be a
        target prime, a model is extracted evidencing this fact, which is then
        reduced into a *dual prime*. The reduction process is based on MUS
        extraction and can involve a linear literal traversal or dichotomic
        similar to the ideas of QuickXPlain [8]_. The choice of the type of
        literal traversal can be made using the ``search`` parameter, which
        can be set either to ``'lin'`` or ``'bin'``.

        .. [8] Ulrich Junker. *QUICKXPLAIN: Preferred Explanations and
            Relaxations for Over-Constrained Problems.* AAAI 2004.
            pp. 167-172

        The complete list of input parameters is as follows:

        :param formula: input formula whose prime representation is sought
        :param negated: input's formula negation (if any)
        :param solver: SAT oracle name
        :param implicates: whether or not prime implicates to target
        :param adapt: detect and adapt intrinsic AtMost1 constraints
        :param dcalls: apply clause D oracle calls (for unsorted enumeration only)
        :param exhaust: do core exhaustion
        :param minz: do heuristic core reduction
        :param puresat: use pure SAT-based hitting set enumeration
        :param search: dual prime reduction strategy
        :param unsorted: apply unsorted MUS enumeration
        :param trim: do core trimming at most this number of times
        :param verbose: verbosity level

        :type formula: :class:`.Formula` or :class:`.CNF`
        :type negated: :class:`.Formula` or :class:`.CNF`
        :type solver: str
        :type implicates: bool
        :type adapt: bool
        :type dcalls: bool
        :type exhaust: bool
        :type minz: bool
        :type puresat: str
        :type search: str
        :type unsorted: bool
        :type trim: int
        :type verbose: int
    """

    def __init__(self, formula, negated=None, solver='cd19', implicates=True,
                 adapt=False, dcalls=False, exhaust=False, minz=False,
                 puresat=False, search='lin', unsorted=False, trim=False,
                 verbose=0):
        """
            Initialiser.
        """

        # copying some of the arguments
        self.form = formula
        self.fneg = negated
        self.mode = bool(implicates)

        # dual prime minimisation strategy
        self.search = search

        # verbosity level
        self.verbose = verbose

        # number of SAT oracle calls
        self.calls = 0

        # creating hitman
        if not unsorted:
            # MaxSAT-based hitting set enumerator
            self.hitman = Hitman(bootstrap_with=[], solver=solver,
                                 htype='sorted', mxs_adapt=adapt,
                                 mxs_exhaust=exhaust, mxs_minz=minz,
                                 mxs_trim=trim)
        elif not puresat:
            # MCS-based hitting set enumerator
            self.hitman = Hitman(bootstrap_with=[], solver=solver,
                                 htype='lbx', mcs_usecld=dcalls)
        else:
            # pure SAT-based hitting set enumerator with preferred phases
            self.hitman = Hitman(bootstrap_with=[], solver=puresat,
                                 htype='sat')

        # creating the checker and reducer oracles
        self.checker = Solver(name=solver, use_timer=True)
        self.reducer = Solver(name=solver, use_timer=True)

        # populate all the oracles with all the relevant clauses
        self.init_oracles()

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

    def delete(self):
        """
            Explicit destructor of the internal hitting set enumerator and
            the SAT oracles.
        """

        self.calls = 0

        if self.hitman:
            self.hitman.delete()
            self.hitman = None

        if self.checker:
            self.checker.delete()
            self.checker = None

        if self.reducer:
            self.reducer.delete()
            self.reducer = None

    def init_oracles(self):
        """
            Encodes the formula in dual-rail representation and initialises
            the hitting set enumerator as well as the two additional SAT
            oracles.

            In particular, this method initialises the hitting set enumerator
            with the dual-rail clauses :math:`(\\neg{p_i} \\vee \\neg{n_i})`
            for each variable :math:`v_i` of the formula. Additionally, the
            two SAT oracles (*prime checker* and *dual reducer*) are fed the
            input formula and its negation, or the other way around (depending
            on whether the user aims at enumerating implicates of implicants).

            Given the above, the method necessarily creates a clausal
            representation of both the original formula and its negation,
        """

        # creating the negated formula
        if self.fneg is None:
            self.fneg = Neg(self.form)

        # initialising the checker and reducer oracles
        if self.mode is True:
            self.checker.append_formula(self.form)
            self.reducer.append_formula(self.fneg)
        else:
            self.checker.append_formula(self.fneg)
            self.reducer.append_formula(self.form)

        # list of original literals
        self.lits = []

        # initialising hitman, with all the dual-rail literals
        self.dpool = IDPool()
        for a in self.form.atoms():
            if type(a) is int:
                self.lits.append(+a)
                self.lits.append(-a)
                self.hitman.block([self.dpool.id(+a), self.dpool.id(-a)])
            else:
                self.lits.append(+a.name)
                self.lits.append(-a.name)
                self.hitman.block([self.dpool.id(a.name), self.dpool.id(-a.name)])

        # converting the list of original literals into a set; it is
        # to be used to filter out auxiliary variables from the model
        self.lits = set(self.lits)

    def compute(self):
        """
            Computes a single prime. Performs as many iterations of the
            Primer-B algorithm as required to get the next prime. This often
            involves the computation of the dual cover of the formula.

            Returns a list of literals included in the result prime.

            :rtype: list(int)
        """

        while True:
            # computing a new candidate prime
            hs = self.hitman.get()

            if hs is None:
                # no more hitting sets exist
                break

            # mapping dual-rail variables to original variables
            prime = [self.dpool.obj(l) for l in hs]

            self.calls += 1
            if not self.checker.solve(assumptions=[(1 - 2 * self.mode) * l for l in prime]):
                if self.verbose > 2:
                    print('c trgt: {0} 0 ✓'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in prime])))

                # this is a target prime: we block it and return
                self.hitman.block(hs)
                return prime
            else:
                if self.verbose > 2:
                    print('c trgt: {0} 0 ✗'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in prime])))

                # candidate is not a target prime, so we
                # need to extract and hit a dual prime

                # filtering the model so that it contains no auxiliary variables
                model = [l for l in self.checker.get_model() if l in self.lits]

                # model minimisation
                dual = [(2 * self.mode - 1) * l for l in self.minimise_dual(model)]
                self.hitman.hit([self.dpool.id(lit) for lit in dual])

                if self.verbose > 2:
                    print('c dual: {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in dual])))

    def minimise_dual(self, core):
        """
            Reduces a *dual* prime from the model of the checker oracle. The
            procedure is initialised with the over-approximation of a prime
            and builds on simple MUS extraction. Hence the name of the input
            parameter to start from: `core`. The result of this method is a
            dual prime.

            The method traverses the dual to reduce either in the linear
            fashion or runs dichotomic QuickXPlain-like literal traversal.
            This is controlled by the input parameter ``search`` passed to the
            constructor of :class:`Primer`.

            :rtype: list(int)

        """

        def _do_linear(core):
            """
                Do linear search.
            """

            def _assump_needed(a):
                if len(to_test) > 1:
                    to_test.remove(a)
                    self.calls += 1
                    if not self.reducer.solve(assumptions=to_test):
                        return False
                    to_test.add(a)
                    return True
                else:
                    return True

            to_test = set(core)
            return list(filter(lambda a: _assump_needed(a), core))

        def _do_binary(core):
            """
                Do dichotomic search similar to QuickXPlain.
            """

            wset = core[:]
            filt_sz = len(wset) / 2.0
            while filt_sz >= 1:
                i = 0
                while i < len(wset):
                    to_test = wset[:i] + wset[(i + int(filt_sz)):]
                    # actual binary hypotheses to test
                    self.calls += 1
                    if to_test and not self.reducer.solve(assumptions=to_test):
                        # assumps are not needed
                        wset = to_test
                    else:
                        # assumps are needed => check the next chunk
                        i += int(filt_sz)
                # decreasing size of the set to filter
                filt_sz /= 2.0
                if filt_sz > len(wset) / 2.0:
                    # next size is too large => make it smaller
                    filt_sz = len(wset) / 2.0
            return wset

        if self.search == 'bin':
            dual = _do_binary(core)
        else:  # by default, linear MUS extraction is used
            dual = _do_linear(core)

        return dual

    def enumerate(self):
        """
            This is generator method iterating through primes and enumerating
            them until the formula has no more primes, or a user decides to
            stop the process (this is controlled from the outside).

            :rtype: list(int)
        """

        done = False

        while not done:
            prime = self.compute()

            if prime is not None:
                yield prime
            else:
                done = True

    def oracle_time(self):
        """
            This method computes and returns the total SAT solving time
            involved, including the time spent by the hitting set enumerator
            and the two SAT oracles.

            :rtype: float
        """

        return self.hitman.oracle_time() + self.checker.time_accum() + self.reducer.time_accum()


#
#==============================================================================
def parse_options():
    """
        Parses command-line options:
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ade:himp:r:s:t:uvx',
                                   ['adapt', 'dcalls', 'enum=', 'help',
                                    'implicants', 'minimize', 'puresat=',
                                    'reduce=', 'solver=', 'trim=', 'unsorted',
                                    'verbose', 'exhaust'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    to_enum = 1
    mode = 1  # 1 = implicates, 0 = implicants
    adapt = False
    dcalls = False
    exhaust = False
    minz = False
    search = 'lin'
    solver = 'cd19'
    puresat = False
    unsorted = False
    trim = 0
    verbose = 1

    for opt, arg in opts:
        if opt in ('-a', '--adapt'):
            adapt = True
        elif opt in ('-d', '--dcalls'):
            dcalls = True
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-i', '--implicants'):
            mode = 0
        elif opt in ('-m', '--minimize'):
            minz = True
        elif opt in ('-p', '--puresat'):
            puresat = str(arg)
        elif opt in ('-r', '--reduce'):
            search = str(arg)
            assert search in ('lin', 'bin'), 'Wrong minimisation method: {0}'.format(search)
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-u', '--unsorted'):
            unsorted = True
        elif opt in ('-t', '--trim'):
            trim = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-x', '--exhaust'):
            exhaust = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return to_enum, mode, adapt, dcalls, exhaust, minz, trim, \
            search, solver, puresat, unsorted, verbose, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options]')
    print('Options:')
    print('        -a, --adapt               Try to adapt (simplify) input formula')
    print('        -d, --dcalls              Apply clause D calls (in unsorted enumeration only)')
    print('        -e, --enum=<int>          Enumerate this many primes')
    print('                                  Available values: [1 .. INT_MAX], all (default = 1)')
    print('        -h, --help                Print this help message')
    print('        -i, --implicants          Target prime implicants instead of implicates')
    print('        -m, --minimize            Use a heuristic unsatisfiable core minimizer')
    print('        -p, --puresat=<string>    Use a pure SAT-based hitting set enumerator')
    print('                                  Available values: cd15, cd19, lgl, mgh (default = mgh)')
    print('                                  Requires: unsorted mode, i.e. \'-u\'')
    print('        -r, --reduce              Dual prime minimiser')
    print('                                  Available values: lin, bin (default = lin)')
    print('        -s, --solver              SAT solver to use')
    print('                                  Available values: cd, cd15, cd19, g3, g41, g42, lgl, mcb, mcm, mpl, m22, mc, mg3, mgh (default = cd19)')
    print('        -t, --trim=<int>          How many times to trim unsatisfiable cores')
    print('                                  Available values: [0 .. INT_MAX] (default = 0)')
    print('        -u, --unsorted            Enumerate MUSes in an unsorted way using LBX')
    print('        -v, --verbose             Be verbose')
    print('        -x, --exhaust             Exhaust new unsatisfiable cores')

#
#==============================================================================
if __name__ == '__main__':
    # parse command-line options
    to_enum, mode, adapt, dcalls, exhaust, minz, trim, search, solver, \
            puresat, unsorted, verbose, files = parse_options()

    if files:
        # read CNF from file
        assert re.search(r'cnf(\.(gz|bz2|lzma|xz|zst))?$', files[0]), 'Unknown input file extension'
        formula = CNF(from_file=files[0])

        # creating an object of Primer
        with Primer(formula, negated=None, solver=solver, implicates=mode,
                    adapt=adapt, dcalls=dcalls, exhaust=exhaust, minz=minz,
                    puresat=puresat, search=search, unsorted=unsorted,
                    trim=trim, verbose=verbose) as primer:

            # iterating over the necessary number of primes
            for i, prime in enumerate(primer.enumerate()):
                # reporting the current solution
                if verbose:
                    print('v {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in prime])))

                # checking if we are done
                if to_enum and i + 1 == to_enum:
                    break

            # reporting the total oracle time
            if verbose > 1:
                print('c primes: {0}'.format(i + 1))
                print('c oracle time: {0:.4f}'.format(primer.oracle_time()))
                print('c oracle calls: {0}'.format(primer.calls))
