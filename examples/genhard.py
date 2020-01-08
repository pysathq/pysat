#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## genhard.py
##
##  Created on: Mar 6, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        CB
        GT
        PAR
        PHP

    ==================
    Module description
    ==================

    This module is designed to provide a few examples illustrating how PySAT
    can be used for encoding practical problems into CNF formulas. These
    include combinatorial principles that are widely studied from the
    propositional proof complexity perspective. Namely, encodings for the
    following principles are implemented: *pigeonhole principle* (:class:`PHP`)
    [1]_, *ordering (greater-than) principle* (:class:`GT`) [2]_, *mutilated
    chessboard principle* (:class:`CB`) [3]_, and *parity principle*
    (:class:`PAR`) [4]_.

    .. [1] Stephen A. Cook, Robert A. Reckhow. *The Relative Efficiency of
        Propositional Proof Systems*. J. Symb. Log. 44(1). 1979. pp. 36-50

    .. [2] Balakrishnan Krishnamurthy. *Short Proofs for Tricky Formulas*. Acta
        Informatica 22(3). 1985. pp. 253-275

    .. [3] Michael Alekhnovich. *Mutilated Chessboard Problem Is Exponentially
        Hard For Resolution*. Theor. Comput. Sci. 310(1-3). 2004. pp. 513-525

    .. [4] Miklós Ajtai. *Parity And The Pigeonhole Principle*. Feasible
        Mathematics. 1990. pp. 1–24

    The module can be used as an executable (the list of available command-line
    options can be shown using ``genhard.py -h``) in the following way

    ::

        $ genhard.py -t php -n 3 -v
        c PHP formula for 4 pigeons and 3 holes
        c (pigeon, hole) pair: (1, 1); bool var: 1
        c (pigeon, hole) pair: (1, 2); bool var: 2
        c (pigeon, hole) pair: (1, 3); bool var: 3
        c (pigeon, hole) pair: (2, 1); bool var: 4
        c (pigeon, hole) pair: (2, 2); bool var: 5
        c (pigeon, hole) pair: (2, 3); bool var: 6
        c (pigeon, hole) pair: (3, 1); bool var: 7
        c (pigeon, hole) pair: (3, 2); bool var: 8
        c (pigeon, hole) pair: (3, 3); bool var: 9
        c (pigeon, hole) pair: (4, 1); bool var: 10
        c (pigeon, hole) pair: (4, 2); bool var: 11
        c (pigeon, hole) pair: (4, 3); bool var: 12
        p cnf 12 22
        1 2 3 0
        4 5 6 0
        7 8 9 0
        10 11 12 0
        -1 -4 0
        -1 -7 0
        -1 -10 0
        -4 -7 0
        -4 -10 0
        -7 -10 0
        -2 -5 0
        -2 -8 0
        -2 -11 0
        -5 -8 0
        -5 -11 0
        -8 -11 0
        -3 -6 0
        -3 -9 0
        -3 -12 0
        -6 -9 0
        -6 -12 0
        -9 -12 0

    Alternatively, each of the considered problem encoders can be accessed with
    the use of the standard ``import`` interface of Python, e.g.

    .. code-block:: python

        >>> from pysat.examples.genhard import PHP
        >>>
        >>> cnf = PHP(3)
        >>> print(cnf.nv, len(cnf.clauses))
        12 22

    Given this example, observe that classes :class:`PHP`, :class:`GT`,
    :class:`CB`, and :class:`PAR` inherit from class
    :class:`pysat.formula.CNF` and, thus, their corresponding clauses can
    accessed through variable ``.clauses``.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import collections
import getopt
import itertools
import os
from pysat.card import *
from pysat.formula import IDPool, CNF
from six.moves import range
import sys


#
#==============================================================================
class PHP(CNF, object):
    """
        Generator of :math:`k` pigeonhole principle (:math:`k`-PHP) formulas.
        Given integer parameters :math:`m` and :math:`k`, the :math:`k`
        pigeonhole principle states that if :math:`k\cdot m+1` pigeons are
        distributes by :math:`m` holes, then at least one hole contains more
        than :math:`k` pigeons.

        Note that if :math:`k` is 1, the principle degenerates to the
        formulation of the original pigeonhole principle stating that
        :math:`m+1` pigeons cannot be distributed by :math:`m` holes.

        Assume that a Boolean variable :math:`x_{ij}` encodes that pigeon
        :math:`i` resides in hole :math:`j`. Then a PHP formula can be seen as
        a conjunction: :math:`\\bigwedge_{i=1}^{k\cdot
        m+1}{\\textsf{AtLeast1}(x_{i1},\ldots,x_{im})}\wedge
        \\bigwedge_{j=1}^{m}{\\textsf{AtMost}k(x_{1j},\ldots,x_{k\cdot
        m+1,j})}`. Here each :math:`\\textsf{AtLeast1}` constraint forces every
        pigeon to be placed into at least one hole while each
        :math:`\\textsf{AtMost}k` constraint allows the corresponding hole to
        have at most :math:`k` pigeons. The overall PHP formulas are
        unsatisfiable.

        PHP formulas are well-known [6]_ to be hard for resolution.

        .. [6] Armin Haken. *The Intractability of Resolution*. Theor. Comput.
            Sci. 39. 1985. pp. 297-308

        :param nof_holes: number of holes (:math:`n`)
        :param kval: multiplier :math:`k`
        :param topv: current top variable identifier
        :param verb: defines whether or not the encoder is verbose

        :type nof_holes: int
        :type kval: int
        :type topv: int
        :type verb: bool

        :returns: object of class :class:`pysat.formula.CNF`.
    """

    def __init__(self, nof_holes, kval=1, topv=0, verb=False):
        """
            Constructor.
        """

        # initializing CNF's internal parameters
        super(PHP, self).__init__()

        # initializing the pool of variable ids
        vpool = IDPool(start_from=topv + 1)
        var = lambda i, j: vpool.id('v_{0}_{1}'.format(i, j))

        # placing all pigeons into holes
        for i in range(1, kval * nof_holes + 2):
            self.append([var(i, j) for j in range(1, nof_holes + 1)])

        # there cannot be more than k pigeons in a hole
        pigeons = range(1, kval * nof_holes + 2)
        for j in range(1, nof_holes + 1):
            for comb in itertools.combinations(pigeons, kval + 1):
                self.append([-var(i, j) for i in comb])

        if verb:
            head = 'c {0}PHP formula for'.format('' if kval == 1 else str(kval) + '-')
            head += ' {0} pigeons and {1} holes'.format(kval * nof_holes + 1, nof_holes)
            self.comments.append(head)

            for i in range(1, kval * nof_holes + 2):
                for j in range(1, nof_holes + 1):
                    self.comments.append('c (pigeon, hole) pair: ({0}, {1}); bool var: {2}'.format(i, j, var(i, j)))


#
#==============================================================================
class GT(CNF, object):
    """
        Generator of ordering (or *greater than*, GT) principle formulas. Given
        an integer parameter :math:`n`, the principle states that any partial
        order on the set :math:`\{1,2,\ldots,n\}` must have a maximal element.

        Assume variable :math:`x_{ij}`, for :math:`i,j\in[n],i\\neq j`, denotes
        the fact that :math:`i \succ j`. Clauses :math:`(\\neg{x_{ij}} \\vee
        \\neg{x_{ji}})` and :math:`(\\neg{x_{ij}} \\vee \\neg{x_{jk}} \\vee
        x_{ik})` ensure that the relation :math:`\succ` is anti-symmetric and
        transitive. As a result, :math:`\succ` is a partial order on
        :math:`[n]`. The additional requirement that each element :math:`i` has
        a successor in :math:`[n]\setminus\{i\}` represented a clause
        :math:`(\\vee_{j \\neq i}{x_{ji}})` makes the formula unsatisfiable.

        GT formulas were originally conjectured [2]_ to be hard for resolution.
        However, [5]_ proved the existence of a polynomial size resolution
        refutation for GT formulas.

        .. [5] Gunnar Stålmarck. *Short Resolution Proofs for a Sequence of
            Tricky Formulas*. Acta Informatica. 33(3). 1996. pp. 277-280

        :param size: number of elements (:math:`n`)
        :param topv: current top variable identifier
        :param verb: defines whether or not the encoder is verbose

        :type size: int
        :type topv: int
        :type verb: bool

        :returns: object of class :class:`pysat.formula.CNF`.
    """

    def __init__(self, size, topv=0, verb=False):
        """
            Constructor.
        """

        # initializing CNF's internal parameters
        super(GT, self).__init__()

        # initializing the pool of variable ids
        vpool = IDPool(start_from=topv + 1)
        var = lambda i, j: vpool.id('v_{0}_{1}'.format(i, j))

        # anti-symmetric relation clauses
        for i in range(1, size):
            for j in range(i + 1, size + 1):
                self.append([-var(i, j), -var(j, i)])

        # transitive relation clauses
        for i in range(1, size + 1):
            for j in range(1, size + 1):
                if j != i:
                    for k in range(1, size + 1):
                        if k != i and k != j:
                            self.append([-var(i, j), -var(j, k), var(i, k)])

        # successor clauses
        for j in range(1, size + 1):
            self.append([var(k, j) for k in range(1, size + 1) if k != j])

        if verb:
            self.comments.append('c GT formula for {0} elements'.format(size))
            for i in range(1, size + 1):
                for j in range(1, size + 1):
                    if i != j:
                        self.comments.append('c orig pair: {0}; bool var: {1}'.format((i, j), var(i, j)))


#
#==============================================================================
class CB(CNF, object):
    """
        Mutilated chessboard principle (CB). Given an integer :math:`n`, the
        principle states that it is impossible to cover a chessboard of size
        :math:`2n\cdot 2n` by domino tiles if two diagonally opposite corners
        of the chessboard are removed.

        Note that the chessboard has :math:`4n^2-2` cells. Introduce a Boolean
        variable :math:`x_{ij}` for :math:`i,j\in[4n^2-2]` s.t. cells :math:`i`
        and :math:`j` are adjacent (no variables are introduced for pairs of
        non-adjacent cells). CB formulas comprise clauses (1)
        :math:`(\\neg{x_{ji} \\vee \\neg{x_{ki}}})` for every :math:`i,j \\neq
        k` meaning that no more than one adjacent cell can be paired with the
        current one; and (2) :math:`(\\vee_{j \in \\text{Adj}(i)} {x_{ij}})\,\,
        \\forall i` enforcing that every cell :math:`i` should be paired with
        at least one adjacent cell.

        Clearly, since the two diagonal corners are removed, the formula is
        unsatisfiable. Also note the following. Assuming that the number of
        black cells is larger than the number of the white ones, CB formulas
        are unsatisfiable even if only a half of the formula is present, e.g.
        when :math:`\\textsf{AtMost1}` constraints are formulated only for the
        white cells while the :math:`\\textsf{AtLeast1}` constraints are
        formulated only for the black cells. Depending on the value of
        parameter ``exhaustive`` the encoder applies the *complete* or
        *partial* formulation of the problem.

        Mutilated chessboard principle is known to be hard for resolution [3]_.

        :param size: problem size (:math:`n`)
        :param exhaustive: encode the problem exhaustively
        :param topv: current top variable identifier
        :param verb: defines whether or not the encoder is verbose

        :type size: int
        :type exhaustive: bool
        :type topv: int
        :type verb: bool

        :returns: object of class :class:`pysat.formula.CNF`.
    """

    def __init__(self, size, exhaustive=False, topv=0, verb=False):
        """
            Constructor.
        """

        # initializing CNF's internal parameters
        super(CB, self).__init__()

        # cell number
        cell = lambda i, j: (i - 1) * 2 * size + j

        # initializing the pool of variable ids
        vpool = IDPool(start_from=topv + 1)
        var = lambda c1, c2: vpool.id('edge: ({0}, {1})'.format(min(c1, c2), max(c1, c2)))

        for i in range(1, 2 * size + 1):
            for j in range(1, 2 * size + 1):
                adj = []

                # current cell
                c = cell(i, j)

                # removing first and last cells (they are white)
                if c in (1, 4 * size * size):
                    continue

                # each cell has 2 <= k <= 4 adjacents
                if i > 1 and cell(i - 1, j) != 1:
                    adj.append(var(c, cell(i - 1, j)))

                if j > 1 and cell(i, j - 1) != 1:
                    adj.append(var(c, cell(i, j - 1)))

                if i < 2 * size and cell(i + 1, j) != 4 * size * size:
                    adj.append(var(c, cell(i + 1, j)))

                if j < 2 * size and cell(i, j + 1) != 4 * size * size:
                    adj.append(var(c, cell(i, j + 1)))

                if not adj:  # when n == 1, no clauses will be added
                    continue

                # adding equals1 constraint for black and white cells
                if exhaustive:
                    cnf = CardEnc.equals(lits=adj, bound=1, encoding=EncType.pairwise)
                    self.extend(cnf.clauses)
                else:
                    # atmost1 constraint for white cells
                    if i % 2 and c % 2 or i % 2 == 0 and c % 2 == 0:
                        am1 = CardEnc.atmost(lits=adj, bound=1, encoding=EncType.pairwise)
                        self.extend(am1.clauses)
                    else:  # atleast1 constrant for black cells
                        self.append(adj)

        if verb:
            head = 'c CB formula for the chessboard of size {0}x{0}'.format(2 * size)
            head += '\nc The encoding is {0}exhaustive'.format('' if exhaustive else 'not ')
            self.comments.append(head)

            for v in range(1, vpool.top + 1):
                self.comments.append('c {0}; bool var: {1}'.format(vpool.obj(v), v))


#
#==============================================================================
class PAR(CNF, object):
    """
        Generator of the parity principle (PAR) formulas. Given an integer
        parameter :math:`n`, the principle states that no graph on :math:`2n+1`
        nodes consists of a complete perfect matching.

        The encoding of the parity principle uses :math:`\\binom{2n+1}{2}`
        variables :math:`x_{ij},i \\neq j`. If variable :math:`x_{ij}` is
        *true*, then there is an edge between nodes :math:`i` and :math:`j`.
        The formula consists of the following clauses: :math:`(\\vee_{j \\neq
        i}{x_{ij}})` for every :math:`i\in[2n+1]`, and :math:`(\\neg{x_{ij}}
        \\vee \\neg{x_{kj}})` for all distinct :math:`i,j,k \in [2n+1]`.

        The parity principle is known to be hard for resolution [4]_.

        :param size: problem size (:math:`n`)
        :param topv: current top variable identifier
        :param verb: defines whether or not the encoder is verbose

        :type size: int
        :type topv: int
        :type verb: bool

        :returns: object of class :class:`pysat.formula.CNF`.
    """

    def __init__(self, size, topv=0, verb=False):
        """
            Constructor.
        """

        # initializing CNF's internal parameters
        super(PAR, self).__init__()

        # initializing the pool of variable ids
        vpool = IDPool(start_from=topv + 1)
        var = lambda i, j: vpool.id('v_{0}_{1}'.format(min(i, j), max(i, j)))

        for i in range(1, 2 * size + 2):
            self.append([var(i, j) for j in range(1, 2 * size + 2) if j != i])

        for j in range(1, 2 * size + 2):
            for i, k in itertools.combinations(range(1, 2 * size + 2), 2):
                if i == j or k == j:
                    continue

                self.append([-var(i, j), -var(k, j)])

        if verb:
            self.comments.append('c Parity formula for m == {0} ({1} vertices)'.format(size, 2 * size + 1))
            for i in range(1, 2 * size + 2):
                for j in range(i + 1, 2 * size + 2):
                    self.comments.append('c edge: {0}; bool var: {1}'.format((i, j), var(i, j)))


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
    print('                               Available values: cb, gt, par, php (default = php)')
    print('        -v, --verb             Be verbose (show comments)')

#
#==============================================================================
if __name__ == '__main__':
    # parse command-line options
    ftype, kval, size, verb = parse_options()

    # generate formula
    if ftype == 'php':
        cnf = PHP(size, kval=kval, verb=verb)
    elif ftype == 'gt':  # gt
        cnf = GT(size, verb=verb)
    elif ftype == 'cb':  # cb
        cnf = CB(size, exhaustive=kval, verb=verb)
    else:  # parity
        cnf = PAR(size, verb=verb)

    # print formula in DIMACS to stdout
    cnf.to_fp(sys.stdout)
