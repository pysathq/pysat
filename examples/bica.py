#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## bica.py
##
##  Created on: Jul 28, 2025
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Bica

    ==================
    Module description
    ==================

    A reimplementation of the Bica algorithm for SAT-based minimisation /
    simplification of Boolean formulas [1]_. Given an arbitrary Boolean
    formula, it computes its smallest size prime cover, i.e. it constructs a
    smallest CNF (DNF, resp.) representation comprising the formula's prime
    implicates (implicants, reps.), which is *equivalent* to the original
    formula.

    The original Bica algorithm is inspired by the well-known Quine-McCluskey
    algorithm [2]_ [3]_ [4]_. It is *entirely* SAT-based and can deal with
    arbitrary Boolean formulas. The algorithm involves two steps: first, it
    enumerates all the prime implicants (or implicates, depending on the
    user's choice) of the formula by utilising the :class:`.Primer` algorithm
    [5]_; second, it computes the formula's smallest prime cover by means of
    reducing the problem to the computation of a smallest minimal
    unsatisfiable subformula (SMUS), invoking the :class:`.OptUx` SMUS solver
    [6]_.

    The word "bica" is Portuguese and means a cup of extremely strong and
    high-quality coffee (often seen as a synonym of espresso). This way, the
    Bica algorithm continues the *coffee inspiration* of the `Espresso logic
    minimizer
    <https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/espresso/>`_
    [7]_, hence signifying the construction of the formula's *essence* or
    *crux*. (In fact, this reimplementation was initially planned to have the
    name *Crux*, to relate with `one of the most prominent constellations of
    the southern sky <https://en.wikipedia.org/wiki/Crux>`_, often used in
    navigation to determine the Southern Celestial Pole.)

    .. [1] Alexey Ignatiev, Alessandro Previti, Joao Marques-Silva.
        *SAT-Based Formula Simplification*. SAT 2015. pp. 287-298

    .. [2] Willard V. Quine. *The Problem of Simplifying Truth Functions*.
        American Mathematical Monthly 59(8). 1952. pp. 521-531

    .. [3] Willard V. Quine. *A Way to Simplify Truth Functions*.
        American Mathematical Monthly 62(9). 1955. pp. 627-631

    .. [4] Edward J. McCluskey. *Minimization of Boolean Functions*. Bell
        System Technical Journal 35(6). 1956. pp 1417-1444

    .. [5] Alessandro Previti, Alexey Ignatiev, António Morgado,
        Joao Marques-Silva. *Prime Compilation of Non-Clausal Formulae.*
        IJCAI 2015. pp. 1980-1988

    .. [6] Alexey Ignatiev, Alessandro Previti, Mark H. Liffiton, Joao
        Marques-Silva. *Smallest MUS Extraction with Minimal Hitting Set
        Dualization*. CP 2015. pp. 173-182

    .. [7] Robert K. Brayton, Alberto L. Sangiovanni-Vincentelli,, Curtis T.
        McMullen, Gary D. Hachtel. *Logic Minimization Algorithms for VLSI
        Synthesis*. Kluwer Academic Publishers. 1984

    The file provides a class :class:`Bica`, which contains the above
    algorithm reimplementation. It can be applied to any formula in the
    :class:`.CNF` or :class:`.Formula` format.

    The implementation can be used as an executable (the list of available
    command-line options can be shown using ``bica.py -h``) in the following
    way:

    ::

        $ xzcat formula.cnf.xz
        p cnf 7 7
        -1 2 0
        1 -2 0
        1 2 -3 4 0
        1 2 3 -4 0
        1 2 3 4 -5 6 0
        1 2 3 4 5 -6 0
        1 2 3 4 5 6 7 0

        $ bica.py -v formula.cnf.xz
        c prime -1 +2 0
        c prime +1 -2 0
        c prime +1 -3 +4 0
        c prime +2 -3 +4 0
        c prime +1 +3 -4 0
        c prime +2 +3 -4 0
        c prime +1 +3 -5 +6 0
        c prime +1 +3 +5 -6 0
        c prime +1 +3 +5 +7 0
        c prime +1 +3 +6 +7 0
        c prime +1 +4 +5 +7 0
        c prime +1 +4 +6 +7 0
        c prime +1 +4 +5 -6 0
        c prime +1 +4 -5 +6 0
        c prime +2 +4 -5 +6 0
        c prime +2 +3 -5 +6 0
        c prime +2 +3 +5 -6 0
        c prime +2 +4 +5 -6 0
        c prime +2 +3 +5 +7 0
        c prime +2 +4 +5 +7 0
        c prime +2 +3 +6 +7 0
        c prime +2 +4 +6 +7 0
        p cnf 7 7
        -1 2 0
        1 -2 0
        2 -3 4 0
        2 3 -4 0
        2 3 -5 6 0
        2 4 5 -6 0
        2 4 6 7 0
        o 7
        c primer time: 0.0002
        c optux  time: 0.0001
        c total  time: 0.0004

    Alternatively, the algorithm can be accessed and invoked through the
    standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.bica import Bica
        >>> from pysat.formula import Atom, CNF, Formula
        >>>
        >>> x, y, z = [Atom(v + 1) for v in range(3)]
        >>> formula = ~(~x >> y) | (x & z)
        >>>
        >>> with Bica(formula) as bica:
        ...     for minf in bica.enumerate():
        ...         minf = CNF(from_clauses=[bica.primes[i - 1] for i in minf])
        ...         print(minf)
        CNF(from_string='p cnf 3 2\\n-1 3 0\\n-2 1 0')

    As the example above demonstrates, Bica can enumerate all irreducible
    prime covers of an input formula (or as many as the user wants). In this
    particular example, the formula :math:`f\\triangleq\\neg{(\\neg{x}
    \\rightarrow y)} \\vee (x \\wedge z)` has the only irreducible prime cover
    :math:`(\\neg{x} \\vee z) \\vee (\\neg{y} \\vee x)`.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import collections
import getopt
import os
from pysat.examples.optux import OptUx
from pysat.examples.primer import Primer
from pysat.formula import IDPool, CNF, Neg, WCNF
from pysat.solvers import Solver
import re
import sys


#
#==============================================================================
class Bica:
    """
        A simple reimplementation of the Bica algorithm. Although the original
        implementation of Bica was also written in Python, both phases of the
        algorithm (prime enumeration and prime cover computation) were written
        in C++ and interfaced through the file IO. The current implementation
        relies on pure Python alternatives for both of the phases. Namely, it
        first calls :class:`.Primer` to enumerate all the primes of a given
        input formula followed by the computation of a smallest size cover
        with :class:`.OptUx`.

        Importantly, thanks to the capabilities of :class:`.OptUx`, the
        current implementation allows one to enumerate multiple (or all)
        smallest size prime covers. Alternatively, one can even opt for
        computing **a minimal** prime cover (not a minimum one).

        The second phase of the approach also allows a user to compute the
        target representation either *unweighted* or *weighted*. In the former
        case, the size is measured as the number of primes included in the
        minimal representation. In the latter case, the lenght of each prime
        is taken into account such that the overall size is counted as the sum
        of lengths of the primes included. This is controlled with the use of
        input parameter ``weighted``.

        Additionally, one may additionally want to specify the negation of the
        input formula, which is required either in first phase of the
        algorithm or in both phases, depending on whether the user wants to
        compute a DNF or CNF representation. If no negated formula is
        provided, Bica will create one internally.

        As both phases of the algorithm rely on implicit hitting set
        enumeration, they share the same input parameters. To allow a user to
        apply various parameters for the two phases, :class:`.Hitman`'s
        parameters of the :class:`.Primer` phase are prefixed with a ``p``
        while the same parameters used by :class:`.OptUx` are prefixed with an
        ``o``.

        The complete list of initialiser's arguments is as follows:

        :param formula: input formula whose prime representation is sought
        :param negated: input's formula negation (if any)
        :param target: either ``'cnf'`` or ``'dnf'``
        :param psolver: SAT oracle name
        :param padapt: detect and adapt intrinsic AtMost1 constraints
        :param pdcalls: apply clause D oracle calls (for unsorted enumeration only)
        :param pexhaust: do core exhaustion
        :param pminz: do heuristic core reduction
        :param ppuresat: use pure SAT-based hitting set enumeration
        :param psearch: dual prime reduction strategy
        :param punsorted: apply unsorted MUS enumeration
        :param ptrim: do core trimming at most this number of times
        :param osolver: SAT oracle name
        :param oadapt: detect and adapt intrinsic AtMost1 constraints
        :param odcalls: apply clause D oracle calls (for unsorted enumeration only)
        :param oexhaust: do core exhaustion
        :param ominz: do heuristic core reduction
        :param onodisj: do not enumerate disjoint MCSes with OptUx
        :param opuresat: use pure SAT-based hitting set enumeration
        :param ounsorted: apply unsorted MUS enumeration
        :param otrim: do core trimming at most this number of times
        :param weighted: get a minimal cover wrt. the total number of literals
        :param verbose: verbosity level

        :type formula: :class:`.Formula` or :class:`.CNF`
        :type negated: :class:`.Formula` or :class:`.CNF`
        :type target: str
        :type psolver: str
        :type padapt: bool
        :type pdcalls: bool
        :type pexhaust: bool
        :type pminz: bool
        :type ppuresat: str
        :type psearch: str
        :type punsorted: bool
        :type ptrim: int
        :type osolver: str
        :type oadapt: bool
        :type odcalls: bool
        :type oexhaust: bool
        :type ominz: bool
        :type onodisj: bool
        :type opuresat: str
        :type ounsorted: bool
        :type otrim: int
        :type weighted: bool
        :type verbose: int
    """

    def __init__(self, formula, negated=None, target='cnf', psolver='cd19',
                 padapt=False, pdcalls=False, pexhaust=False, pminz=False,
                 ppuresat=False, psearch='lin', punsorted=False, ptrim=False,
                 osolver='mgh', oadapt=False, odcalls=False, oexhaust=False,
                 ominz=False, onodisj=False, opuresat=False, ounsorted=False,
                 otrim=False, weighted=False, verbose=0):
        """
            Initialiser.
        """

        # copying some of the arguments
        self.form = formula
        self.fneg = negated
        self.target = target
        self.verbose = verbose
        self.weighted = weighted

        # Primer's parameters
        self.psolver = psolver
        self.padapt = padapt
        self.pdcalls = pdcalls
        self.pexhaust = pexhaust
        self.pminz = pminz
        self.ppuresat = ppuresat
        self.psearch = psearch
        self.punsorted = punsorted
        self.ptrim = ptrim

        # OptUx's parameters
        self.osolver = osolver
        self.oadapt = oadapt
        self.odcalls = odcalls
        self.oexhaust = oexhaust
        self.ominz = ominz
        self.onodisj = onodisj
        self.opuresat = opuresat
        self.ounsorted = ounsorted
        self.otrim = otrim

        # oracles solving the two subproblems
        self.primer, self.optux, self.primes = None, None, []

        # if no negated formula was given, we create one
        if self.fneg is None:
            self.fneg = Neg(self.form)

        # input formula for OptUx to be gradually constructed
        # during prime enumeration phase;
        self.pform = WCNF()
        if self.target == 'dnf':
            for cl in self.form:
                self.pform.append(cl)
        else:
            # if the target is CNF, we need to add the negated formula
            for cl in self.fneg:
                self.pform.append(cl)

        self._init_primer()

    def _init_primer(self):
        """
            Constructs and initialises the Primer object.
        """

        implicates = False if self.target == 'dnf' else True

        self.primer = Primer(self.form, negated=self.fneg,
                             solver=self.psolver, implicates=implicates,
                             adapt=self.padapt, dcalls=self.pdcalls,
                             exhaust=self.pexhaust, minz=self.pminz,
                             puresat=self.ppuresat, search=self.psearch,
                             unsorted=self.punsorted, trim=self.ptrim,
                             verbose=self.verbose - 1)

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
            Explicit destructor of both primer and optux. Also, clears the
            list of primes computed.

            (The former is constructed in Bica's initialiser while the latter
            is created on demand, once the first phase of the algorithm has
            been finished, i.e. when all the primes have been enumerated.)
        """

        self.primes = []

        if self.primer:
            self.primer.delete()
            self.primer = None

        if self.optux:
            self.optux.delete()
            self.optux = None

    def compute(self):
        """
            Computes a single minimum representation of the input formula as a
            list of indices of prime implicants (or implicates) determined to
            comprise the representation.

            Note that the indices in the returned list start from ``1``, i.e.
            the user is supposed to subtract ``1`` for each of them to get the
            correct list of primes. Consider the following example:

            .. code-block:: python

                >>> from pysat.examples.bica import Bica
                >>> from pysat.formula import CNF
                >>>
                >>> cnf = CNF(from_clauses=[[-1, 2], [-2, 3], [-3, 4], [4, 5]])
                >>>
                >>> with Bica(formula) as bica:
                ...     for minf in bica.enumerate():
                ...         minf = CNF(from_clauses=[bica.primes[i - 1] for i in minf])
                ...         print(minf)
                ...     print(f'all primes implicates: {bica.primes}')
                CNF(from_string='p cnf 4 3\\n4 0\\n-2 3 0\\n-1 2 0')
                all prime implicates: [[4], [-2, 3], [-1, 3], [-1, 2]]

            :rtype: list(int)
        """

        # first, collecing all the primes
        if not self.primes:
            for prime in self.primer.enumerate():
                self.primes.append(prime)

                # recording the prime
                if self.target == 'cnf':
                    self.pform.append(prime, weight=len(prime) if self.weighted else 1)
                else:
                    self.pform.append([-l for l in prime], weight=len(prime) if self.weighted else 1)

                # reporting it
                if self.verbose > 1:
                    print('c prime {0} 0'.format(' '.join(['{0}{1}'.format('+' if v > 0 else '', v) for v in prime])))

        if not self.optux:
            # creating an OptUx object
            self.optux = OptUx(self.pform, solver=self.osolver,
                               adapt=self.oadapt, cover=None,
                               dcalls=self.odcalls, exhaust=self.oexhaust,
                               minz=self.ominz, nodisj=self.onodisj,
                               puresat=self.opuresat, unsorted=self.ounsorted,
                               trim=self.otrim, verbose=self.verbose)

        return self.optux.compute()

    def enumerate(self):
        """
            This is generator method iterating through minimum representations
            and enumerating them until no more of them exists, or a user
            decides to stop the process.

            .. code-block:: python

                >>> from pysat.examples.bica import Bica
                >>> from pysat.formula import *
                >>>
                >>> cnf = CNF(from_file='test.cnf')
                >>> print(cnf)
                CNF(from_string='c n orig vars 5\\np cnf 11 5\\n-1 2 0\\n1 -2 0\\n1 2 -3 4 0\\n1 2 3 -4 0\\n1 2 3 4 5 0')
                >>>
                >>> with Bica(cnf) as bica:
                ...     for minf in bica.enumerate():
                ...         print(minf)  # prime indices start from 1!
                [1, 2, 8, 9, 10]
                [1, 2, 3, 8, 10]
                [1, 2, 3, 6, 10]
                [1, 2, 3, 4, 8]
                [1, 2, 3, 4, 6]
                [1, 2, 4, 7, 8]
                [1, 2, 4, 8, 9]
                [1, 2, 4, 5, 8]
                [1, 2, 4, 6, 7]
                [1, 2, 4, 5, 6]
                [1, 2, 4, 6, 9]
                [1, 2, 6, 7, 10]
                [1, 2, 7, 8, 10]
                [1, 2, 5, 8, 10]
                [1, 2, 5, 6, 10]
                [1, 2, 6, 9, 10]

            :rtype: list(int)
        """

        done = False

        while not done:
            minf = self.compute()

            if minf is not None:
                yield minf
            else:
                done = True

    def oracle_time(self):
        """
            This method computes and returns the total SAT solving time
            involved, including the time spent by :class:`.Primer` and
            :class:`.OptUx`, which implement the first and second phases
            of the algorithm, respectively.

            :rtype: float
        """

        return self.primer.oracle_time() + self.optux.oracle_time()


class Crux(Bica):
    """
        A clone of Bica, to be used interchangeably.
    """

    pass


#
#==============================================================================
def parse_options():
    """
        Parses command-line options:
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'aAdDe:hmMnp:P:r:R:s:S:t:T:uUvwxX',
                                   ['padapt', 'oadapt', 'pdcalls', 'odcalls',
                                    'enum=', 'help', 'pminimize', 'ominimize',
                                    'no-disj', 'ppuresat=', 'opuresat=',
                                    'reduce=', 'repr=', 'psolver=',
                                    'osolver=', 'ptrim=', 'otrim=',
                                    'punsorted', 'ounsorted', 'verbose',
                                    'weighted', 'pexhaust', 'oexhaust'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    to_enum = 1
    mode = 'cnf'
    search = 'lin'
    verbose = 1
    weighted = False

    padapt = False
    oadapt = False
    pdcalls = False
    odcalls = False
    pexhaust = False
    oexhaust = False
    pminz = False
    ominz = False
    nodisj = False
    psolver = 'cd19'
    osolver = 'mgh'
    ppuresat = False
    opuresat = False
    punsorted = False
    ounsorted = False
    ptrim = 0
    otrim = 0

    for opt, arg in opts:
        if opt in ('-a', '--padapt'):
            padapt = True
        elif opt in ('-A', '--oadapt'):
            oadapt = True
        elif opt in ('-d', '--pdcalls'):
            pdcalls = True
        elif opt in ('-D', '--odcalls'):
            odcalls = True
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-m', '--pminimize'):
            pminz = True
        elif opt in ('-M', '--ominimize'):
            ominz = True
        elif opt in ('-n', '--no-disj'):
            nodisj = True
        elif opt in ('-p', '--ppuresat'):
            ppuresat = str(arg)
        elif opt in ('-P', '--opuresat'):
            opuresat = str(arg)
        elif opt in ('-r', '--reduce'):
            search = str(arg)
            assert search in ('lin', 'bin'), 'Wrong minimisation method: {0}'.format(search)
        elif opt in ('-R', '--repr'):
            mode = str(arg)
        elif opt in ('-s', '--psolver'):
            psolver = str(arg)
        elif opt in ('-S', '--osolver'):
            osolver = str(arg)
        elif opt in ('-u', '--punsorted'):
            punsorted = True
        elif opt in ('-U', '--ounsorted'):
            ounsorted = True
        elif opt in ('-t', '--ptrim'):
            ptrim = int(arg)
        elif opt in ('-T', '--otrim'):
            otrim = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-w', '--weighted'):
            weighted = True
        elif opt in ('-x', '--pexhaust'):
            pexhaust = True
        elif opt in ('-X', '--oexhaust'):
            oexhaust = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return to_enum, mode, padapt, oadapt, pdcalls, odcalls, pexhaust, \
            oexhaust, pminz, ominz, nodisj, ptrim, otrim, search, psolver, \
            osolver, ppuresat, opuresat, punsorted, ounsorted, verbose, \
            weighted, args


#
#==============================================================================
def usage():
    """
        Prints usage message.
    """

    print('Usage:', os.path.basename(sys.argv[0]), '[options]')
    print('Options:')
    print('        -a, --padapt               Try to adapt (simplify) input formula [Primer]')
    print('        -A, --oadapt               Try to adapt (simplify) input formula [OptUx]')
    print('        -d, --pdcalls              Apply clause D calls (in unsorted enumeration only) [Primer]')
    print('        -D, --odcalls              Apply clause D calls (in unsorted enumeration only) [OptUx]')
    print('        -e, --enum=<int>           Enumerate this many "top-k" solutions')
    print('                                   Available values: [1 .. INT_MAX], all (default = 1)')
    print('        -h, --help                 Print this help message')
    print('        -m, --pminimize            Use a heuristic unsatisfiable core minimizer [Primer]')
    print('        -M, --ominimize            Use a heuristic unsatisfiable core minimizer [OptUx]')
    print('        -n, --no-disj              Do not enumerate disjoint MCSes [OptUx]')
    print('        -p, --ppuresat=<string>    Use a pure SAT-based hitting set enumerator [Primer]')
    print('                                   Available values: cd15, cd19, lgl, mgh (default = mgh)')
    print('                                   Requires: unsorted mode, i.e. \'-u\'')
    print('        -P, --opuresat=<string>    Use a pure SAT-based hitting set enumerator [OptUx]')
    print('                                   Available values: cd15, cd19, lgl, mgh (default = mgh)')
    print('                                   Requires: unsorted mode, i.e. \'-U\'')
    print('        -r, --reduce               Dual prime minimiser [Primer]')
    print('                                   Available values: lin, bin (default = lin)')
    print('        -R, --repr=<string>        Target representation')
    print('                                   Available values: dnf, cnf (default = cnf)')
    print('        -s, --psolver              SAT solver to use [Primer]')
    print('                                   Available values: cd, cd15, cd19, g3, g41, g42, lgl, mcb, mcm, mpl, m22, mc, mg3, mgh (default = cd19)')
    print('        -S, --osolver              SAT solver to use [OptUx]')
    print('                                   Available values: cd, cd15, cd19, g3, g41, g42, lgl, mcb, mcm, mpl, m22, mc, mg3, mgh (default = mgh)')
    print('        -t, --ptrim=<int>          How many times to trim unsatisfiable cores [Primer]')
    print('                                   Available values: [0 .. INT_MAX] (default = 0)')
    print('        -T, --otrim=<int>          How many times to trim unsatisfiable cores [OptUx]')
    print('                                   Available values: [0 .. INT_MAX] (default = 0)')
    print('        -u, --punsorted            Enumerate MUSes in an unsorted way using LBX [Primer]')
    print('        -U, --ounsorted            Enumerate MUSes in an unsorted way using LBX [OptUx]')
    print('        -v, --verbose              Be verbose')
    print('        -w, --weighted             Target optimal representations with respect the total number of literals')
    print('        -x, --pexhaust             Exhaust new unsatisfiable cores [Primer]')
    print('        -X, --oexhaust             Exhaust new unsatisfiable cores [OptUx]')


#
#==============================================================================
if __name__ == '__main__':
    # parse command-line options
    to_enum, mode, padapt, oadapt, pdcalls, odcalls, pexhaust, oexhaust, \
            pminz, ominz, nodisj, ptrim, otrim, search, psolver, osolver, \
            ppuresat, opuresat, punsorted, ounsorted, verbose, weighted, \
            files = parse_options()

    if files:
        # read CNF from file
        assert re.search(r'cnf(\.(gz|bz2|lzma|xz|zst))?$', files[0]), 'Unknown input file extension'
        formula = CNF(from_file=files[0])

        # creating an object of Primer
        with Bica(formula, negated=None, target=mode, psolver=psolver,
                  padapt=padapt, pdcalls=pdcalls, pexhaust=pexhaust,
                  pminz=pminz, ppuresat=ppuresat, psearch=search,
                  punsorted=punsorted, ptrim=ptrim, osolver=osolver,
                  oadapt=oadapt, odcalls=odcalls, oexhaust=oexhaust,
                  ominz=ominz, onodisj=nodisj, opuresat=opuresat,
                  ounsorted=ounsorted, otrim=otrim, weighted=weighted,
                  verbose=verbose) as bica:

            for i, minf in enumerate(bica.enumerate()):
                if verbose > 1:
                    minf = CNF(from_clauses=[bica.primes[i - 1] for i in minf])
                    minf.to_fp(sys.stdout, as_dnf=True if mode == 'dnf' else False)

                print('o {0}'.format(bica.optux.cost))

                # checking if we are done
                if to_enum and i + 1 == to_enum:
                    break

            # reporting the total oracle time
            print('c primer time: {0:.4f}'.format(bica.primer.oracle_time()))
            print('c optux  time: {0:.4f}'.format(bica.optux.oracle_time()))
            print('c total  time: {0:.4f}'.format(bica.oracle_time()))
