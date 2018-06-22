#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## card.py
##
##  Created on: Sep 26, 2017
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
        CardEnc
        ITotalizer

    ==================
    Module description
    ==================

    This module provides access to various *cardinality constraint* [1]_
    encodings to formulas in conjunctive normal form (CNF). These include
    pairwise [2]_, bitwise [2]_, ladder/regular [3]_ [4]_, sequential counters
    [5]_, sorting [6]_ and cardinality networks [7]_, totalizer [8]_, modulo
    totalizer [9]_, and modulo totalizer for :math:`k`-cardinality [10]_, as
    well as a *native* cardinality constraint representation supported by the
    `MiniCard solver <https://github.com/liffiton/minicard>`__.

    .. [1] Olivier Roussel, Vasco M. Manquinho. *Pseudo-Boolean and Cardinality
        Constraints*. Handbook of Satisfiability.  2009. pp. 695-733

    .. [2] Steven David Prestwich. *CNF Encodings*. Handbook of Satisfiability.
        2009. pp. 75-97

    .. [3] Carlos Ansótegui, Felip Manyà. *Mapping Problems with Finite-Domain
        Variables to Problems with Boolean Variables*. SAT (Selected Papers)
        2004. pp. 1-15

    .. [4] Ian P. Gent, Peter Nightingale. *A New Encoding of Alldifferent Into
        SAT*. In International workshop on modelling and reformulating
        constraint satisfaction problems 2004. pp. 95-110

    .. [5] Carsten Sinz. *Towards an Optimal CNF Encoding of Boolean
        Cardinality Constraints*. CP 2005. pp. 827-831

    .. [6] Kenneth E. Batcher. *Sorting Networks and Their Applications*.
        AFIPS Spring Joint Computing Conference 1968. pp. 307-314

    .. [7] Roberto Asin, Robert Nieuwenhuis, Albert Oliveras,
        Enric Rodriguez-Carbonell. *Cardinality Networks and Their
        Applications*. SAT 2009. pp. 167-180

    .. [8] Olivier Bailleux, Yacine Boufkhad. *Efficient CNF Encoding of
        Boolean Cardinality Constraints*. CP 2003. pp. 108-122

    .. [9] Toru Ogawa, Yangyang Liu, Ryuzo Hasegawa, Miyuki Koshimura,
        Hiroshi Fujita. *Modulo Based CNF Encoding of Cardinality Constraints
        and Its Application to MaxSAT Solvers*. ICTAI 2013. pp. 9-17

    .. [10] António Morgado, Alexey Ignatiev, Joao Marques-Silva. *MSCG: Robust
        Core-Guided MaxSAT Solving*. System Description. JSAT 2015. vol. 9,
        pp. 129-134

    A cardinality constraint is a constraint of the form:
    :math:`\sum_{i=1}^n{x_i}\leq k`. Cardinality constraints are ubiquitous in
    practical problem formulations. Note that the implementation of the
    pairwise, bitwise, and ladder encodings can only deal with AtMost1
    constraints, e.g. :math:`\sum_{i=1}^n{x_i}\leq 1`.

    Access to all cardinality encodings can be made through the main class of
    this module, which is :class:`.CardEnc`.

    Additionally, to the standard cardinality encodings that are basically
    "static" CNF formulas, the module is designed to able to construct
    *incremental* cardinality encodings, i.e. those that can be incrementally
    extended at a later stage. At this point only the *iterative totalizer*
    [11]_ encoding is supported. Iterative totalizer can be accessed with the
    use of the :class:`.ITotalizer` class.

    .. [11] Ruben Martins, Saurabh Joshi, Vasco M. Manquinho, Inês Lynce.
        *Incremental Cardinality Constraints for MaxSAT*. CP 2014. pp. 531-548

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from pysat.formula import CNF, CNFPlus
import pycard
import signal


#
#==============================================================================
class NoSuchEncodingError(Exception):
    """
        This exception is raised when creating an unknown an AtMostk, AtLeastK,
        or EqualK constraint encoding.
    """

    pass


#
#==============================================================================
class EncType(object):
    """
        This class represents a C-like ``enum`` type for choosing the
        cardinality encoding to use. The values denoting the encodings are:

        ::

            pairwise    = 0
            seqcounter  = 1
            sortnetwrk  = 2
            cardnetwrk  = 3
            bitwise     = 4
            ladder      = 5
            totalizer   = 6
            mtotalizer  = 7
            kmtotalizer = 8
            native      = 9

        The desired encoding can be selected either directly by its integer
        identifier, e.g. ``2``, or by its alphabetical name, e.g.
        ``EncType.sortnetwrk``.

        Note that while most of the encodings are produced as a list of
        clauses, the "native" encoding of `MiniCard
        <https://github.com/liffiton/minicard>`__ is managed as one clause.
        Given an AtMostK constraint :math:`\sum_{i=1}^n{x_i\leq k}`, the native
        encoding represents it as a pair ``[lits, k]``, where ``lits`` is a
        list of size ``n`` containing literals in the sum.
    """

    pairwise    = 0
    seqcounter  = 1
    sortnetwrk  = 2
    cardnetwrk  = 3
    bitwise     = 4
    ladder      = 5
    totalizer   = 6
    mtotalizer  = 7
    kmtotalizer = 8
    native      = 9  # native representation used by Minicard


#
#==============================================================================
class CardEnc(object):
    """
        This abstract class is responsible for the creation of cardinality
        constraints encoded to a CNF formula. The class has three *class
        methods* for creating AtMostK, AtLeastK, and EqualsK constraints. Given
        a list of literals, an integer bound and an encoding type, each of
        these methods returns an object of class :class:`pysat.formula.CNFPlus`
        representing the resulting CNF formula.

        Since the class is abstract, there is no need to create an object of
        it. Instead, the methods should be called directly as class methods,
        e.g. ``CardEnc.atmost(lits, bound)`` or ``CardEnc.equals(lits,
        bound)``. An example usage is the following:

        .. code-block:: python

            >>> from pysat.card import *
            >>> cnf = CardEnc.atmost(lits=[1, 2, 3], encoding=EncType.pairwise)
            >>> print cnf.clauses
            [[-1, -2], [-1, -3], [-2, -3]]
            >>> cnf = CardEnc.equals(lits=[1, 2, 3], encoding=EncType.pairwise)
            >>> print cnf.clauses
            [[1, 2, 3], [-1, -2], [-1, -3], [-2, -3]]
    """

    @classmethod
    def atmost(cls, lits, bound=1, top_id=None, encoding=EncType.seqcounter):
        """
            This method can be used for creating a CNF encoding of an AtMostK
            constraint, i.e. of :math:`\sum_{i=1}^{n}{x_i}\leq k`. The method
            shares the arguments and the return type with method
            :meth:`CardEnc.atleast`. Please, see it for details.
        """

        if encoding < 0 or encoding > 9:
            raise(NoSuchEncodingError(encoding))

        if not top_id:
            top_id = max(map(lambda x: abs(x), lits))

        # we are going to return this formula
        ret = CNFPlus()

        # MiniCard's native representation is handled separately
        if encoding == 9:
            ret.atmosts, ret.nv = [(lits, bound)], top_id
            return ret

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        res = pycard.encode_atmost(lits, bound, top_id, encoding)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        if res:
            ret.clauses, ret.nv = res

        return ret

    @classmethod
    def atleast(cls, lits, bound=1, top_id=None, encoding=EncType.seqcounter):
        """
            This method can be used for creating a CNF encoding of an AtLeastK
            constraint, i.e. of :math:`\sum_{i=1}^{n}{x_i}\geq k`. The method
            takes 1 mandatory argument ``lits`` and 3 default arguments can be
            specified: ``bound``, ``top_id``, and ``encoding``.

            :param lits: a list of literals in the sum.
            :param bound: the value of bound :math:`k`.
            :param top_id: top variable identifier used so far.
            :param encoding: identifier of the encoding to use.

            :type lits: list(int)
            :type bound: int
            :type top_id: integer or None
            :type encoding: integer

            Parameter ``top_id`` serves to increase integer identifiers of
            auxiliary variables introduced during the encoding process. This is
            helpful when augmenting an existing CNF formula with the new
            cardinality encoding to make sure there is no collision between
            identifiers of the variables. If specified the identifiers of the
            first auxiliary variable will be ``top_id+1``.

            The default value of ``encoding`` is :attr:`Enctype.seqcounter`.

            The method *translates* the AtLeast constraint into an AtMost
            constraint by *negating* the literals of ``lits``, creating a new
            bound :math:`n-k` and invoking :meth:`CardEnc.atmost` with the
            modified list of literals and the new bound.

            :raises NoSuchEncodingError: if encoding does not exist.

            :rtype: a :class:`.CNFPlus` object where the new \
            clauses (or the new native atmost constraint) are stored.
        """

        if encoding < 0 or encoding > 9:
            raise(NoSuchEncodingError(encoding))

        if not top_id:
            top_id = max(map(lambda x: abs(x), lits))

        # we are going to return this formula
        ret = CNFPlus()

        # Minicard's native representation is handled separately
        if encoding == 9:
            ret.atmosts, ret.nv = [([-l for l in lits], len(lits) - bound)], top_id
            return ret

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        res = pycard.encode_atleast(lits, bound, top_id, encoding)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        if res:
            ret.clauses, ret.nv = res

        return ret

    @classmethod
    def equals(cls, lits, bound=1, top_id=None, encoding=EncType.seqcounter):
        """
            This method can be used for creating a CNF encoding of an EqualsK
            constraint, i.e. of :math:`\sum_{i=1}^{n}{x_i}= k`. The method
            makes consecutive calls of both :meth:`CardEnc.atleast` and
            :meth:`CardEnc.atmost`. It shares the arguments and the return type
            with method :meth:`CardEnc.atleast`. Please, see it for details.
        """

        res1 = cls.atleast(lits, bound, top_id, encoding)
        res2 = cls.atmost(lits, bound, res1.nv, encoding)

        # merging together AtLeast and AtMost constraints
        res1.nv = res2.nv
        res1.clauses.extend(res2.clauses)
        res1.atmosts.extend(res2.atmosts)

        return res1


#
#==============================================================================
class ITotalizer(object):
    """
        This class implements the iterative totalizer encoding [11]_. Note that
        :class:`ITotalizer` can be used only for creating AtMostK constraints.
        In contrast to class :class:`EncType`, this class is not abstract and
        its objects once created can be reused several times. The idea is that
        a *totalizer tree* can be extended, or the bound can be increased, as
        well as two totalizer trees can be merged into one.

        The constructor of the class object takes 3 default arguments.

        :param lits: a list of literals to sum.
        :param ubound: the largest potential bound to use.
        :param top_id: top variable identifier used so far.

        :type lits: list(int)
        :type ubound: int
        :type top_id: integer or None

        The encoding of the current tree can be accessed with the use of
        :class:`.CNF` variable stored as ``self.cnf``. Potential bounds **are
        not** imposed by default but can be added as unit clauses in the final
        CNF formula. The bounds are stored in the list of Boolean variables as
        ``self.rhs``. A concrete bound :math:`k` can be enforced by considering
        a unit clause ``-self.rhs[k]``. **Note** that ``-self.rhs[0]`` enforces
        all literals of the sum to be *false*.

        An :class:`ITotalizer` object should be deleted if it is not needed
        anymore.

        Possible usage of the class is shown below:

        .. code-block:: python

            >>> from pysat.card import ITotalizer
            >>> t = ITotalizer(lits=[1, 2, 3], ubound=1)
            >>> print t.cnf.clauses
            [[-2, 4], [-1, 4], [-1, -2, 5], [-4, 6], [-5, 7], [-3, 6], [-3, -4, 7]]
            >>> print t.rhs
            [6, 7]
            >>> t.delete()

        Alternatively, an object can be created using the ``with`` keyword. In
        this case, the object is deleted automatically:

        .. code-block:: python

            >>> from pysat.card import ITotalizer
            >>> with ITotalizer(lits=[1, 2, 3], ubound=1) as t:
            ...     print t.cnf.clauses
            [[-2, 4], [-1, 4], [-1, -2, 5], [-4, 6], [-5, 7], [-3, 6], [-3, -4, 7]]
            ...     print t.rhs
            [6, 7]
    """

    def __init__(self, lits=[], ubound=1, top_id=None):
        """
            Constructor.
        """

        # internal totalizer object
        self.tobj = None

        # its characteristics
        self.lits = []
        self.ubound = None
        self.top_id = None

        # encoding result
        self.cnf = CNF()  # CNF formula encoding the totalizer object
        self.rhs = []     # upper bounds on the number of literals (rhs)

        # number of new clauses
        self.nof_new = 0

        # this newly created totalizer object is not yet merged in any other
        self._merged = False

        if lits:
            self.new(lits=lits, ubound=ubound, top_id=top_id)

    def new(self, lits=[], ubound=1, top_id=None):
        """
            The actual constructor of :class:`ITotalizer`. Invoked from
            ``self.__init__()``. Creates an object of :class:`ITotalizer` given
            a list of literals in the sum, the largest potential bound to
            consider, as well as the top variable identifier used so far. See
            the description of :class:`ITotalizer` for details.
        """

        self.lits = lits
        self.ubound = ubound
        self.top_id = max(map(lambda x: abs(x), self.lits + [top_id if top_id != None else 0]))

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        # creating the object
        self.tobj, clauses, self.rhs, self.top_id = pycard.itot_new(self.lits,
                self.ubound, self.top_id)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        # saving the result
        self.cnf.clauses = clauses
        self.cnf.nv = self.top_id

        # for convenience, keeping the number of clauses
        self.nof_new = len(clauses)

    def delete(self):
        """
            Destroys a previously constructed :class:`ITotalizer` object.
            Internal variables ``self.cnf`` and ``self.rhs`` get cleaned.
        """

        if self.tobj:
            if not self._merged:
                pycard.itot_del(self.tobj)

                # otherwise, this totalizer object is merged into a larger one
                # therefore, this memory should be freed in its destructor

            self.tobj = None

        self.lits = []
        self.ubound = None
        self.top_id = None

        self.cnf = CNF()
        self.rhs = []

        self.nof_new = 0

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

    def __del__(self):
        """
            Destructor.
        """

        self.delete()

    def increase(self, ubound=1, top_id=None):
        """
            Increases a potential upper bound that can be imposed on the
            literals in the sum of an existing :class:`ITotalizer` object to a
            new value.

            :param ubound: a new upper bound.
            :param top_id: a new top variable identifier.

            :type ubound: int
            :type top_id: integer or None

            The top identifier ``top_id`` applied only if it is greater than
            the one used in ``self``.

            This method creates additional clauses encoding the existing
            totalizer tree up to the new upper bound given and appends them to
            the list of clauses of :class:`.CNF` ``self.cnf``. The number of
            newly created clauses is stored in variable ``self.nof_new``.

            Also, a list of bounds ``self.rhs`` gets increased and its length
            becomes ``ubound+1``.

            The method can be used in the following way:

            .. code-block:: python

                >>> from pysat.card import ITotalizer
                >>> t = ITotalizer(lits=[1, 2, 3], ubound=1)
                >>> print t.cnf.clauses
                [[-2, 4], [-1, 4], [-1, -2, 5], [-4, 6], [-5, 7], [-3, 6], [-3, -4, 7]]
                >>> print t.rhs
                [6, 7]
                >>>
                >>> t.increase(ubound=2)
                >>> print t.cnf.clauses
                [[-2, 4], [-1, 4], [-1, -2, 5], [-4, 6], [-5, 7], [-3, 6], [-3, -4, 7], [-3, -5, 8]]
                >>> print t.cnf.clauses[-t.nof_new:]
                [[-3, -5, 8]]
                >>> print t.rhs
                [6, 7, 8]
                >>> t.delete()
        """

        self.top_id = max(self.top_id, top_id)

        # do nothing if the bound is set incorrectly
        if ubound <= self.ubound or self.ubound >= len(self.lits):
            self.nof_new = 0
            return
        else:
            self.ubound = ubound

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        # updating the object and adding more variables and clauses
        clauses, self.rhs, self.top_id = pycard.itot_inc(self.tobj,
                self.ubound, self.top_id)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        # saving the result
        self.cnf.clauses.extend(clauses)
        self.cnf.nv = self.top_id

        # keeping the number of newly added clauses
        self.nof_new = len(clauses)

    def extend(self, lits=[], ubound=None, top_id=None):
        """
            Extends the list of literals in the sum and (if needed) increases a
            potential upper bound that can be imposed on the complete list of
            literals in the sum of an existing :class:`ITotalizer` object to a
            new value.

            :param lits: additional literals to be included in the sum.
            :param ubound: a new upper bound.
            :param top_id: a new top variable identifier.

            :type lits: list(int)
            :type ubound: int
            :type top_id: integer or None

            The top identifier ``top_id`` applied only if it is greater than
            the one used in ``self``.

            This method creates additional clauses encoding the existing
            totalizer tree augmented with new literals in the sum and updating
            the upper bound. As a result, it appends the new clauses to the
            list of clauses of :class:`.CNF` ``self.cnf``. The number of newly
            created clauses is stored in variable ``self.nof_new``.

            Also, if the upper bound is updated, a list of bounds ``self.rhs``
            gets increased and its length becomes ``ubound+1``. Otherwise, it
            is updated with new values.

            The method can be used in the following way:

            .. code-block:: python

                >>> from pysat.card import ITotalizer
                >>> t = ITotalizer(lits=[1, 2], ubound=1)
                >>> print t.cnf.clauses
                [[-2, 3], [-1, 3], [-1, -2, 4]]
                >>> print t.rhs
                [3, 4]
                >>>
                >>> t.extend(lits=[5], ubound=2)
                >>> print t.cnf.clauses
                [[-2, 3], [-1, 3], [-1, -2, 4], [-5, 6], [-3, 6], [-4, 7], [-3, -5, 7], [-4, -5, 8]]
                >>> print t.cnf.clauses[-t.nof_new:]
                [[-5, 6], [-3, 6], [-4, 7], [-3, -5, 7], [-4, -5, 8]]
                >>> print t.rhs
                [6, 7, 8]
                >>> t.delete()
        """

        # preparing a new list of distinct input literals
        lits = list(set(lits).difference(set(self.lits)))

        if not lits:
            # nothing to merge with -> just increase the bound
            if ubound:
                self.increase(ubound=ubound, top_id=top_id)

            return

        self.top_id = max(map(lambda x: abs(x), self.lits + [self.top_id, top_id if top_id != None else 0]))
        self.ubound = max(self.ubound, ubound)

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        # updating the object and adding more variables and clauses
        self.tobj, clauses, self.rhs, self.top_id = pycard.itot_ext(self.tobj,
                lits, self.ubound, self.top_id)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        # saving the result
        self.cnf.clauses.extend(clauses)
        self.cnf.nv = self.top_id
        self.lits.extend(lits)

        # for convenience, keeping the number of new clauses
        self.nof_new = len(clauses)

    def merge_with(self, another, ubound=None, top_id=None):
        """
            This method merges a tree of the current :class:`ITotalizer`
            object, with a tree of another object and (if needed) increases a
            potential upper bound that can be imposed on the complete list of
            literals in the sum of an existing :class:`ITotalizer` object to a
            new value.

            :param another: another totalizer to merge with.
            :param ubound: a new upper bound.
            :param top_id: a new top variable identifier.

            :type another: :class:`ITotalizer`
            :type ubound: int
            :type top_id: integer or None

            The top identifier ``top_id`` applied only if it is greater than
            the one used in ``self``.

            This method creates additional clauses encoding the existing
            totalizer tree merged with another totalizer tree into *one* sum
            and updating the upper bound. As a result, it appends the new
            clauses to the list of clauses of :class:`.CNF` ``self.cnf``. The
            number of newly created clauses is stored in variable
            ``self.nof_new``.

            Also, if the upper bound is updated, a list of bounds ``self.rhs``
            gets increased and its length becomes ``ubound+1``. Otherwise, it
            is updated with new values.

            The method can be used in the following way:

            .. code-block:: python

                >>> from pysat.card import ITotalizer
                >>> with ITotalizer(lits=[1, 2], ubound=1) as t1:
                ...     print t1.cnf.clauses
                [[-2, 3], [-1, 3], [-1, -2, 4]]
                ...     print t1.rhs
                [3, 4]
                ...
                ...     t2 = ITotalizer(lits=[5, 6], ubound=1)
                ...     print t1.cnf.clauses
                [[-6, 7], [-5, 7], [-5, -6, 8]]
                ...     print t1.rhs
                [7, 8]
                ...
                ...     t1.merge_with(t2)
                ...     print t1.cnf.clauses
                [[-2, 3], [-1, 3], [-1, -2, 4], [-6, 7], [-5, 7], [-5, -6, 8], [-7, 9], [-8, 10], [-3, 9], [-4, 10], [-3, -7, 10]]
                ...     print t1.cnf.clauses[-t1.nof_new:]
                [[-6, 7], [-5, 7], [-5, -6, 8], [-7, 9], [-8, 10], [-3, 9], [-4, 10], [-3, -7, 10]]
                ...     print t1.rhs
                [9, 10]
                ...
                ...     t2.delete()
        """

        self.top_id = max(self.top_id, top_id, another.top_id)
        self.ubound = max(self.ubound, ubound, another.ubound)

        # extending the list of input literals
        self.lits.extend(another.lits)

        # saving default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

        # updating the object and adding more variables and clauses
        self.tobj, clauses, self.rhs, self.top_id = pycard.itot_mrg(self.tobj,
                another.tobj, self.ubound, self.top_id)

        # recovering default SIGINT handler
        def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

        # saving the result
        self.cnf.clauses.extend(another.cnf.clauses)
        self.cnf.clauses.extend(clauses)
        self.cnf.nv = self.top_id

        # for convenience, keeping the number of new clauses
        self.nof_new = len(another.cnf.clauses) + len(clauses)

        # memory deallocation should not be done for the merged tree
        another._merged = True
