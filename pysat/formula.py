#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## formula.py
##
##  Created on: Dec 7, 2016
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        IDPool
        Formula
        Atom
        And
        Or
        Neg
        Implies
        Equals
        XOr
        ITE
        CNF
        CNFPlus
        WCNF
        WCNFPlus

    ==================
    Module description
    ==================

    This module is designed to facilitate fast and easy PySAT-development by
    providing a simple way to manipulate formulas in PySAT. The toolkit
    implements several facilities to manupulate Boolean formulas. Namely, one
    can opt for creating arbitrary non-clausal formulas suitable for simple
    problem encodings requiring no or little knowledge about the process of
    logical encoding. However, the main and most often used kind of formula in
    PySAT is represented by the :class:`CNF` class, which can be used to
    define a formula in `conjunctive normal form (CNF)
    <https://en.wikipedia.org/wiki/Conjunctive_normal_form>`__.

    Recall that a CNF formula is conventionally seen as a set of clauses, each
    being a set of literals. A literal is a Boolean variable or its negation.
    In PySAT, a Boolean variable and a literal should be specified as an
    integer. For instance, a Boolean variable :math:`x_{25}` is represented as
    integer ``25``. A literal :math:`\\neg{x_{10}}` should be specified as
    ``-10``. Moreover, a clause :math:`(\\neg{x_2}\\vee x_{19}\\vee x_{46})`
    should be specified as ``[-2, 19, 46]`` in PySAT. *Unit size clauses* are
    to be specified as unit size lists as well, e.g. a clause :math:`(x_3)` is
    a list ``[3]``.

    CNF formulas can be created as an object of class :class:`CNF`. For
    instance, the following piece of code creates a CNF formula
    :math:`(\\neg{x_1}\\vee x_2)\\wedge(\\neg{x_2}\\vee x_3)`.

    .. code-block:: python

        >>> from pysat.formula import CNF
        >>> cnf = CNF()
        >>> cnf.append([-1, 2])
        >>> cnf.append([-2, 3])

    The clauses of a formula can be accessed through the ``clauses`` variable
    of class :class:`CNF`, which is a list of lists of integers:

    .. code-block:: python

        >>> print(cnf.clauses)
        [[-1, 2], [-2 ,3]]

    The number of variables in a CNF formula, i.e. the *largest variable
    identifier*, can be obtained using the ``nv`` variable, e.g.

    .. code-block:: python

        >>> print(cnf.nv)
        3

    Class :class:`CNF` has a few methods to read and write a CNF formula into a
    file or a string. The formula is read/written in the standard `DIMACS CNF
    <https://en.wikipedia.org/wiki/Boolean_satisfiability_problem#SAT_problem_format>`__
    format. A clause in the DIMACS format is a string containing
    space-separated integer literals  followed by ``0``. For instance, a clause
    :math:`(\\neg{x_2}\\vee x_{19}\\vee x_{46})` is written as ``-2 19 46 0``
    in DIMACS. The clauses in DIMACS should be preceded by a *preamble*, which
    is a line ``p cnf nof_variables nof_clauses``, where ``nof_variables`` and
    ``nof_clauses`` are integers. A preamble line for formula
    :math:`(\\neg{x_1}\\vee x_2)\\wedge(\\neg{x_2}\\vee x_3)` would be ``p cnf
    3 2``. The complete DIMACS file describing the formula looks this:

    ::

        p cnf 3 2
        -1 2 0
        -2 3 0

    Reading and writing formulas in DIMACS can be done with PySAT in the
    following way:

    .. code-block:: python

        >>> from pysat.formula import CNF
        >>> f1 = CNF(from_file='some-file-name.cnf')  # reading from file
        >>> f1.to_file('another-file-name.cnf')  # writing to a file
        >>>
        >>> with open('some-file-name.cnf', 'r+') as fp:
        ...     f2 = CNF(from_fp=fp)  # reading from a file pointer
        ...
        ...     fp.seek(0)
        ...     f2.to_fp(fp)  # writing to a file pointer
        >>>
        >>> f3 = CNF(from_string='p cnf 3 3\\n-1 2 0\\n-2 3 0\\n-3 0\\n')
        >>> print(f3.clauses)
        [[-1, 2], [-2, 3], [-3]]
        >>> print(f3.nv)
        3

    Besides plain CNF formulas, the :mod:`pysat.formula` module implements an
    additional class for dealing with *partial* and *weighted partial* CNF
    formulas, i.e. WCNF formulas. A WCNF formula is a conjunction of two sets
    of clauses: *hard* clauses and *soft* clauses, i.e.
    :math:`\\mathcal{F}=\\mathcal{H}\\wedge\\mathcal{S}`. Soft clauses of a WCNF
    are labeled with integer *weights*, i.e. a soft clause of
    :math:`\\mathcal{S}` is a pair :math:`(c_i, w_i)`. In partial (unweighted)
    formulas, all soft clauses have weight 1.

    WCNF can be of help when solving optimization problems using the SAT
    technology. A typical example of where a WCNF formula can be used is
    `maximum satisfiability (MaxSAT)
    <https://en.wikipedia.org/wiki/Maximum_satisfiability_problem>`__, which
    given a WCNF formula :math:`\\mathcal{F}=\\mathcal{H}\\wedge\\mathcal{S}`
    targets satisfying all its hard clauses :math:`\\mathcal{H}` and maximizing
    the sum of weights of satisfied soft clauses, i.e. maximizing the value of
    :math:`\\sum_{c_i\\in\\mathcal{S}}{w_i\\cdot c_i}`.

    An object of class :class:`WCNF` has two variables to access the hard and
    soft clauses of the corresponding formula: ``hard`` and ``soft``. The
    weights of soft clauses are stored in variable ``wght``.

    .. code-block:: python

        >>> from pysat.formula import WCNF
        >>>
        >>> wcnf = WCNF()
        >>> wcnf.append([-1, -2])
        >>> wcnf.append([1], weight=1)
        >>> wcnf.append([2], weight=3)  # the formula becomes unsatisfiable
        >>>
        >>> print(wcnf.hard)
        [[-1, -2]]
        >>> print(wcnf.soft)
        [[1], [2]]
        >>> print(wcnf.wght)
        [1, 3]

    A properly constructed WCNF formula must have a *top weight*, which should
    be equal to :math:`1+\\sum_{c_i\\in\\mathcal{S}}{w_i}`. Top weight of a
    formula can be accessed through variable ``topw``.

    .. code-block:: python

        >>> wcnf.topw = sum(wcnf.wght) + 1  # (1 + 3) + 1
        >>> print(wcnf.topw)
        5

    .. note::

        Although it is not aligned with the WCNF format description, starting
        with the 0.1.5.dev8 release, PySAT is able to deal with WCNF formulas
        having not only integer clause weights but also weights represented as
        *floating point numbers*. Moreover, *negative weights* are also
        supported.

    Additionally to classes :class:`CNF` and :class:`WCNF`, the module
    provides the extended classes :class:`CNFPlus` and :class:`WCNFPlus`. The
    only difference between ``?CNF`` and ``?CNFPlus`` is the support for
    *native* cardinality constraints provided by the `MiniCard solver
    <https://github.com/liffiton/minicard>`__ (see :mod:`pysat.card` for
    details). The corresponding variable in objects of ``CNFPlus``
    (``WCNFPlus``, resp.) responsible for storing the AtMostK constraints is
    ``atmosts`` (``atms``, resp.). **Note** that at this point, AtMostK
    constraints in ``WCNF`` can be *hard* only.

    Apart from the aforementioned variants of (W)CNF formulas, the module now
    offers a few additional classes for managing non-clausal Boolean formulas.
    Namely, a user may create complex formulas using variables (atomic
    formulas implemented as objects of class :class:`Atom`), and the following
    logic connectives: :class:`And`, :class:`Or`, :class:`Neg`,
    :class:`Implies`, :class:`Equals`, :class:`XOr`, and :class:`ITE`. (All of
    these classes inherit from the base class :class:`Formula`.) Arbitrary
    combinations of these logic connectives are allowed. Importantly, the
    module provides seamless integration of :class:`CNF` and various
    subclasses of :class:`Formula` with the possibility to clausify these on
    demand.

    .. code-block:: python

        >>> from pysat.formula import *
        >>> from pysat.solvers import Solver

        # creating two formulas: CNF and XOr
        >>> cnf = CNF(from_clauses=[[-1, 2], [-2, 3]])
        >>> xor = Atom(1) ^ Atom(2) ^ Atom(4)

        # passing the conjunction of these to the solver
        >>> with Solver(bootstrap_with=xor & cnf) as solver:
        ...    # setting Atom(3) to false results in only one model
        ...    for model in solver.enum_models(assumptions=Formula.literals([~Atom(3)])):
        ...        print(Formula.formulas(model, atoms_only=True))  # translating the model back to atoms
        >>>
        [Neg(Atom(1)), Neg(Atom(2)), Neg(Atom(3)), Atom(4)]

    .. note::

        Combining CNF formulas with non-CNF ones will not necessarily result
        in the best possible encoding of the complex formula. The on-the-fly
        encoder may introduce variables that a human would avoid using, e.g.
        if ``cnf1`` and ``cnf2`` are :class:`CNF` formulas then ``And(cnf1,
        cnf2)`` will introduce auxiliary variables ``v1`` and ``v2`` encoding
        them, respectively (although it is enough to join their sets of
        clauses).

    Besides the implementations of CNF and WCNF formulas in PySAT, the
    :mod:`pysat.formula` module also provides a way to manage variable
    identifiers. This can be done with the use of the :class:`IDPool` manager.
    With the use of the :class:`CNF` and :class:`WCNF` classes as well as with
    the :class:`IDPool` variable manager, it is pretty easy to develop
    practical problem encoders into SAT or MaxSAT/MinSAT. As an example, a PHP
    formula encoder is shown below (the implementation can also be found in
    :class:`.examples.genhard.PHP`).

    .. code-block:: python

        from pysat.formula import CNF
        cnf = CNF()  # we will store the formula here

        # nof_holes is given

        # initializing the pool of variable ids
        vpool = IDPool(start_from=1)
        pigeon = lambda i, j: vpool.id('pigeon{0}@{1}'.format(i, j))

        # placing all pigeons into holes
        for i in range(1, nof_holes + 2):
            cnf.append([pigeon(i, j) for j in range(1, nof_holes + 1)])

        # there cannot be more than 1 pigeon in a hole
        pigeons = range(1, nof_holes + 2)
        for j in range(1, nof_holes + 1):
            for comb in itertools.combinations(pigeons, 2):
                cnf.append([-pigeon(i, j) for i in comb])

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from __future__ import print_function
import collections
from collections.abc import Iterable
import copy
import decimal
from enum import Enum
import itertools
import os
from pysat._fileio import FileObject
import sys

# checking whether or not py-aiger-cnf is available and working as expected
aiger_present = True
try:
    import aiger_cnf
except ImportError:
    aiger_present = False

try:  # for Python2
    from cStringIO import StringIO
except ImportError:  # for Python3
    from io import StringIO


#
#==============================================================================
class IDPool(object):
    """
        A simple manager of variable IDs. It can be used as a pool of integers
        assigning an ID to any object. Identifiers are to start from ``1`` by
        default. The list of occupied intervals is empty be default. If
        necessary the top variable ID can be accessed directly using the
        ``top`` variable.

        The final parameter ``with_neg``, if set to ``True``, indicates that
        the *negation* of an object assigned a variable ID ``n`` is to be
        represented using the negative integer ``-n``. For this to work, the
        object must have the method ``__neg__()`` implemented. This behaviour
        is disabled by default.

        :param start_from: the smallest ID to assign.
        :param occupied: a list of occupied intervals.
        :param with_neg: whether to support automatic negation handling

        :type start_from: int
        :type occupied: list(list(int))
        :type with_neg: bool
    """

    def __init__(self, start_from=1, occupied=[], with_neg=False):
        """
            Constructor.
        """

        self.restart(start_from=start_from, occupied=occupied,
                     with_neg=with_neg)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'IDPool(start_from={self.top+1}, occupied={self._occupied})'

    def restart(self, start_from=1, occupied=[], with_neg=False):
        """
            Restart the manager from scratch. The arguments replicate those of
            the constructor of :class:`IDPool`.
        """

        # initial ID
        self.top = start_from - 1

        # occupied IDs
        self._occupied = sorted(occupied, key=lambda x: x[0])

        # main dictionary storing the mapping from objects to variable IDs
        self.obj2id = collections.defaultdict(lambda: self._next())

        # mapping back from variable IDs to objects
        # (if for whatever reason necessary)
        self.id2obj = {}

        # flag to indicate whether this IDPool object
        # should support automatic negation handling
        self.with_neg = with_neg

    def id(self, obj=None):
        """
            The method is to be used to assign an integer variable ID for a
            given new object. If the object already has an ID, no new ID is
            created and the old one is returned instead.

            An object can be anything. In some cases it is convenient to use
            string variable names. Note that if the object is not provided,
            the method will return a new id unassigned to any object.

            :param obj: an object to assign an ID to.

            :rtype: int.

            Example:

            .. code-block:: python

                >>> from pysat.formula import IDPool
                >>> vpool = IDPool(occupied=[[12, 18], [3, 10]])
                >>>
                >>> # creating 5 unique variables for the following strings
                >>> for i in range(5):
                ...    print(vpool.id('v{0}'.format(i + 1)))
                1
                2
                11
                19
                20

            In some cases, it makes sense to create an external function for
            accessing IDPool, e.g.:

            .. code-block:: python

                >>> # continuing the previous example
                >>> var = lambda i: vpool.id('var{0}'.format(i))
                >>> var(5)
                20
                >>> var('hello_world!')
                21
        """

        if obj is not None:
            vid = self.obj2id[obj]

            if vid not in self.id2obj:
                self.id2obj[vid] = obj

                # adding the object's negation, if required and supported
                if self.with_neg and hasattr(obj, '__neg__'):
                    self.obj2id[-obj] = -vid
                    self.id2obj[-vid] = -obj
        else:
            # no object is provided => simply return a new ID
            vid = self._next()

        return vid

    def obj(self, vid):
        """
            The method can be used to map back a given variable identifier to
            the original object labeled by the identifier.

            :param vid: variable identifier.
            :type vid: int

            :return: an object corresponding to the given identifier.

            Example:

            .. code-block:: python

                >>> vpool.obj(21)
                'hello_world!'
        """

        if vid in self.id2obj:
            return self.id2obj[vid]

        return None

    def occupy(self, start, stop):
        """
            Mark a given interval as occupied so that the manager could skip
            the values from ``start`` to ``stop`` (**inclusive**).

            :param start: beginning of the interval.
            :param stop: end of the interval.

            :type start: int
            :type stop: int
        """

        if stop >= start:
            # the following check serves to remove unnecessary interval
            # spawning; since the intervals are sorted, we are checking
            # if the previous interval is a (non-strict) subset of the new one
            if len(self._occupied) and self._occupied[-1][0] >= start and self._occupied[-1][1] <= stop:
                self._occupied.pop()

            self._occupied.append([start, stop])
            self._occupied.sort(key=lambda x: x[0])

    def _next(self):
        """
            Get next variable ID. Skip occupied intervals if any.
        """

        self.top += 1

        while self._occupied and self.top >= self._occupied[0][0]:
            if self.top <= self._occupied[0][1]:
                self.top = self._occupied[0][1] + 1

            self._occupied.pop(0)

        return self.top


#
#==============================================================================
class FormulaError(Exception):
    """
        This exception is raised when an formula-related issue occurs.
    """

    pass


#
#==============================================================================
class FormulaType(Enum):
    """
        This class represents a C-like ``enum`` type for choosing the formula
        type to use. The values denoting all the formula types are as follows:

        ::

            ATOM = 0
            AND = 1
            OR = 2
            NEG = 3
            IMPL = 4
            EQ = 5
            XOR = 6
            ITE = 7
    """

    ATOM = 0
    AND = 1
    OR = 2
    NEG = 3
    IMPL = 4
    EQ = 5
    XOR = 6
    ITE = 7
    CNF = 8  # not in the description intentionally - it should not be used directly


#
#==============================================================================
class Formula(object):
    """
        Abstract formula class. At the same time, the class is a factory for
        its children and can be used this way although it is recommended to
        create objects of the children classes directly. In particular, its
        children classes include :class:`Atom` (atomic formulas - variables
        and constants), :class:`Neg` (negations), :class:`And` (conjunctions),
        :class:`Or` (disjunctions), :class:`Implies` (implications),
        :class:`Equals` (equalities), :class:`XOr` (exclusive disjunctions),
        and :class:`ITE` (if-then-else operations).

        Due to the need to clausify formulas, an object of any subclass of
        :class:`Formula` is meant to be represented in memory by a single
        copy. This is achieved by storing a dictionary of all the known
        formulas attached to a given *context*. Thus, once a particular
        context is activated, its dictionary will make sure each formula
        variable refers to a single representation of the formula object it
        aims to refer. When it comes to clausifying this formula, the formula
        is encoded exactly once, despite it may be potentially used multiple
        times as part of one of more complex formulas.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>>
            >>> x1, x2 = Atom('x'), Atom('x')
            >>> id(x1) == id(x2)
            True  # x1 and x2 refer to the same atom
            >>> id(x1 & Atom('y')) == id(Atom('y') & x2)
            True  # it holds if constructing complex formulas with them as subformulas

        The class supports multi-context operation. A user may have formulas
        created and clausified in different context. They can also switch from
        one context to another and/or cleanup the instances known in some or
        all contexts.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> f1 = Or(And(...))  # arbitrary formula
            >>> # by default, the context is set to 'default'
            >>> # another context can be created like this:
            >>> Formula.set_context(context='some-other-context')
            >>> # the new context knows nothing about formula f1
            >>> # ...
            >>> # cleaning up context 'some-other-context'
            >>> # this deletes all the formulas known in this context
            >>> Formula.cleanup(context='some-other-context')
            >>> # switching back to 'default'
            >>> Formula.set_context(context='default')

        A user may also want to disable duplicate blocking, which can be
        achieved by setting the context to ``None``.

        Boolean constants False and True are represented by the atomic
        "formulas" ``Atom(False)`` and ``Atom(True)``, respectively. There are
        two constants storing these values: ``PYSAT_FALSE`` and
        ``PYSAT_TRUE``.

        .. code-block:: python

            >>> PYSAT_FALSE, PYSAT_TRUE
            (Atom(False), Atom(True))
    """

    # we don't want duplicated formulas => let's keep one copy of each
    _instances = collections.defaultdict(lambda: {})

    # similarly, we create a variable pool in case we need the formulas encoded
    _vpool = collections.defaultdict(lambda: IDPool())

    # formulas can duplicate when they appear in different contexts
    _context = 'default'

    @staticmethod
    def set_context(context='default'):
        """
            Set the current context of interest. If set to ``None``, no
            context will be assumed and duplicate checking will be disabled as
            a result.

            :param context: new active context
            :type context: hashable
        """

        Formula._context = context

    @staticmethod
    def attach_vpool(vpool, context='default'):
        """
            Attach an external :class:`IDPool` to be associated with a given
            context. This is useful when a user has an already created
            :class:`IDPool` object and wants to reuse it when clausifying
            their :class:`Formula` objects.

            :param vpool: an external variable manager
            :param context: target context to be the user of the vpool

            :type vpool: :class:`IDPool`
            :type context: hashable
        """

        Formula._vpool[context] = vpool

    @staticmethod
    def export_vpool(active=True, context='default'):
        """
            Opposite to :meth:`attach_vpool`, this method returns a variable
            managed attached to a given context, which may be useful for
            external use.

            :param active: export the currently active context
            :param context: context using the vpool we are interested in (if ``active`` is ``False``)

            :type active: bool
            :type context: hashable

            :rtype: :class:`IDPool`
        """

        if active:
            return Formula._vpool[Formula._context]
        else:
            return Formula._vpool[context]

    @staticmethod
    def cleanup(context=None):
        """
            Clean up either a given context (if specified as different from
            ``None``) or all contexts (otherwise); afterwards, start the
            "default" context from scratch.

            A context is cleaned by destroying all the associated
            :class:`Formula` objects and all the corresponding variable
            managers. This may be useful if a user wants to start encoding
            their problem from scratch.

            .. note::

                Once cleaning of a context is done, the objects referring to
                the context's formulas must not be used. At this point, they
                are orphaned and can't get re-clausified.

            :param context: target context
            :type context: ``None`` or hashable
        """

        # preparing what needs to be cleaned
        if context is not None:
            # only a given context
            to_clean = [context] if context in Formula._instances else []
        else:
            # everything
            to_clean = list(set(Formula._vpool).union(set(Formula._instances)))

        # actual cleaning
        for ctx in to_clean:
            # we never clean the '_global' context
            if ctx == '_global':
                continue

            # deleting the content of all the formulas' in the context
            for key in list(Formula._instances[ctx].keys()):
                Formula._instances[ctx][key].__del__()

            # deleting the corresponding instances and variable manager
            del Formula._instances[ctx]
            if ctx in Formula._vpool:
                del Formula._vpool[ctx]

        if not Formula._instances:
            # there is no context left; updating the context to 'default'
            Formula.set_context(context='default')

    @staticmethod
    def formulas(lits, atoms_only=True):
        """
            Given a list of integer literal identifiers, this method returns a
            list of formulas corresponding to these identifiers. Basically,
            the method can be seen as mapping auxiliary variables naming
            formulas to the corresponding formulas they name.

            If the argument ``atoms_only`` is set to ``True`` only, the method
            will return a subset of formulas, including only atomic formulas
            (literals). Otherwise, any formula whose name occurs in the input
            list will be included in the result.

            :param lits: input list of literals
            :param atoms_only: include all known formulas or atomic ones only

            :type lits: iterable
            :type atoms_only: bool

            :rtype: list(:class:`Formula`)

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> from pysat.solvers import Solver
                >>>
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) ^ z
                >>>
                >>> with Solver(bootstrap_with=a) as solver:
                ...     for model in solver.enum_models():
                ...         # using method formulas to map the model back to atoms
                ...         print(Formula.formulas(model, atoms_only=True))
                ...
                [Neg(Atom('x')), Neg(Atom('y')), Neg(Atom('z'))]
                [Neg(Atom('x')), Atom('y'), Atom('z')]
                [Atom('x'), Atom('y'), Neg(Atom('z'))]
                [Atom('x'), Neg(Atom('y')), Atom('z')]
        """

        forms = []

        for lit in lits:
            if lit in Formula._vpool[Formula._context].id2obj:
                forms.append( Formula._vpool[Formula._context].obj(+lit))
            elif -lit in Formula._vpool[Formula._context].id2obj:
                forms.append(~Formula._vpool[Formula._context].obj(-lit))

        # if required, we need to filter out everything but atomic forms
        if atoms_only:
            forms = [f for f in forms if type(f) == Atom or type(f) == Neg and type(f.subformula) == Atom]

        return forms

    @staticmethod
    def literals(forms):
        """
            Extract formula names for a given list of formulas and return them
            as a list of integer identifiers. Essentially, the method is the
            opposite to :meth:`formulas`.

            :param forms: list of formulas to map
            :type forms: iterable

            :rtype: list(int)

            Example:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> from pysat.formula import *
                >>>
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) ^ z
                >>>
                >>> # applying Tseitin transformation to formula a
                >>> a.clausify()
                >>>
                >>> # checking what facts the internal vpool knows
                >>> print(Formula.export_vpool().id2obj)
                {1: Atom('x'), 2: Atom('y'), 3: Equals[Atom('x'), Atom('y')], 4: Atom('z')}
                >>>
                >>> # now, mapping two atoms to their integer id representations
                >>> Formula.literals(forms=[Atom('x'), ~Atom('z')])
                [1, -4]
        """

        lits = []

        for form in forms:
            if form in (PYSAT_TRUE, PYSAT_FALSE):
                continue

            if not form.name:
                form._clausify(name_required=True)

            lits.append(Formula._vpool[Formula._context].id(form))

        return lits

    def __init__(self, *args, **kwargs):
        """
            Base Formula initialiser. Expects a sole keyword argument
            ``type``, which must be assigned to an enumeration value of
            :class:`FormulaType`.

            :param type: type of the formula
            :type type: :class:`FormulaType`
        """

        assert 'type' in kwargs, 'No \'type\' of the formula is provided'
        self.type = kwargs['type']

        self.name = None   # Tseitin variable encoding the formula clausification
        self.clauses = []  # raw clausal representation of the formula
        self.encoded = []  # tseitin-encoded clauses representing the formula

    @classmethod
    def __new__(cls, *args, **kwargs):
        """
            Factory-like formula constructor, which avoids creating duplicated
            formulas if we are currently using a context. Otherwise, simply
            creates a formula object of a given type, without duplicate
            checking.
        """

        def _create_object():
            if cls is Formula:
                assert 'type' in kwargs, 'No \'type\' of the formula is provided'
                type = kwargs['type']

                if type == FormulaType.ATOM:
                    return super(Formula, Atom).__new__(Atom)
                if type == FormulaType.AND:
                    return super(Formula, And).__new__(And)
                if type == FormulaType.OR:
                    return super(Formula, Or).__new__(Or)
                if type == FormulaType.NEG:
                    return super(Formula, Neg).__new__(Neg)
                if type == FormulaType.IMPL:
                    return super(Formula, Implies).__new__(Implies)
                if type == FormulaType.EQ:
                    return super(Formula, Equals).__new__(Equals)
                if type == FormulaType.XOR:
                    return super(Formula, XOr).__new__(XOr)
                if type == FormulaType.ITE:
                    return super(Formula, ITE).__new__(ITE)
                else:
                    raise FormulaError('Unexpected formula type')
            else:
                return super(Formula, cls).__new__(cls)

        if Formula._context is not None:
            # there is an active context different from None
            # hence, we need to make sure we don't duplicate formulas

            # getting the key to associate the formula with
            key = Formula._get_key(args, kwargs)

            # first, checking if the key is known to represent a global constant
            if key in Formula._instances['_global']:
                return Formula._instances['_global'][key]

            # then, checking if the key is known in the current context
            if key not in Formula._instances[Formula._context]:
                # this key is yet unknown; creating a new formula object
                Formula._instances[Formula._context][key] = _create_object()

            # returning the object associated with the requested formula
            return Formula._instances[Formula._context][key]
        else:
            return _create_object()

    def __deepcopy__(self, memo):
        """
            As no duplicates are allowed, no deep copying is allowed either.
        """

        raise FormulaError('Formula class does not allow deep copying')

    @staticmethod
    def _get_key(*args, **kwargs):
        """
            The method is used to extract and return a list of attributes to
            serve as a key associated with the formula requested by a user.
            The flattened result will contain string, i.e. ``repr()``,
            representation of all the attributes. The method is meant to be
            internal and not to be used by formula users.
        """

        def _hashable(entity):
            try:
                hash(entity)
                return True
            except TypeError:
                return False

        def _flatten(collection, prefix='', sep='_'):
            items = []

            # first, assuming it is a flat unhashable collection
            if type(collection) in (tuple, list, set):
                collection = tuple(filter(lambda x: x or x == False, collection))

                for item in collection:
                    if isinstance(item, Iterable):
                        items.extend(_flatten(item, prefix=prefix))
                    else:
                        items.append((prefix, item))

            # next, checking if it is a dictionary
            elif isinstance(collection, dict):
                for key in collection.keys():
                    value = collection[key]
                    new_key = prefix + sep + key if prefix else key
                    if isinstance(value, Iterable) and value:
                        items.extend(_flatten(value, prefix=new_key, sep=sep))
                    else:

                        items.append((new_key, value))

            # finally, it is a simple non-empty object
            elif collection or collection == False:
                items.append((prefix, collection))

            return items

        # in case the class of the formula is passed in the arguments
        # we filter it out so that it does not mess up the key computation
        if args:
            args = list(args)
            if type(args[0]) == tuple and type(args[0][0]) == type:
                args[0] = tuple(args[0][1:])

        # flattening all the inputs
        items = _flatten(args) + _flatten(kwargs)
        ftype, subfs, extra = None, [], []

        # ignoring everything except subformulas and the type
        for item in items:
            if item[0] == 'type':
                ftype = item
            elif item[0] != 'merge':
                subfs.append(item)
            else:
                extra = [('merge', repr(item[1]))]

        # the ugly part:
        # reconstructing the key pairs, depending on the type of Formula
        if ftype[1] == FormulaType.ATOM:
            assert len(subfs) == 1, 'A single object is required for an Atom formula'
            subfs[0] = ('object', repr(subfs[0][1]))
        elif ftype[1] == FormulaType.NEG:
            assert len(subfs) == 1, 'A single subformula is required for a Neg formula'
            subfs[0] = ('subformula', id(subfs[0][1]))
        elif ftype[1] == FormulaType.IMPL:
            assert len(subfs) == 2, 'Two subformulas are required for an Implies formula'
            if subfs[0][0] == '' and subfs[1][0] == '':
                subfs[0] = ('left', id(subfs[0][1]))
                subfs[1] = ('right', id(subfs[1][1]))
            elif subfs[1][0] == 'left':
                subfs[0] = ('right', id(subfs[0][1]))
            elif subfs[1][0] == 'right':
                subfs[0] = ('left', id(subfs[0][1]))
        elif ftype[1] == FormulaType.ITE:
            assert len(subfs) == 3, 'Three subformulas are required for an ITE formula'
            if subfs[0][0] == '' and subfs[1][0] == '' and subfs[2][0] == '':
                subfs[0] = ('cond', id(subfs[0][1]))
                subfs[1] = ('cons1', id(subfs[1][1]))
                subfs[2] = ('cons2',  id(subfs[2][1]))
            elif subfs[0][0] == subfs[1][0] == '':
                if subfs[2][0] == 'cond':
                    subfs[0] = ('cons1', id(subfs[0][1]))
                    subfs[1] = ('cons2', id(subfs[1][1]))
                elif subfs[2][0] == 'cons1':
                    subfs[0] = ('cond',  id(subfs[0][1]))
                    subfs[1] = ('cons2', id(subfs[1][1]))
                elif subfs[2][0] == 'cons2':
                    subfs[0] = ('cond',  id(subfs[0][1]))
                    subfs[1] = ('cons1', id(subfs[1][1]))
            elif subfs[0] == '':
                if 'cond' not in (subfs[1][0], subfs[2][0]):
                    subfs[0] = ('cond', id(subfs[0][0]))
                elif 'cons1' not in (subfs[1][0], subfs[2][0]):
                    subfs[0] = ('cons1', id(subfs[0][0]))
                elif 'cons2' not in (subfs[1][0], subfs[2][0]):
                    subfs[0] = ('cons2', id(subfs[0][0]))
        else:
            # these are commutative connectives; we need to sort the arguments
            assert len(subfs) >= 1, 'At least one subformula is required for an And/Equals/Or/XOr formula'
            subfs = sorted(map(lambda p: (p[0], repr(id(p[1]))), subfs))

            if not extra:
                extra = [('merge', repr(False))]

        # the key is a string combining all the parts
        return ' '.join([f'{repr(p[0])}:{repr(p[1])}' for p in [ftype] + subfs + extra])

    def __hash__(self):
        """
            This method provides us with a trivial way to make
            :class:`Formula` objects hashable. Currently, the implementation
            returns a hash of the string representation of the object.
        """

        return hash(repr(self))

    def _merge_suboperands(self):
        """
            Auxiliary method used when constructing a new formula to flatten
            repetitive operations, i.e. if ``self`` equals ``And(left,
            And(center, right))``, it turns it into formula ``And(left,
            center, right)`` instead. No arguments are expected. The method is
            meant for internal use of :class:`Formula` only.
        """

        for i, subf in enumerate(self.subformulas):
            # is there any term of our type among the operands?
            if subf.type == self.type:
                operands = subf.subformulas[:]

                # yes => try to put everything under its cap
                for j in itertools.filterfalse(lambda j: j == i, range(len(self.subformulas))):
                    if self.subformulas[j].type == self.type:
                        operands.extend(self.subformulas[j].subformulas)
                    else:
                        operands.append(self.subformulas[j])

                # we are done with simplification by now
                self.subformulas = operands
                break

    def __invert__(self):
        """
            Negation operator overloaded for class :class:`Formula`. Given an
            object ``f`` of class :class:`Formula`, applying ``~f`` returns a
            new object ``Neg(f)``.
        """

        if self.type != FormulaType.NEG:
            if self == PYSAT_TRUE:
                return PYSAT_FALSE
            if self == PYSAT_FALSE:
                return PYSAT_TRUE
            return Neg(self)
        return self.subformula

    def __neg__(self):
        """
            Negation operator. Takes the same effect as ``__invert__()``.
        """

        return self.__invert__()

    def __and__(self, other):
        """
            Logical conjunction operator overloaded for class
            :class:`Formula`. Given two objects ``a`` and ``b`` of class
            :class:`Formula`, doing ``a & b`` returns a new object ``And(a,
            b)``. Applies merging sub-operands.
        """

        return And(self, other, merge=True)

    def __iand__(self, other):
        """
            An in-place equivalent of :meth:`__and__`. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a &= b`` replaces
            ``a`` with a new object ``And(a, b)``. Applies merging
            sub-operands.
        """

        return And(self, other, merge=True)

    def __or__(self, other):
        """
            Logical disjunction operator overloaded for class
            :class:`Formula`. Given two objects ``a`` and ``b`` of class
            :class:`Formula`, doing ``a | b`` returns a new object ``Or(a,
            b)``. Applies merging sub-operands.
        """

        return Or(self, other, merge=True)

    def __ior__(self, other):
        """
            An in-place equivalent of :meth:`__or__`. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a |= b`` replaces
            ``a`` with a new object ``Or(a, b)``. Applies merging
            sub-operands.
        """

        return Or(self, other, merge=True)

    def __rshift__(self, other):
        """
            Bitwise right shift operator overloaded for class :class:`Formula`
            with the semantics of logical implication. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a >> b`` returns a
            new object ``Implies(a, b)``.
        """

        return Implies(self, other)

    def __irshift__(self, other):
        """
            An in-place equivalent of :meth:`__rshift__`. Given two objects
            ``a`` and ``b`` of class :class:`Formula`, doing ``a >>= b``
            assigns ``a`` to a new object ``Implies(a, b)``.
        """

        return Implies(self, other)

    def __lshift__(self, other):
        """
            Bitwise left shift operator overloaded for class :class:`Formula`
            with the semantics of logical implication. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a << b`` returns a
            new object ``Implies(b, a)``.
        """

        return Implies(other, self)

    def __ilshift__(self, other):
        """
            An in-place equivalent of :meth:`__lshift__`. Given two objects
            ``a`` and ``b`` of class :class:`Formula`, doing ``a <<= b``
            assigns ``a`` to a new object ``Implies(b, a)``.
        """

        return Implies(other, self)

    def __matmul__(self, other):
        """
            Vector multiplication operator overloaded for class
            :class:`Formula` with the semantics of logical equivalence. Given
            two objects ``a`` and ``b`` of class :class:`Formula`, doing ``a @
            b`` returns a new object ``Equals(a, b)``. Applies merging
            sub-operands.
        """

        return Equals(self, other, merge=True)

    def __imatmul__(self, other):
        """
            An in-place variant of :meth:`__matmul__`. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a @= b`` assigns
            ``a`` to a new object ``Equals(a, b)``. Applies merging
            sub-operands.
        """

        return Equals(self, other, merge=True)

    def __xor__(self, other):
        """
            Bitwise exclusive disjunction overloaded for class
            :class:`Formula`. Given two objects ``a`` and ``b`` of class
            :class:`Formula`, doing ``a ^ b`` returns a new object ``XOr(a,
            b)``.
        """

        return XOr(self, other, merge=True)

    def __ixor__(self, other):
        """
            An in-place variant of :meth:`__xor__`. Given two objects ``a``
            and ``b`` of class :class:`Formula`, doing ``a ^= b`` assigns
            ``a`` to a new object ``XOr(a, b)``.
        """

        return XOr(self, other, merge=True)

    def __iter__(self):
        """
            Implements an iterator over all clauses of the formula. As the
            clauses are stored not only in ``self`` but also in its
            subformulas, the iterator runs recursively by means of calling
            recursive method :meth:`_iter`.

            Before iterating through the clauses, applies Tseitin
            transformation (see :meth:`clausify`).

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) | z
                >>> # iterating through the clauses and printing them as a list
                >>> [cl for cl in a]
                [[-1, 2, -3], [1, -2, -3], [3, -1, -2], [3, 1, 2], [3, 4]]
                >>>
                >>> # let's see what meaning the identifiers have
                >>> Formula.export_vpool().id2obj
                {1: Atom('x'), 2: Atom('y'), 3: Equals[Atom('x'), Atom('y')], 4: Atom('z')}
        """

        # first, make sure there is a clausal representation
        self.clausify()

        # then recursively iterate through the clauses
        for cl in self._iter({}, outermost=True):
            if PYSAT_TRUE.name not in cl:
                yield [l for l in cl if l != PYSAT_FALSE.name]

    def clausify(self):
        """
            This method applies Tseitin transformation to the formula.
            Recursively gives all the formulas Boolean names accordingly and
            uses them in the current logic connective following its semantics.
            As a result, each subformula stores its clausal representation
            independently of other subformulas (and independently of the root
            formula).

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) | z
                >>>
                >>> a.clausify()  # clausifying formula a
                >>>
                >>> # let's what clauses represent the root logic connective
                >>> a.clauses
                [[3, 4]]  # 4 corresponds to z while 3 represents the equality x @ y
        """

        self._clausify(name_required=False)

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption atomic formula literals, this method
            recursively assigns these atoms to the corresponding values
            followed by formula simplification. As a result, a new formula
            object is returned.

            :param assumptions: atomic formula objects
            :type assumptions: list

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>>
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) | z  # a formula over 3 variables: x, y, and z
                >>>
                >>> a.simplified(assumptions=[z])
                Atom(True)
                >>>
                >>> a.simplified(assumptions=[~z])
                Equals[Atom('x'), Atom('y')]
                >>>
                >>> b = a ^ Atom('p')  # a more complex formula
                >>>
                >>> b.simplified(assumptions=[x, ~Atom('p')])
                Or[Atom('y'), Atom('z')]
        """

        raise FormulaError('No simplification method found for this formula type')

    def satisfied(self, model):
        """
            Given a list of atomic formulas, this method checks whether the
            current formula is satisfied by assigning these atoms. The method
            returns ``True`` if the formula gets satisfied, ``False`` if it is
            falsified, and ``None`` if the answer is unknown.

            :param model: list of atomic formulas
            :type model: list(:class:`Formula`)

            :rtype: bool or ``None``

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>>
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) | z
                >>>
                >>> a.satisfied(model=[z])
                True
                >>> a.satisfied(model=[~z])
                >>> # None, as it is not enough to set ~z to determine satisfiability of a
        """

        simp = self.simplified(assumptions=model)

        if simp == PYSAT_TRUE:
            return True
        elif simp == PYSAT_FALSE:
            return False

    def atoms(self, constants=False):
        """
            Returns a list of all the atomic formulas (variables and, if
            required, constants) that this formula is built from. The method
            recursively traverses the formula tree and collects all the atoms
            it finds.

            :param constants: include Boolean constants in the list
            :type constants: bool

            :rtype: list(:class:`Atom`)

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>>
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = (x @ y) | z
                >>>
                >>> a.atoms()
                [Atom('x'), Atom('y'), Atom('z')]
        """

        dest = set()
        self._atoms(dest)

        if constants is False:
            if PYSAT_TRUE in dest:
                dest.remove(PYSAT_TRUE)

            if PYSAT_FALSE in dest:
                dest.remove(PYSAT_FALSE)

        return list(dest)


#
#==============================================================================
class Atom(Formula):
    """
        Atomic formula, i.e. a variable or constant. Although we often refer
        to negated literals as atomic formulas too, they are techically
        implemented as ``Neg(Atom)``.

        To create an atomic formula, a user needs to specify an ``object``
        this formula should signify. When it comes to clausifying the formulas
        this atom is involved in, the atom receives an auxiliary variable
        assigned to it as a ``name``.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x = Atom('x')
            >>> y = Atom(object='y')
            >>> # checking x's name
            >>> x.name
            >>> # None
            >>> # right, that's because the atom is not yet clausified
            >>> x.clausify()
            >>> x.name
            1

        If a given object is a positive integer (negative integers aren't
        allowed), the integer itself serves as the atom's name, which is
        assigned in the constructor, i.e. no call to :meth:`clausify` is
        required.

        Example:

        .. code-block:: python

            >>> from pysat.formula import Atom
            >>> x, y = Atom(1), Atom(2)
            >>> x.name
            1
            >>> y.name
            2

        Special atoms are reserved for the Boolean constants ``True`` and
        ``False``. Namely, ``Atom(False)`` and ``Atom(True)`` can be accessed
        through the constants ``PYSAT_FALSE`` and ``PYSAT_TRUE``,
        respectively.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>>
            >>> print(PYSAT_TRUE, repr(PYSAT_TRUE))
            T Atom(True)
            >>>
            >>> print(PYSAT_FALSE, repr(PYSAT_FALSE))
            F Atom(False)

        .. note::

            Constant ``Atom(True)`` is distinguished from variable ``Atom(1)``
            by checking the type of the object (bool vs int).
    """

    def __new__(cls, *args, **kwargs):
        """
            Atom constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.ATOM)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. The method should receive either an argument or a
            keyword argument ``object`` signifying the object the new atom is
            meant to represent.

            :param object: object of interest
            :type object: any
        """

        super(Atom, self).__init__(type=FormulaType.ATOM)

        if args:
            self.object = args[0]
        elif 'object' in kwargs:
            self.object = kwargs['object']
        else:
            assert 0, 'No object is given for this atom'

        if type(self.object) == int:
            # user seems to want to use integer variable directly
            assert self.object > 0, 'Variables should be represented as positive integers'

            self.name = self.object  # using the integer id as the name
            self.clauses = [[self.name]]

            Formula._vpool[Formula._context].obj2id[self] = self.name
            Formula._vpool[Formula._context].id2obj[self.name] = self
            Formula._vpool[Formula._context].occupy(1, self.name)

    def __del__(self):
        """
            Atom destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []  # always empty
        self.object = None

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. Does nothing as there are no
            clauses to iterate through.
        """

        if not self in seen:
            seen[self] = True

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def _clausify(self, name_required=True):
        """
            Atom clausification. Basically, the method just assigns an
            auxiliary variable to serve as a ``name`` of the atom. It does not
            produce any clauses (the name is left for consistency with the
            rest of formula types).
        """

        # true and false constants shouldn't be encoded
        if not self.name and self.object not in (False, True):
            self.name = Formula._vpool[Formula._context].id(self)
            self.clauses = [[self.name]]

    def simplified(self, assumptions=[]):
        """
            Checks if the current literal appears in the list of assumptions
            provided in argument ``assumptions``. If it is, the method returns
            ``PYSAT_TRUE``. If the opposite atom is present in
            ``assumptions``, the method returns ``PYSAT_FALSE``. Otherwise, it
            return ``self``.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: PYSAT_TRUE, PYSAT_FALSE, or self
        """

        if self in assumptions:
            return PYSAT_TRUE
        elif ~self in assumptions:
            return PYSAT_FALSE
        return self

    def _atoms(self, dest):
        """
            The base case of recursive atom collection. Updates the collection
            with ``self`` atom.

            :param dest: the set of atoms to collect
            :type dest: set(:class:`Atom`)
        """

        dest.add(self)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}({repr(self.object)})'

    def __str__(self):
        """
            Informal representation of the Atom. Returns a string
            representation of the underlying object. For constants
            ``PYSAT_FALSE`` and ``PYSAT_TRUE``, the method returns ``'F'`` and
            ``'T'``, respectively.
        """

        if not isinstance(self.object, bool):
            return str(self.object)
        else:
            return 'F' if self.object == False else 'T'


# true and false constants (stored in the '_global' context)
# in fact, this is where the '_global' context is first created
#==============================================================================
Formula.set_context('_global')
PYSAT_FALSE, PYSAT_TRUE = Atom(False), Atom(True)
PYSAT_FALSE.name, PYSAT_TRUE.name = -0.5, 0.5 # special (floating-point) values for the constants
                                              # different from all variable names
PYSAT_FALSE.clauses, PYSAT_TRUE.clauses = [[-0.5]], [[0.5]] # unit clauses for the constants
                                                            # FALSE should turn into an empty clause;
                                                            # while the clause for TRUE should be removed
Formula.set_context('default')


#
#==============================================================================
class And(Formula):
    """
        Conjunction. Given a list of operands (subformulas) :math:`f_i`,
        :math:`i \\in \\{1,\\ldots,n\\}, n \\in \\mathbb{N}`, it creates a
        formula :math:`\\bigwedge_{i=1}^{n}{f_i}`. The list of operands *of
        size at least 1* should be passed as arguments to the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
            >>> conj = And(x, y, z)

        If an additional Boolean keyword argument ``merge`` is provided set to
        ``True``, the toolkit will try to flatten the current :class:`And`
        formula merging its *conjuctive* sub-operands into the list of
        operands. For example, if ``And(And(x, y), z, merge=True)`` is called,
        a new Formula object will be created with two operands: ``And(x, y)``
        and ``z``, followed by merging ``x`` and ``y`` into the list of
        root-level ``And``. This will result in a formula ``And(x, y, z)``.
        Merging sub-operands is enabled by default if bitwise operations are
        used to create ``And`` formulas.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> a1 = And(And(Atom('x'), Atom('y')), Atom('z'))
            >>> a2 = And(And(Atom('x'), Atom('y')), Atom('z'), merge=True)
            >>> a3 = Atom('x') & Atom('y') & Atom('z')
            >>>
            >>> repr(a1)
            "And[And[Atom('x'), Atom('y')], Atom('z')]"
            >>> repr(a2)
            "And[Atom('x'), Atom('y'), Atom('z')]"
            >>> repr(a3)
            "And[Atom('x'), Atom('y'), Atom('z')]"
            >>>
            >>> id(a1) == id(a2)
            False
            >>>
            >>> id(a2) == id(a3)
            True  # formulas a2 and a3 refer to the same object

        .. note::

            If there are two formulas representing the same fact with and
            without merging enabled, they technically sit in two distinct
            objects. Although PySAT tries to avoid it, clausification of these
            two formulas may result in unique (different) auxiliary variables
            assigned to such two formulas.
        """

    def __new__(cls, *args, **kwargs):
        """
            Conjunction constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.AND)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects a list of arguments signifying the operands
            of the conjunction. Additionally, a user may set a keyword
            argument ``merge=True``, which will enable merging sub-operands.
        """

        super(And, self).__init__(type=FormulaType.AND)

        self.subformulas = list(args)

        if 'merge' in kwargs and kwargs['merge'] == True:
            self._merge_suboperands()
            self.merged = True
        else:
            self.merged = False

    def __del__(self):
        """
            And destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.subformulas = []

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. First, iterates through the
            clauses of the subformulas followed by the formula's own clauses.
        """

        if not self in seen:
            seen[self] = True

            for sub in self.subformulas:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformulas and creates a new formula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = x & y & z
                >>>
                >>> print(a.simplified(assumptions=[y]))
                x & z
                >>> print(a.simplified(assumptions=[~y]))
                F  # False
        """

        oset = set()
        operands = []

        for sub in self.subformulas:
            # execute simplification recursively
            sub = sub.simplified(assumptions=set(assumptions))

            # simplify the current term
            if sub is PYSAT_FALSE or ~sub in oset:
                return PYSAT_FALSE

            # a new yet unsimplified term
            elif sub != PYSAT_TRUE and sub not in oset:
                oset.add(sub)
                operands.append(sub)

        # there is nothing left and we did not come across False
        # we should return True
        if not operands:
            return PYSAT_TRUE

        # there is one operand left; we need to return it instead
        if len(operands) == 1:
            return operands[0]

        return And(*operands, merge=True) if self.merged else And(*operands)

    def _clausify(self, name_required=True):
        """
            Conjuction clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the subformulas and populates self's clauses with unit clauses,
            each containing the auxiliary "name" of the corresponding
            subformula, thus representing their conjunction.

            If ``name_required`` is set to ``True``, the method encodes the
            conjunction using the standard logic: :math:`x \\equiv
            \\bigwedge{y_i}`, if :math:`x` is the new auxiliary variable
            encoding ``self`` and :math:`y_i` is the auxiliary variable
            representing :math:`i`'s subformula.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformulas
            for sub in self.subformulas:
                sub._clausify(name_required=True)

                # adding unit clauses
                self.clauses.append([sub.name])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            self.name = Formula._vpool[Formula._context].id(self)

            cl = [self.name]  # final clause (converse implication)
            for i in range(len(self.encoded)):
                cl.append(-self.encoded[i][0])      # updating final clause
                self.encoded[i].append(-self.name)  # updating direct implication

            # adding final clause
            self.encoded.append(cl)

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        for sub in self.subformulas:
            sub._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}{repr(self.subformulas)}'

    def __str__(self):
        """
            Informal representation of the ``And`` formula. Returns a string
            representations of the underlying subformulas joined with ``' &
            '``.
        """

        return ' & '.join([f'{str(sub)}' if sub.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(sub)})' for sub in self.subformulas])


#
#==============================================================================
class Or(Formula):
    """
        Disjunction. Given a list of operands (subformulas) :math:`f_i`,
        :math:`i \\in \\{1,\\ldots,n\\}, n \\in \\mathbb{N}`, it creates a
        formula :math:`\\bigvee_{i=1}^{n}{f_i}`. The list of operands *of size
        at least 1* should be passed as arguments to the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
            >>> conj = Or(x, y, z)

        If an additional Boolean keyword argument ``merge`` is provided set to
        ``True``, the toolkit will try to flatten the current :class:`Or`
        formula merging its *conjuctive* sub-operands into the list of
        operands. For example, if ``Or(Or(x, y), z, merge=True)`` is called, a
        new Formula object will be created with two operands: ``Or(x, y)`` and
        ``z``, followed by merging ``x`` and ``y`` into the list of root-level
        ``Or``. This will result in a formula ``Or(x, y, z)``. Merging
        sub-operands is enabled by default if bitwise operations are used to
        create ``Or`` formulas.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> a1 = Or(Or(Atom('x'), Atom('y')), Atom('z'))
            >>> a2 = Or(Or(Atom('x'), Atom('y')), Atom('z'), merge=True)
            >>> a3 = Atom('x') | Atom('y') | Atom('z')
            >>>
            >>> repr(a1)
            "Or[Or[Atom('x'), Atom('y')], Atom('z')]"
            >>> repr(a2)
            "Or[Atom('x'), Atom('y'), Atom('z')]"
            >>> repr(a2)
            "Or[Atom('x'), Atom('y'), Atom('z')]"
            >>>
            >>> id(a1) == id(a2)
            False
            >>>
            >>> id(a2) == id(a3)
            True  # formulas a2 and a3 refer to the same object

        .. note::

            If there are two formulas representing the same fact with and
            without merging enabled, they technically sit in two distinct
            objects. Although PySAT tries to avoid it, clausification of these
            two formulas may result in unique (different) auxiliary variables
            assigned to such two formulas.
    """

    def __new__(cls, *args, **kwargs):
        """
            Disjunction constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.OR)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects a list of arguments signifying the operands
            of the disjunction. Additionally, a user may set a keyword
            argument ``merge=True``, which will enable merging sub-operands.
        """

        super(Or, self).__init__(type=FormulaType.OR)

        self.subformulas = list(args)

        if 'merge' in kwargs and kwargs['merge'] == True:
            self._merge_suboperands()
            self.merged = True
        else:
            self.merged = False

    def __del__(self):
        """
            Destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.subformulas = []

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. First, iterates through the
            clauses of the subformulas followed by the formula's own clauses.
        """

        if not self in seen:
            seen[self] = True

            for sub in self.subformulas:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformulas and creates a new formula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = x | y | z
                >>>
                >>> print(a.simplified(assumptions=[y]))
                T  # True
                >>> print(a.simplified(assumptions=[~y]))
                x | z
        """

        oset = set()
        operands = []

        for sub in self.subformulas:
            # execute simplification recursively
            sub = sub.simplified(assumptions=set(assumptions))

            # simplify the current term
            if sub is PYSAT_TRUE or ~sub in oset:
                return PYSAT_TRUE

            # a new yet unsimplified term
            elif sub != PYSAT_FALSE and sub not in oset:
                oset.add(sub)
                operands.append(sub)

        # there is nothing left and we did not come across True
        # we should return False
        if not operands:
            return PYSAT_FALSE

        # there is one operand left; we need to return it instead
        if len(operands) == 1:
            return operands[0]

        return Or(*operands, merge=True) if self.merged else Or(*operands)

    def _clausify(self, name_required=True):
        """
            Disjunction clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the subformulas and populates self's clauses with unit clauses,
            each containing the auxiliary "name" of the corresponding
            subformula, thus representing their conjunction.

            If ``name_required`` is set to ``True``, the method encodes the
            conjunction using the standard logic: :math:`x \\equiv
            \\bigvee{y_i}`, if :math:`x` is the new auxiliary variable
            encoding ``self`` and :math:`y_i` is the auxiliary variable
            representing :math:`i`'s subformula.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformulas
            self.clauses.append([])  # empty clause, to be filled out
            for sub in self.subformulas:
                sub._clausify(name_required=True)

                # adding operand names to the clause
                self.clauses[0].append(sub.name)

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            self.name = Formula._vpool[Formula._context].id(self)

            # direct implication
            self.encoded[0].append(-self.name)

            # clauses representing converse implication
            for i in range(len(self.encoded[0]) - 1):
                self.encoded.append([self.name, -self.encoded[0][i]])

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        for sub in self.subformulas:
            sub._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}{repr(self.subformulas)}'

    def __str__(self):
        """
            Informal representation of the ``Or`` formula. Returns a string
            representations of the underlying subformulas joined with ``' |
            '``.
        """

        return ' | '.join([f'{str(sub)}' if sub.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(sub)})' for sub in self.subformulas])


#
#==============================================================================
class Neg(Formula):
    """
        Negation. Given a single operand (subformula) :math:`f`, it creates a
        formula :math:`\\neg{f}`. The operand must be passed as an argument to
        the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x = Atom('x')
            >>> n1 = Neg(x)
            >>> n2 = Neg(subformula=x)
            >>> print(n1, n2)
            ~x, ~x
            >>> n3 = ~n1
            >>> print(n3)
            x
    """

    def __new__(cls, *args, **kwargs):
        """
            Negation constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.NEG)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects either a single argument or a single keyword
            argument ``subformula`` to specify the operand of the negation.
        """

        super(Neg, self).__init__(type=FormulaType.NEG)

        if args:
            self.subformula = args[0]
        elif 'subformula' in kwargs:
            self.subformula = kwargs['subformula']
        else:
            assert 0, 'No subformula is given for this atom'

    def __del__(self):
        """
            Destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.subformula = None

    def _iter(self, seen, outermost=False):
        """
            Recursive iterator through the clauses.
        """

        if not self in seen:
            seen[self] = True

            for cl in self.subformula._iter(seen):
                yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformula and then creates and returns a new formula with this
            simplified subformula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = x & y | z
                >>> b = ~a
                >>>
                >>> print(b.simplified(assumptions=[y]))
                ~(x | z)
                >>> print(b.simplified(assumptions=[~y]))
                ~z
        """

        subformula = self.subformula.simplified(assumptions=set(assumptions))

        if subformula is PYSAT_FALSE:
            return PYSAT_TRUE
        elif subformula is PYSAT_TRUE:
            return PYSAT_FALSE
        else:
            return Neg(subformula)

    def _clausify(self, name_required=True):
        """
            Negation clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the subformula and populates self's clauses with a single unit clause
            containing the negation of the subformula's "name".

            If ``name_required`` is set to ``True``, the method removes this
            single unit clause and instead gives name to the negation, which
            is equal to the negation of subformula's name.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        if not self.clauses:
            # first, recursively encoding subformula
            self.subformula._clausify(name_required=True)
            self.clauses.append([-self.subformula.name])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            self.name = self.clauses[0][0]

            Formula._vpool[Formula._context].obj2id[self] = self.name
            Formula._vpool[Formula._context].id2obj[self.name] = self

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        self.subformula._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}({repr(self.subformula)})'

    def __str__(self):
        """
            Informal representation of the ``Neg`` formula. Returns a string
            representation of the underlying subformula prefixed with
            ``'~'``.
        """

        return f'~{str(self.subformula)}' if self.subformula.type == FormulaType.ATOM else f'~({str(self.subformula)})'


#
#==============================================================================
class Implies(Formula):
    """
        Implication. Given two operands :math:`f_1` and :math:`f_2`, it
        creates a formula :math:`f_1 \\rightarrow f_2`. The operands must be
        passed to the constructors either as two arguments or two keyword
        arguments ``left`` and ``right``.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y = Atom('x'), Atom('y')
            >>> a = Implies(x, y)
            >>> print(a)
            x >> y
    """

    def __new__(cls, *args, **kwargs):
        """
            Implication constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.IMPL)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects two arguments (either unnamed or keyword
            arguments) with the input formulas: left and right.
        """

        super(Implies, self).__init__(type=FormulaType.IMPL)

        # initially, there are no operands
        self.left = self.right = None

        pos = 0
        if 'left' in kwargs:
            self.left = kwargs['left']
        else:
            assert args, '\'left\' argument for Implies is not found'
            self.left = args[0]
            pos += 1

        if 'right' in kwargs:
            self.right = kwargs['right']
        else:
            assert len(args) > pos, '\'right\' argument for Implies is not found'
            self.right = args[pos]

        assert self.left and self.right, 'Implications accept two (left and right) operands'

    def __del__(self):
        """
            Implication destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.left = self.right = None

    def _iter(self, seen, outermost=False):
        """
            Clause iterator. Recursively iterates through the clauses of
            ``left`` and ``right`` subformulas followed by own clause
            traversal.
        """

        if not self in seen:
            seen[self] = True

            for sub in [self.left, self.right]:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """

            Given a list of assumption literals, recursively simplifies the
            left and right subformulas and then creates and returns a new
            formula with these simplified subformulas.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y')
                >>> a = x >> y
                >>>
                >>> print(a.simplified(assumptions=[y]))
                T
                >>> print(a.simplified(assumptions=[~y]))
                ~x
        """

        left  = self.left.simplified (assumptions=set(assumptions))
        right = self.right.simplified(assumptions=set(assumptions))

        if left is PYSAT_FALSE or right is PYSAT_TRUE or left == right:
            return PYSAT_TRUE
        elif left is PYSAT_TRUE:
            return right
        elif right is PYSAT_FALSE:
            return ~left
        elif self.left == ~right:
            return right

        return Implies(left, right)

    def _clausify(self, name_required=True):
        """
            Implication clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the left and right subformulas giving them names, say, :math:`x`
            and :math:`y` respectively and the populates self's clauses with a
            single binary clause :math:`(\\neg{x}\\lor y)`.

            If ``name_required`` is set to ``True``, the method removes this
            single clause and instead gives a name to the implication by
            Tseitin-encoding it, i.e. :math:`n \\equiv (\\neg{x}\\lor y)`.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformula
            self.left._clausify(name_required=True)
            self.right._clausify(name_required=True)
            self.clauses.append([-self.left.name, self.right.name])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            self.name = Formula._vpool[Formula._context].id(self)

            # direct implication
            self.encoded[0].append(-self.name)

            # clauses representing converse implication
            for i in range(len(self.encoded[0]) - 1):
                self.encoded.append([self.name, -self.encoded[0][i]])

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        self.left._atoms(dest)
        self.right._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}({repr(self.left)}, {repr(self.right)})'

    def __str__(self):
        """
            Informal representation of the ``Implies`` formula. Returns a
            string representation of the left and right subformulas with with
            a ``'>>'`` in the middle.
        """

        return '{0} >> {1}'.format(f'{str(self.left)}' if self.left.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(self.left)})',
                                   f'{str(self.right)}' if self.right.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(self.right)})')


#
#==============================================================================
class Equals(Formula):
    """
        Equivalence. Given a list of operands (subformulas) :math:`f_i`,
        :math:`i \\in \\{1,\\ldots,n\\}, n \\in \\mathbb{N}`, it creates a
        formula :math:`f_1 \\leftrightarrow f_2
        \\leftrightarrow\\ldots\\leftrightarrow f_n`. The list of operands *of
        size at least 2* should be passed as arguments to the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
            >>> equiv = Equals(x, y, z)

        If an additional Boolean keyword argument ``merge`` is provided set to
        ``True``, the toolkit will try to flatten the current :class:`Equals`
        formula merging its *equivalence* sub-operands into the list of
        operands. For example, if ``Equals(Equals(x, y), z, merge=True)`` is
        called, a new Formula object will be created with two operands:
        ``Equals(x, y)`` and ``z``, followed by merging ``x`` and ``y`` into
        the list of root-level ``Equals``. This will result in a formula
        ``Equals(x, y, z)``. Merging sub-operands is enabled by default if
        bitwise operations are used to create ``Equals`` formulas.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> a1 = Equals(Equals(Atom('x'), Atom('y')), Atom('z'))
            >>> a2 = Equals(Equals(Atom('x'), Atom('y')), Atom('z'), merge=True)
            >>> a3 = Atom('x') == Atom('y') == Atom('z')
            >>>
            >>> print(a1)
            (x @ y) @ z
            >>> print(a2)
            x @ y @ z
            >>> print(a3)
            x @ y @ z
            >>>
            >>> id(a1) == id(a2)
            False
            >>>
            >>> id(a2) == id(a3)
            True  # formulas a2 and a3 refer to the same object

        .. note::

            If there are two formulas representing the same fact with and
            without merging enabled, they technically sit in two distinct
            objects. Although PySAT tries to avoid it, clausification of these
            two formulas may result in unique (different) auxiliary variables
            assigned to such two formulas.
    """

    def __new__(cls, *args, **kwargs):
        """
            Equivalence constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.EQ)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects a list of arguments signifying the operands
            of the equivalence. Additionally, a user may set a keyword
            argument ``merge=True``, which will enable merging sub-operands.
        """

        super(Equals, self).__init__(type=FormulaType.EQ)

        self.subformulas = list(args)

        if 'merge' in kwargs and kwargs['merge'] == True:
            self._merge_suboperands()
            self.merged = True
        else:
            self.merged = False

        if len(self.subformulas) < 2:
            raise FormulaError('Equivalence requires at least 2 arguments')

    def __del__(self):
        """
            Destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.subformulas = []

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. First, iterates through the
            clauses of the subformulas followed by the formula's own clauses.
        """

        if not self in seen:
            seen[self] = True

            for sub in self.subformulas:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformulas and creates a new formula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = x @ y @ z
                >>>
                >>> print(a.simplified(assumptions=[y]))
                x & z    # x and z must also be True
                >>> print(a.simplified(assumptions=[~y]))
                ~x & ~z  # x and z must also be False
        """

        oset = set()
        operands = []
        t_present, f_present = False, False

        for sub in self.subformulas:
            # execute simplification recursively
            sub = sub.simplified(assumptions=set(assumptions))

            # record if the subterms degenerated to a True constant
            if sub is PYSAT_TRUE:
                if f_present:
                    return PYSAT_FALSE
                t_present = True
            # same for False
            elif sub is PYSAT_FALSE:
                if t_present:
                    return PYSAT_FALSE
                f_present = True
            # there is an opposite subformula too; equality is unsatisfiable
            elif ~sub in oset:
                return PYSAT_FALSE

            # a new yet unsimplified term
            elif sub not in oset:
                oset.add(sub)
                operands.append(sub)

        if not operands:
            return PYSAT_FALSE if f_present and t_present else PYSAT_TRUE

        if len(operands) == 1:
            if not (t_present or f_present):
                # we got a single subformula but nothing is simplified above;
                # hence, the single subformula results from duplicate removal
                # i.e. we have a tautological equality
                return PYSAT_TRUE

            return operands[0] if not f_present else Neg(operands[0])

        if f_present or t_present:
            if f_present:
                operands = [Neg(sub) for sub in operands]
            return And(*operands, merge=True) if self.merged else And(*operands)

        return Equals(*operands, merge=True) if self.merged else Equals(*operands)

    def _clausify(self, name_required=True):
        """
            Equivalence clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the subformulas and populates self's clauses with binary clauses
            connecting two consecutive subformulas :math:`f_i` and
            :math:`f_{i+1}` by introducing two clauses :math:`(\\neg{f_i}\\lor
            f_{i+1})` and :math:`(f_i\\lor\\neg{f_i+1})`.

            If ``name_required`` is set to ``True``, the method introduces an
            new auxiliary name for the equivalence term and clausifies it by
            relating it with the names of subformulas.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformulas
            for sub in self.subformulas:
                sub._clausify(name_required=True)

            for i in range(len(self.subformulas) - 1):
                # current subformula is equivalent to the next one
                self.clauses.append([-self.subformulas[i].name, +self.subformulas[i + 1].name])
                self.clauses.append([+self.subformulas[i].name, -self.subformulas[i + 1].name])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            self.name = Formula._vpool[Formula._context].id(self)

            # direct implication (just adding the selector)
            for cl in self.encoded:
                cl.append(-self.name)

            # clauses representing converse implication
            self.encoded.append([self.name] + [-s.name for s in self.subformulas])
            self.encoded.append([self.name] + [+s.name for s in self.subformulas])

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        for sub in self.subformulas:
            sub._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}{repr(self.subformulas)}'

    def __str__(self):
        """
            Informal representation of the ``Equals`` formula. Returns a
            string representation of the subformulas with with joined by
            ``' @ '``.
        """

        return ' @ '.join([f'{str(sub)}' if sub.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(sub)})' for sub in self.subformulas])


#
#==============================================================================
class XOr(Formula):
    """
        Exclusive disjunction. Given a list of operands (subformulas)
        :math:`f_i`, :math:`i \\in \\{1,\\ldots,n\\}, n \\in \\mathbb{N}`, it
        creates a formula :math:`f_1 \\oplus f_2 \\oplus\\ldots\\oplus f_n`.
        The list of operands *of size at least 2* should be passed as
        arguments to the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
            >>> xor = XOr(x, y, z)

        If an additional Boolean keyword argument ``merge`` is provided set to
        ``True``, the toolkit will try to flatten the current :class:`XOr`
        formula merging its *equivalence* sub-operands into the list of
        operands. For example, if ``XOr(XOr(x, y), z, merge=True)`` is called,
        a new Formula object will be created with two operands: ``XOr(x, y)``
        and ``z``, followed by merging ``x`` and ``y`` into the list of
        root-level ``XOr``. This will result in a formula ``XOr(x, y, z)``.
        Merging sub-operands is disabled by default if bitwise operations are
        used to create ``XOr`` formulas.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> a1 = XOr(XOr(Atom('x'), Atom('y')), Atom('z'))
            >>> a2 = XOr(XOr(Atom('x'), Atom('y')), Atom('z'), merge=True)
            >>> a3 = Atom('x') ^ Atom('y') ^ Atom('z')
            >>>
            >>> print(a1)
            (x ^ y) ^ z
            >>> print(a2)
            x ^ y ^ z
            >>> print(a3)
            (x ^ y) ^ z
            >>>
            >>> id(a1) == id(a2)
            False
            >>>
            >>> id(a1) == id(a3)
            True  # formulas a1 and a3 refer to the same object

        .. note::

            If there are two formulas representing the same fact with and
            without merging enabled, they technically sit in two distinct
            objects. Although PySAT tries to avoid it, clausification of these
            two formulas may result in unique (different) auxiliary variables
            assigned to such two formulas.
    """

    def __new__(cls, *args, **kwargs):
        """
            Equivalence constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.XOR)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects a list of arguments signifying the operands
            of the exclusive disjunction. Additionally, a user may set a
            keyword argument ``merge=True``, which will enable merging
            sub-operands.
        """

        super(XOr, self).__init__(type=FormulaType.XOR)

        self.subformulas = list(args)

        if 'merge' in kwargs and kwargs['merge'] == True:
            self._merge_suboperands()
            self.merged = True
        else:
            self.merged = False

        if len(self.subformulas) < 2:
            raise FormulaError('XOr requires at least 2 arguments')

    def __del__(self):
        """
            Destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.subformulas = []

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. First, iterates through the
            clauses of the subformulas followed by the formula's own clauses.
        """

        if not self in seen:
            seen[self] = True

            for sub in self.subformulas:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformulas and creates a new formula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> a = x ^ y ^ z
                >>>
                >>> print(a.simplified(assumptions=[y]))
                ~x ^ z
                >>> print(a.simplified(assumptions=[~y]))
                x ^ z
        """

        oset = {}
        nof_trues = 0

        for sub in self.subformulas:
            # execute simplification recursively
            sub = sub.simplified(assumptions=set(assumptions))

            # record if the subterms degenerated to a True constant
            if sub is PYSAT_TRUE:
                nof_trues += 1

            # we've got x ^ ~x, which results in a True constant
            elif ~sub in oset:
                nof_trues += 1
                oset.pop(~sub)

            # this is a duplicate of an already seen sub-term
            # as a result, they cancel each other out
            elif sub in oset:
                oset.pop(sub)

            # a new yet unsimplified term
            elif sub is not PYSAT_FALSE:
                oset[sub] = None

        # getting the actual list of operands
        operands = list(oset)

        if not operands:
            return PYSAT_TRUE if nof_trues % 2 else PYSAT_FALSE

        if len(operands) == 1:
            return operands[0] if nof_trues % 2 == 0 else Neg(operands[0])

        if nof_trues % 2 == 1:
            return Neg(XOr(*operands, merge=True)) if self.merged else Neg(XOr(*operands))

        return XOr(*operands, merge=True) if self.merged else XOr(*operands)

    def _clausify(self, name_required=True):
        """
            XOr clausification. If the number of subformulas is more than 2,
            encodes the XOr sequentially by gradually introducing an auxiliary
            variable for each pair of operands.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformulas
            inputs = []
            for sub in self.subformulas:
                sub._clausify(name_required=True)
                inputs.append(sub.name)

            if len(self.subformulas) > 2:
                # build a hierarchy of binary XOR constraints
                # until there are exactly two inputs left
                while len(inputs) > 2:
                    n2 = inputs.pop()
                    n1 = inputs.pop()

                    f1 = Formula._vpool[Formula._context].obj(n1)
                    f2 = Formula._vpool[Formula._context].obj(n2)

                    # creating auxiliary XOr formulas and encoding them
                    ao = XOr(f1, f2)
                    ao._clausify(name_required=True)

                    # collecting all the corresponding clauses
                    self.clauses += ao.encoded

                    inputs.append(ao.name)

                assert len(inputs) == 2, 'Wrong number of operands for XOr when encoding'

                # final XOr, without a name (for now)
                f1 = Formula._vpool[Formula._context].obj(inputs[0])
                f2 = Formula._vpool[Formula._context].obj(inputs[1])

                final = XOr(f1, f2)
                final.clauses.append([-inputs[0], -inputs[1]])
                final.clauses.append([+inputs[0], +inputs[1]])

                self.clauses += final.clauses
            else:
                self.clauses.append([-inputs[0], -inputs[1]])
                self.clauses.append([+inputs[0], +inputs[1]])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            n1, n2 = self.encoded[-1]
            if len(self.subformulas) > 2:
                # reconstructing the final subterm
                f1 = Formula._vpool[Formula._context].obj(n1)
                f2 = Formula._vpool[Formula._context].obj(n2)
                final = XOr(f1, f2)

                final.name = Formula._vpool[Formula._context].id(final)
                self.name = final.name
            else:
                self.name = Formula._vpool[Formula._context].id(self)
                final = None

            # direct implication (just adding the selector)
            self.encoded[-2].append(-self.name)
            self.encoded[-1].append(-self.name)

            # clauses representing converse implication
            self.encoded.append([self.name, -n1, +n2])
            self.encoded.append([self.name, +n1, -n2])

            if final:
                # sharing converse implication with final subterm (if any)
                final.encoded.append(self.encoded[-2])
                final.encoded.append(self.encoded[-1])

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        for sub in self.subformulas:
            sub._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}{repr(self.subformulas)}'

    def __str__(self):
        """
            Informal representation of the ``XOr`` formula. Returns a
            string representation of the subformulas with with joined by
            ``' ^ '``.
        """

        return ' ^ '.join([f'{str(sub)}' if sub.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(sub)})' for sub in self.subformulas])


#
#==============================================================================
class ITE(Formula):
    """
        If-then-else operator. Given three operands (subformulas) :math:`x`,
        :math:`y`, and :math:`z`, it creates a formula :math:`(x \\rightarrow
        y) \\land (\\neg{x} \\rightarrow z)`. The operands should be passed as
        arguments to the constructor.

        Example:

        .. code-block:: python

            >>> from pysat.formula import *
            >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
            >>> ite = ITE(x, y, z)
            >>>
            >>> print(ite)
            >>> (x >> y) & (~x >> z)
    """

    def __new__(cls, *args, **kwargs):
        """
            ITE constructor.
        """

        return Formula.__new__(cls, args, kwargs, type=FormulaType.ITE)

    def __init__(self, *args, **kwargs):
        """
            Initialiser. Expects three arguments (either unnamed or keyword
            arguments) with the input formulas: ``cond`` (condition),
            ``cons1`` (consequence1) and ``cons2`` (consequence2).
        """

        super(ITE, self).__init__(type=FormulaType.ITE)

        # initially, there are no operands
        self.cond = self.cons1 = self.cons2 = None

        pos = 0
        if 'cond' in kwargs:
            self.cond = kwargs['cond']
        else:
            assert args, '\'cond\' argument for ITE is not found'
            self.cond = args[0]
            pos += 1

        if 'cons1' in kwargs:
            self.cons1 = kwargs['cons1']
        else:
            assert len(args) > pos, '\'cons1\' argument for ITE is not found'
            self.cons1 = args[pos]
            pos += 1

        if 'cons2' in kwargs:
            self.cons2 = kwargs['cons2']
        else:
            assert len(args) > pos, '\'cons2\' argument for ITE is not found'
            self.cons2 = args[pos]

        assert self.cond and self.cons1 and self.cons2, 'ITE formulas accept three (cond, cons1, and cons2) operands'

    def __del__(self):
        """
            Destructor.
        """

        self.name = None
        self.clauses = []
        self.encoded = []
        self.cond = self.cons1 = self.cons2 = None

    def _iter(self, seen, outermost=False):
        """
            Internal iterator over the clauses. First, iterates through the
            clauses of the subformulas followed by the formula's own clauses.
        """

        if not self in seen:
            seen[self] = True

            for sub in [self.cond, self.cons1, self.cons2]:
                for cl in sub._iter(seen):
                    yield cl

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            Given a list of assumption literals, recursively simplifies the
            subformulas and creates a new formula.

            :param assumptions: atomic assumptions
            :type assumptions: list(:class:`Formula`)

            :rtype: :class:`Formula`

            Example:

            .. code-block:: python

                >>> from pysat.formula import *
                >>> x, y, z = Atom('x'), Atom('y'), Atom('z')
                >>> ite = ITE(x, y, z)
                >>>
                >>> print(ite.simplified(assumptions=[y]))
                x | z
                >>> print(ite.simplified(assumptions=[~y]))
                ~x & z
        """

        assumptions = set(assumptions)
        cond  = self.cond .simplified(assumptions)
        cons1 = self.cons1.simplified(assumptions)
        cons2 = self.cons2.simplified(assumptions)

        # a heavy list of conditions, each of which can simplify the expression
        if cond is PYSAT_TRUE:
            return cons1
        elif cond is PYSAT_FALSE:
            return cons2
        elif cons1 is PYSAT_TRUE or cons1 == cond:
            return Or(cond, cons2).simplified(assumptions)
        elif cons2 is PYSAT_TRUE or cons2 == Neg(cond) or cond == Neg(cons2):
            return Implies(cond, cons1).simplified(assumptions)
        elif cond == Neg(cons1) or Neg(cond) == cons1 or cond == cons2:
            return And(cons1, cons2).simplified(assumptions)
        elif cons1 is PYSAT_FALSE:
            return And(Neg(cond), cons2).simplified(assumptions)
        elif cons2 is PYSAT_FALSE:
            return And(cond, cons1).simplified(assumptions)
        elif cons1 == Neg(cons2) or Neg(cons1) == cons2:
            return Equals(cond, cons1).simplified(assumptions)

        return ITE(cond, cons1, cons2)

    def _clausify(self, name_required=True):
        """
            ITE clausification.

            If ``name_required`` is ``False``, the method recursively encodes
            the ``cond``, ``cons1``, and ``cons2`` subformulas giving them
            names, say, :math:`x`, :math:`y`, and :math:`z`, respectivela, and
            the populates self's clauses with two binary clauses
            :math:`(\\neg{x}\\lor y)` and :math:`(x \\lor y)`.

            If ``name_required`` is set to ``True``, the method removes these
            clauses and instead gives a name to the ITE by Tseitin-encoding
            it, i.e. encoding :math:`n \\equiv \\left[(\\neg{x}\\lor
            y)\\land(x\\lor y)\\right]`.

            :param name_required: whether or not a Tseitin variable is needed
            :param name_required: bool
        """

        save_clauses = bool(self.clauses)

        if not self.clauses:
            # first, recursively encoding subformula
            self.cond._clausify(name_required=True)
            self.cons1._clausify(name_required=True)
            self.cons2._clausify(name_required=True)
            self.clauses.append([-self.cond.name, self.cons1.name])
            self.clauses.append([+self.cond.name, self.cons2.name])

        # introducing a new name for this formula if required
        if name_required and not self.name:
            if save_clauses:
                self.encoded = [clause.copy() for clause in self.clauses]
            else:
                self.encoded = self.clauses
                self.clauses = []

            self.name = Formula._vpool[Formula._context].id(self)

            # direct implication
            self.encoded[0].append(-self.name)
            self.encoded[1].append(-self.name)

            # converse implication
            self.encoded.append([self.name, -self.cond.name,  -self.cons1.name])
            self.encoded.append([self.name, +self.cond.name,  -self.cons2.name])
            self.encoded.append([self.name, -self.cons1.name, -self.cons2.name])

    def _atoms(self, dest):
        """
            Recursive atom collection.

            :param dest: where the atoms are collected
            :type dest: set(:class:`Atom`)
        """

        self.cond._atoms(dest)
        self.cons1._atoms(dest)
        self.cons2._atoms(dest)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        return f'{self.__class__.__name__}({repr(self.cond)}, {repr(self.cons1)}, {repr(self.cons2)})'

    def __str__(self):
        """
            Informal representation of the ``ITE`` formula. Returns a string
            representation of the subformulas as two implications connected
            with the conjuction symbol ``' & '``
        """

        cons1 = '{0} >> {1}'.format(f'{str(self.cond)}' if self.cond.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(self.cond)})',
                                   f'{str(self.cons1)}' if self.cons1.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(self.cons1)})')

        cons2 = '{0} >> {1}'.format(f'~{str(self.cond)}' if self.cond.type in (FormulaType.ATOM, FormulaType.NEG) else f'~({str(self.cond)})',
                                   f'{str(self.cons2)}' if self.cons2.type in (FormulaType.ATOM, FormulaType.NEG) else f'({str(self.cons2)})')

        return '({0}) & ({1})'.format(cons1, cons2)


#
#==============================================================================
class CNF(Formula, object):
    """
        Class for manipulating CNF formulas. It can be used for creating
        formulas, reading them from a file, or writing them to a file. The
        ``comment_lead`` parameter can be helpful when one needs to parse
        specific comment lines starting not with character ``c`` but with
        another character or a string.

        :param from_file: a DIMACS CNF filename to read from
        :param from_fp: a file pointer to read from
        :param from_string: a string storing a CNF formula
        :param from_clauses: a list of clauses to bootstrap the formula with
        :param from_aiger: an AIGER circuit to bootstrap the formula with
        :param comment_lead: a list of characters leading comment lines
        :param by_ref: flag to indicate how to copy clauses - by reference or deep-copy

        :type from_file: str
        :type from_fp: file_pointer
        :type from_string: str
        :type from_clauses: list(list(int))
        :type from_aiger: :class:`aiger.AIG` (see `py-aiger package <https://github.com/mvcisback/py-aiger>`__)
        :type comment_lead: list(str)
        :type by_ref: bool
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None,
            from_clauses=[], from_aiger=None, comment_lead=['c'], by_ref=False):
        """
            Constructor.
        """

        self.nv = 0
        self.clauses = []
        self.encoded = []
        self.comments = []

        # this variable is required for integration with Formula
        self.name = None
        self.type = FormulaType.CNF

        if from_file:
            self.from_file(from_file, comment_lead, compressed_with='use_ext')
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)
        elif from_clauses:
            self.from_clauses(from_clauses, by_ref)
        elif from_aiger:
            self.from_aiger(from_aiger)

    def __new__(cls, *args, **kwargs):
        """
            While :class:`CNF` inherits from :class:`Formula` (and so do its
            children), we don't want it to invoke the complex mechanisms of
            formula construction for CNF formulas. Instead, they should behave
            as in the previous versions of PySAT. Therefore, we call a simple
            object constructor here.
        """

        return object.__new__(cls)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        s = self.to_dimacs().replace('\n', '\\n')
        return f'CNF(from_string=\'{s}\')'

    def _compute_nv(self):
        """
            Search and store the highest variable.
        """

        self.nv = max(map(abs, itertools.chain(*self.clauses)), default=self.nv)

        # in case we use this CNF as a subformula in the future,
        # let's put the number of used variables in Formula's IDPool
        Formula._vpool[Formula._context].occupy(1, self.nv)

    def from_file(self, fname, comment_lead=['c'], compressed_with='use_ext'):
        """
            Read a CNF formula from a file in the DIMACS format. A file name is
            expected as an argument. A default argument is ``comment_lead`` for
            parsing comment lines. A given file can be compressed by either
            gzip, bzip2, lzma, or zstd.

            :param fname: name of a file to parse.
            :param comment_lead: a list of characters leading comment lines
            :param compressed_with: file compression algorithm

            :type fname: str
            :type comment_lead: list(str)
            :type compressed_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``,
            ``'zstd'``, or ``'use_ext'``. The latter value indicates that
            compression type should be automatically determined based on the
            file extension. Using ``'lzma'`` in Python 2 requires the
            ``backports.lzma`` package to be additionally installed. Using
            ``'zstd'`` requires Python 3.14.

            Usage example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf1 = CNF()
                >>> cnf1.from_file('some-file.cnf.gz', compressed_with='gzip')
                >>>
                >>> cnf2 = CNF(from_file='another-file.cnf')
        """

        with FileObject(fname, mode='r', compression=compressed_with) as fobj:
            self.from_fp(fobj.fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read a CNF formula from a file pointer. A file pointer should be
            specified as an argument. The only default argument is
            ``comment_lead``, which can be used for parsing specific comment
            lines.

            :param file_pointer: a file pointer to read the formula from.
            :param comment_lead: a list of characters leading comment lines

            :type file_pointer: file pointer
            :type comment_lead: list(str)

            Usage example:

            .. code-block:: python

                >>> with open('some-file.cnf', 'r') as fp:
                ...     cnf1 = CNF()
                ...     cnf1.from_fp(fp)
                >>>
                >>> with open('another-file.cnf', 'r') as fp:
                ...     cnf2 = CNF(from_fp=fp)
        """

        self.nv = 0
        self.clauses = []
        self.comments = []
        comment_lead = set(['p']).union(set(comment_lead))

        for line in file_pointer:
            line = line.rstrip()
            if line:
                if line[0] not in comment_lead:
                    self.clauses.append(list(map(int, line.split()[:-1])))
                elif not line.startswith('p cnf '):
                    self.comments.append(line)

        self._compute_nv()

    def from_string(self, string, comment_lead=['c']):
        """
            Read a CNF formula from a string. The string should be specified as
            an argument and should be in the DIMACS CNF format. The only
            default argument is ``comment_lead``, which can be used for parsing
            specific comment lines.

            :param string: a string containing the formula in DIMACS.
            :param comment_lead: a list of characters leading comment lines

            :type string: str
            :type comment_lead: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf1 = CNF()
                >>> cnf1.from_string('p cnf 2 2\\n-1 2 0\\n1 -2 0')
                >>> print(cnf1.clauses)
                [[-1, 2], [1, -2]]
                >>>
                >>> cnf2 = CNF(from_string='p cnf 3 3\\n-1 2 0\\n-2 3 0\\n-3 0\\n')
                >>> print(cnf2.clauses)
                [[-1, 2], [-2, 3], [-3]]
                >>> print(cnf2.nv)
                3
        """

        self.from_fp(StringIO(string), comment_lead)

    def from_clauses(self, clauses, by_ref=False):
        """
            This methods copies a list of clauses into a CNF object. The
            optional keyword argument ``by_ref``, which is by default set to
            ``False``, signifies whether the clauses should be deep-copied or
            copied by reference (by default, deep-copying is applied although
            it is slower).

            :param clauses: a list of clauses
            :param by_ref: a flag to indicate whether to deep-copy the clauses or copy them by reference

            :type clauses: list(list(int))
            :type by_ref: bool

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [1, -2], [5]])
                >>> print(cnf.clauses)
                [[-1, 2], [1, -2], [5]]
                >>> print(cnf.nv)
                5
        """

        self.clauses = clauses if by_ref else copy.deepcopy(clauses)

        self._compute_nv()

    def from_aiger(self, aig, vpool=None):
        """

            Create a CNF formula by Tseitin-encoding an input AIGER circuit.

            Input circuit is expected to be an object of class
            :class:`aiger.AIG`. Alternatively, it can be specified as an
            :class:`aiger.BoolExpr`, or an ``*.aag`` filename, or an AIGER
            string to parse. (Classes :class:`aiger.AIG` and
            :class:`aiger.BoolExpr` are defined in the `py-aiger package
            <https://github.com/mvcisback/py-aiger>`__.)

            :param aig: an input AIGER circuit
            :param vpool: pool of variable identifiers (optional)

            :type aig: :class:`aiger.AIG` (see `py-aiger package <https://github.com/mvcisback/py-aiger>`__)
            :type vpool: :class:`.IDPool`

            Example:

            .. code-block:: python

                >>> import aiger
                >>> x, y, z = aiger.atom('x'), aiger.atom('y'), aiger.atom('z')
                >>> expr = ~(x | y) & z
                >>> print(expr.aig)
                aag 5 3 0 1 2
                2
                4
                8
                10
                6 3 5
                10 6 8
                i0 y
                i1 x
                i2 z
                o0 6c454aea-c9e1-11e9-bbe3-3af9d34370a9
                >>>
                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_aiger=expr.aig)
                >>> print(cnf.nv)
                5
                >>> print(cnf.clauses)
                [[3, 2, 4], [-3, -4], [-2, -4], [-4, -1, 5], [4, -5], [1, -5]]
                >>> print(['{0} <-> {1}'.format(v, cnf.vpool.obj(v)) for v in cnf.inps])
                ['3 <-> y', '2 <-> x', '1 <-> z']
                >>> print(['{0} <-> {1}'.format(v, cnf.vpool.obj(v)) for v in cnf.outs])
                ['5 <-> 6c454aea-c9e1-11e9-bbe3-3af9d34370a9']
        """

        assert aiger_present, 'Package \'py-aiger-cnf\' is unavailable. Check your installation.'

        # creating a pool of variable IDs if necessary
        self.vpool = vpool if vpool else IDPool()

        # Use py-aiger-cnf to insulate from internal py-aiger details.
        aig_cnf = aiger_cnf.aig2cnf(aig, fresh=self.vpool.id, force_true=False)

        self.clauses = [list(cls) for cls in aig_cnf.clauses]
        self.comments = ['c ' + c.strip() for c in aig_cnf.comments]
        self._compute_nv()

        # saving input and output variables
        self.inps = list(aig_cnf.input2lit.values())
        self.outs = list(aig_cnf.output2lit.values())

    def copy(self):
        """
            This method can be used for creating a copy of a CNF object. It
            creates another object of the :class:`CNF` class and makes use of
            the *deepcopy* functionality to copy the clauses.

            :return: an object of class :class:`CNF`.

            Example:

            .. code-block:: python

                >>> cnf1 = CNF(from_clauses=[[-1, 2], [1]])
                >>> cnf2 = cnf1.copy()
                >>> print(cnf2.clauses)
                [[-1, 2], [1]]
                >>> print(cnf2.nv)
                2
        """

        cnf = CNF()
        cnf.nv = self.nv
        cnf.clauses = copy.deepcopy(self.clauses)
        cnf.encoded = copy.deepcopy(self.encoded)
        cnf.comments = copy.deepcopy(self.comments)

        return cnf

    def to_file(self, fname, comments=None, as_dnf=False, compress_with='use_ext'):
        """
            The method is for saving a CNF formula into a file in the DIMACS
            CNF format. A file name is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter. Also, a file can be compressed using either gzip, bzip2,
            lzma (xz), or zstd.

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.
            :param as_dnf: a flag to use for specifying "dnf" in the preamble.
            :param compress_with: file compression algorithm.

            :type fname: str
            :type comments: list(str)
            :type as_dnf: bool
            :type compress_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``,
            ``'zstd'``, or ``'use_ext'``. The latter value indicates that
            compression type should be automatically determined based on the
            file extension. Using ``'lzma'`` in Python 2 requires the
            ``backports.lzma`` package to be additionally installed. Using
            ``'zstd'`` requires Python 3.14.

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> cnf.to_file('some-file-name.cnf')  # writing to a file
        """

        with FileObject(fname, mode='w', compression=compress_with) as fobj:
            self.to_fp(fobj.fp, comments, as_dnf)

    def to_fp(self, file_pointer, comments=None, as_dnf=False):
        """
            The method can be used to save a CNF formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param comments: additional comments to put in the file.
            :param as_dnf: a flag to use for specifying "dnf" in the preamble.

            :type file_pointer: file pointer
            :type comments: list(str)
            :type as_dnf: bool

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.cnf', 'w') as fp:
                ...     cnf.to_fp(fp)  # writing to the file pointer
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        print('p cnf' if not as_dnf else 'p dnf', self.nv, len(self.clauses), file=file_pointer)

        for cl in self.clauses:
            print(' '.join(str(l) for l in cl), '0', file=file_pointer)

    def to_dimacs(self):
        """
            Return the current state of the object in DIMACS format.

            For example, if 'some-file.cnf' contains:

            ::

                c Example
                p cnf 3 3
                -1 2 0
                -2 3 0
                -3 0

            Then you can obtain the DIMACS with:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_file='some-file.cnf')
                >>> print(cnf.to_dimacs())
                c Example
                p cnf 3 3
                -1 2 0
                -2 3 0
                -3 0
        """

        header_lines = [f'p cnf {self.nv} {len(self.clauses)}']
        comment_lines = [f'{comment}' for comment in self.comments]
        clause_lines = [' '.join(map(str,clause)) + ' 0' for clause in self.clauses]

        lines = '\n'.join(comment_lines + header_lines + clause_lines)
        return lines

    def to_alien(self, file_pointer, format='opb', comments=None):
        """
            The method can be used to dump a CNF formula into a file pointer
            in an alien file format, which at this point can either be LP,
            OPB, or SMT. The file pointer is expected as an argument.
            Additionally, the target format 'lp', 'opb', or 'smt' may be
            specified (equal to 'opb' by default). Finally, supplementary
            comment lines can be specified in the ``comments`` parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param format: alien file format to use
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type format: str
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.lp', 'w') as fp:
                ...     cnf.to_alien(fp, format='lp')  # writing to the file pointer
        """

        cchars = {'lp': '\\', 'opb': '*', 'smt': ';'}

        # saving formula's internal comments
        for c in self.comments:
            print(cchars[format], c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(cchars[format], c, file=file_pointer)

        if format == 'opb':
            print('* #variable= {0} #constraint= {1}'.format(self.nv, len(self.clauses)),
                    file=file_pointer)
        elif format == 'lp':
            print('Minimize', file=file_pointer)
            print('obj:', file=file_pointer)
            print('Subject To', file=file_pointer)
        elif format == 'smt':
            for v in range(1, self.nv + 1):
                print('(declare-fun x{0} () Bool)'.format(v), file=file_pointer)

        for i, cl in enumerate(self.clauses, 1):
            line, neg = [], 0
            for l in cl:
                if l > 0:
                    if format == 'smt':
                        line.append('x{0}'.format(l))
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', l))
                else:
                    if format == 'smt':
                        line.append('(not x{0})'.format(-l))
                    else:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', -l))
                        neg += 1

            if format == 'smt':
                print('(assert (or {0}))'.format(' '.join(line)), file=file_pointer)
            else:
                print('{0} {1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}:'.format(i),
                        ' '.join(l for l in line),
                        1 - neg, ';' if format == 'opb' else ''),
                        file=file_pointer)

        if format == 'lp':
            print('Bounds', file=file_pointer)
            for v in range(1, self.nv + 1):
                print('0 <= x{0} <= 1'.format(v), file=file_pointer)
            print('Binary', file=file_pointer)
            for v in range(1, self.nv + 1):
                print('x{0}'.format(v), file=file_pointer)
            print('End', file=file_pointer)
        elif format == 'smt':
            print('(check-sat)', file=file_pointer)
            print('(exit)', file=file_pointer)

    def append(self, clause, update_vpool=False):
        """
            Add one more clause to CNF formula. This method additionally
            updates the number of variables, i.e. variable ``self.nv``, used
            in the formula.

            The additional keyword argument ``update_vpool`` can be set to
            ``True`` if the user wants to update for default static pool of
            variable identifiers stored in class :class:`Formula`. In light of
            the fact that a user may encode their problem manually and add
            thousands to millions of clauses using this method, the value of
            ``update_vpool`` is set to ``False`` by default.

            .. note::

                Setting ``update_vpool=True`` is required if a user wants to
                combine this :class:`CNF` formula with other (clausal or
                non-clausal) formulas followed by the clausification of the
                result combination. Alternatively, a user may resort to using
                the method :meth:`extend` instead.

            :param clause: a new clause to add
            :param update_vpool: update or not the static vpool

            :type clause: list(int)
            :type update_vpool: bool

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [3]])
                >>> cnf.append([-3, 4])
                >>> print(cnf.clauses)
                [[-1, 2], [3], [-3, 4]]
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])
        self.clauses.append(list(clause))

        if update_vpool:
            Formula._vpool[Formula._context].occupy(1, self.nv)

    def extend(self, clauses):
        """
            Add several clauses to CNF formula. The clauses should be given in
            the form of list. For every clause in the list, method
            :meth:`append` is invoked.

            :param clauses: a list of new clauses to add
            :type clauses: list(list(int))

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [3]])
                >>> cnf.extend([[-3, 4], [5, 6]])
                >>> print(cnf.clauses)
                [[-1, 2], [3], [-3, 4], [5, 6]]
        """

        for cl in clauses:
            self.append(cl)

        # updating the default vpool here, once all the clauses are appended
        Formula._vpool[Formula._context].occupy(1, self.nv)

    def __iter__(self):
        """
            Iterator over all clauses of the formula.
        """

        for cl in self.clauses:
            yield cl

    def weighted(self):
        """
            This method creates a weighted copy of the internal formula. As a
            result, an object of class :class:`WCNF` is returned. Every clause
            of the CNF formula is *soft* in the new WCNF formula and its weight
            is equal to ``1``. The set of hard clauses of the formula is empty.

            :return: an object of class :class:`WCNF`.

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [3, 4]])
                >>>
                >>> wcnf = cnf.weighted()
                >>> print(wcnf.hard)
                []
                >>> print(wcnf.soft)
                [[-1, 2], [3, 4]]
                >>> print(wcnf.wght)
                [1, 1]
        """

        wcnf = WCNF()

        wcnf.nv = self.nv
        wcnf.hard = []
        wcnf.soft = copy.deepcopy(self.clauses)
        wcnf.wght = [1 for cl in wcnf.soft]
        wcnf.topw = len(wcnf.wght) + 1
        wcnf.comments = self.comments[:]

        return wcnf

    def negate(self, topv=None):
        """
            Given a CNF formula :math:`\\mathcal{F}`, this method creates a
            CNF formula :math:`\\neg{\\mathcal{F}}`. The negation of the
            formula is encoded to CNF with the use of *auxiliary* Tseitin
            variables [1]_. A new CNF formula is returned keeping all the
            newly introduced variables that can be accessed through the
            ``auxvars`` variable. All the literals used to encode the negation
            of the original clauses can be accessed through the ``enclits``
            variable.

            **Note** that the negation of each clause is encoded with one
            auxiliary variable if it is not unit size. Otherwise, no auxiliary
            variable is introduced.

            :param topv: top variable identifier if any.
            :type topv: int

            :return: an object of class :class:`CNF`.

            .. [1] G. S. Tseitin. *On the complexity of derivations in the
                propositional calculus*.  Studies in Mathematics and
                Mathematical Logic, Part II. pp.  115–125, 1968

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> pos = CNF(from_clauses=[[-1, 2], [3]])
                >>> neg = pos.negate()
                >>> print(neg.clauses)
                [[1, -4], [-2, -4], [-1, 2, 4], [4, -3]]
                >>> print(neg.auxvars)
                [4]
                >>> print(neg.enclits)  # literals encoding the negation of clauses
                [4, -3]
        """

        negated = CNF()

        negated.nv = topv
        if not negated.nv:
            negated.nv = self.nv

        negated.clauses = []
        negated.auxvars = []
        negated.enclits = []

        for cl in self.clauses:
            auxv = -cl[0]
            if len(cl) > 1:
                negated.nv += 1
                auxv = negated.nv

                # direct implication
                for l in cl:
                    negated.clauses.append([-l, -auxv])

                # opposite implication
                negated.clauses.append(cl + [auxv])

                # keeping all Tseitin variables
                negated.auxvars.append(auxv)

            # literals representing negated clauses
            negated.enclits.append(auxv)

        negated.clauses.append(negated.enclits)
        return negated

    def _clausify(self, name_required=False):
        """
            As a means of seamless integration of :class:`CNF` and
            :class:`Formula` objects, this method Tseitin-encodes a CNF
            formula, which results in a new Boolean variable "naming" it.

            If ``name_required`` is ``False``, nothing is done as the formula
            is already clausal.
        """

        # no clausification is required as we have a CNF already
        # but a name may be required; hence, the following Tseitin-encoding

        if name_required and not self.name:
            # we do not update top variable id, allowing a user to reuse variables
            clauses, auxvars, enclits = [], [], []

            # encoding the clauses
            for cl in self.clauses:
                auxv = cl[0]
                if len(cl) > 1:
                    auxv = Formula._vpool[Formula._context].id()

                    # direct implication
                    for l in cl:
                        clauses.append([-l, auxv])

                    # opposite implication
                    clauses.append(cl + [-auxv])

                    # keeping all Tseitin variables
                    auxvars.append(auxv)

                # literals representing the clauses
                enclits.append(auxv)

            # encoding the conjunction
            if len(enclits) > 1:
                self.name = Formula._vpool[Formula._context].id(self)

                for lit in enclits:
                    clauses.append([-self.name, lit])
                clauses.append([self.name] + [-lit for lit in enclits])
            else:  # single clause - nothing left to encode
                self.name = enclits[0]  # existing variable

                # connecting it to the CNF object as its name
                Formula._vpool[Formula._context].obj2id[self] = self.name
                Formula._vpool[Formula._context].id2obj[self.name] = self

                # just in case, marking all ids below self.name as occupied
                Formula._vpool[Formula._context].occupy(1, self.name)

            self.encoded = clauses
            self.auxvars = auxvars
            self.enclits = enclits
            self.nv = self.name

    def _atoms(self, dest):
        """
            The base case of recursive atom collection. Extends the collection
            with all the variables in the CNF formula.

            :param dest: the set of atoms to collect
            :type dest: set(:class:`Atom`)
        """

        dest |= set(range(1, self.nv + 1))

    def _iter(self, seen, outermost=False):
        """
            This is a copy of :meth:`__iter__`, to be consistent with
            :class:`Formula`.
        """

        if not self in seen:
            seen[self] = True

            if outermost:
                yield from self.clauses
            else:
                yield from self.encoded

    def simplified(self, assumptions=[]):
        """
            As any other Formula type, CNF formulas have this method, although
            intentionally left unimplemented. Raises a ``FormulaError``
            exception.
        """

        raise FormulaError('Cannot simplify a CNF formula')


#
#==============================================================================
class WCNF(object):
    """
        Class for manipulating partial (weighted) CNF formulas. It can be used
        for creating formulas, reading them from a file, or writing them to a
        file. The ``comment_lead`` parameter can be helpful when one needs to
        parse specific comment lines starting not with character ``c`` but with
        another character or a string.

        :param from_file: a DIMACS CNF filename to read from
        :param from_fp: a file pointer to read from
        :param from_string: a string storing a CNF formula
        :param comment_lead: a list of characters leading comment lines

        :type from_file: str
        :type from_fp: file_pointer
        :type from_string: str
        :type comment_lead: list(str)
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None,
            comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.hard = []
        self.soft = []
        self.wght = []
        self.topw = 1
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead, compressed_with='use_ext')
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        s = self.to_dimacs().replace('\n', '\\n')
        return f'WCNF(from_string=\'{s}\')'

    def from_file(self, fname, comment_lead=['c'], compressed_with='use_ext'):
        """
            Read a WCNF formula from a file in the DIMACS format. A file name
            is expected as an argument. A default argument is ``comment_lead``
            for parsing comment lines. A given file can be compressed by either
            gzip, bzip2, lzma, or zstd.

            :param fname: name of a file to parse.
            :param comment_lead: a list of characters leading comment lines
            :param compressed_with: file compression algorithm

            :type fname: str
            :type comment_lead: list(str)
            :type compressed_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``,
            ``'zstd'``, or ``'use_ext'``. The latter value indicates that
            compression type should be automatically determined based on the
            file extension. Using ``'lzma'`` in Python 2 requires the
            ``backports.lzma`` package to be additionally installed. Using
            ``'zstd'`` requires Python 3.14.

            Usage example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf1 = WCNF()
                >>> cnf1.from_file('some-file.wcnf.bz2', compressed_with='bzip2')
                >>>
                >>> cnf2 = WCNF(from_file='another-file.wcnf')
        """

        with FileObject(fname, mode='r', compression=compressed_with) as fobj:
            self.from_fp(fobj.fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read a WCNF formula from a file pointer. A file pointer should be
            specified as an argument. The only default argument is
            ``comment_lead``, which can be used for parsing specific comment
            lines.

            :param file_pointer: a file pointer to read the formula from.
            :param comment_lead: a list of characters leading comment lines

            :type file_pointer: file pointer
            :type comment_lead: list(str)

            Usage example:

            .. code-block:: python

                >>> with open('some-file.cnf', 'r') as fp:
                ...     cnf1 = WCNF()
                ...     cnf1.from_fp(fp)
                >>>
                >>> with open('another-file.cnf', 'r') as fp:
                ...     cnf2 = WCNF(from_fp=fp)
        """

        def parse_wght(string):
            wght = float(string)
            return int(wght) if wght.is_integer() else decimal.Decimal(string)

        self.nv = 0
        self.hard = []
        self.soft = []
        self.wght = []
        self.topw = 1
        self.comments = []
        comment_lead = set(['p']).union(set(comment_lead))

        # soft clauses with negative weights
        negs = []

        for line in file_pointer:
            line = line.rstrip()
            if line:
                if line[0] not in comment_lead:
                    w, items = line.split(sep=None, maxsplit=1)
                    w = parse_wght(w)

                    if w >= self.topw:
                        self.hard.append(list(map(int, items.split()[:-1])))
                    elif w > 0:
                        self.soft.append(list(map(int, items.split()[:-1])))
                        self.wght.append(w)
                    else:
                        # this clause has a negative weight
                        # it will be processed later
                        negs.append(tuple([list(map(int, items.split()[:-1])), -w]))
                elif not line.startswith('p wcnf '):
                    self.comments.append(line)
                else: # expecting the preamble
                    preamble = line.split(' ')
                    if len(preamble) == 5: # preamble should be "p wcnf nvars nclauses topw"
                        self.topw = parse_wght(preamble[-1])
                    else: # preamble should be "p wcnf nvars nclauses", with topw omitted
                        self.topw = decimal.Decimal('+inf')

        self.nv = max(map(lambda cl: max(map(abs, cl)), itertools.chain.from_iterable([[[self.nv]], self.hard, self.soft])))

        # if there is any soft clause with negative weight
        # normalize it, i.e. transform into a set of clauses
        # with a positive weight
        if negs:
            self.normalize_negatives(negs)

        # if topw was unspecified and assigned to +infinity,
        # we will assign it to the sum of all soft clause weights plus one
        if type(self.topw) == decimal.Decimal and self.topw.is_infinite():
            self.topw = 1 + sum(self.wght)

    def normalize_negatives(self, negatives):
        """
            Iterate over all soft clauses with negative weights and add their
            negation either as a hard clause or a soft one.

            :param negatives: soft clauses with their negative weights.
            :type negatives: list(list(int))
        """

        for cl, w in negatives:
            selv = cl[0]

            # tseitin-encoding the clause if it is not unit-size
            if len(cl) > 1:
                self.nv += 1
                selv = self.nv

                for l in cl:
                    self.hard.append([selv, -l])
                self.hard.append([-selv] + cl)

            # adding the negation of the clause either as hard or soft
            if w >= self.topw:
                self.hard.append([-selv])
            else:
                self.soft.append([-selv])
                self.wght.append(w)

    def from_string(self, string, comment_lead=['c']):
        """
            Read a WCNF formula from a string. The string should be specified
            as an argument and should be in the DIMACS CNF format. The only
            default argument is ``comment_lead``, which can be used for parsing
            specific comment lines.

            :param string: a string containing the formula in DIMACS.
            :param comment_lead: a list of characters leading comment lines

            :type string: str
            :type comment_lead: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf1 = WCNF()
                >>> cnf1.from_string('p wcnf 2 2 2\\n 2 -1 2 0\\n1 1 -2 0')
                >>> print(cnf1.hard)
                [[-1, 2]]
                >>> print(cnf1.soft)
                [[1, 2]]
                >>>
                >>> cnf2 = WCNF(from_string='p wcnf 3 3 2\\n2 -1 2 0\\n2 -2 3 0\\n1 -3 0\\n')
                >>> print(cnf2.hard)
                [[-1, 2], [-2, 3]]
                >>> print(cnf2.soft)
                [[-3]]
                >>> print(cnf2.nv)
                3
        """

        self.from_fp(StringIO(string), comment_lead)

    def copy(self):
        """
            This method can be used for creating a copy of a WCNF object. It
            creates another object of the :class:`WCNF` class and makes use of
            the *deepcopy* functionality to copy both hard and soft clauses.

            :return: an object of class :class:`WCNF`.

            Example:

            .. code-block:: python

                >>> cnf1 = WCNF()
                >>> cnf1.append([-1, 2])
                >>> cnf1.append([1], weight=10)
                >>>
                >>> cnf2 = cnf1.copy()
                >>> print(cnf2.hard)
                [[-1, 2]]
                >>> print(cnf2.soft)
                [[1]]
                >>> print(cnf2.wght)
                [10]
                >>> print(cnf2.nv)
                2
        """

        wcnf = WCNF()
        wcnf.nv = self.nv
        wcnf.topw = self.topw
        wcnf.hard = copy.deepcopy(self.hard)
        wcnf.soft = copy.deepcopy(self.soft)
        wcnf.wght = copy.deepcopy(self.wght)
        wcnf.comments = copy.deepcopy(self.comments)

        return wcnf

    def to_file(self, fname, comments=None, compress_with='use_ext'):
        """
            The method is for saving a WCNF formula into a file in the DIMACS
            CNF format. A file name is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter. Also, a file can be compressed using either gzip, bzip2,
            lzma (xz), or zstd.

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.
            :param compress_with: file compression algorithm

            :type fname: str
            :type comments: list(str)
            :type compress_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``,
            ``'zstd'``, or ``'use_ext'``. The latter value indicates that
            compression type should be automatically determined based on the
            file extension. Using ``'lzma'`` in Python 2 requires the
            ``backports.lzma`` package to be additionally installed. Using
            ``'zstd'`` requires Python 3.14.

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> wcnf = WCNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> wcnf.to_file('some-file-name.wcnf')  # writing to a file
        """

        with FileObject(fname, mode='w', compression=compress_with) as fobj:
            self.to_fp(fobj.fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a WCNF formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> wcnf = WCNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.wcnf', 'w') as fp:
                ...     wcnf.to_fp(fp)  # writing to the file pointer
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        print('p wcnf', self.nv, len(self.hard) + len(self.soft), self.topw, file=file_pointer)

        # soft clauses are dumped first because
        # some tools (e.g. LBX) cannot count them properly
        for i, cl in enumerate(self.soft):
            print(self.wght[i], ' '.join(str(l) for l in cl), '0', file=file_pointer)

        for cl in self.hard:
            print(self.topw, ' '.join(str(l) for l in cl), '0', file=file_pointer)

    def to_dimacs(self):
        """
            Return the current state of the object in extended DIMACS format.

            For example, if 'some-file.cnf' contains:

            ::

                c Example
                p wcnf 2 3 10
                1 -1 0
                2 -2 0
                10 1 2 0

            Then you can obtain the DIMACS with:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf = WCNF(from_file='some-file.cnf')
                >>> print(cnf.to_dimacs())
                c Example
                p wcnf 2 3 10
                10 1 2 0
                1 -1 0
                2 -2 0
        """

        header_lines = [f'p wcnf {self.nv} {len(self.hard) + len(self.soft)} {self.topw}']
        comment_lines = [f'{comment}' for comment in self.comments]
        hard_lines = [f'{self.topw} ' + ' '.join(map(str, clause)) + ' 0' for clause in self.hard]
        soft_lines = [f'{weight} ' + ' '.join(map(str, clause)) + ' 0' for clause, weight in zip(self.soft, self.wght)]

        lines = '\n'.join(comment_lines + header_lines + hard_lines + soft_lines)
        return lines

    def to_alien(self, file_pointer, format='opb', comments=None):
        """
            The method can be used to dump a WCNF formula into a file pointer
            in an alien file format, which at this point can either be LP,
            OPB, or SMT. The file pointer is expected as an argument.
            Additionally, the target format 'lp', 'opb', or 'smt' may be
            specified (equal to 'opb' by default). Finally, supplementary
            comment lines can be specified in the ``comments`` parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param format: alien file format to use
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type format: str
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf = WCNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.lp', 'w') as fp:
                ...     cnf.to_alien(fp, format='lp')  # writing to the file pointer
        """

        cchars = {'lp': '\\', 'opb': '*', 'smt': ';'}

        # saving formula's internal comments
        for c in self.comments:
            print(cchars[format], c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(cchars[format], c, file=file_pointer)

        # normalized soft clauses
        soft, hard = [], []
        topv = self.nv + 1
        for cl in self.soft:
            if len(cl) == 1:
                soft.append(cl)
            else:
                hard.append([topv] + cl)
                soft.append([topv])
                topv += 1

        if format == 'opb':
            print('* #variable= {0} #constraint= {1}'.format(self.nv, len(self.hard) + len(hard)),
                    file=file_pointer)
            print('min:',
                    ' '.join(['{0}{1} x{2}'.format('-' if s[0] > 0 else '+', w, abs(s[0])) for s, w in zip(soft, self.wght)]),
                    ';', file=file_pointer)
        elif format == 'lp':
            print('Minimize', file=file_pointer)
            print('obj:',
                    ' '.join(['{0}{1} x{2}'.format('-' if s[0] > 0 else '+', w, abs(s[0])) for s, w in zip(soft, self.wght)]),
                    file=file_pointer)
            print('Subject To', file=file_pointer)
        elif format == 'smt':
            for v in range(1, self.nv + 1):
                print('(declare-fun x{0} () Bool)'.format(v), file=file_pointer)

        for i, cl in enumerate(self.hard + hard, 1):
            line, neg = [], 0
            for l in cl:
                if l > 0:
                    if format == 'smt':
                        line.append('x{0}'.format(l))
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', l))
                else:
                    if format == 'smt':
                        line.append('(not x{0})'.format(-l))
                    else:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', -l))
                        neg += 1

            if format == 'smt':
                print('(assert (or {0}))'.format(' '.join(line)), file=file_pointer)
            else:
                print('{0}{1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}: '.format(i),
                        ' '.join(l for l in line),
                        1 - neg, ';' if format == 'opb' else ''),
                        file=file_pointer)

        if format == 'lp':
            print('Bounds', file=file_pointer)
            for v in range(1, topv):
                print('0 <= x{0} <= 1'.format(v), file=file_pointer)
            print('Binary', file=file_pointer)
            for v in range(1, topv):
                print('x{0}'.format(v), file=file_pointer)
            print('End', file=file_pointer)
        elif format == 'smt':
            for cl, w in zip(soft, self.wght):
                l = 'x{0}'.format(cl[0]) if cl[0] > 0 else '(not x{0})'.format(-cl[0])
                print('(assert-soft {0} :weight {1})'.format(l, w), file=file_pointer)

            print('(check-sat)', file=file_pointer)
            print('(get-model)', file=file_pointer)
            print('(get-objectives)', file=file_pointer)
            print('(exit)', file=file_pointer)

    def append(self, clause, weight=None):
        """
            Add one more clause to WCNF formula. This method additionally
            updates the number of variables, i.e. variable ``self.nv``, used in
            the formula.

            The clause can be hard or soft depending on the ``weight``
            argument. If no weight is set, the clause is considered to be hard.

            :param clause: a new clause to add.
            :param weight: integer weight of the clause.

            :type clause: list(int)
            :type weight: integer or None

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf = WCNF()
                >>> cnf.append([-1, 2])
                >>> cnf.append([1], weight=10)
                >>> cnf.append([-2], weight=20)
                >>> print(cnf.hard)
                [[-1, 2]]
                >>> print(cnf.soft)
                [[1], [-2]]
                >>> print(cnf.wght)
                [10, 20]
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])

        if weight:
            self.soft.append(list(clause))
            self.wght.append(weight)

            self.topw += weight
        else:
            self.hard.append(list(clause))

    def extend(self, clauses, weights=None):
        """
            Add several clauses to WCNF formula. The clauses should be given in
            the form of list. For every clause in the list, method
            :meth:`append` is invoked.

            The clauses can be hard or soft depending on the ``weights``
            argument. If no weights are set, the clauses are considered to be
            hard.

            :param clauses: a list of new clauses to add.
            :param weights: a list of integer weights.

            :type clauses: list(list(int))
            :type weights: list(int)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> cnf = WCNF()
                >>> cnf.extend([[-3, 4], [5, 6]])
                >>> cnf.extend([[3], [-4], [-5], [-6]], weights=[1, 5, 3, 4])
                >>> print(cnf.hard)
                [[-3, 4], [5, 6]]
                >>> print(cnf.soft)
                [[3], [-4], [-5], [-6]]
                >>> print(cnf.wght)
                [1, 5, 3, 4]
        """

        if weights:
            # clauses are soft
            for i, cl in enumerate(clauses):
                self.append(cl, weight=weights[i])
        else:
            # clauses are hard
            for cl in clauses:
                self.append(cl)

    def unweighted(self):
        """
            This method creates a *plain* (unweighted) copy of the internal
            formula. As a result, an object of class :class:`CNF` is returned.
            Every clause (both hard or soft) of the WCNF formula is copied to
            the ``clauses`` variable of the resulting plain formula, i.e. all
            weights are discarded.

            :return: an object of class :class:`CNF`.

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> wcnf = WCNF()
                >>> wcnf.extend([[-3, 4], [5, 6]])
                >>> wcnf.extend([[3], [-4], [-5], [-6]], weights=[1, 5, 3, 4])
                >>>
                >>> cnf = wcnf.unweighted()
                >>> print(cnf.clauses)
                [[-3, 4], [5, 6], [3], [-4], [-5], [-6]]
        """

        cnf = CNF()

        cnf.nv = self.nv
        cnf.clauses = copy.deepcopy(self.hard) + copy.deepcopy(self.soft)
        cnf.comments = self.comments[:]

        return cnf


#
#==============================================================================
class CNFPlus(CNF, object):
    """
        CNF formulas augmented with *native* cardinality constraints.

        This class inherits most of the functionality of the :class:`CNF`
        class. The only difference between the two is that :class:`CNFPlus`
        supports *native* cardinality constraints of `MiniCard
        <https://github.com/liffiton/minicard>`__.

        The parser of input DIMACS files of :class:`CNFPlus` assumes the
        syntax of AtMostK and AtLeastK constraints defined in the `description
        <https://github.com/liffiton/minicard>`__ of MiniCard:

        ::

            c Example: Two cardinality constraints followed by a clause
            p cnf+ 7 3
            1 -2 3 5 -7 <= 3
            4 5 6 -7 >= 2
            3 5 7 0

        Additionally, :class:`CNFPlus` support pseudo-Boolean constraints,
        i.e. weighted linear constraints by extending the above format.
        Basically, a pseudo-Boolean constraint needs to specify all the
        summands as ``weight*literal`` with the entire constraint being
        prepended with character ``w`` as follows:

        ::

            c Example: One cardinality constraint and one PB constraint followed by a clause
            p cnf+ 7 3
            1 -2 3 5 -7 <= 3
            w 1*4 2*5 1*6 3*-7 >= 2
            3 5 7 0

        Each AtLeastK constraint is translated into an AtMostK constraint in
        the standard way: :math:`\\sum_{i=1}^{n}{x_i}\\geq k \\leftrightarrow
        \\sum_{i=1}^{n}{\\neg{x_i}}\\leq (n-k)`. Internally, AtMostK
        constraints are stored in variable ``atmosts``, each being a pair
        ``(lits, k)``, where ``lits`` is a list of literals in the sum and
        ``k`` is the upper bound.

        Example:

        .. code-block:: python

            >>> from pysat.formula import CNFPlus
            >>> cnf = CNFPlus(from_string='p cnf+ 7 3\\n1 -2 3 5 -7 <= 3\\n4 5 6 -7 >= 2\\n 3 5 7 0\\n')
            >>> print(cnf.clauses)
            [[3, 5, 7]]
            >>> print(cnf.atmosts)
            [[[1, -2, 3, 5, -7], 3], [[-4, -5, -6, 7], 2]]
            >>> print(cnf.nv)
            7

        For details on the functionality, see :class:`CNF`.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None,
            comment_lead=['c']):
        """
            Constructor.
        """

        # atmost constraints are initially empty
        self.atmosts = []

        # calling the base class constructor
        super(CNFPlus, self).__init__(from_file=from_file, from_fp=from_fp,
                from_string=from_string, comment_lead=comment_lead)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        s = self.to_dimacs().replace('\n', '\\n')
        return f'CNFPlus(from_string=\'{s}\')'

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read a CNF+ formula from a file pointer. A file pointer should be
            specified as an argument. The only default argument is
            ``comment_lead``, which can be used for parsing specific comment
            lines.

            :param file_pointer: a file pointer to read the formula from.
            :param comment_lead: a list of characters leading comment lines

            :type file_pointer: file pointer
            :type comment_lead: list(str)

            Usage example:

            .. code-block:: python

                >>> with open('some-file.cnf+', 'r') as fp:
                ...     cnf1 = CNFPlus()
                ...     cnf1.from_fp(fp)
                >>>
                >>> with open('another-file.cnf+', 'r') as fp:
                ...     cnf2 = CNFPlus(from_fp=fp)
        """

        self.nv = 0
        self.clauses = []
        self.atmosts = []
        self.comments = []
        comment_lead = set(['p']).union(set(comment_lead))

        for line in file_pointer:
            line = line.rstrip()
            if line:
                if line[0] not in comment_lead:
                    if line.endswith(' 0'):  # normal case
                        self.clauses.append(list(map(int, line.split()[:-1])))
                    else:  # atmost/atleast constraint
                        items = line.split()

                        if items[0] == 'w':  # literals are weighted here
                            wght, lits = list(map(list, zip(*[map(int, pair.split('*')) for pair in items[1:-2]])))
                            sumw = sum(wght)
                        else:
                            lits = [int(l) for l in items[:-2]]
                            sumw = len(lits)

                        rhs = int(items[-1])
                        self.nv = max([abs(l) for l in lits] + [self.nv])

                        if items[-2][0] == '>':
                            lits = list(map(lambda l: -l, lits))
                            rhs = sumw - rhs

                        self.atmosts.append([lits, rhs, wght] if items[0] == 'w' else [lits, rhs])

                elif not line.startswith('p cnf'):  # cnf is allowed here
                    self.comments.append(line)

        self.nv = max(map(lambda cl: max(map(abs, cl)), itertools.chain.from_iterable([[[self.nv]], self.clauses])))

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a CNF+ formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf = CNFPlus()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.cnf+', 'w') as fp:
                ...     cnf.to_fp(fp)  # writing to the file pointer
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        ftype = 'cnf+' if self.atmosts else 'cnf'
        print('p', ftype, self.nv, len(self.clauses) + len(self.atmosts),
                file=file_pointer)

        for cl in self.clauses:
            print(' '.join(str(l) for l in cl), '0', file=file_pointer)

        for am in self.atmosts:
            if len(am) == 2:  # cardinality constraint
                print(' '.join(str(l) for l in am[0]), '<=', am[1], file=file_pointer)
            else:  # len(am) == 3 => PB constraint
                assert len(am[0]) == len(am[2]), 'Number of literals should be equal to the number of weights'
                print('w', ' '.join('{0}*{1}'.format(str(w), str(l)) for w, l in zip(am[2], am[0])), '<=', am[1], file=file_pointer)

    def to_dimacs(self):
        """
            Return the current state of the object in extended DIMACS format.

            For example, if 'some-file.cnf' contains:

            ::

                c Example
                p cnf+ 7 3
                1 -2 3 5 -7 <= 3
                4 5 6 -7 >= 2
                3 5 7 0

            Then you can obtain the DIMACS with:

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf = CNFPlus(from_file='some-file.cnf')
                >>> print(cnf.to_dimacs())
                c Example
                p cnf+ 7 3
                3 5 7 0
                1 -2 3 5 -7 <= 3
                -4 -5 -6 7 <= 2
        """

        header_lines = [f'p cnf+ {self.nv} {len(self.clauses) + len(self.atmosts)}']
        comment_lines = [f'{comment}' for comment in self.comments]
        clause_lines = [' '.join(map(str, clause)) + ' 0' for clause in self.clauses]

        atmost_lines = []
        for am in self.atmosts:
            if len(am) == 2:  # cardinality constraint
                atmost_lines.append(' '.join(str(l) for l in am[0]) + ' <= ' + str(am[1]))
            else:  # len(am) == 3 => PB constraint
                assert len(am[0]) == len(am[2]), 'Number of literals should be equal to the number of weights'
                atmost_lines.append('w ' + ' '.join('{0}*{1}'.format(str(w), str(l)) for w, l in zip(am[2], am[0])) + ' <= ' + str(am[1]))

        lines = '\n'.join(comment_lines + header_lines + clause_lines + atmost_lines)
        return lines

    def to_alien(self, file_pointer, format='opb', comments=None):
        """
            The method can be used to dump a CNF+ formula into a file pointer
            in an alien file format, which at this point can either be LP,
            OPB, or SMT. The file pointer is expected as an argument.
            Additionally, the target format 'lp', 'opb', or 'smt' may be
            specified (equal to 'opb' by default). Finally, supplementary
            comment lines can be specified in the ``comments`` parameter.

            .. note::

                `SMT-LIB2 <http://smtlib.cs.uiowa.edu/language.shtml>`__ does
                not directly support PB constraints. As a result, native
                cardinality constraints of CNF+ cannot be translated to
                SMT-LIB2 unless an explicit cardinality encoding is applied.
                You may want to use Z3's API instead (see its PB interface).

            :param file_pointer: a file pointer where to store the formula.
            :param format: alien file format to use
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type format: str
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf = CNFPlus()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.lp', 'w') as fp:
                ...     cnf.to_alien(fp, format='lp')  # writing to the file pointer
        """

        if self.atmosts and format == 'smt':
            raise NotImplementedError('SMT-LIB2 does not support PB constraints directly; you may want to use Z3\'s API instead')

        cchars = {'lp': '\\', 'opb': '*', 'smt': ';'}

        # saving formula's internal comments
        for c in self.comments:
            print(cchars[format], c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(cchars[format], c, file=file_pointer)

        if format == 'opb':
            print('* #variable= {0} #constraint= {1}'.format(self.nv, len(self.clauses)),
                    file=file_pointer)
        elif format == 'lp':
            print('Minimize', file=file_pointer)
            print('obj:', file=file_pointer)
            print('Subject To', file=file_pointer)
        elif format == 'smt':
            for v in range(1, self.nv + 1):
                print('(declare-fun x{0} () Bool)'.format(v), file=file_pointer)

        for i, cl in enumerate(self.clauses, 1):
            line, neg = [], 0
            for l in cl:
                if l > 0:
                    if format == 'smt':
                        line.append('x{0}'.format(l))
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', l))
                else:
                    if format == 'smt':
                        line.append('(not x{0})'.format(-l))
                    else:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', -l))
                        neg += 1

            if format == 'smt':
                print('(assert (or {0}))'.format(' '.join(line)), file=file_pointer)
            else:
                print('{0} {1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}:'.format(i),
                        ' '.join(l for l in line),
                        1 - neg, ';' if format == 'opb' else ''),
                        file=file_pointer)

        for i, am in enumerate(self.atmosts, len(self.clauses) + 1):
            line, neg = [], 0

            if len(am) == 2:
                for l in am[0]:
                    if l > 0:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', l))
                        neg += 1
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', -l))
            else:
                for w, l in zip(am[2], am[0]):
                    if l > 0:
                        line.append('-{0} x{1}'.format(w, l))
                        neg += w
                    else:
                        line.append('+{0} x{1}'.format(w, -l))

            print('{0} {1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}:'.format(i),
                    ' '.join(l for l in line),
                    (len(am[0]) if len(am) == 2 else sum(am[2])) - am[1] - neg, ';' if format == 'opb' else ''),
                    file=file_pointer)

        if format == 'lp':
            print('Bounds', file=file_pointer)
            for v in range(1, self.nv + 1):
                print('0 <= x{0} <= 1'.format(v), file=file_pointer)
            print('Binary', file=file_pointer)
            for v in range(1, self.nv + 1):
                print('x{0}'.format(v), file=file_pointer)
            print('End', file=file_pointer)
        elif format == 'smt':
            print('(check-sat)', file=file_pointer)
            print('(exit)', file=file_pointer)

    def append(self, clause, is_atmost=False):
        """
            Add a single clause or a single AtMostK constraint to CNF+ formula.
            This method additionally updates the number of variables, i.e.
            variable ``self.nv``, used in the formula.

            If the clause is an AtMostK constraint, this should be set with the
            use of the additional default argument ``is_atmost``, which is set
            to ``False`` by default.

            :param clause: a new clause to add.
            :param is_atmost: if ``True``, the clause is AtMostK.

            :type clause: list(int)
            :type is_atmost: bool

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf = CNFPlus()
                >>> cnf.append([-3, 4])
                >>> cnf.append([[1, 2, 3], 1], is_atmost=True)
                >>> print(cnf.clauses)
                [[-3, 4]]
                >>> print(cnf.atmosts)
                [[1, 2, 3], 1]
        """

        if not is_atmost:
            self.nv = max([abs(l) for l in clause] + [self.nv])
            self.clauses.append(list(clause))
        else:
            self.nv = max([abs(l) for l in clause[0]] + [self.nv])
            self.atmosts.append(clause)

    def extend(self, formula):
        """
            Extend the CNF+ formula with more clauses and/or AtMostK
            constraints. The additional clauses and AtMostK constraints to add
            should be given in the form of :class:`CNFPlus`. Alternatively, a
            list of clauses can be added too. For every single clause and
            AtMostK constraint in the input formula, method :meth:`append` is
            invoked.

            :param formula: new constraints to add.
            :type formula: :class:`CNFPlus`

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf1 = CNFPlus()
                >>> cnf1.extend([[-3, 4], [5, 6], [[1, 2, 3], 1]])
                >>> print(cnf1.clauses)
                [[-3, 4], [5, 6]]
                >>> print(cnf1.atmosts)
                [[[1, 2, 3], 1]]
                >>> cnf2 = CNFPlus()
                >>> cnf2.extend(cnf1)
                >>> print(cnf1.clauses)
                [[-3, 4], [5, 6]]
                >>> print(cnf1.atmosts)
                [[[1, 2, 3], 1]]
        """

        for cl in formula:
            if len(cl) != 2 or isinstance(cl[0], int):  # it is a clause
                self.append(cl)
            else:
                self.append(cl, is_atmost=True)

    def __iter__(self):
        """
            Iterator over all clauses and AtMostK constraints of the formula.
        """

        for cl in self.clauses:
            yield cl

        for am in self.atmosts:
            yield am

    def weighted(self):
        """
            This method creates a weighted copy of the internal formula. As a
            result, an object of class :class:`WCNFPlus` is returned. Every
            clause of the CNFPlus formula is *soft* in the new WCNFPlus
            formula and its weight is equal to ``1``. The set of hard clauses
            of the new formula is empty. The set of cardinality constraints
            remains unchanged.

            :return: an object of class :class:`WCNFPlus`.

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNFPlus
                >>> cnf = CNFPlus()
                >>> cnf.append([-1, 2])
                >>> cnf.append([3, 4])
                >>> cnf.append([[1, 2], 1], is_atmost=True)
                >>>
                >>> wcnf = cnf.weighted()
                >>> print(wcnf.hard)
                []
                >>> print(wcnf.soft)
                [[-1, 2], [3, 4]]
                >>> print(wcnf.wght)
                [1, 1]
                >>> print(wcnf.atms)
                [[[1, 2], 1]]
        """

        wcnf = WCNFPlus()

        wcnf.nv = self.nv
        wcnf.hard = []
        wcnf.soft = copy.deepcopy(self.clauses)
        wcnf.atms = copy.deepcopy(self.atmosts)
        wcnf.wght = [1 for cl in wcnf.soft]
        wcnf.topw = len(wcnf.wght) + 1
        wcnf.comments = self.comments[:]

        return wcnf

    def copy(self):
        """
            This method can be used for creating a copy of a CNFPlus object.
            It creates another object of the :class:`CNFPlus` class, call the
            copy function of CNF class and makes use of the *deepcopy*
            functionality to copy the atmost constraints.

            :return: an object of class :class:`CNFPlus`.

            Example:

            .. code-block:: python

                >>> cnf1 = CNFPlus()
                >>> cnf1.extend([[-1, 2], [1]])
                >>> cnf1.append([[1, 2], 1], is_atmost=True)
                >>> cnf2 = cnf1.copy()
                >>> print(cnf2.clauses)
                [[-1, 2], [1]]
                >>> print(cnf2.nv)
                2
                >>> print(cnf2.atmosts)
                [[[1, 2], 1]]
        """

        cnfplus = super(CNFPlus, self).copy()
        cnfplus.atmosts = copy.deepcopy(self.atmosts)
        cnfplus.__class__ = CNFPlus  # casting it to CNF+

        return cnfplus

    def _clausify(self, name_required=False):
        """
            This method currently only raises an error as there is no support
            of ``atmosts`` in :class:`Formula`. This may potentially be fixed
            in the future.
        """

        raise FormulaError('Integration of CNFPlus and Formula is not yet supported')


#
#==============================================================================
class WCNFPlus(WCNF, object):
    """
        WCNF formulas augmented with *native* cardinality constraints.

        This class inherits most of the functionality of the :class:`WCNF`
        class. The only difference between the two is that :class:`WCNFPlus`
        supports *native* cardinality constraints of `MiniCard
        <https://github.com/liffiton/minicard>`__.

        The parser of input DIMACS files of :class:`WCNFPlus` assumes the
        syntax of AtMostK and AtLeastK constraints following the one defined
        for :class:`CNFPlus` in the `description
        <https://github.com/liffiton/minicard>`__ of MiniCard:

        ::

            c Example: Two (hard) cardinality constraints followed by a soft clause
            p wcnf+ 7 3 10
            10 1 -2 3 5 -7 <= 3
            10 4 5 6 -7 >= 2
            5 3 5 7 0

        Additionally, :class:`WCNFPlus` support pseudo-Boolean constraints,
        i.e. weighted linear constraints by extending the above format.
        Basically, a pseudo-Boolean constraint needs to specify all the
        summands as ``weight*literal`` with the entire constraint being
        prepended with character ``w`` as follows:

        ::

            c Example: One cardinality constraint and one PB constraint followed by a soft clause
            p wcnf+ 7 3 10
            10 1 -2 3 5 -7 <= 3
            10 w 1*4 2*5 1*6 3*-7 >= 2
            5 3 5 7 0

        **Note** that every cardinality constraint is assumed to be *hard*,
        i.e. soft cardinality constraints are currently *not supported*.

        Each AtLeastK constraint is translated into an AtMostK constraint in
        the standard way: :math:`\\sum_{i=1}^{n}{x_i}\\geq k \\leftrightarrow
        \\sum_{i=1}^{n}{\\neg{x_i}}\\leq (n-k)`. Internally, AtMostK
        constraints are stored in variable ``atms``, each being a pair
        ``(lits, k)``, where ``lits`` is a list of literals in the sum and
        ``k`` is the upper bound.

        Example:

        .. code-block:: python

            >>> from pysat.formula import WCNFPlus
            >>> cnf = WCNFPlus(from_string='p wcnf+ 7 3 10\\n10 1 -2 3 5 -7 <= 3\\n10 4 5 6 -7 >= 2\\n5 3 5 7 0\\n')
            >>> print(cnf.soft)
            [[3, 5, 7]]
            >>> print(cnf.wght)
            [5]
            >>> print(cnf.hard)
            []
            >>> print(cnf.atms)
            [[[1, -2, 3, 5, -7], 3], [[-4, -5, -6, 7], 2]]
            >>> print(cnf.nv)
            7

        For details on the functionality, see :class:`WCNF`.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None, comment_lead=['c']):
        """
            Constructor.
        """

        # atmost constraints are initially empty
        self.atms = []

        # calling the base class constructor
        super(WCNFPlus, self).__init__(from_file=from_file, from_fp=from_fp,
                from_string=from_string, comment_lead=comment_lead)

    def __repr__(self):
        """
            State reproducible string representaion of object.
        """

        s = self.to_dimacs().replace('\n', '\\n')
        return f'WCNFPlus(from_string=\'{s}\')'

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read a WCNF+ formula from a file pointer. A file pointer should be
            specified as an argument. The only default argument is
            ``comment_lead``, which can be used for parsing specific comment
            lines.

            :param file_pointer: a file pointer to read the formula from.
            :param comment_lead: a list of characters leading comment lines

            :type file_pointer: file pointer
            :type comment_lead: list(str)

            Usage example:

            .. code-block:: python

                >>> with open('some-file.wcnf+', 'r') as fp:
                ...     cnf1 = WCNFPlus()
                ...     cnf1.from_fp(fp)
                >>>
                >>> with open('another-file.wcnf+', 'r') as fp:
                ...     cnf2 = WCNFPlus(from_fp=fp)
        """

        def parse_wght(string):
            wght = float(string)
            return int(wght) if wght.is_integer() else decimal.Decimal(string)

        self.nv = 0
        self.hard = []
        self.atms = []
        self.soft = []
        self.wght = []
        self.topw = 1
        self.comments = []
        comment_lead = set(['p']).union(set(comment_lead))

        # soft clauses with negative weights
        negs = []

        for line in file_pointer:
            line = line.rstrip()
            if line:
                if line[0] not in comment_lead:
                    if line.endswith(' 0'):  # normal case
                        w, items = line.split(sep=None, maxsplit=1)
                        w = parse_wght(w)

                        if w >= self.topw:
                            self.hard.append(list(map(int, items.split()[:-1])))
                        elif w > 0:
                            self.soft.append(list(map(int, items.split()[:-1])))
                            self.wght.append(w)
                        else:
                            # this clause has a negative weight
                            # it will be processed later
                            negs.append(tuple([list(map(int, items.split()[:-1])), -w]))
                    else:  # atmost/atleast constraint
                        items = line.split()

                        if items[1] == 'w':  # literals are weighted here
                            wght, lits = list(map(list, zip(*[map(int, pair.split('*')) for pair in items[2:-2]])))
                            sumw = sum(wght)
                        else:
                            lits = [int(l) for l in items[1:-2]]
                            sumw = len(lits)

                        rhs = int(items[-1])
                        self.nv = max([abs(l) for l in lits] + [self.nv])

                        if items[-2][0] == '>':
                            lits = list(map(lambda l: -l, lits))
                            rhs = sumw - rhs

                        self.atms.append([lits, rhs, wght] if items[1] == 'w' else [lits, rhs])

                elif not line.startswith('p wcnf'):  # wcnf is allowed here
                    self.comments.append(line)
                else:  # expecting the preamble
                    preamble = line.split(' ')
                    if len(preamble) == 5: # preamble should be "p wcnf nvars nclauses topw"
                        self.topw = parse_wght(preamble[-1])
                    else: # preamble should be "p wcnf nvars nclauses", with topw omitted
                        self.topw = decimal.Decimal('+inf')

        self.nv = max(map(lambda cl: max(map(abs, cl)), itertools.chain.from_iterable([[[self.nv]], self.hard, self.soft])))

        # if there is any soft clause with negative weight
        # normalize it, i.e. transform into a set of clauses
        # with a positive weight
        if negs:
            self.normalize_negatives(negs)

        # if topw was unspecified and assigned to +infinity,
        # we will assign it to the sum of all soft clause weights plus one
        if type(self.topw) == decimal.Decimal and self.topw.is_infinite():
            self.topw = 1 + sum(self.wght)

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a WCNF+ formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param file_pointer: a file pointer where to store the formula.
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNFPlus
                >>> cnf = WCNFPlus()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.wcnf+', 'w') as fp:
                ...     cnf.to_fp(fp)  # writing to the file pointer
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        ftype = 'wcnf+' if self.atms else 'wcnf'
        print('p', ftype, self.nv, len(self.hard) + len(self.soft) + len(self.atms),
                self.topw, file=file_pointer)

        # soft clauses are dumped first because
        # some tools (e.g. LBX) cannot count them properly
        for i, cl in enumerate(self.soft):
            print(self.wght[i], ' '.join(str(l) for l in cl), '0', file=file_pointer)

        for cl in self.hard:
            print(self.topw, ' '.join(str(l) for l in cl), '0', file=file_pointer)

        # atmost constraints are hard
        for am in self.atms:
            if len(am) == 2:  # cardinality constraint
                print(self.topw, ' '.join(str(l) for l in am[0]), '<=', am[1], file=file_pointer)
            else:  # len(am) == 3 => PB constraint
                assert len(am[0]) == len(am[2]), 'Number of literals should be equal to the number of weights'
                print(self.topw, 'w', ' '.join('{0}*{1}'.format(str(w), str(l)) for w, l in zip(am[2], am[0])), '<=', am[1], file=file_pointer)

    def to_dimacs(self):
        """
            Return the current state of the object in extended DIMACS format.

            For example, if 'some-file.cnf' contains:

            ::

                c Example
                p wcnf+ 7 3 10
                10 1 -2 3 5 -7 <= 3
                10 4 5 6 -7 >= 2
                5 3 5 7 0

            Then you can obtain the DIMACS with:

            .. code-block:: python

                >>> from pysat.formula import WCNFPlus
                >>> cnf = WCNFPlus(from_file='some-file.cnf')
                >>> print(cnf.to_dimacs())
                c Example
                p wcnf+ 7 4 10
                10 -1 3 5 0
                5 3 5 7 0
                10 1 -2 3 5 -7 <= 3
                10 -4 -5 -6 7 <= 2
        """

        header_lines = [f'p wcnf+ {self.nv} {len(self.hard) + len(self.soft) + len(self.atms)} {self.topw}']
        comment_lines = [f'{comment}' for comment in self.comments]
        hard_lines = [f'{self.topw} ' + ' '.join(map(str,clause)) + ' 0' for clause in self.hard]
        soft_lines = [f'{weight} ' + ' '.join(map(str,clause)) + ' 0' for clause, weight in zip(self.soft, self.wght)]

        atmost_lines = []
        for am in self.atms:
            if len(am) == 2:  # cardinality constraint
                atmost_lines.append(f'{self.topw} ' + ' '.join(str(l) for l in am[0]) + ' <= ' + str(am[1]))
            else:  # len(am) == 3 => PB constraint
                assert len(am[0]) == len(am[2]), 'Number of literals should be equal to the number of weights'
                atmost_lines.append(f'{self.topw} ' + 'w ' + ' '.join('{0}*{1}'.format(str(w), str(l)) for w, l in zip(am[2], am[0])) + ' <= ' + str(am[1]))

        lines = '\n'.join(comment_lines + header_lines + hard_lines + soft_lines + atmost_lines) + '\n'

        return lines

    def to_alien(self, file_pointer, format='opb', comments=None):
        """
            The method can be used to dump a WCNF+ formula into a file pointer
            in an alien file format, which at this point can either be LP,
            OPB, or SMT. The file pointer is expected as an argument.
            Additionally, the target format 'lp', 'opb', or 'smt' may be
            specified (equal to 'opb' by default). Finally, supplementary
            comment lines can be specified in the ``comments`` parameter.

            .. note::

                `SMT-LIB2 <http://smtlib.cs.uiowa.edu/language.shtml>`__ does
                not directly support PB constraints. As a result, native
                cardinality constraints of CNF+ cannot be translated to
                SMT-LIB2 unless an explicit cardinality encoding is applied.
                You may want to use Z3's API instead (see its PB interface).

            :param file_pointer: a file pointer where to store the formula.
            :param format: alien file format to use
            :param comments: additional comments to put in the file.

            :type file_pointer: file pointer
            :type format: str
            :type comments: list(str)

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNFPlus
                >>> cnf = WCNFPlus()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> with open('some-file.lp', 'w') as fp:
                ...     cnf.to_alien(fp, format='lp')  # writing to the file pointer
        """

        if self.atms and format == 'smt':
            raise NotImplementedError('SMT-LIB2 does not support PB constraints directly; you may want to use Z3\'s API instead')

        cchars = {'lp': '\\', 'opb': '*', 'smt': ';'}

        # saving formula's internal comments
        for c in self.comments:
            print(cchars[format], c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(cchars[format], c, file=file_pointer)

        # normalized soft clauses
        soft, hard = [], []
        topv = self.nv + 1
        for cl in self.soft:
            if len(cl) == 1:
                soft.append(cl)
            else:
                hard.append([topv] + cl)
                soft.append([topv])
                topv += 1

        if format == 'opb':
            print('* #variable= {0} #constraint= {1}'.format(self.nv, len(self.hard) + len(hard)),
                    file=file_pointer)
            print('min:',
                    ' '.join(['{0}{1} x{2}'.format('-' if s[0] > 0 else '+', w, abs(s[0])) for s, w in zip(soft, self.wght)]),
                    ';', file=file_pointer)
        elif format == 'lp':
            print('Minimize', file=file_pointer)
            print('obj:',
                    ' '.join(['{0}{1} x{2}'.format('-' if s[0] > 0 else '+', w, abs(s[0])) for s, w in zip(soft, self.wght)]),
                    file=file_pointer)
            print('Subject To', file=file_pointer)
        elif format == 'smt':
            for v in range(1, self.nv + 1):
                print('(declare-fun x{0} () Bool)'.format(v), file=file_pointer)

        for i, cl in enumerate(self.hard + hard, 1):
            line, neg = [], 0
            for l in cl:
                if l > 0:
                    if format == 'smt':
                        line.append('x{0}'.format(l))
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', l))
                else:
                    if format == 'smt':
                        line.append('(not x{0})'.format(-l))
                    else:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', -l))
                        neg += 1

            if format == 'smt':
                print('(assert (or {0}))'.format(' '.join(line)), file=file_pointer)
            else:
                print('{0}{1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}: '.format(i),
                        ' '.join(l for l in line),
                        1 - neg, ';' if format == 'opb' else ''),
                        file=file_pointer)

        for i, am in enumerate(self.atms, len(self.hard) + len(hard) + 1):
            line, neg = [], 0

            if len(am) == 2:
                for l in am[0]:
                    if l > 0:
                        line.append('-{0} x{1}'.format('1' if format == 'opb' else '', l))
                        neg += 1
                    else:
                        line.append('+{0} x{1}'.format('1' if format == 'opb' else '', -l))
            else:
                for w, l in zip(am[2], am[0]):
                    if l > 0:
                        line.append('-{0} x{1}'.format(w, l))
                        neg += w
                    else:
                        line.append('+{0} x{1}'.format(w, -l))

            print('{0} {1} >= {2} {3}'.format('' if format == 'opb' else 'c{0}:'.format(i),
                    ' '.join(l for l in line),
                    (len(am[0]) if len(am) == 2 else sum(am[2])) - am[1] - neg, ';' if format == 'opb' else ''),
                    file=file_pointer)

        if format == 'lp':
            print('Bounds', file=file_pointer)
            for v in range(1, topv):
                print('0 <= x{0} <= 1'.format(v), file=file_pointer)
            print('Binary', file=file_pointer)
            for v in range(1, topv):
                print('x{0}'.format(v), file=file_pointer)
            print('End', file=file_pointer)
        elif format == 'smt':
            for cl, w in zip(soft, self.wght):
                l = 'x{0}'.format(cl[0]) if cl[0] > 0 else '(not x{0})'.format(-cl[0])
                print('(assert-soft {0} :weight {1})'.format(l, w), file=file_pointer)

            print('(check-sat)', file=file_pointer)
            print('(get-model)', file=file_pointer)
            print('(get-objectives)', file=file_pointer)
            print('(exit)', file=file_pointer)

    def append(self, clause, weight=None, is_atmost=False):
        """
            Add a single clause or a single AtMostK constraint to WCNF+
            formula. This method additionally updates the number of variables,
            i.e.  variable ``self.nv``, used in the formula.

            If the clause is an AtMostK constraint, this should be set with the
            use of the additional default argument ``is_atmost``, which is set
            to ``False`` by default.

            If ``is_atmost`` is set to ``False``, the clause can be either hard
            or soft depending on the ``weight`` argument. If no weight is
            specified, the clause is considered hard. Otherwise, the clause is
            soft.

            :param clause: a new clause to add.
            :param weight: an integer weight of the clause.
            :param is_atmost: if ``True``, the clause is AtMostK.

            :type clause: list(int)
            :type weight: integer or None
            :type is_atmost: bool

            .. code-block:: python

                >>> from pysat.formula import WCNFPlus
                >>> cnf = WCNFPlus()
                >>> cnf.append([-3, 4])
                >>> cnf.append([[1, 2, 3], 1], is_atmost=True)
                >>> cnf.append([-1, -2], weight=35)
                >>> print(cnf.hard)
                [[-3, 4]]
                >>> print(cnf.atms)
                [[1, 2, 3], 1]
                >>> print(cnf.soft)
                [[-1, -2]]
                >>> print(cnf.wght)
                [35]
        """

        if not is_atmost:
            self.nv = max([abs(l) for l in clause] + [self.nv])

            if weight:
                self.soft.append(list(clause))
                self.wght.append(weight)

                self.topw += weight
            else:
                self.hard.append(list(clause))
        else:
            self.nv = max([abs(l) for l in clause[0]] + [self.nv])
            self.atms.append(clause)

    def unweighted(self):
        """
            This method creates a *plain* (unweighted) copy of the internal
            formula. As a result, an object of class :class:`CNFPlus` is
            returned. Every clause (both hard or soft) of the original
            WCNFPlus formula is copied to the ``clauses`` variable of the
            resulting plain formula, i.e. all weights are discarded.

            Note that the cardinality constraints of the original (weighted)
            formula remain unchanged in the new (plain) formula.

            :return: an object of class :class:`CNFPlus`.

            Example:

            .. code-block:: python

                >>> from pysat.formula import WCNF
                >>> wcnf = WCNFPlus()
                >>> wcnf.extend([[-3, 4], [5, 6]])
                >>> wcnf.extend([[3], [-4], [-5], [-6]], weights=[1, 5, 3, 4])
                >>> wcnf.append([[1, 2, 3], 1], is_atmost=True)
                >>>
                >>> cnf = wcnf.unweighted()
                >>> print(cnf.clauses)
                [[-3, 4], [5, 6], [3], [-4], [-5], [-6]]
                >>> print(cnf.atmosts)
                [[[1, 2, 3], 1]]
        """

        cnf = CNFPlus()

        cnf.nv = self.nv
        cnf.clauses = copy.deepcopy(self.hard) + copy.deepcopy(self.soft)
        cnf.atmosts = copy.deepcopy(self.atms)
        cnf.comments = self.comments[:]

        return cnf

    def copy(self):
        """
            This method can be used for creating a copy of a WCNFPlus object.
            It creates another object of the :class:`WCNFPlus` class, call the
            copy function of WCNF class and makes use of the *deepcopy*
            functionality to copy the atmost constraints.

            :return: an object of class :class:`WCNFPlus`.

            Example:

            .. code-block:: python

                >>> cnf1 = WCNFPlus()
                >>> cnf1.append([-1, 2])
                >>> cnf1.append([1], weight=10)
                >>> cnf1.append([[1, 2], 1], is_atmost=True)
                >>> cnf2 = cnf1.copy()
                >>> print(cnf2.hard)
                [[-1, 2]]
                >>> print(cnf2.soft)
                [[1]]
                >>> print(cnf2.wght)
                [10]
                >>> print(cnf2.nv)
                2
                >> print(cnf2.atms)
                [[[1, 2], 1]]

        """

        wcnfplus = super(WCNFPlus, self).copy()
        wcnfplus.atms = copy.deepcopy(self.atms)
        wcnfplus.__class__ = WCNFPlus  # casting it to WCNF+

        return wcnfplus
