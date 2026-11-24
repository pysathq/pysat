#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## vector.py
##
##  Created on: Nov 21, 2026
##      Author: Ali Keramatipour
##      E-mail: alikeramatipour@gmail.com
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        VecEnc

    ==================
    Module description
    ==================

    This module provides CNF encodings of constraints over *vectors* of
    Boolean literals, i.e. ordered lists of literals such as ``[1, -2, 3]``.
    Similarly to :mod:`pysat.card` and :mod:`pysat.pb`, each encoding takes
    the literals of a constraint and returns a CNF formula, which can be
    added to a SAT solver or combined with other formulas.

    A constraint over vectors concerns the *truth values* of the literals
    under an assignment, not their integer identifiers. For instance, the
    vector ``[1, -2]`` takes the value :math:`(1, 1)` under the assignment
    :math:`\\{x_1 = 1, x_2 = 0\\}`.

    Currently, the module supports *lexicographic ordering* constraints.
    Given vectors :math:`a = (a_1, \\ldots, a_n)` and
    :math:`b = (b_1, \\ldots, b_m)`, vector :math:`a` is lexicographically
    smaller than :math:`b`, written :math:`a <_{lex} b`, if either
    :math:`a_k = 0` and :math:`b_k = 1` at the first position :math:`k`
    where the two vectors differ, or :math:`a` is a proper prefix of
    :math:`b`. The first position is thus the most significant one, and the
    order is the same as the one Python uses for tuples of Booleans. As
    usual, :math:`a \\leq_{lex} b` means that :math:`a <_{lex} b` or
    :math:`a = b`. Lexicographic ordering constraints are widely used for
    *symmetry breaking*, e.g. to order interchangeable rows of a matrix of
    variables.

    Access to all the encodings can be made through the main class of this
    module, which is :class:`.VecEnc`.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import numbers

from pysat.formula import CNF


#
#==============================================================================
class VecEnc:
    """
        This abstract class is responsible for the creation of constraints
        over vectors of literals encoded to a CNF formula. The class has two
        *class methods* for creating lexicographic ordering constraints:
        :meth:`lex_leq` for :math:`a \\leq_{lex} b` and :meth:`lex_lt` for
        :math:`a <_{lex} b`. Given two lists of literals, each of these
        methods returns an object of class :class:`pysat.formula.CNF`
        representing the resulting CNF formula.

        Since the class is abstract, there is no need to create an object of
        it. Instead, the methods should be called directly as class methods,
        e.g. ``VecEnc.lex_leq(a, b)`` or ``VecEnc.lex_lt(a, b)``.

        Both encodings introduce a helper variable for each position of the
        shorter vector but the last one, which is forced to be true whenever
        the vectors are equal up to that position, and at most three clauses
        per position. The helper variables are numbered above ``top_id``, or
        above the largest variable of the vectors if that one is larger.
        Instead of ``top_id``, one may want to use a pool of variable
        identifiers ``vpool``, which is automatically updated during the
        method call and whose occupied ranges are skipped. Note that
        parameters ``top_id`` and ``vpool`` **cannot** be specified
        *simultaneously*. In both cases, the ``nv`` attribute of the
        resulting formula is the largest variable identifier used so far.
        An example usage is the following:

        .. code-block:: python

            >>> from pysat.formula import IDPool
            >>> from pysat.vector import VecEnc
            >>> vpool = IDPool(occupied=[[5, 10]])
            >>> cnf = VecEnc.lex_leq([1, 2], [3, 4], vpool=vpool)
            >>> print(cnf.clauses)
            [[-1, 3], [-1, 11], [3, 11], [-11, -2, 4]]
            >>> print(cnf.nv, vpool.top)
            11 11
    """

    @classmethod
    def lex_leq(cls, a, b, top_id=None, vpool=None):
        """
            This method can be used for creating a CNF encoding of a
            lexicographic ordering constraint, i.e. of
            :math:`a \\leq_{lex} b`, where :math:`a` and :math:`b` are
            vectors of literals. The vectors may have different lengths (see
            the module description for how such vectors are ordered). Equal
            vectors satisfy the constraint. The helper variables of the
            encoding are numbered as described in :class:`VecEnc`.

            :param a: the left-hand side vector of literals.
            :param b: the right-hand side vector of literals.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.

            :type a: iterable(int)
            :type b: iterable(int)
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`

            :raises ValueError: if a vector contains something other than a
                non-zero integer, e.g. ``0`` or ``True``.

            :rtype: :class:`pysat.formula.CNF`

            Example:

            .. code-block:: python

                >>> from pysat.vector import VecEnc
                >>> cnf = VecEnc.lex_leq([1, 2], [3, 4])
                >>> print(cnf.clauses)
                [[-1, 3], [-1, 5], [3, 5], [-5, -2, 4]]
                >>> print(cnf.nv)
                5
        """

        return cls._encode(a, b, False, top_id, vpool)

    @classmethod
    def lex_lt(cls, a, b, top_id=None, vpool=None):
        """
            This method can be used for creating a CNF encoding of a strict
            lexicographic ordering constraint, i.e. of
            :math:`a <_{lex} b`, where :math:`a` and :math:`b` are vectors
            of literals. The vectors may have different lengths (see the
            module description for how such vectors are ordered). Equal
            vectors do not satisfy the constraint. The helper variables of
            the encoding are numbered as described in :class:`VecEnc`.

            :param a: the left-hand side vector of literals.
            :param b: the right-hand side vector of literals.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.

            :type a: iterable(int)
            :type b: iterable(int)
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`

            :raises ValueError: if a vector contains something other than a
                non-zero integer, e.g. ``0`` or ``True``.

            :rtype: :class:`pysat.formula.CNF`

            Example:

            .. code-block:: python

                >>> from pysat.vector import VecEnc
                >>> cnf = VecEnc.lex_lt([1, 2], [3, 4])
                >>> print(cnf.clauses)
                [[-1, 3], [-1, 5], [3, 5], [-5, -2], [-5, 4]]
                >>> print(cnf.nv)
                5
        """

        return cls._encode(a, b, True, top_id, vpool)

    @classmethod
    def _encode(cls, a, b, strict, top_id, vpool):
        """
            This is the method that implements both :meth:`lex_leq` and
            :meth:`lex_lt`. Although the method can be invoked directly, a
            user is expected to call one of these two methods instead.

            :param a: the left-hand side vector of literals.
            :param b: the right-hand side vector of literals.
            :param strict: whether ``a`` must be strictly smaller than ``b``.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.

            :type a: list(int)
            :type b: list(int)
            :type strict: bool
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`

            :raises ValueError: if a vector contains something other than a
                non-zero integer, e.g. ``0`` or ``True``.

            :rtype: :class:`pysat.formula.CNF`
        """

        assert not top_id or not vpool, (
            'Use either a top id or a pool of variables but not both.')

        # accept any iterables, e.g. tuples or numpy arrays, and work on new
        # lists, so that the caller's vectors are never modified
        a, b = list(a), list(b)

        for lit in a + b:
            # bool is a subclass of int, but True is not meant as literal 1
            integral = isinstance(lit, numbers.Integral)
            if not integral or isinstance(lit, bool) or lit == 0:
                raise ValueError('Not a literal: {0!r}'.format(lit))

        # integers of other types, e.g. from numpy, become plain ints
        a, b = [int(lit) for lit in a], [int(lit) for lit in b]

        if top_id is None:
            top_id = 0
        top_id = max([top_id] + [abs(lit) for lit in a + b])

        # positions are compared up to the end of the shorter vector
        size = min(len(a), len(b))

        # if a is longer and starts with b, then a is larger, so the common
        # part of a must be strictly smaller; if a is shorter, an equal
        # common part is enough
        if len(a) != len(b):
            strict = len(a) > len(b)

        if vpool:
            vpool.top = max(top_id, vpool.top)
            e = [vpool.id() for _ in range(size - 1)]
            nv = vpool.top
        else:
            e = [i for i in range(top_id + 1, top_id + size)]
            nv = max([top_id] + e)

        clauses = cls._build_clauses(a[:size], b[:size], e, strict)

        cnf = CNF(from_clauses=clauses)
        cnf.nv = nv  # the largest variable used so far

        return cnf

    @classmethod
    def _build_clauses(cls, a, b, e, strict=False):
        """
            Create the clauses of :math:`a \\leq_{lex} b`, or of
            :math:`a <_{lex} b` if ``strict`` is true, for two vectors of the
            same length. Helper variable ``e[i]`` is forced to be true
            whenever ``a`` and ``b`` are equal on positions ``0`` to ``i``.
            There is no helper variable for the last position.

            :param a: the left-hand side vector of literals.
            :param b: the right-hand side vector of literals.
            :param e: the helper variables, one fewer than the positions.
            :param strict: whether ``a`` must be strictly smaller than ``b``.

            :type a: list(int)
            :type b: list(int)
            :type e: list(int)
            :type strict: bool

            :rtype: list(list(int))
        """

        if not a:
            # empty vectors are equal: a non-strict comparison always holds,
            # and a strict one never does (an empty clause is unsatisfiable)
            return [[]] if strict else []

        clauses = []
        last = len(a) - 1

        for i in range(len(a)):
            # clauses only apply if all previous positions are equal
            prefix = [-e[i - 1]] if i > 0 else []

            if i < last:
                clauses += [prefix + [-a[i], b[i]],
                            prefix + [-a[i], e[i]],
                            prefix + [b[i], e[i]]]
            elif strict:
                # a[i] must be false and b[i] must be true
                clauses += [prefix + [-a[i]],
                            prefix + [b[i]]]
            else:
                # a[i] must not be larger than b[i]
                clauses.append(prefix + [-a[i], b[i]])

        return clauses
