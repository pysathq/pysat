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
        CNF
        CNFPlus
        WCNF
        WCNFPlus

    ==================
    Module description
    ==================

    This module is designed to facilitate fast and easy PySAT-development by
    providing a simple way to manipulate formulas in PySAT. Although only
    clausal formulas are supported at this point, future releases of PySAT are
    expected to implement data structures and methods to manipulate arbitrary
    Boolean formulas. The module implements the :class:`CNF` class, which
    represents a formula in `conjunctive normal form (CNF)
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
    :math:`\mathcal{F}=\mathcal{H}\wedge\mathcal{S}`. Soft clauses of a WCNF
    are labeled with integer *weights*, i.e. a soft clause of
    :math:`\mathcal{S}` is a pair :math:`(c_i, w_i)`. In partial (unweighted)
    formulas, all soft clauses have weight 1.

    WCNF can be of help when solving optimization problems using the SAT
    technology. A typical example of where a WCNF formula can be used is
    `maximum satisfiability (MaxSAT)
    <https://en.wikipedia.org/wiki/Maximum_satisfiability_problem>`__, which
    given a WCNF formula :math:`\mathcal{F}=\mathcal{H}\wedge\mathcal{S}`
    targets satisfying all its hard clauses :math:`\mathcal{H}` and maximizing
    the sum of weights of satisfied soft clauses, i.e. maximizing the value of
    :math:`\sum_{c_i\in\mathcal{S}}{w_i\\cdot c_i}`.

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
    be equal to :math:`1+\sum_{c_i\in\mathcal{S}}{w_i}`. Top weight of a
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

    Additionally to classes :class:`CNF` and :class:`WCNF`, the module provides
    the extended classes :class:`CNFPlus` and :class:`WCNFPlus`. The only
    difference between ``?CNF`` and ``?CNFPlus`` is the support for *native*
    cardinality constraints provided by the `MiniCard solver
    <https://github.com/liffiton/minicard>`__ (see :mod:`pysat.card` for
    details). The corresponding variable in objects of ``CNFPlus``
    (``WCNFPlus``, resp.) responsible for storing the AtMostK constraints is
    ``atmosts`` (``atms``, resp.). **Note** that at this point, AtMostK
    constraints in ``WCNF`` can be *hard* only.

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
import copy
import decimal
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

        :param start_from: the smallest ID to assign.
        :param occupied: a list of occupied intervals.

        :type start_from: int
        :type occupied: list(list(int))
    """

    def __init__(self, start_from=1, occupied=[]):
        """
            Constructor.
        """

        self.restart(start_from=start_from, occupied=occupied)

    def restart(self, start_from=1, occupied=[]):
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

    def id(self, obj):
        """
            The method is to be used to assign an integer variable ID for a
            given new object. If the object already has an ID, no new ID is
            created and the old one is returned instead.

            An object can be anything. In some cases it is convenient to use
            string variable names.

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

        vid = self.obj2id[obj]

        if vid not in self.id2obj:
            self.id2obj[vid] = obj

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
class CNF(object):
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

        :type from_file: str
        :type from_fp: file_pointer
        :type from_string: str
        :type from_clauses: list(list(int))
        :type from_aiger: :class:`aiger.AIG` (see `py-aiger package <https://github.com/mvcisback/py-aiger>`__)
        :type comment_lead: list(str)
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None,
            from_clauses=[], from_aiger=None, comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.clauses = []
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead, compressed_with='use_ext')
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)
        elif from_clauses:
            self.from_clauses(from_clauses)
        elif from_aiger:
            self.from_aiger(from_aiger)

    def from_file(self, fname, comment_lead=['c'], compressed_with='use_ext'):
        """
            Read a CNF formula from a file in the DIMACS format. A file name is
            expected as an argument. A default argument is ``comment_lead`` for
            parsing comment lines. A given file can be compressed by either
            gzip, bzip2, or lzma.

            :param fname: name of a file to parse.
            :param comment_lead: a list of characters leading comment lines
            :param compressed_with: file compression algorithm

            :type fname: str
            :type comment_lead: list(str)
            :type compressed_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``, or
            ``'use_ext'``. The latter value indicates that compression type
            should be automatically determined based on the file extension.
            Using ``'lzma'`` in Python 2 requires the ``backports.lzma``
            package to be additionally installed.

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
        comment_lead = tuple('p') + tuple(comment_lead)

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    cl = [int(l) for l in line.split()[:-1]]
                    self.nv = max([abs(l) for l in cl] + [self.nv])

                    self.clauses.append(cl)
                elif not line.startswith('p cnf '):
                    self.comments.append(line)

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
                >>> cnf1.from_string(='p cnf 2 2\\n-1 2 0\\n1 -2 0')
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

    def from_clauses(self, clauses):
        """
            This methods copies a list of clauses into a CNF object.

            :param clauses: a list of clauses
            :type clauses: list(list(int))

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [1, -2], [5]])
                >>> print(cnf.clauses)
                [[-1, 2], [1, -2], [5]]
                >>> print(cnf.nv)
                5
        """

        self.clauses = copy.deepcopy(clauses)

        for cl in self.clauses:
            self.nv = max([abs(l) for l in cl] + [self.nv])

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
        self.nv = max(map(abs, itertools.chain(*self.clauses)))

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
        cnf.comments = copy.deepcopy(self.comments)

        return cnf

    def to_file(self, fname, comments=None, compress_with='use_ext'):
        """
            The method is for saving a CNF formula into a file in the DIMACS
            CNF format. A file name is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter. Also, a file can be compressed using either gzip, bzip2,
            or lzma (xz).

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.
            :param compress_with: file compression algorithm

            :type fname: str
            :type comments: list(str)
            :type compress_with: str

            Note that the ``compress_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``, or
            ``'use_ext'``. The latter value indicates that compression type
            should be automatically determined based on the file extension.
            Using ``'lzma'`` in Python 2 requires the ``backports.lzma``
            package to be additionally installed.

            Example:

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF()
                ...
                >>> # the formula is filled with a bunch of clauses
                >>> cnf.to_file('some-file-name.cnf')  # writing to a file
        """

        with FileObject(fname, mode='w', compression=compress_with) as fobj:
            self.to_fp(fobj.fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a CNF formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.

            :type fname: str
            :type comments: list(str)

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

        print('p cnf', self.nv, len(self.clauses), file=file_pointer)

        for cl in self.clauses:
            print(' '.join(str(l) for l in cl), '0', file=file_pointer)

    def append(self, clause):
        """
            Add one more clause to CNF formula. This method additionally
            updates the number of variables, i.e. variable ``self.nv``, used in
            the formula.

            :param clause: a new clause to add.
            :type clause: list(int)

            .. code-block:: python

                >>> from pysat.formula import CNF
                >>> cnf = CNF(from_clauses=[[-1, 2], [3]])
                >>> cnf.append([-3, 4])
                >>> print(cnf.clauses)
                [[-1, 2], [3], [-3, 4]]
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])
        self.clauses.append(clause)

    def extend(self, clauses):
        """
            Add several clauses to CNF formula. The clauses should be given in
            the form of list. For every clause in the list, method
            :meth:`append` is invoked.

            :param clauses: a list of new clauses to add.
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
            Given a CNF formula :math:`\mathcal{F}`, this method creates a CNF
            formula :math:`\\neg{\mathcal{F}}`. The negation of the formula is
            encoded to CNF with the use of *auxiliary* Tseitin variables [1]_.
            A new CNF formula is returned keeping all the newly introduced
            variables that can be accessed through the ``auxvars`` variable.

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
                [4, -3]
        """

        negated = CNF()

        negated.nv = topv
        if not negated.nv:
            negated.nv = self.nv

        negated.clauses = []
        negated.auxvars = []

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

        negated.clauses.append(negated.auxvars)
        return negated


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

    def from_file(self, fname, comment_lead=['c'], compressed_with='use_ext'):
        """
            Read a WCNF formula from a file in the DIMACS format. A file name
            is expected as an argument. A default argument is ``comment_lead``
            for parsing comment lines. A given file can be compressed by either
            gzip, bzip2, or lzma.

            :param fname: name of a file to parse.
            :param comment_lead: a list of characters leading comment lines
            :param compressed_with: file compression algorithm

            :type fname: str
            :type comment_lead: list(str)
            :type compressed_with: str

            Note that the ``compressed_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``, or
            ``'use_ext'``. The latter value indicates that compression type
            should be automatically determined based on the file extension.
            Using ``'lzma'`` in Python 2 requires the ``backports.lzma``
            package to be additionally installed.

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
        comment_lead = tuple('p') + tuple(comment_lead)

        # soft clauses with negative weights
        negs = []

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    items = line.split()[:-1]
                    w, cl = parse_wght(items[0]), [int(l) for l in items[1:]]
                    self.nv = max([abs(l) for l in cl] + [self.nv])

                    if w <= 0:
                        # this clause has a negative weight
                        # it will be processed later
                        negs.append(tuple([cl, -w]))
                    elif w >= self.topw:
                        self.hard.append(cl)
                    else:
                        self.soft.append(cl)
                        self.wght.append(w)
                elif not line.startswith('p wcnf '):
                    self.comments.append(line)
                else:  # expecting the preamble
                    self.topw = parse_wght(line.rsplit(' ', 1)[1])

        # if there is any soft clause with negative weight
        # normalize it, i.e. transform into a set of clauses
        # with a positive weight
        if negs:
            self.normalize_negatives(negs)

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
                >>> cnf1.from_string(='p wcnf 2 2 2\\n 2 -1 2 0\\n1 1 -2 0')
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
            or lzma (xz).

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.
            :param compress_with: file compression algorithm

            :type fname: str
            :type comments: list(str)
            :type compress_with: str

            Note that the ``compress_with`` parameter can be ``None`` (i.e.
            the file is uncompressed), ``'gzip'``, ``'bzip2'``, ``'lzma'``, or
            ``'use_ext'``. The latter value indicates that compression type
            should be automatically determined based on the file extension.
            Using ``'lzma'`` in Python 2 requires the ``backports.lzma``
            package to be additionally installed.

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

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.

            :type fname: str
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
            self.soft.append(clause)
            self.wght.append(weight)

            self.topw += weight
        else:
            self.hard.append(clause)

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
        cnf.commends = self.comments[:]

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

        The parser of input DIMACS files of :class:`CNFPlus` assumes the syntax
        of AtMostK and AtLeastK constraints defined in the `description
        <https://github.com/liffiton/minicard>`__ of MiniCard:

        ::

            c Example: Two cardinality constraints followed by a clause
            p cnf+ 7 3
            1 -2 3 5 -7 <= 3
            4 5 6 -7 >= 2
            3 5 7 0

        Each AtLeastK constraint is translated into an AtMostK constraint in
        the standard way: :math:`\sum_{i=1}^{n}{x_i}\geq k \leftrightarrow
        \sum_{i=1}^{n}{\\neg{x_i}}\leq (n-k)`. Internally, AtMostK constraints
        are stored in variable ``atmosts``, each being a pair ``(lits, k)``,
        where ``lits`` is a list of literals in the sum and ``k`` is the upper
        bound.

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
        comment_lead = tuple('p') + tuple(comment_lead)

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    if int(line.rsplit(' ', 1)[-1]) == 0:  # normal clause
                        cl = [int(l) for l in line.split()[:-1]]
                        self.nv = max([abs(l) for l in cl] + [self.nv])

                        self.clauses.append(cl)
                    else:  # atmost/atleast constraint
                        items = [i for i in line.split()]
                        lits = [int(l) for l in items[:-2]]
                        rhs = int(items[-1])
                        self.nv = max([abs(l) for l in lits] + [self.nv])

                        if items[-2][0] == '>':
                            lits = list(map(lambda l: -l, lits))
                            rhs = len(lits) - rhs

                        self.atmosts.append([lits, rhs])
                elif not line.startswith('p cnf'):  # cnf is allowed here
                    self.comments.append(line)

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a CNF+ formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.

            :type fname: str
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
            print(' '.join(str(l) for l in am[0]), '<=', am[1], file=file_pointer)

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
            self.clauses.append(clause)
        else:
            self.nv = max([abs(l) for l in clause[0]] + [self.nv])
            self.atmosts.append(clause)

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

        return cnfplus


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

        **Note** that every cardinality constraint is assumed to be *hard*,
        i.e. soft cardinality constraints are currently *not supported*.

        Each AtLeastK constraint is translated into an AtMostK constraint in
        the standard way: :math:`\sum_{i=1}^{n}{x_i}\geq k \leftrightarrow
        \sum_{i=1}^{n}{\\neg{x_i}}\leq (n-k)`. Internally, AtMostK constraints
        are stored in variable ``atms``, each being a pair ``(lits, k)``, where
        ``lits`` is a list of literals in the sum and ``k`` is the upper bound.

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
        comment_lead = tuple('p') + tuple(comment_lead)

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    if int(line.rsplit(' ', 1)[-1]) == 0:  # normal clause
                        items = line.split()[:-1]
                        w, cl = parse_wght(items[0]), [int(l) for l in items[1:]]
                        self.nv = max([abs(l) for l in cl] + [self.nv])

                        if w <= 0:
                            # this clause has a negative weight
                            # it will be processed later
                            negs.append(tuple([cl, -w]))
                        elif w >= self.topw:
                            self.hard.append(cl)
                        else:
                            self.soft.append(cl)
                            self.wght.append(w)
                    else:  # atmost/atleast constraint
                        items = [i for i in line.split()]
                        lits = [int(l) for l in items[1:-2]]
                        rhs = int(items[-1])
                        self.nv = max([abs(l) for l in lits] + [self.nv])

                        if items[-2][0] == '>':
                            lits = list(map(lambda l: -l, lits))
                            rhs = len(lits) - rhs

                        self.atms.append([lits, rhs])
                elif not line.startswith('p wcnf'):  # wcnf is allowed here
                    self.comments.append(line)
                else:  # expecting the preamble
                    self.topw = parse_wght(line.rsplit(' ', 1)[1])

    def to_fp(self, file_pointer, comments=None):
        """
            The method can be used to save a WCNF+ formula into a file pointer.
            The file pointer is expected as an argument. Additionally,
            supplementary comment lines can be specified in the ``comments``
            parameter.

            :param fname: a file name where to store the formula.
            :param comments: additional comments to put in the file.

            :type fname: str
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
            print(self.topw, ' '.join(str(l) for l in am[0]), '<=', am[1], file=file_pointer)

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
                self.soft.append(clause)
                self.wght.append(weight)

                self.topw += weight
            else:
                self.hard.append(clause)
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
        cnf.commends = self.comments[:]

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

        return wcnfplus
