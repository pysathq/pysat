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

        Functionality of this module is available only if the `Pindakaas`
        package is installed, e.g. from PyPI:

        .. code-block::

            $ pip install python-sat[pb]

    This module provides access to the pseudo-Boolean encodings of the
    `Pindakaas library <https://pypi.org/project/pindakaas/>`__ [1]_, a Rust
    library for encoding pseudo-Boolean and integer constraints into CNF.
    Pindakaas has a number of additional features (e.g. integer variables
    and further encodings) that are not accessible through this module. If
    a user needs any of them, Pindakaas can be used as a standalone library
    alongside PySAT.

    .. [1] Hendrik Bierlee, Jip J. Dekker. *Pindakaas*. Software.
        https://doi.org/10.5281/zenodo.10851855

    A *pseudo-Boolean constraint* is a constraint of the form:
    :math:`\\left(\\sum_{i=1}^n{a_i\\cdot x_i}\\right)\\circ k`, where
    :math:`a_i\\in\\mathbb{N}`, :math:`x_i\\in\\{y_i,\\neg{y_i}\\}`,
    :math:`y_i\\in\\mathbb{B}`, and :math:`\\circ\\in\\{\\leq,=,\\geq\\}`.
    Pseudo-Boolean constraints arise in a number of important practical
    applications. Thus, several *encodings* of pseudo-Boolean constraints into
    CNF formulas are known [2]_. The list of pseudo-Boolean encodings
    supported by this module include BDD [3]_ [4]_, sequential weight counters
    [5]_, sorting networks [3]_, adder networks [3]_, binary merge [6]_, the
    watchdog encoding [7]_, the generalized totalizer [8]_, and the mixed
    radix encoding [9]_.
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

    .. [7] Olivier Bailleux, Yacine Boufkhad, Olivier Roussel. *New
        Encodings of Pseudo-Boolean Constraints into CNF*. SAT 2009.
        pp. 181-194

    .. [8] Saurabh Joshi, Ruben Martins, Vasco Manquinho. *Generalized Totalizer
        Encoding for Pseudo-Boolean Constraints*. CP 2015. pp. 200-209

    .. [9] Anpeng Zha, Miyuki Koshimura, Hiroshi Fujita. *N-level Modulo-based
        CNF Encodings of Pseudo-Boolean Constraints for MaxSAT*. Constraints
        24(2). 2019. pp. 133-161

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import operator
from pysat.card import CardEnc
from pysat.formula import CNFPlus

# checking whether or not pindakaas is available
pindakaas_present = True
try:
    import pindakaas
except ImportError:
    pindakaas_present = False


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
            native     = 6
            watchdog   = 7
            totalizer  = 8
            mixedradix = 9

        The desired encoding can be selected either directly by its integer
        identifier, e.g. ``2``, or by its alphabetical name, e.g.
        ``EncType.seqcounter``.

        All the encodings are produced and returned as a list of clauses in
        the :class:`pysat.formula.CNFPlus` format.

        Note that the encoding type can be set to ``best``, in which case
        Pindakaas uses its default encoder for the shape of the constraint
        (e.g. the totalizer for PB and cardinality constraints). Any other
        encoding is applied to *every* shape of constraint, including
        cardinality and AtMostOne constraints. Finally, ``binmerge`` is the
        ``watchdog`` encoding of Pindakaas, counting with sorting networks
        rather than totalizers.
    """

    assert pindakaas_present, 'Package \'pindakaas\' is unavailable. Install it with \'pip install python-sat[pb]\'.'

    best       = 0
    bdd        = 1
    seqcounter = 2
    sortnetwrk = 3
    adder      = 4
    binmerge   = 5
    native     = 6
    watchdog   = 7
    totalizer  = 8
    mixedradix = 9

    # mapping from internal encoding identifiers to Pindakaas encoders and
    # their options
    _to_encoder = {
            best:       (None, {}),
            bdd:        (pindakaas.Encoder.DECISION_DIAGRAM, {}),
            seqcounter: (pindakaas.Encoder.SEQUENTIAL_COUNTER, {}),
            sortnetwrk: (pindakaas.Encoder.SORTING_NETWORK, {}),
            adder:      (pindakaas.Encoder.ADDER, {}),
            binmerge:   (pindakaas.Encoder.WATCHDOG, {'sorting_networks': True}),
            watchdog:   (pindakaas.Encoder.WATCHDOG, {}),
            totalizer:  (pindakaas.Encoder.TOTALIZER, {}),
            mixedradix: (pindakaas.Encoder.MIXED_RADIX, {})
        }

    # mapping from internal comparator identifiers to operators
    _to_cmp = {'<': operator.le, '>': operator.ge, '=': operator.eq}


#
#==============================================================================
def _pindakaas_db(top_id):
    """
        Create an empty ``pindakaas.CNF``, in which all new (auxiliary)
        variables are larger than ``top_id``.
    """

    db = pindakaas.CNF()
    db.new_vars(top_id)

    return db


#
#==============================================================================
def _pindakaas_cnf(db, top_id, vpool=None):
    """
        Convert the clauses of a ``pindakaas.CNF`` created by
        :func:`_pindakaas_db` into a :class:`pysat.formula.CNFPlus`. If
        ``vpool`` is given, it is updated to account for the auxiliary
        variables, i.e. those larger than ``top_id``.
    """

    ret = CNFPlus()
    ret.clauses = db._clauses_as_int()
    ret.nv = len(db.variables())

    # updating vpool if necessary
    if vpool:
        CardEnc._update_vids(ret, top_id, vpool)

    return ret


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
        :class:`pysat.formula.CNFPlus` representing the resulting CNF formula.

        Since the class is abstract, there is no need to create an object of
        it. Instead, the methods should be called directly as class methods,
        e.g. ``PBEnc.atmost(wlits, bound)`` or ``PBEnc.equals(lits, weights,
        bound)``. An example usage is the following:

        .. code-block:: python

            >>> from pysat.pb import *
            >>> cnf = PBEnc.atmost(lits=[1, 2, 3], weights=[1, 2, 3], bound=3)
            >>> print(cnf.clauses)
            [[-5, 4], [-6, 5], [-2, 5], [-1, 4], [-1, -2, 6], [-4, -3]]
            >>> cnf = PBEnc.equals(lits=[1, 2, 3], weights=[1, 2, 3], bound=3, encoding=EncType.bdd)
            >>> print(cnf.clauses)
            [[-1, 5], [1, -5], [-2, 4], [-5, 4], [2, -4], [5, -4], [-4, -3], [4, 3]]
    """

    @classmethod
    def _encode(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, comparator='<', conditionals=None):
        """
            This is the method that wraps the encoders of Pindakaas. Although the
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

            :rtype: :class:`pysat.formula.CNFPlus`
        """

        if encoding < 0 or encoding > 9:
            raise(NoSuchEncodingError(encoding))

        # checking if the bound is meaningless for any encoding
        if bound < 0:
            raise ValueError('Wrong bound: {0}'.format(bound))

        assert not top_id or not vpool, \
                'Use either a top id or a pool of variables but not both.'

        # we are going to return this formula
        ret = CNFPlus()

        # if the list of literals is empty, return empty formula
        if not lits:
            return ret

        # preparing weighted literals
        if weights:
            assert len(lits) == len(weights), 'Same number of literals and weights is expected.'
            lits, weights = list(lits), list(weights)
        else:
            if all(map(lambda lw: (type(lw) in (list, tuple)) and len(lw) == 2, lits)):
                # literals are already weighted
                lits, weights = map(list, zip(*lits))
            elif all(map(lambda l: type(l) is int, lits)):
                # no weights are provided => all weights are units
                lits, weights = list(lits), [1 for l in lits]
            else:
                assert 0, 'Incorrect literals given.'

        # obtaining the top id from the variable pool
        if vpool:
            top_id = vpool.top

        # choosing the maximum id among the current top and the list of literals
        if conditionals is None:
            conditionals = []
        top_id = max(map(lambda x: abs(x), conditionals + lits + [top_id if top_id != None else 0]))

        # native representation
        if encoding == 6:
            ret.nv = top_id

            if comparator == '<':
                ret.atmosts = [(lits, bound, weights)]
            elif comparator == '>':
                ret.atmosts = [(list(map(lambda l: -l, lits)), sum(weights) - bound, weights)]
            elif comparator:  # comparator == '='
                ret.atmosts = [(lits, bound, weights),
                        (list(map(lambda l: -l, lits)), sum(weights) - bound, weights)]

            return ret

        Lit = pindakaas.Lit.from_raw

        # the weighted sum (in place, as `+` copies the sum)
        lhs = 0
        for l, w in zip(lits, weights):
            lhs += w * Lit(l)

        constr = EncType._to_cmp[comparator](lhs, bound)
        encoder, options = EncType._to_encoder[encoding]

        db = _pindakaas_db(top_id)
        try:
            db.add_encoding(constr, encoder,
                            conditions=[Lit(l) for l in conditionals], **options)
        except pindakaas.Unsatisfiable:
            # the constraint cannot hold, so neither can all conditionals
            ret = _pindakaas_cnf(db, top_id, vpool=vpool)
            ret.clauses = [[-l for l in conditionals]]
            return ret

        return _pindakaas_cnf(db, top_id, vpool=vpool)

    @classmethod
    def leq(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, conditionals=None):
        """
            This method can be used for creating a CNF encoding of a LEQ
            (weighted AtMostK) constraint, i.e. of
            :math:`\\sum_{i=1}^{n}{a_i\\cdot x_i}\\leq k`. The resulting set
            of clauses is returned as an object of class
            :class:`.formula.CNFPlus`.

            The input list of literals can contain either integers or pairs
            ``(l, w)``, where ``l`` is an integer literal and ``w`` is an
            integer weight. The latter can be done only if no ``weights`` are
            specified separately. The type of encoding to use can be specified
            using the ``encoding`` parameter. By default, it is set to
            ``EncType.best``, i.e. it is up to Pindakaas to choose the
            encoding type.

            The final optional argument is ``conditionals``, where a list of
            literals can be passed to be used as the antecedent for the PB
            constraint, which makes it *"reified"*. If the argument is set to
            ``None``, the constraint won't be reified.

            :param lits: a list of literals in the sum.
            :param weights: a list of weights
            :param bound: the value of bound :math:`k`.
            :param top_id: top variable identifier used so far.
            :param vpool: variable pool for counting the number of variables.
            :param encoding: identifier of the encoding to use.
            :param conditionals: a list of variables that imply this constraint.

            :type lits: iterable(int)
            :type weights: iterable(int)
            :type bound: int
            :type top_id: integer or None
            :type vpool: :class:`.IDPool`
            :type encoding: integer
            :type conditionals: list(int) or None

            :rtype: :class:`pysat.formula.CNFPlus`
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                           vpool=vpool, encoding=encoding, comparator='<',
                           conditionals=conditionals)

    @classmethod
    def atmost(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, conditionals=None):
        """
            A synonym for :meth:`PBEnc.leq`.
        """

        return cls.leq(lits, weights=weights, bound=bound, top_id=top_id,
                       vpool=vpool, encoding=encoding,
                       conditionals=conditionals)

    @classmethod
    def geq(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, conditionals=None):
        """
            This method can be used for creating a CNF encoding of a GEQ
            (weighted AtLeastK) constraint, i.e. of
            :math:`\\sum_{i=1}^{n}{a_i\\cdot x_i}\\geq k`. The method shares
            the arguments and the return type with method :meth:`PBEnc.leq`.
            Please, see it for details.
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                           vpool=vpool, encoding=encoding, comparator='>',
                           conditionals=conditionals)

    @classmethod
    def atleast(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, conditionals=None):
        """
            A synonym for :meth:`PBEnc.geq`.
        """

        return cls.geq(lits, weights=weights, bound=bound, top_id=top_id,
                       vpool=vpool, encoding=encoding,
                       conditionals=conditionals)

    @classmethod
    def equals(cls, lits, weights=None, bound=1, top_id=None, vpool=None,
            encoding=EncType.best, conditionals=None):
        """
            This method can be used for creating a CNF encoding of a weighted
            EqualsK constraint, i.e. of :math:`\\sum_{i=1}^{n}{a_i\\cdot x_i}=
            k`. The method shares the arguments and the return type with
            method :meth:`PBEnc.leq`. Please, see it for details.
        """

        return cls._encode(lits, weights=weights, bound=bound, top_id=top_id,
                           vpool=vpool, encoding=encoding, comparator='=',
                           conditionals=conditionals)
