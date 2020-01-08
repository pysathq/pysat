#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## pb.py
##
##  Created on: Mar 13, 2019
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        EncType
        PBEnc

    ==================
    Module description
    ==================

    .. note::

        Functionality of this module is available only if the `PyPBLib`
        package is installed, e.g. from PyPI:

        .. code-block::

            $ pip install pypblib

    This module provides access to the basic functionality of the `PyPBLib
    library <https://pypi.org/project/pypblib/>`__ developed by the `Logic
    Optimization Group <http://ulog.udl.cat/>`__ of the University of Lleida.
    PyPBLib provides a user with an extensive Python API to the well-known
    `PBLib library <http://tools.computational-logic.org/content/pblib.php>`__
    [1]_. Note the PyPBLib has a number of `additional features
    <http://hardlog.udl.cat/static/doc/pypblib/html/index.html>`__ that cannot
    be accessed through PySAT *at this point*. (One concrete example is a
    range of cardinality encodings, which clash with the internal
    :mod:`pysat.card` module.) If a user needs some functionality of PyPBLib
    missing in this module, he/she may apply PyPBLib as a standalone library,
    when working with PySAT.

    .. [1] Tobias Philipp, Peter Steinke. *PBLib - A Library for Encoding
        Pseudo-Boolean Constraints into CNF*. SAT 2015. pp. 9-16

    A *pseudo-Boolean constraint* is a constraint of the form:
    :math:`\left(\sum_{i=1}^n{a_i\cdot x_i}\\right)\circ k`, where
    :math:`a_i\in\mathbb{N}`, :math:`x_i\in\{y_i,\\neg{y_i}\}`,
    :math:`y_i\in\mathbb{B}`, and :math:`\circ\in\{\leq,=,\geq\}`.
    Pseudo-Boolean constraints arise in a number of important practical
    applications. Thus, several *encodings* of pseudo-Boolean constraints into
    CNF formulas are known [2]_. The list of pseudo-Boolean encodings
    supported by this module include BDD [3]_ [4]_, sequential weight counters
    [5]_, sorting networks [3]_, adder networks [3]_, and binary merge [6]_.
    Access to all cardinality encodings can be made through the main class of
    this module, which is :class:`.PBEnc`.

    .. [2] Olivier Roussel, Vasco M. Manquinho. *Pseudo-Boolean and
        Cardinality Constraints*. Handbook of Satisfiability. 2009.
        pp. 695-733

    .. [3] Niklas Eén, Niklas Sörensson. *Translating Pseudo-Boolean
        Constraints into SAT*. JSAT. vol. 2(1-4). 2006. pp. 1-26

    .. [4] Ignasi Abío, Robert Nieuwenhuis, Albert Oliveras,
        Enric Rodríguez-Carbonell. *BDDs for Pseudo-Boolean Constraints -
        Revisited*. SAT. 2011. pp. 61-75

    .. [5] Steffen Hölldobler, Norbert Manthey, Peter Steinke. *A Compact
        Encoding of Pseudo-Boolean Constraints into SAT*. KI. 2012.
        pp. 107-118

    .. [6] Norbert Manthey, Tobias Philipp, Peter Steinke. *A More Compact
        Translation of Pseudo-Boolean Constraints into CNF Such That
        Generalized Arc Consistency Is Maintained*. KI. 2014. pp. 123-134

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import math
from pysat.formula import CNF

# checking whether or not pypblib is available and working as expected
pblib_present = True
try:
    from pypblib import pblib
except ImportError:
    pblib_present = False


#
#==============================================================================
class NoSuchEncodingError(Exception):
    """
        This exception is raised when creating an unknown LEQ, GEQ, or Equals
        constraint encoding.
    """

    pass


#
#==============================================================================
class EncType(object):
    """
        This class represents a C-like ``enum`` type for choosing the
        pseudo-Boolean encoding to use. The values denoting the encodings are:

        ::

            best       = 0
            bdd        = 1
            seqcounter = 2
            sortnetwrk = 3
            adder      = 4
            binmerge   = 5

        The desired encoding can be selected either directly by its integer
        identifier, e.g. ``2``, or by its alphabetical name, e.g.
        ``EncType.seqcounter``.

        All the encodings are produced and returned as a list of clauses in
        the :class:`pysat.formula.CNF` format.

        Note that the encoding type can be set to ``best``, in which case the
        encoder selects one of the other encodings from the list (in most
        cases, this invokes the ``bdd`` encoder).
    """

    best       = 0
    bdd        = 1
    seqcounter = 2
    sortnetwrk = 3
    adder      = 4
    binmerge   = 5

    # mapping from internal encoding identifiers to the ones of PyPBLib
    _to_pbenc = {
            best:       pblib.PB_BEST,
            bdd:        pblib.PB_BDD,
            seqcounter: pblib.PB_SWC,
            sortnetwrk: pblib.PB_SORTINGNETWORKS,
            adder:      pblib.PB_ADDER,
            binmerge:   pblib.PB_BINARY_MERGE
        }

    # mapping from internal comparator identifiers to the ones of PyPBLib
    _to_pbcmp = {
            '<': pblib.LEQ,
            '>': pblib.GEQ,
            '=': pblib.BOTH
        }


#
#==============================================================================
class PBEnc(object):
    """
        Abstract class responsible for the creation of pseudo-Boolean
        constraints encoded to a CNF formula. The class has three main *class
        methods* for creating LEQ, GEQ, and Equals constraints. Given (1)
        either a list of weighted literals or a list of unweighted literals
        followed by a list of weights, (2) an integer bound and an encoding
        type, each of these methods returns an object of class
        :class:`pysat.formula.CNF` representing the resulting CNF formula.

        Since the class is abstract, there is no need to create an object of
        it. Instead, the methods should be called directly as class methods,
        e.g. ``PBEnc.atmost(wlits, bound)`` or ``PBEnc.equals(lits, weights,
        bound)``. An example usage is the following:

        .. code-block:: python

            >>> from pysat.pb import *
            >>> cnf = PBEnc.atmost(lits=[1, 2, 3], weights=[1, 2, 3], bound=3)
            >>> print(cnf.clauses)
            [[4], [-1, -5], [-2, -5], [5, -3, -6], [6]]
            >>> cnf = PBEnc.equals(lits=[1, 2, 3], weights=[1, 2, 3], bound=3, encoding=EncType.bdd)
            >>> print(cnf.clauses)
            [[4], [-5, -2], [-5, 2, -1], [-5, -1], [-6, 1], [-7, -2, 6], [-7, 2], [-7, 6], [-8, -3, 5], [-8, 3, 7], [-8, 5, 7], [8]]
    """

    @classmethod
    def _update_vids(cls, cnf, vpool):
        """
            Update variable ids in the given formula and id pool.

            :param cnf: a list of literals in the sum.
            :param vpool: the value of bound :math:`k`.

            :type cnf: :class:`.formula.CNF`
            :type vpool: :class:`.formula.IDPool`
        """

        top, vmap = vpool.top, {}  # current top and variable mapping

        # creating a new variable mapping, taking into
        # account variables marked as "occupied"
        while top < cnf.nv:
            top += 1
            vpool.top += 1

            while vpool._occupied and vpool.top >= vpool._occupied[0][0]:
                if vpool.top <= vpool._occupied[0][1] + 1:
                    vpool.top = vpool._occupied[0][1] + 1

                vpool._occupied.pop(0)

            vmap[top] = vpool.top

        # updating the clauses
        for cl in cnf.clauses:
            cl[:] = map(lambda l: int(math.copysign(vmap[abs(l)], l)) if abs(l) in vmap else l, cl)

        # updating the number of variables
        cnf.nv = vpool.top

    @classmethod
    def _encode(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, comparator='<'):
        """
            This is the method that wraps the encoder of PyPBLib. Although the
            method can be invoked directly, a user is expected to call one of
            the following methods instead: :meth:`atmost`, :meth:`atleast`, or
            :meth:`equals`.

            The list of literals can contain either integers or pairs ``(l,
            w)``, where ``l`` is an integer literal and ``w`` is an integer
            weight. The latter can be done only if no ``weights`` are
            specified separately.

            :param lits: a list of literals in the sum.
            :param weights: a list of weights
            :param bound: the value of bound :math:`k`.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.
            :param encoding: identifier of the encoding to use.
            :param comparator: identifier of the comparison operator

            :type lits: iterable(int)
            :type weights: iterable(int)
            :type bound: int
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`
            :type encoding: integer
            :type comparator: str

            :rtype: :class:`pysat.formula.CNF`
        """

        assert pblib_present, 'Package \'pypblib\' is unavailable. Check your installation.'

        if encoding < 0 or encoding > 5:
            raise(NoSuchEncodingError(encoding))

        assert lits, 'No literals are provided.'

        assert not top_id or not vpool, \
                'Use either a top id or a pool of variables but not both.'

        # preparing weighted literals
        if weights:
            assert len(lits) == len(weights), 'Same number of literals and weights is expected.'
            wlits = [pblib.WeightedLit(l, w) for l, w in zip(lits, weights)]
        else:
            if all(map(lambda lw: (type(lw) in (list, tuple)) and len(lw) == 2, lits)):
                # literals are already weighted
                wlits = [pblib.WeightedLit(*wl) for wl in lits]
                lits = zip(*lits)[0]  # unweighted literals for getting top_id
            elif all(map(lambda l: type(l) is int, lits)):
                # no weights are provided => all weights are units
                wlits = [pblib.WeightedLit(l, 1) for l in lits]
            else:
                assert 0, 'Incorrect literals given.'

        # obtaining the top id from the variable pool
        if vpool:
            top_id = vpool.top

        if not top_id:
            top_id = max(map(lambda x: abs(x), lits))

        # pseudo-Boolean constraint and variable manager
        constr = pblib.PBConstraint(wlits, EncType._to_pbcmp[comparator], bound)
        varmgr = pblib.AuxVarManager(top_id + 1)

        # encoder configuration
        config = pblib.PBConfig()
        config.set_PB_Encoder(EncType._to_pbenc[encoding])

        # encoding
        result = pblib.VectorClauseDatabase(config)
        pb2cnf = pblib.Pb2cnf(config)
        pb2cnf.encode(constr, result, varmgr)

        # extracting clauses
        ret = CNF(from_clauses=result.get_clauses())

        # updating vpool if necessary
        if vpool:
            if vpool._occupied and vpool.top <= vpool._occupied[0][0] <= ret.nv:
                cls._update_vids(ret, vpool)
            else:
                vpool.top = ret.nv - 1
                vpool._next()

        return ret

    @classmethod
    def leq(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best):
        """
            This method can be used for creating a CNF encoding of a LEQ
            (weighted AtMostK) constraint, i.e. of
            :math:`\sum_{i=1}^{n}{a_i\cdot x_i}\leq k`. The resulting set of
            clauses is returned as an object of class :class:`.formula.CNF`.

            The input list of literals can contain either integers or pairs
            ``(l, w)``, where ``l`` is an integer literal and ``w`` is an
            integer weight. The latter can be done only if no ``weights`` are
            specified separately. The type of encoding to use can be specified
            using the ``encoding`` parameter. By default, it is set to
            ``EncType.best``, i.e. it is up to the PBLib encoder to choose the
            encoding type.

            :param lits: a list of literals in the sum.
            :param weights: a list of weights
            :param bound: the value of bound :math:`k`.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.
            :param encoding: identifier of the encoding to use.

            :type lits: iterable(int)
            :type weights: iterable(int)
            :type bound: int
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`
            :type encoding: integer

            :rtype: :class:`pysat.formula.CNF`
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                vpool=vpool, encoding=encoding, comparator='<')

    @classmethod
    def atmost(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best):
        """
            A synonim for :meth:`PBEnc.leq`.
        """

        return cls.leq(lits, weights=weights, bound=bound, top_id=top_id,
                vpool=vpool, encoding=encoding)

    @classmethod
    def geq(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best):
        """
            This method can be used for creating a CNF encoding of a GEQ
            (weighted AtLeastK) constraint, i.e. of
            :math:`\sum_{i=1}^{n}{a_i\cdot x_i}\geq k`. The method shares the
            arguments and the return type with method :meth:`PBEnc.leq`.
            Please, see it for details.
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                vpool=vpool, encoding=encoding, comparator='>')

    @classmethod
    def atleast(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best):
        """
            A synonym for :meth:`PBEnc.geq`.
        """

        return cls.geq(lits, weights=weights, bound=bound, top_id=top_id,
                vpool=vpool, encoding=encoding)

    @classmethod
    def equals(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best):
        """
            This method can be used for creating a CNF encoding of a weighted
            EqualsK constraint, i.e. of :math:`\sum_{i=1}^{n}{a_i\cdot x_i}=
            k`. The method shares the arguments and the return type with
            method :meth:`PBEnc.leq`. Please, see it for details.
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                vpool=vpool, encoding=encoding, comparator='=')
