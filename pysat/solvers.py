#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## solvers.py
##
##  Created on: Nov 27, 2016
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        SolverNames
        Solver
        Glucose3
        Glucose4
        Lingeling
        Minicard
        Minisat22
        MinisatGH

    ==================
    Module description
    ==================

    This module provides *incremental* access to a few modern SAT solvers. The
    solvers supported by PySAT are:

    -  Glucose (`3.0 <http://www.labri.fr/perso/lsimon/glucose/>`__)
    -  Glucose (`4.1 <http://www.labri.fr/perso/lsimon/glucose/>`__)
    -  Lingeling (`bbc-9230380-160707 <http://fmv.jku.at/lingeling/>`__)
    -  Minicard (`1.2 <https://github.com/liffiton/minicard>`__)
    -  Minisat (`2.2 release <http://minisat.se/MiniSat.html>`__)
    -  Minisat (`GitHub version <https://github.com/niklasso/minisat>`__)

    All solvers can be accessed through a unified MiniSat-like [1]_ incremental
    [2]_ interface described below.

    .. [1] Niklas Eén, Niklas Sörensson. *An Extensible SAT-solver*. SAT 2003.
        pp. 502-518

    .. [2] Niklas Eén, Niklas Sörensson. *Temporal induction by incremental SAT
        solving*. Electr. Notes Theor. Comput. Sci. 89(4). 2003. pp. 543-560

    The module provides direct access to all supported solvers using the
    corresponding classes :class:`Glucose3`, :class:`Glucose4`,
    :class:`Lingeling`, :class:`Minicard`, :class:`Minisat22`, and
    :class:`MinisatGH`. However, the solvers can also be accessed through the
    common base class :class:`Solver` using the solver ``name`` argument. For
    example, both of the following pieces of code create a copy of the
    :class:`Glucose3` solver:

    .. code-block:: python

        >>> from pysat.solvers import Glucose3, Solver
        >>>
        >>> g = Glucose3()
        >>> g.delete()
        >>>
        >>> s = Solver(name='g3')
        >>> s.delete()

    The :mod:`pysat.solvers` module is designed to create and manipulate SAT
    solvers as *oracles*, i.e. it does not give access to solvers' internal
    parameters such as variable polarities or activities. PySAT provides a user
    with the following basic SAT solving functionality:

    -  creating and deleting solver objects
    -  adding individual clauses and formulas to solver objects
    -  making SAT calls with or without assumptions
    -  propagating a given set of assumption literals
    -  setting preferred polarities for a (sub)set of variables
    -  extracting a model of a satisfiable input formula
    -  enumerating models of an input formula
    -  extracting an unsatisfiable core of an unsatisfiable formula
    -  extracting a `DRUP proof <http://www.cs.utexas.edu/~marijn/drup/>`__ logged by the solver

    PySAT supports both non-incremental and incremental SAT solving.
    Incrementality can be achieved with the use of the MiniSat-like
    *assumption-based* interface [2]_. It can be helpful if multiple calls to a
    SAT solver are needed for the same formula using different sets of
    "assumptions", e.g. when doing consecutive SAT calls for formula
    :math:`\mathcal{F}\land (a_{i_1}\land\ldots\land a_{i_1+j_1})` and
    :math:`\mathcal{F}\land (a_{i_2}\land\ldots\land a_{i_2+j_2})`, where every
    :math:`a_{l_k}` is an assumption literal.

    There are several advantages of using assumptions: (1) it enables one to
    *keep and reuse* the clauses learnt during previous SAT calls at a later
    stage and (2) assumptions can be easily used to extract an *unsatisfiable
    core* of the formula. A drawback of assumption-based SAT solving is that
    the clauses learnt are longer (they typically contain many assumption
    literals), which makes the SAT calls harder.

    In PySAT, assumptions should be provided as a list of literals given to the
    ``solve()`` method:

    .. code-block:: python

        >>> from pysat.solvers import Solver
        >>> s = Solver()
        >>>
        ... # assume that solver s is fed with a formula
        >>>
        >>> s.solve()  # a simple SAT call
        True
        >>>
        >>> s.solve(assumptions=[1, -2, 3])  # a SAT call with assumption literals
        False
        >>> s.get_core()  # extracting an unsatisfiable core
        [3, 1]

    In order to shorten the description of the module, the classes providing
    direct access to the individual solvers, i.e. classes :class:`Glucose3`,
    :class:`Glucose4`, :class:`Lingeling`, :class:`Minicard`,
    :class:`Minisat22`, and :class:`MinisatGH`, are **omitted**. They replicate
    the interface of the base class :class:`Solver` and, thus, can be used the
    same exact way.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
import pysolvers
import signal
import tempfile
import time


#
#==============================================================================
class NoSuchSolverError(Exception):
    """
        This exception is raised when creating a new SAT solver whose name does
        not match any name in :class:`SolverNames`. The list of *known* solvers
        includes the names `'glucose3'`, `'glucose4'`, `'lingeling'`,
        `'minicard'`, `'minisat22'`, and `'minisatgh'`.
    """

    pass


#
#==============================================================================
class SolverNames(object):
    """
        This class serves to determine the solver requested by a user given a
        string name. This allows for using several possible names for
        specifying a solver.

        .. code-block:: python

            glucose3  = ('g3', 'g30', 'glucose3', 'glucose30')
            glucose4  = ('g4', 'g41', 'glucose4', 'glucose41')
            lingeling = ('lgl', 'lingeling')
            minicard  = ('mc', 'mcard', 'minicard')
            minisat22 = ('m22', 'msat22', 'minisat22')
            minisatgh = ('mgh', 'msat-gh', 'minisat-gh')

        As a result, in order to select Glucose3, a user can specify the
        solver's name: either ``'g3'``, ``'g30'``, ``'glucose3'``, or
        ``'glucose30'``. *Note that the capitalized versions of these names are
        also allowed*.
    """

    glucose3  = ('g3', 'g30', 'glucose3', 'glucose30')
    glucose4  = ('g4', 'g41', 'glucose4', 'glucose41')
    lingeling = ('lgl', 'lingeling')
    minicard  = ('mc', 'mcard', 'minicard')
    minisat22 = ('m22', 'msat22', 'minisat22')
    minisatgh = ('mgh', 'msat-gh', 'minisat-gh')


#
#==============================================================================
class Solver(object):
    """
        Main class for creating and manipulating a SAT solver. Any available
        SAT solver can be accessed as an object of this class and so
        :class:`Solver` can be seen as a wrapper for all supported solvers.

        The constructor of :class:`Solver` has only one mandatory argument
        ``name``, while all the others are default. This means that explicit
        solver constructors, e.g. :class:`Glucose3` or :class:`MinisatGH` etc.,
        have only default arguments.

        :param name: solver's name (see :class:`SolverNames`).
        :param bootstrap_with: a list of clauses for solver initialization.
        :param use_timer: whether or not to measure SAT solving time.

        :type name: str
        :type bootstrap_with: iterable(iterable(int))
        :type use_timer: bool

        The ``bootstrap_with`` argument is useful when there is an input CNF
        formula to feed the solver with. The argument expects a list of
        clauses, each clause being a list of literals, i.e. a list of integers.

        If set to ``True``, the ``use_timer`` parameter will force the solver
        to accumulate the time spent by all SAT calls made with this solver but
        also to keep time of the last SAT call.

        Once created and used, a solver must be deleted with the :meth:`delete`
        method. Alternatively, if created using the ``with`` statement,
        deletion is done automatically when the end of the ``with`` block is
        reached.

        Given the above, a couple of examples of solver creation are the
        following:

        .. code-block:: python

            >>> from pysat.solvers import Solver, Minisat22
            >>>
            >>> s = Solver(name='g4')
            >>> s.add_clause([-1, 2])
            >>> s.add_clause([-1, -2])
            >>> s.solve()
            True
            >>> print s.get_model()
            [-1, -2]
            >>> s.delete()
            >>>
            >>> with Minisat22(bootstrap_with=[[-1, 2], [-1, -2]]) as m:
            ...     m.solve()
            True
            ...     print m.get_model()
            [-1, -2]

        Note that while all explicit solver classes necessarily have default
        arguments ``bootstrap_with`` and ``use_timer``, solvers
        :class:`Lingeling`, :class:`Glucose3`, and :class:`Glucose4` can have
        additional default arguments. One such argument supported by
        :class:`Glucose3` and :class:`Glucose4` but also by ``Lingeling`` is
        `DRUP proof <http://www.cs.utexas.edu/~marijn/drup/>`__ logging. This
        can be enabled by setting the ``with_proof`` argument to ``True``
        (``False`` by default):

        .. code-block:: python

            >>> from pysat.solvers import Lingeling
            >>> from pysat.examples.genhard import PHP
            >>>
            >>> cnf = PHP(nof_holes=2)  # pigeonhole principle for 3 pigeons
            >>>
            >>> with Lingeling(bootstrap_with=cnf.clauses, with_proof=True) as l:
            ...     l.solve()
            False
            ...     l.get_proof()
            ['-5 0', '6 0', '-2 0', '-4 0', '1 0', '3 0', '0']

        Additionally and in contrast to :class:`Lingeling`, both
        :class:`Glucose3` and :class:`Glucose4` have one more default argument
        ``incr`` (``False`` by default), which enables incrementality features
        introduced in Glucose3 [3]_. To summarize, the additional arguments of
        Glucose are:

        :param incr: enable the incrementality features of Glucose3 [3]_.
        :param with_proof: enable proof logging in the `DRUP format <http://www.cs.utexas.edu/~marijn/drup/>`__.

        :type incr: bool
        :type with_proof: bool

        .. [3] Gilles Audemard, Jean-Marie Lagniez, Laurent Simon. *Improving
            Glucose for Incremental SAT Solving with Assumptions: Application
            to MUS Extraction*. SAT 2013. pp. 309-317
    """

    def __init__(self, name='m22', bootstrap_with=None, use_timer=False, **kwargs):
        """
            Basic constructor.
        """

        self.solver = None
        self.new(name, bootstrap_with, use_timer, **kwargs)

    def __enter__(self):
        """
            'with' constructor.
        """

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
            'with' destructor.
        """

        self.solver.delete()
        self.solver = None

    def new(self, name='m22', bootstrap_with=None, use_timer=False, **kwargs):
        """

            The actual solver constructor invoked from ``__init__()``. Chooses
            the solver to run, based on its name. See :class:`Solver` for the
            parameters description.

            :raises NoSuchSolverError: if there is no solver matching the given
                name.
        """

        if not self.solver:
            name_ = name.lower()
            if name_ in SolverNames.glucose3:
                self.solver = Glucose3(bootstrap_with, use_timer, **kwargs)
            elif name_ in SolverNames.glucose4:
                self.solver = Glucose4(bootstrap_with, use_timer, **kwargs)
            elif name_ in SolverNames.lingeling:
                self.solver = Lingeling(bootstrap_with, use_timer, **kwargs)
            elif name_ in SolverNames.minicard:
                self.solver = Minicard(bootstrap_with, use_timer)
            elif name_ in SolverNames.minisat22:
                self.solver = Minisat22(bootstrap_with, use_timer)
            elif name_ in SolverNames.minisatgh:
                self.solver = MinisatGH(bootstrap_with, use_timer)
            else:
                raise(NoSuchSolverError(name))

    def delete(self):
        """
            Solver destructor, which must be called explicitly if the solver is
            to be removed. This is not needed inside an ``with`` block.
        """

        if self.solver:
            self.solver.delete()
            self.solver = None

    def solve(self, assumptions=[]):
        """
            This method is used to check satisfiability of a CNF formula given
            to the solver (see methods :meth:`add_clause` and
            :meth:`append_formula`). Unless interrupted with SIGINT, the method
            returns either ``True`` or ``False``.

            Incremental SAT calls can be made with the use of assumption
            literals. (**Note** that the ``assumptions`` argument is optional
            and disabled by default.)

            :param assumptions: a list of assumption literals.
            :type assumptions: iterable(int)

            :rtype: Boolean or ``None``.

            Example:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> s = Solver(bootstrap_with=[[-1, 2], [-2, 3])
                >>> s.solve()
                True
                >>> s.solve(assumptions=[1, -3])
                False
                >>> s.delete()
        """

        if self.solver:
            return self.solver.solve(assumptions)

    def solve_limited(self, assumptions=[]):
        """
            This method is used to check satisfiability of a CNF formula given
            to the solver (see methods :meth:`add_clause` and
            :meth:`append_formula`), taking into account the upper bounds on
            the *number of conflicts* (see :meth:`conf_budget`) and the *number
            of propagations* (see :meth:`prop_budget`). If the number of
            conflicts or propagations is set to be larger than 0 then the
            following SAT call done with :meth:`solve_limited` will not exceed
            these values, i.e. it will be *incomplete*. Otherwise, such a call
            will be identical to :meth:`solve`.

            As soon as the given upper bound on the number of conflicts or
            propagations is reached, the SAT call is dropped returning
            ``None``, i.e. *unknown*. ``None`` can also be returned if the call
            is interrupted by SIGINT. Otherwise, the method returns ``True`` or
            ``False``.

            **Note** that only MiniSat-like solvers support this functionality
            (e.g. :class:`Lingeling` does not support it).

            Incremental SAT calls can be made with the use of assumption
            literals. (**Note** that the ``assumptions`` argument is optional
            and disabled by default.)

            :param assumptions: a list of assumption literals.
            :type assumptions: iterable(int)

            :rtype: Boolean or ``None``.

            Doing limited SAT calls can be of help if it is known that
            *complete* SAT calls are too expensive. For instance, it can be
            useful when minimizing unsatisfiable cores in MaxSAT (see
            :meth:`pysat.examples.RC2.minimize_core` also shown below).

            Usage example:

            .. code-block:: python

                ... # assume that a SAT oracle is set up to contain an unsatisfiable
                ... # formula, and its core is stored in variable "core"
                oracle.conf_budget(1000)  # getting at most 1000 conflicts be call

                i = 0
                while i < len(core):
                    to_test = core[:i] + core[(i + 1):]

                    # doing a limited call
                    if oracle.solve_limited(assumptions=to_test) == False:
                        core = to_test
                    else:  # True or *unknown*
                        i += 1
        """

        if self.solver:
            return self.solver.solve_limited(assumptions)

    def conf_budget(self, budget=-1):
        """
            Set limit (i.e. the upper bound) on the number of conflicts in the
            next limited SAT call (see :meth:`solve_limited`). The limit value
            is given as a ``budget`` variable and is an integer greater than
            ``0``.  If the budget is set to ``0`` or ``-1``, the upper bound on
            the number of conflicts is disabled.

            :param budget: the upper bound on the number of conflicts.
            :type budget: int

            Example:

            .. code-block:: python

                >>> from pysat.solvers import MinisatGH
                >>> from pysat.examples.genhard import PHP
                >>>
                >>> cnf = PHP(nof_holes=20)  # PHP20 is too hard for a SAT solver
                >>> m = MinisatGH(bootstrap_with=cnf.clauses)
                >>>
                >>> m.conf_budget(2000)  # getting at most 2000 conflicts
                >>> print m.solve_limited()  # making a limited oracle call
                None
                >>> m.delete()
        """

        if self.solver:
            self.solver.conf_budget(budget)

    def prop_budget(self, budget=-1):
        """
            Set limit (i.e. the upper bound) on the number of propagations in
            the next limited SAT call (see :meth:`solve_limited`). The limit
            value is given as a ``budget`` variable and is an integer greater
            than ``0``. If the budget is set to ``0`` or ``-1``, the upper
            bound on the number of conflicts is disabled.

            :param budget: the upper bound on the number of propagations.
            :type budget: int

            Example:

            .. code-block:: python

                >>> from pysat.solvers import MinisatGH
                >>> from pysat.examples.genhard import Parity
                >>>
                >>> cnf = Parity(size=10)  # too hard for a SAT solver
                >>> m = MinisatGH(bootstrap_with=cnf.clauses)
                >>>
                >>> m.prop_budget(100000)  # doing at most 100000 propagations
                >>> print m.solve_limited()  # making a limited oracle call
                None
                >>> m.delete()
        """

        if self.solver:
            self.solver.prop_budget(budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            The method takes a list of assumption literals and does unit
            propagation of each of these literals consecutively. A Boolean
            status is returned followed by a list of assigned (assumed and also
            propagated) literals. The status is ``True`` if no conflict arised
            during propagation. Otherwise, the status is ``False``.
            Additionally, a user may specify an optional argument
            ``phase_saving`` (``0`` by default) to enable MiniSat-like phase
            saving.

            **Note** that only MiniSat-like solvers support this functionality
            (e.g. :class:`Lingeling` does not support it).

            :param assumptions: a list of assumption literals.
            :param phase_saving: enable phase saving (can be ``0``, ``1``, and
                ``2``).

            :type assumptions: iterable(int)
            :type phase_saving: int

            :rtype: tuple(bool, list(int)).

            Usage example:

            .. code-block:: python

                >>> from pysat.solvers import Glucose3
                >>> from pysat.card import *
                >>>
                >>> cnf = CardEnc.atmost(lits=range(1, 6), bound=1, encoding=EncType.pairwise)
                >>> g = Glucose3(bootstrap_with=cnf.clauses)
                >>>
                >>> g.propagate(assumptions=[1])
                (True, [1, -2, -3, -4, -5])
                >>>
                >>> g.add_clause([2])
                >>> g.propagate(assumptions=[1])
                (False, [])
                >>>
                >>> g.delete()
        """

        if self.solver:
            return self.solver.propagate(assumptions, phase_saving)

    def set_phases(self, literals=[]):
        """
            The method takes a list of literals as an argument and sets
            *phases* (or MiniSat-like *polarities*) of the corresponding
            variables respecting the literals. For example, if a given list of
            literals is ``[1, -513]``, the solver will try to set variable
            :math:`x_1` to true while setting :math:`x_{513}` to false.

            **Note** that once these preferences are specified,
            :class:`MinisatGH` and :class:`Lingeling` will always respect them
            when branching on these variables. However, solvers
            :class:`Glucose3`, :class:`Glucose4`, :class:`Minisat22`, and
            :class:`Minicard` can redefine the preferences in any of the
            following SAT calls due to the phase saving heuristic.

            :param literals: a list of literals.
            :type literals: iterable(int)

            Usage example:

            .. code-block:: python

                >>> from pysat.solvers import Glucose3
                >>>
                >>> g = Glucose3(bootstrap_with=[[1, 2]])
                >>> # the formula has 3 models: [-1, 2], [1, -2], [1, 2]
                >>>
                >>> g.set_phases(literals=[1, 2])
                >>> g.solve()
                True
                >>> g.get_model()
                [1, 2]
                >>>
                >>> g.delete()
        """

        if self.solver:
            return self.solver.set_phases(literals)

    def get_status(self):
        """
            The result of a previous SAT call is stored in an internal
            variable and can be later obtained using this method.

            :rtype: Boolean or ``None``.

            ``None`` is returned if a previous SAT call was interrupted.
        """

        if self.solver:
            return self.solver.get_status()

    def get_model(self):
        """

            The method is to be used for extracting a satisfying assignment for
            a CNF formula given to the solver. A model is provided if a
            previous SAT call returned ``True``. Otherwise, ``None`` is
            reported.

            :rtype: list(int) or ``None``.

            Example:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> s = Solver()
                >>> s.add_clause([-1, 2])
                >>> s.add_clause([-1, -2])
                >>> s.add_clause([1, -2])
                >>> s.solve()
                True
                >>> print s.get_model()
                [-1, -2]
                >>> s.delete()
        """

        if self.solver:
            return self.solver.get_model()

    def get_core(self):
        """

            This method is to be used for extracting an unsatisfiable core in
            the form of a subset of a given set of assumption literals, which
            are responsible for unsatisfiability of the formula. This can be
            done only if the previous SAT call returned ``False`` (*UNSAT*).
            Otherwise, ``None`` is returned.

            :rtype: list(int) or ``None``.

            Usage example:

            .. code-block:: python

                >>> from pysat.solvers import Minisat22
                >>> m = Minisat22()
                >>> m.add_clause([-1, 2])
                >>> m.add_clause([-2, 3])
                >>> m.add_clause([-3, 4])
                >>> m.solve(assumptions=[1, 2, 3, -4])
                False
                >>> print m.get_core()  # literals 2 and 3 are not in the core
                [-4, 1]
                >>> m.delete()
        """

        if self.solver:
            return self.solver.get_core()

    def get_proof(self):
        """
            A DRUP proof can be extracted using this method if the solver was
            set up to provide a proof. Otherwise, the method returns ``None``.

            :rtype: list(str) or ``None``.

            Example:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> from pysat.examples.genhard import PHP
                >>>
                >>> cnf = PHP(nof_holes=3)
                >>> with Solver(name='g4', with_proof=True) as g:
                ...     g.append_formula(cnf.clauses)
                ...     g.solve()
                False
                ...     print g.get_proof()
                ['-8 4 1 0', '-10 0', '-2 0', '-4 0', '-8 0', '-6 0', '0']
        """

        if self.solver:
            return self.solver.get_proof()

    def time(self):
        """
            Get the time spent when doing the last SAT call. **Note** that the
            time is measured only if the ``use_timer`` argument was previously
            set to ``True`` when creating the solver (see :class:`Solver` for
            details).

            :rtype: float.

            Example usage:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> from pysat.examples.genhard import PHP
                >>>
                >>> cnf = PHP(nof_holes=10)
                >>> with Solver(bootstrap_with=cnf.clauses, use_timer=True) as s:
                ...     print s.solve()
                False
                ...     print '{0:.2f}s'.format(s.time())
                150.16s
        """

        if self.solver:
            return self.solver.time()

    def time_accum(self):
        """
            Get the time spent for doing all SAT calls accumulated. **Note**
            that the time is measured only if the ``use_timer`` argument was
            previously set to ``True`` when creating the solver (see
            :class:`Solver` for details).

            :rtype: float.

            Example usage:

            .. code-block:: python

                >>> from pysat.solvers import Solver
                >>> from pysat.examples.genhard import PHP
                >>>
                >>> cnf = PHP(nof_holes=10)
                >>> with Solver(bootstrap_with=cnf.clauses, use_timer=True) as s:
                ...     print s.solve(assumptions=[1])
                False
                ...     print '{0:.2f}s'.format(s.time())
                1.76s
                ...     print s.solve(assumptions=[-1])
                False
                ...     print '{0:.2f}s'.format(s.time())
                113.58s
                ...     print '{0:.2f}s'.format(s.time_accum())
                115.34s
        """

        if self.solver:
            return self.solver.time_accum()

    def nof_vars(self):
        """
            This method returns the number of variables currently appearing in
            the formula given to the solver.

            :rtype: int.

            Example:

            .. code-block:: python

                >>> s = Solver(bootstrap_with=[[-1, 2], [-2, 3]])
                >>> s.nof_vars()
                3
        """

        if self.solver:
            return self.solver.nof_vars()

    def nof_clauses(self):
        """
            This method returns the number of clauses currently appearing in
            the formula given to the solver.

            :rtype: int.

            Example:

            .. code-block:: python

                >>> s = Solver(bootstrap_with=[[-1, 2], [-2, 3]])
                >>> s.nof_clauses()
                2
        """

        if self.solver:
            return self.solver.nof_clauses()

    def enum_models(self, assumptions=[]):
        """
            This method can be used to enumerate models of a CNF formula. It
            can be used as a standard Python iterator. The method can be used
            without arguments but also with an argument ``assumptions``, which
            is a list of literals to "assume".

            :param assumptions: a list of assumption literals.
            :type assumptions: iterable(int)

            :rtype: list(int).

            Example:

            .. code-block:: python

                >>> with Solver(bootstrap_with=[[-1, 2], [-2, 3]]) as s:
                ...     for m in s.enum_models():
                ...         print m
                [-1, -2, -3]
                [-1, -2, 3]
                [-1, 2, 3]
                [1, 2, 3]
                >>>
                >>> with Solver(bootstrap_with=[[-1, 2], [-2, 3]]) as s:
                ...     for m in s.enum_models(assumptions=[1]):
                ...         print m
                [1, 2, 3]
        """

        if self.solver:
            return self.solver.enum_models(assumptions)

    def add_clause(self, clause, no_return=True):
        """
            This method is used to add a single clause to the solver. An
            optional argument ``no_return`` controls whether or not to check
            the formula's satisfiability after adding the new clause.

            :param clause: an iterable over literals.
            :param no_return: check solver's internal formula and return the
                result, if set to ``False``.

            :type clause: iterable(int)
            :type no_return: bool

            :rtype: bool if ``no_return`` is set to ``False``.

            Note that a clause can be either a ``list`` of integers or another
            iterable type over integers, e.g. ``tuple`` or ``set`` among
            others.

            A usage example is the following:

            .. code-block:: python

                >>> s = Solver(bootstrap_with=[[-1, 2], [-1, -2]])
                >>> s.add_clause([1], no_return=False)
                False
        """

        if self.solver:
            res = self.solver.add_clause(clause, no_return)
            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            This method is responsible for adding a new *native* AtMostK (see
            :mod:`pysat.card`) constraint into :class:`Minicard`.

            **Note that none of the other solvers supports native AtMostK
            constraints**.

            An AtMostK constraint is :math:`\sum_{i=1}^{n}{x_i}\leq k`. A
            native AtMostK constraint should be given as a pair ``lits`` and
            ``k``, where ``lits`` is a list of literals in the sum.

            :param lits: a list of literals.
            :param k: upper bound on the number of satisfied literals
            :param no_return: check solver's internal formula and return the
                result, if set to ``False``.

            :type lits: iterable(int)
            :type k: int
            :type no_return: bool

            :rtype: bool if ``no_return`` is set to ``False``.

            A usage example is the following:

            .. code-block:: python

                >>> s = Solver(name='mc', bootstrap_with=[[1], [2], [3]])
                >>> s.add_atmost(lits=[1, 2, 3], k=2, no_return=False)
                False
                >>> # the AtMostK constraint is in conflict with initial unit clauses
        """

        if self.solver:
            res = self.solver.add_atmost(lits, k, no_return)
            if not no_return:
                return res

    def append_formula(self, formula, no_return=True):
        """
            This method can be used to add a given list of clauses into the
            solver.

            :param formula: a list of clauses.
            :param no_return: check solver's internal formula and return the
                result, if set to ``False``.

            :type formula: iterable(iterable(int))
            :type no_return: bool

            The ``no_return`` argument is set to ``True`` by default.

            :rtype: bool if ``no_return`` is set to ``False``.

            .. code-block:: python

                >>> cnf = CNF()
                ... # assume the formula contains clauses
                >>> s = Solver()
                >>> s.append_formula(cnf.clauses, no_return=False)
                True
        """

        if self.solver:
            res = self.solver.append_formula(formula, no_return)
            if not no_return:
                return res


#
#==============================================================================
class Glucose3(object):
    """
        Glucose 3 SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False, incr=False,
            with_proof=False):
        """
            Basic constructor.
        """

        self.glucose = None
        self.status = None
        self.prfile = None

        self.new(bootstrap_with, use_timer, incr, with_proof)

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
        self.glucose = None

    def new(self, bootstrap_with=None, use_timer=False, incr=False,
            with_proof=False):
        """
            Actual constructor of the solver.
        """

        assert not incr or not with_proof, 'Incremental mode and proof tracing cannot be set together.'

        if not self.glucose:
            self.glucose = pysolvers.glucose3_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

            if incr:
                pysolvers.glucose3_setincr(self.glucose)

            if with_proof:
                self.prfile = tempfile.TemporaryFile()
                pysolvers.glucose3_tracepr(self.glucose, self.prfile)

    def delete(self):
        """
            Destructor.
        """

        if self.glucose:
            pysolvers.glucose3_del(self.glucose)
            self.glucose = None

            if self.prfile:
                self.prfile.close()

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.glucose3_solve(self.glucose, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.glucose3_solve_lim(self.glucose, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.glucose:
            pysolvers.glucose3_cbudget(self.glucose, budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.glucose:
            pysolvers.glucose3_pbudget(self.glucose, budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            st, props = pysolvers.glucose3_propagate(self.glucose, assumptions, phase_saving)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return bool(st), props if props != None else []

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.glucose:
            pysolvers.glucose3_setphases(self.glucose, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.glucose:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.glucose and self.status == True:
            model = pysolvers.glucose3_model(self.glucose)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.glucose and self.status == False:
            return pysolvers.glucose3_core(self.glucose)

    def get_proof(self):
        """
            Get a proof produced when deciding the formula.
        """

        if self.glucose and self.prfile:
            self.prfile.seek(0)
            return [line.rstrip() for line in self.prfile.readlines()]

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.glucose:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.glucose:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.glucose:
            return pysolvers.glucose3_nof_vars(self.glucose)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.glucose:
            return pysolvers.glucose3_nof_cls(self.glucose)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.glucose:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.glucose3_solve(self.glucose, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.glucose:
            res = pysolvers.glucose3_add_cl(self.glucose, clause)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Atmost constraints are not supported by Glucose.
        """

        raise NotImplementedError('Atmost constraints are not supported by Glucose.')

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.glucose:
            res = None
            for clause in formula:
                res = self.add_clause(clause, no_return)

            if not no_return:
                return res


#
#==============================================================================
class Glucose4(object):
    """
        Glucose 4.1 SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False, incr=False,
            with_proof=False):
        """
            Basic constructor.
        """

        self.glucose = None
        self.status = None
        self.prfile = None

        self.new(bootstrap_with, use_timer, incr, with_proof)

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
        self.glucose = None

    def new(self, bootstrap_with=None, use_timer=False, incr=False,
            with_proof=False):
        """
            Actual constructor of the solver.
        """

        assert not incr or not with_proof, 'Incremental mode and proof tracing cannot be set together.'

        if not self.glucose:
            self.glucose = pysolvers.glucose41_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

            if incr:
                pysolvers.glucose41_setincr(self.glucose)

            if with_proof:
                self.prfile = tempfile.TemporaryFile()
                pysolvers.glucose41_tracepr(self.glucose, self.prfile)

    def delete(self):
        """
            Destructor.
        """

        if self.glucose:
            pysolvers.glucose41_del(self.glucose)
            self.glucose = None

            if self.prfile:
                self.prfile.close()

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.glucose41_solve(self.glucose, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.glucose41_solve_lim(self.glucose, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.glucose:
            pysolvers.glucose41_cbudget(self.glucose, budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.glucose:
            pysolvers.glucose41_pbudget(self.glucose, budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        if self.glucose:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            st, props = pysolvers.glucose41_propagate(self.glucose, assumptions, phase_saving)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return bool(st), props if props != None else []

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.glucose:
            pysolvers.glucose41_setphases(self.glucose, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.glucose:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.glucose and self.status == True:
            model = pysolvers.glucose41_model(self.glucose)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.glucose and self.status == False:
            return pysolvers.glucose41_core(self.glucose)

    def get_proof(self):
        """
            Get a proof produced when deciding the formula.
        """

        if self.glucose and self.prfile:
            self.prfile.seek(0)
            return [line.rstrip() for line in self.prfile.readlines()]

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.glucose:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.glucose:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.glucose:
            return pysolvers.glucose41_nof_vars(self.glucose)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.glucose:
            return pysolvers.glucose41_nof_cls(self.glucose)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.glucose:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.glucose41_solve(self.glucose, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.glucose:
            res = pysolvers.glucose41_add_cl(self.glucose, clause)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Atmost constraints are not supported by Glucose.
        """

        raise NotImplementedError('Atmost constraints are not supported by Glucose.')

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.glucose:
            res = None
            for clause in formula:
                res = self.add_clause(clause, no_return)

            if not no_return:
                return res


#
#==============================================================================
class Lingeling(object):
    """
        Lingeling SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False, incr=False,
            with_proof=False):
        """
            Basic constructor.
        """

        if incr:
            raise NotImplementedError('Incremental mode is not supported by Lingeling.')

        self.lingeling = None
        self.status = None
        self.prfile = None

        self.new(bootstrap_with, use_timer, with_proof)

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
        self.lingeling = None

    def new(self, bootstrap_with=None, use_timer=False, with_proof=False):
        """
            Actual constructor of the solver.
        """

        if not self.lingeling:
            self.lingeling = pysolvers.lingeling_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

            if with_proof:
                self.prfile = tempfile.TemporaryFile()
                pysolvers.lingeling_tracepr(self.lingeling, self.prfile)

    def delete(self):
        """
            Destructor.
        """

        if self.lingeling:
            pysolvers.lingeling_del(self.lingeling, self.prfile)
            self.lingeling = None

            if self.prfile:
                self.prfile.close()

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.lingeling:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.lingeling_solve(self.lingeling, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            self.prev_assumps = assumptions
            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        raise NotImplementedError('Limited solve is currently unsupported by Lingeling.')

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        raise NotImplementedError('Limited solve is currently unsupported by Lingeling.')

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        raise NotImplementedError('Limited solve is currently unsupported by Lingeling.')

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        raise NotImplementedError('Simple literal propagation is not yet implemented for Lingeling.')

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.lingeling:
            pysolvers.lingeling_setphases(self.lingeling, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.lingeling:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.lingeling and self.status == True:
            model = pysolvers.lingeling_model(self.lingeling)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.lingeling and self.status == False:
            return pysolvers.lingeling_core(self.lingeling, self.prev_assumps)

    def get_proof(self):
        """
            Get a proof produced when deciding the formula.
        """

        if self.lingeling and self.prfile:
            self.prfile.seek(0)
            return [line.rstrip() for line in self.prfile.readlines()]

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.lingeling:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.lingeling:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.lingeling:
            return pysolvers.lingeling_nof_vars(self.lingeling)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.lingeling:
            return pysolvers.lingeling_nof_cls(self.lingeling)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.lingeling:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.lingeling_solve(self.lingeling, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.lingeling:
            pysolvers.lingeling_add_cl(self.lingeling, clause)

    def add_atmost(self, lits, k, no_return=True):
        """
            Atmost constraints are not supported by Lingeling.
        """

        raise NotImplementedError('Atmost constraints are not supported by Lingeling.')

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.lingeling:
            for clause in formula:
                self.add_clause(clause, no_return)


#
#==============================================================================
class Minicard(object):
    """
        Minicard SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False):
        """
            Basic constructor.
        """

        self.minicard = None
        self.status = None

        self.new(bootstrap_with, use_timer)

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
        self.minicard = None

    def new(self, bootstrap_with=None, use_timer=False):
        """
            Actual constructor of the solver.
        """

        if not self.minicard:
            self.minicard = pysolvers.minicard_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

    def delete(self):
        """
            Destructor.
        """

        if self.minicard:
            pysolvers.minicard_del(self.minicard)
            self.minicard = None

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.minicard:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minicard_solve(self.minicard, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.minicard:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minicard_solve_lim(self.minicard, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.minicard:
            pysolvers.minicard_cbudget(self.minicard, budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minicard:
            pysolvers.minicard_pbudget(self.minicard, budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        if self.minicard:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            st, props = pysolvers.minicard_propagate(self.minicard, assumptions, phase_saving)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return bool(st), props if props != None else []

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.minicard:
            pysolvers.minicard_setphases(self.minicard, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.minicard:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.minicard and self.status == True:
            model = pysolvers.minicard_model(self.minicard)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.minicard and self.status == False:
            return pysolvers.minicard_core(self.minicard)

    def get_proof(self):
        """
            Get a proof produced while deciding the formula.
        """

        raise NotImplementedError('Proof tracing is not supported by Minicard.')

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.minicard:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.minicard:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.minicard:
            return pysolvers.minicard_nof_vars(self.minicard)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.minicard:
            return pysolvers.minicard_nof_cls(self.minicard)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.minicard:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.minicard_solve(self.minicard, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.minicard:
            res = pysolvers.minicard_add_cl(self.minicard, clause)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Add a new atmost constraint to solver's internal formula.
        """

        if self.minicard:
            res = pysolvers.minicard_add_am(self.minicard, lits, k)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.minicard:
            res = None
            for clause in formula:
                res = self.add_clause(clause, no_return)

            if not no_return:
                return res


#
#==============================================================================
class Minisat22(object):
    """
        MiniSat 2.2 SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False):
        """
            Basic constructor.
        """

        self.minisat = None
        self.status = None

        self.new(bootstrap_with, use_timer)

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
        self.minisat = None

    def new(self, bootstrap_with=None, use_timer=False):
        """
            Actual constructor of the solver.
        """

        if not self.minisat:
            self.minisat = pysolvers.minisat22_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

    def delete(self):
        """
            Destructor.
        """

        if self.minisat:
            pysolvers.minisat22_del(self.minisat)
            self.minisat = None

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minisat22_solve(self.minisat, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minisat22_solve_lim(self.minisat, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.minisat:
            pysolvers.minisat22_cbudget(self.minisat, budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minisat:
            pysolvers.minisat22_pbudget(self.minisat, budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            st, props = pysolvers.minisat22_propagate(self.minisat, assumptions, phase_saving)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return bool(st), props if props != None else []

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.minisat:
            pysolvers.minisat22_setphases(self.minisat, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.minisat:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.minisat and self.status == True:
            model = pysolvers.minisat22_model(self.minisat)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.minisat and self.status == False:
            return pysolvers.minisat22_core(self.minisat)

    def get_proof(self):
        """
            Get a proof produced while deciding the formula.
        """

        raise NotImplementedError('Proof tracing is not supported by MiniSat.')

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.minisat:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.minisat:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.minisat:
            return pysolvers.minisat22_nof_vars(self.minisat)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.minisat:
            return pysolvers.minisat22_nof_cls(self.minisat)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.minisat:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.minisat22_solve(self.minisat, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.minisat:
            res = pysolvers.minisat22_add_cl(self.minisat, clause)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Atmost constraints are not supported by MiniSat.
        """

        raise NotImplementedError('Atmost constraints are not supported by MiniSat.')

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.minisat:
            res = None
            for clause in formula:
                res = self.add_clause(clause, no_return)

            if not no_return:
                return res


#
#==============================================================================
class MinisatGH(object):
    """
        MiniSat SAT solver (version from github).
    """

    def __init__(self, bootstrap_with=None, use_timer=False):
        """
            Basic constructor.
        """

        self.minisat = None
        self.status = None

        self.new(bootstrap_with, use_timer)

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
        self.minisat = None

    def new(self, bootstrap_with=None, use_timer=False):
        """
            Actual constructor of the solver.
        """

        if not self.minisat:
            self.minisat = pysolvers.minisatgh_new()

            if bootstrap_with:
                for clause in bootstrap_with:
                    self.add_clause(clause)

            self.use_timer = use_timer
            self.call_time = 0.0  # time spent for the last call to oracle
            self.accu_time = 0.0  # time accumulated for all calls to oracle

    def delete(self):
        """
            Destructor.
        """

        if self.minisat:
            pysolvers.minisatgh_del(self.minisat)
            self.minisat = None

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minisatgh_solve(self.minisat, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            self.status = pysolvers.minisatgh_solve_lim(self.minisat, assumptions)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return self.status

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.minisat:
            pysolvers.minisatgh_cbudget(self.minisat, budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minisat:
            pysolvers.minisatgh_pbudget(self.minisat, budget)

    def propagate(self, assumptions=[], phase_saving=0):
        """
            Propagate a given set of assumption literals.
        """

        if self.minisat:
            if self.use_timer:
                 start_time = time.clock()

            # saving default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)

            st, props = pysolvers.minisatgh_propagate(self.minisat, assumptions, phase_saving)

            # recovering default SIGINT handler
            def_sigint_handler = signal.signal(signal.SIGINT, def_sigint_handler)

            if self.use_timer:
                self.call_time = time.clock() - start_time
                self.accu_time += self.call_time

            return bool(st), props if props != None else []

    def set_phases(self, literals=[]):
        """
            Sets polarities of a given list of variables.
        """

        if self.minisat:
            pysolvers.minisatgh_setphases(self.minisat, literals)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.minisat:
            return self.status

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.minisat and self.status == True:
            model = pysolvers.minisatgh_model(self.minisat)
            return model if model != None else []

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.minisat and self.status == False:
            return pysolvers.minisatgh_core(self.minisat)

    def get_proof(self):
        """
            Get a proof produced while deciding the formula.
        """

        raise NotImplementedError('Proof tracing is not supported by MiniSat.')

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.minisat:
            return self.call_time

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.minisat:
            return self.accu_time

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.minisat:
            return pysolvers.minisatgh_nof_vars(self.minisat)

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.minisat:
            return pysolvers.minisatgh_nof_cls(self.minisat)

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.minisat:
            done = False
            while not done:
                if self.use_timer:
                    start_time = time.clock()

                self.status = pysolvers.minisatgh_solve(self.minisat, assumptions)

                if self.use_timer:
                    self.call_time = time.clock() - start_time
                    self.accu_time += self.call_time

                model = self.get_model()

                if model:
                    self.add_clause([-l for l in model])  # blocking model
                    yield model
                else:
                    done = True

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.minisat:
            res = pysolvers.minisatgh_add_cl(self.minisat, clause)

            if res == False:
                self.status = False

            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Atmost constraints are not supported by MiniSat.
        """

        raise NotImplementedError('Atmost constraints are not supported by MiniSat.')

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
        """

        if self.minisat:
            res = None
            for clause in formula:
                res = self.add_clause(clause, no_return)

            if not no_return:
                return res
