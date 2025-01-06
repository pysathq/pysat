#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## engines.py
##
##  Created on: Sep 20, 2023
##      Author: Alexey Ignatiev, Zi Li Tan
##      E-mail: alexey.ignatiev@monash.edu, ztan0050@student.monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Propagator
        BooleanEngine
        LinearConstraint
        ParityConstraint

    ==================
    Module description
    ==================

    This module provides a user with the possibility to define their own
    propagation engines, i.e. constraint propagators, attachable to a SAT
    solver. The implementation of this functionality builds on the use of the
    IPASIR-UP interface [1]_. This may come in handy when it is beneficial to
    reason over non-clausal constraints, for example, in the settings of
    satisfiability modulo theories (SMT), constraint programming (CP) and lazy
    clause generation (LCG).

    .. [1] Katalin Fazekas, Aina Niemetz, Mathias Preiner, Markus Kirchweger,
        Stefan Szeider, Armin Biere. *IPASIR-UP: User Propagators for CDCL*.
        SAT. 2023. pp. 8:1-8:13

    .. note::

        Currently, the only SAT solver available in PySAT supporting the
        interface is CaDiCaL 1.9.5.

    The interface allows a user to attach a single reasoning engine to the
    solver. This means that if one needs to support multiple kinds of
    constraints simultaneously, the implementation of the engine may need to
    be sophisticated enough to make it work.

    It is imperative that any propagator a user defines must inherit the
    interface of the abstract class :class:`Propagator` and defines all the
    required methods for the correct operation of the engine.

    An example propagator is shown in the class :class:`BooleanEngine`. It
    currently supports two kinds of example constraints: linear (cardinality
    and pseudo-Boolean) constraints and parity (exclusive OR, XOR)
    constraints. The engine can run in the *adaptive mode*, i.e. it can enable
    and disable itself on the fly.

    Once an engine is implemented, it should be attached to a solver object by
    calling :meth:`connect_propagator` of :class:`Cadical195`. The propagator
    will then need to inform the solver what variable it requires to observe.

    .. code-block:: python

            solver = Solver(name='cadical195', bootstrap_with=some_formula)

            engine = MyPowerfulEngine(...)
            solver.connect_propagator(engine)

            # attached propagator wants to observe these variables
            for var in range(some_variables):
                solver.observe(var)

            ...

    .. note::

        A user is encouraged to examine the source code of
        :class:`BooleanEngine` in order to see how an external reasoning
        engine can be implemented and attached to CaDiCaL 1.9.5. Also consult
        the implementation of the corresponding methods of
        :class:`.Cadical195`.

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from collections import Counter, defaultdict
import functools
import itertools
from typing import List


#
#==============================================================================
class LinearConstraint:
    """
        A possible implementation of linear constraints over Boolean
        variables, including cardinality and pseudo-Boolean constraints. Each
        such constraint is meant to be in the less-than form, i.e. a user
        should transform the literals, weights and the right-hand side of the
        constraint into this form before creating an object of
        :class:`LinearConstraint`. The class is designed to work with
        :class:`BooleanEngine`.

        The implementation of linear constraint propagation builds on the use
        of counters. Basically, each time a literal is assigned to a positive
        value, it is assumed to contribute to the total weight on the
        left-hand side of the constraint, which is calculated and compared to
        the right-hand side.

        The constructor receives three arguments: ``lits``, ``weights``, and
        ``bound``. Argument ``lits`` represents a list of literals on the
        left-hand side of the constraint while argument ``weights`` contains
        either a list of their weights or a dictionary mapping literals to
        weights. Finally, argument ``bound`` is the right-hand side of the
        constraint.

        Note that if no weights are provided, each occurrence of a literal is
        assumed to have weight 1.

        .. note::

            All weights are supposed to be non-negative values.

        :param lits: list of literals (left-hand side)
        :param weights: weights of the literals
        :param bound: right-hand side of the constraint

        :type lits:
        :type weights: list or dict
        :type bound: int or float
    """

    def __init__(self, lits=[], weights={}, bound=1):
        """
            Constraint initialiser.
        """

        if not weights or type(weights) == dict:
            # the same literal may appear multiple times in the list
            # so we need to calculate it's actual weight
            cntr = Counter(lits)

            # left-hand side in terms of literals and their weights
            self.lits = sorted(cntr.keys())
            self.wght = {l: cntr[l] * (weights[l] if weights else 1) for l in self.lits}
        else:
            assert len(lits) == len(weights), 'The number of weights differs from the number of literals'

            # first, computing the weights (there may be literal repetition)
            self.wght = defaultdict(lambda: 0)
            for l, w in zip(lits, weights):
                self.wght[l] += w

            # second, extracting the list of unique literals
            self.lits = sorted(self.wght.keys())

        # right-hand side and value counter
        self.rbnd = bound
        self.vcnt = 0

        # auxiliary data used during propagation
        # None is needed here for propagation without an assignment
        self.lset = set(self.lits + [None])
        self.lval = None

        # a model that falsifies the constraint (if any)
        self.fmod = None

        if min(self.wght.values()) == max(self.wght.values()):
            if self.wght[self.lits[0]] != 1:
                self.rbnd //= self.wght[self.lits[0]]
                self.wght = {l: 1 for l in lits}

            # unweighted / cardinality propagation
            self.propagate = self.propagate_unweighted

            # constraint propagates all literals at once,
            # i.e. they all share the same reason
            self.expl = []
            self.justify = self.justify_unweighted
            self.abandon = self.abandon_unweighted
        else:
            # weighted / pseudo-Boolean propagation
            self.propagate = self.propagate_weighted

            # constraint may propagate different literals
            # at different points in time, reasons may differ
            self.expl = defaultdict(lambda: [])
            self.justify = self.justify_weighted
            self.abandon = self.abandon_weighted

        # for weighted case only: a flag for indicating whether we can propagate
        self.done = False

        # adding literal 'None' with 0-weight
        self.wght[None] = 0

    def register_watched(self, to_watch):
        """
            Add self to the centralised watched literals lists in
            :class:`BooleanEngine`.
        """

        for lit in self.lits:
            to_watch[lit].append(self)

    def attach_values(self, values):
        """
            Give the constraint access to centralised values exposed from
            :class:`BooleanEngine`.
        """

        self.lval = values

    def propagate_unweighted(self, lit=None):
        """
            Get all the consequences of a given literal in the unweighted
            case. The implementation *counts* how many literals on the
            left-hand side are assigned to true.
        """

        if not self.expl:
            self.vcnt += self.wght[lit]

            if self.vcnt == self.rbnd:  # this is when we should propagate
                iter1, iter2 = itertools.tee(self.lits)
                self.expl = list(-l for l in iter1 if self.lval[abs(l)] == l)
                to_entail = list(-l for l in iter2 if self.lval[abs(l)] is None)

                return to_entail

        return []

    def justify_unweighted(self, dummy_lit):
        """
            Provide a reason for a literal propagated by this constraint. In
            the unweighted case, all the literals propagated by this
            constraint share the same reason.
        """

        return self.expl

    def abandon_unweighted(self, dummy_lit):
        """
            Clear the reason of a given literal.
        """

        self.expl.clear()

    def propagate_weighted(self, lit=None):
        """
            Get all the consequences of a given literal in the weighted case.
            The implementation counts the weights of all the literals assigned
            to true and propagates all the other literals (yet unassigned)
            such that adding their weights to the total sum would exceed the
            right-hand side of the constraint.
        """

        if not self.done:
            self.vcnt += self.wght[lit]

            iter1, iter2, iter3 = itertools.tee(self.lits, 3)
            expl = list(-l for l in iter1 if self.lval[abs(l)] == l)
            to_entail = list(-l for l in iter2 if self.lval[abs(l)] is None and self.vcnt + self.wght[l] > self.rbnd and not self.expl[-l])

            # counting the number of unassigned literals to check
            # whether there is something left to do in the future
            nunknown = functools.reduce(lambda x, y: x + 1 if self.lval[abs(y)] is not None else x, iter3, 0)

            # are we done with constraint for now?
            if len(to_entail) == nunknown:
                self.done = True

            # setting the reason for each of the propagated literals
            for l in to_entail:
                self.expl[l] = expl

            return to_entail

        return []

    def justify_weighted(self, lit):
        """
            Provide a reason for a literal propagated by this constraint. In
            the case of weighted constraints, a literal may have a reason
            different from the other literals propagated by the same
            constraint.
        """

        return self.expl[lit]

    def abandon_weighted(self, lit):
        """
            Clear the reason of a given literal.
        """

        self.expl[lit].clear()

    def unassign(self, lit):
        """
            Unassign a given literal, which is done by decrementing the
            literal's contribution to the total sum of the weights of assigned
            literals.
        """

        self.vcnt -= self.wght[lit]
        self.done = False

    def falsified_by(self, model):
        """
            Check if the constraint is violated by a given assignment. Upon
            receiving such an input assignment, the method counts the sum of
            the weights of all satisfied literals and checks if it exceeds the
            right-hand side.
        """

        value = functools.reduce(lambda x, y: x + self.wght[y] if y in self.lset else x, model, 0)

        if value > self.rbnd:
            self.fmod = model
            return True

        return False

    def explain_failure(self):
        """
            Provide a reason clause for why the previous model falsified
            the constraint. This will clause will be added to the solver.
        """

        return [-l for l in self.fmod if l in self.lset]


#
#==============================================================================
class ParityConstraint:
    """
        A possible implementation of parity constraints. These are constraints
        of the form :math:`l_1 \\oplus l_2 \\oplus \\ldots \\oplus l_n = b`
        where each :math:`l_i` is a Boolean literal while :math:`b` is a
        Boolean constant. The class is designed to exemplify the work with
        :class:`BooleanEngine`.

        The implementation is pretty naive. It propagates a last unassigned
        literal if all but one literals got their values. The value the
        propagated literals is assigned to depends on the other values in the
        constraint as well as on the right-hand side value.

        The constructor receives two arguments: ``lits`` and ``value``.
        Argument ``lits`` represents a list of literals on the left-hand side
        of the constraint while argument ``value`` represents the right-hand
        side. By default, ``value`` equals ``1``.

        :param lits: list of literals (left-hand side)
        :param value: right-hand side of the constraint

        :type lits:
        :type value: bool
    """

    def __init__(self, lits=[], value=1):
        """
            Constraint initialiser.
        """

        # checking whether the right-hand side is correct
        assert value in (0, 1), 'incorrect right-hand side value'

        # left-hand side of the parity constraint
        # trivially removing all the negative literals
        self.lits = []
        for lit in lits:
            if lit < 0:
                lit = -lit
                value ^= value
            self.lits.append(lit)

        # right-hand side, current value, and variable counter
        self.rval = value
        self.curr = 0
        self.vcnt = 0

        # auxiliary data used during propagation
        # None is needed here for propagation without an assignment
        self.lset = set(self.lits + [None])
        self.lval = None

        # reason for the propagated literals
        self.expl = []

        # a model that falsifies the constraint (if any)
        self.fmod = None

        # a copy of watched literals, watched length, and
        # a mapping to the index of an opposite literal
        self.wlst = None
        self.wopp = defaultdict(lambda: None)

        # if it is unit clause then propagate its sole literal at level 0
        self.zlev = self.lits[0] * (2 * self.rval - 1) if len(self.lits) == 1 else None

    def register_watched(self, to_watch):
        """
            Add self to the centralised watched literals lists in
            :class:`BooleanEngine`.
        """

        if len(self.lits) > 1:
            # copying the watched lists
            if self.wlst is None:
                self.wlst = to_watch

            # we need to trigger this constraint
            # no matter what value a variable gets
            for lit in self.lits[:2]:
                self.wopp[+lit] = len(self.wlst[-lit])
                self.wopp[-lit] = len(self.wlst[+lit])

                self.wlst[+lit].append(self)
                self.wlst[-lit].append(self)

    def replace_watched(self, old, new):
        """
            Register this constraint as to be watched for a new literal.
        """

        # clean up the old literal
        p, n = self.wopp[-old], self.wopp[+old]
        self.wlst[+old][p] = n
        self.wopp[+old] = None  # technically, we don't have to remove these
        self.wopp[-old] = None

        # register the new literal
        self.wopp[+new] = len(self.wlst[-new])
        self.wopp[-new] = len(self.wlst[+new])
        self.wlst[+new].append(self)
        self.wlst[-new].append(self)

    def attach_values(self, values):
        """
            Give the constraint access to centralised values exposed from
            :class:`BooleanEngine`.
        """

        self.lval = values

    def propagate(self, lit=None):
        """
            Get all the consequences of a given literal. Propagation here
            should be similar to that of normal clauses (2-watched scheme).
        """

        if not self.expl:
            if lit:
                if self.lits[0] in (lit, -lit):  # this is the first literal
                                                # so make it the second one
                    self.lits[0], self.lits[1] = self.lits[1], self.lits[0]

                # find the new watch
                value = self.lval[abs(self.lits[1])] in self.lset
                for i in range(2, len(self.lits)):
                    v = abs(self.lits[i])

                    if self.lval[v] is None:  # v is going to be a new watch
                        self.replace_watched(lit, self.lits[i])
                        self.lits[1], self.lits[i] = self.lits[i], self.lits[1]
                        break

                    value ^= self.lval[v] in self.lset
                else:  # failed to find a new watch!
                    self.expl = [-self.lval[abs(self.lits[i])] for i in range(1, len(self.lits))]
                    to_entail = self.lits[0]
                    if value == self.rval:
                        to_entail *= -1
                    return [to_entail]
            elif self.zlev is not None:
                self.expl, to_entail, self.zlev = [], self.zlev, None
                return [to_entail]

        return []

    def justify(self, dummy_lit):
        """
            Provide a reason for the literal propagated from here.
        """

        return self.expl

    def abandon(self, dummy_lit):
        """
            Clear the reason of a given literal.
        """

        self.expl.clear()

    def unassign(self, lit):
        """
            Unassign a given literal. A dummy method, which does nothing.
        """

        pass

    def falsified_by(self, model):
        """
            Check if the constraint is violated by a given assignment, which
            is done by xor'ing up all the values on the left-hand side (given
            a model) and comparing with the right-hand side value.
        """

        value = functools.reduce(lambda x, y: x ^ 1 if y in self.lset else x, model, 0)

        if value != self.rval:
            self.fmod = model
            return True

        return False

    def explain_failure(self):
        """
            Provide a reason clause for why the previous model falsified
            the constraint. This will clause will be added to the solver.
        """

        return [-l for l in self.fmod if l in self.lset or -l in self.lset]


#
#==============================================================================
class Propagator(object):
    """
        An abstract class for creating external user-defined propagators /
        reasoning engines to be used with solver :class:`Cadical195` through
        the IPASIR-UP interface. All user-defined propagators should inherit
        the interface of this abstract class, i.e. all the below methods need
        to be properly defined. The interface is as follows:

        .. code-block:: python

            class Propagator(object):
                def on_assignment(self, lit: int, fixed: bool = False) -> None:
                    pass      # receive a new literal assigned by the solver

                def on_new_level(self) -> None:
                    pass      # get notified about a new decision level

                def on_backtrack(self, to: int) -> None:
                    pass      # process backtracking to a given level

                def check_model(self, model: List[int]) -> bool:
                    pass      # check if a given assignment is indeed a model

                def decide(self) -> int:
                    return 0  # make a decision and (if any) inform the solver

                def propagate(self) -> List[int]:
                    return [] # propagate and return inferred literals (if any)

                def provide_reason(self, lit: int) -> List[int]:
                    pass      # explain why a given literal was propagated

                def add_clause(self) -> List[int]:
                    return [] # add an(y) external clause to the solver
    """

    def __init__(self):
        """
            Initialiser / constructor. Declare/define all the variables
            required for the propagator's functionality here.
        """

        # internal flag to declare the propagator "lazy"
        # (a lazy propagator only checks complete assignments;
        # currently, checked only when it gets connected)
        self.is_lazy = False

    def __delete__(self):
        """
            Destructor.
        """

        pass

    def on_assignment(self, lit: int, fixed: bool = False) -> None:
        """
            The method is called to notify the propagator about an assignment
            made for one of the observed variables. An assignment is set to be
            "fixed" if it is permanent, i.e. the propagator is not allowed to
            undo it.

            :param lit: assigned literal
            :param fixed: a flag to mark the assignment as "fixed"

            :type lit: int
            :type fixed: bool
        """

        pass

    def on_new_level(self) -> None:
        """
            The method called to notify the propagator about a new decision
            level created by the solver.
        """

        pass

    def on_backtrack(self, to: int) -> None:
        """
            The method for notifying the propagator about backtracking to a
            given decision level. Accepts a single argument ``to`` signifying
            the backtrack level.

            :param to: backtrack level
            :type to: int
        """

        pass

    def check_model(self, model: List[int]) -> bool:
        """
            The method is used for checking if a given (complete) truth
            assignment satisfies the constraint managed by the propagator.
            Receives a single argument storing the truth assignment found by
            the solver.

            .. note::

                If this method returns ``False``, the propagator must be ready
                to provide an external clause in the following callback.

            :param model: a list of integers representing the current model
            :type model: iterable(int)

            :rtype: bool
        """

        pass

    def decide(self) -> int:
        """
            This method allows the propagator to influence the decision
            process. Namely, it is used when the solver asks the propagator
            for the next decision literal (if any). If the method returns
            ``0``, the solver will make its own choice.

            :rtype: int
        """

        return 0

    def propagate(self) -> List[int]:
        """
            The method should invoke propagation under the current assignment.
            It can return either a list of literals propagated or an empty
            list ``[]``, informing the solver that no propagation is made
            under the current assignment.

            :rtype: int
        """

        return []

    def provide_reason(self, lit: int) -> List[int]:
        """
            The method is called by the solver when asking the propagator for
            the reason / antecedent clause for a literal the propagator
            previously inferred. This clause will be used in the following
            conflict analysis.

            .. note::

                The clause must contain the propagated literal.

            :param lit: literal to provide reason for
            :type lit: int

            :rtype: iterable(int)
        """

        pass

    def add_clause(self) -> List[int]:
        """
            The method is called by the solver to add an external clause if
            there is any. The clause can be arbitrary but if it is
            root-satisfied or tautological, the solver will ignore it without
            learning it.

            Root-falsified literals are eagerly removed from the clause.
            Falsified clauses trigger conflict analysis, propagating clauses
            trigger propagation. Unit clauses always (unless root-satisfied,
            see above) trigger backtracking to level 0.

            An empty clause (or root falsified clause, see above) makes the
            formula unsatisfiable and stops the search immediately.

            :rtype: iterable(int)
        """

        pass


#
#==============================================================================
class BooleanEngine(Propagator):
    """
        A simple *example* Boolean constraint propagator inheriting from the
        class :class:`Propagator`. The idea is to exemplify the use of
        external reasoning engines. The engine should be general enough to
        support various constraints over Boolean variables.

        .. note::

            Note that this is not meant to be a model implementation of an
            external engine. One can devise a more efficient implementation
            with the same functionality.

        The initialiser of of the class object may be provided with a list of
        constraints, each being a tuple ('type', constraint), as a value for
        parameter ``bootstrap_with``.

        Currently, there are two types of constraints supported (to be
        specified) in the constraints passed in: ``'linear'`` and ``'parity'``
        (exclusive OR). The former will be handled as objects of class
        :class:`LinearConstraint` while the latter will be transformed into
        objects of :class:`ParityConstraint`.

        Here, each type of constraint is meant to have a list of literals
        stored in variable ``.lits``. This is required to set up watched lists
        properly.

        The second keyword argument ``adaptive`` (set to ``True`` by default)
        denotes the fact that the engine should check its own efficiency and
        disable or enable itself on the fly. This functionality is meant to
        exemplify how adaptive external engines can be created. A user is
        referred to the source code of the implementation for the details.
    """

    def __init__(self, bootstrap_with=[], adaptive=True):
        """
            Initialiser.
        """

        self.vars = []                       # all known variables
        self.vset = set()                    # a set of all variables
        self.cons = []                       # all known constraints
        self.lins = []                       # linear constraints
        self.xors = []                       # parity constraints
        self.wlst = defaultdict(lambda: [])  # constraints to watch

        # this propagator may disable itself depending on the circumstances
        self.is_adaptive = adaptive

        # setting up individual constraint handlers
        if bootstrap_with:
            for cs in bootstrap_with:
                cs = self._add_constraint(cs)

                # updating the set of known variables
                self.vset.update(set(abs(l) for l in cs.lits))

            # setting all known variables
            self.vars = sorted(self.vset)

            # run the preprocessing techniques (if any)
            self.preprocess()

            # attaching new constraints after processing to the watched lists
            for cs in self.cons:
                cs.register_watched(self.wlst)

        # value and trail handling
        self.value = {v: None for v in self.vars}
        self.fixed = {v: False for v in self.vars}
        self.trail = []
        self.trlim = []
        self.props = defaultdict(lambda: [])
        self.qhead = None

        # decision level
        self.decision_level = 0
        self.level = {v: None for v in self.vars}

        # reasons for propagated literals
        self.origin = defaultdict(lambda: None)

        # this variable points to the constraint previously violated by a
        # given model offered by the solver
        self.falsified = None

        # giving constraints access to the values
        for cs in self.cons:
            cs.attach_values(self.value)

        # currently, no solver is known to this propagator
        # this will be update upon calling self.setup_observe()
        self.solver = None

        # the following constants are used in adaptive mode:
        # the number of calls to propagate() between model checks and
        # the number of propagated literals found between those checks
        # followed by decaying propagation ratio-related constants
        self.nprops, self.ncalls = 0, 0
        self.pratio, self.pdecay, self.pbound = 0, 2, 0.2

        # decaying ratio of falsifying assignments
        # over all assignments offered by the solver
        self.mratio, self.mdecay, self.mbound = 0, 2, 2

    def adaptive_constants(self, pdecay, pbound, mdecay, mbound):
        """
            Set magic numeric constants used in adaptive mode.
        """

        self.pdecay = pdecay
        self.pbound = pbound

        self.mdecay = mdecay
        self.mbound = mbound

    def enable(self):
        """
            Notify the solver that the propagator is willing to become active
            from now on.
        """

        assert self.solver, 'Solver is not connected!'
        self.solver.enable_propagator()

    def disable(self):
        """
            Notify the solver that the propagator should become inactive as it
            does not contribute much to the inference process. From now on, it
            will only be called to check complete models obtained by the
            solver (see :meth:`check_model`).
        """

        assert self.solver, 'Solver is not connected!'
        self.solver.disable_propagator()

    def is_active(self):
        """
            Return engine's status. It is deemed active if the method returns
            ``True`` and passive otherwise.
        """

        assert self.solver, 'Solver is not connected!'
        return self.solver.propagator_active()

    def add_constraint(self, constraint):
        """
            Add a new constraint to the engine and integrate it to the
            internal structures, i.e. watched lists. Also, return the newly
            added constraint to the callee.
        """

        cs = self._add_constraint(constraint)

        # adding it to the watched lists
        cs.register_watched(self.wlst)

        # updating the other structures of the propagator
        for lit in cs.lits:
            var = abs(lit)
            if var not in self.vset:
                # this variable is currently unknown
                self.vset.add(var)
                self.value[var] = None
                self.level[var] = None
                self.fixed[var] = False

                # letting the solver know we observe this variable
                self.solver.observe(var)

        # passing values to the constraint
        cs.attach_values(self.value)

    def _add_constraint(self, cs):
        """
            Create a new constraint, add to the list and return for further
            processing.
        """

        if cs[0] == 'linear':
            cs = LinearConstraint(lits=cs[1][0],
                                  weights={} if len(cs[1]) == 2 else cs[1][2],
                                  bound=cs[1][1])
            self.lins.append(cs)
        elif cs[0] == 'parity':
            cs = ParityConstraint(lits=cs[1][0], value=cs[1][1])
            self.xors.append(cs)
        else:
            assert 0, 'Unknown type of constraint'

        # adding the newly created constraint
        # to the list of known constraints
        self.cons.append(cs)

        return cs

    def setup_observe(self, solver):
        """
            Inform the solver about all the variables the engine is interested
            in. The solver will mark them as observed by the propagator.
        """

        # saving the solver for the future
        self.solver = solver

        for var in self.vars:
            self.solver.observe(var)

    def preprocess(self):
        """
            Run some (naive) preprocessing techniques if available for the
            types of constraints under considerations. Each type of
            constraints is handled separately of the rest of constraints.
        """

        if self.lins:
            self.process_linear()

        if self.xors:
            self.process_parity()

    def process_linear(self):
        """
            Process linear constraints. Here we apply simple pairwise
            summation of constraints. As the number of result constraints is
            quadratic, we stop the process as soon as we get 100 new
            constraints. Also, if a result of the sum is longer than each of
            the summands, the result constraint is ignored.

            This is trivial procedure is made to illustrate how constraint
            processing can be done. It can be made dependent on user-specified
            parameters, e.g. the number of rounds or a numeric value
            indicating when a pair of constraints should be added and when
            they should not be added. For consideration in the future.
        """

        newc = []

        for cs1, cs2 in itertools.combinations(self.lins, 2):
            seen, wght, remd = set(), defaultdict(lambda: 0), 0

            # traversing the first constraint and handling clashes
            for l in cs1.lits:
                if l in cs2.lset:
                    # the literal appears in both constraints
                    wght[l] = cs1.wght[l] + cs2.wght[l]
                elif -l in cs2.lset:
                    # the literal appears in opposite phases
                    maxp = max([(l, cs1.wght[l]), (-l, cs2.wght[-l])], key=lambda pair: pair[1])
                    minp = min([(l, cs1.wght[l]), (-l, cs2.wght[-l])], key=lambda pair: pair[1])

                    if maxp[1] != minp[1]:  # the weights aren't equal
                        wght[maxp[0]] = maxp[1] - minp[1]

                    # saving the remainder
                    remd += minp[1]
                else:
                    # no clash
                    wght[l] = cs1.wght[l]

                seen.add(abs(l))

            # traversing the remainder of 2nd constraints; no clashes
            for l in cs2.lits:
                if abs(l) in seen:
                    continue
                wght[l] = cs2.wght[l]

            # right-hand side of the result constraint
            rbnd = cs1.rbnd + cs2.rbnd - remd

            if wght and rbnd >= 0:
                #  left-hand size of the result constraint
                lits = sorted(wght.keys())

                if len(lits) > len(cs1.lits) and len(lits) > len(cs2.lits):
                    # the result constraint is not valuable -> ignore it
                    continue

                # all good, recording the constraint
                newc.append(['linear', [lits, rbnd, wght]])

                if len(newc) == 100:
                    break

            elif rbnd < 0:  # negative bound signifies unsatisfiability
                            # stopping immediately
                newc = [('linear', [[cs1.lits[0]], 0]), ('linear', [[-cs1.lits[0]], 0])]
                break

        if newc:  # there are some new constraints to add
            for cs in newc:
                # adding constraint to the engine
                cs = self._add_constraint(cs)

                # updating the set of known variables
                self.vset.update(set(abs(l) for l in cs.lits))

            # updating all known variables
            self.vars = sorted(self.vset)

    def process_parity(self):
        """
            Process parity/XOR constraints. Basically, this runs Gaussian
            elimination and see if anything can be derived from it.
        """

        status = True

        # removing None from all sets
        for cs in self.xors:
            cs.lset.remove(None)

        # forward simplification
        for i, csi in enumerate(self.xors):
            v = csi.lits[0]  # pivot variable

            # going over all the other constraints and eliminating the pivot
            for j in range(i + 1, len(self.xors)):
                csj = self.xors[j]

                if v not in csj.lset: # do nothing if pivot var is not present
                    continue

                # summing i'th and j'th constraints up
                csj.lset ^= csi.lset
                csj.rval ^= csi.rval

                if not csj.lset and csj.rval:
                    # inconsistency detected
                    status = False

                    # adding two inconsistent level-0 literals: 1 and -1
                    csi.lits, csj.lits = [1], [-1]
                    csi.zlev, csj.zlev = 1, -1

                    break

                # final result
                csj.lits = sorted(csj.lset)

        if status:
            # back substitution if no inconsistency was detected
            vals = {}
            for i in range(len(self.xors) - 1, -1, -1):
                cs = self.xors[i]

                lits = []
                for l in cs.lits:
                    if l in vals:
                        cs.rval ^= vals[l]  # substitution
                    else:
                        lits.append(l)
                cs.lits = lits

                if len(cs.lits) == 1:  # checking if substitution propagates
                    vals[cs.lits[0]] = cs.rval
                    cs.zlev = cs.lits[0] * (2 * cs.rval - 1)

        # updating the sets of literals and putting None back
        for cs in self.xors:
            cs.lset = set(cs.lits + [None])

    def on_assignment(self, lit, fixed):
        """
            Update the propagator's state given a new assignment.
        """

        self.level[abs(lit)] = self.decision_level

        if self.qhead is None:
            # this is the first assignment we get after backtracking
            # marking that next propagation should start from here
            self.qhead = len(self.trail)

        self.trail.append(lit)

        if fixed:
            self.fixed[abs(lit)] = True

    def on_new_level(self):
        """
            Keep track of decision level updates.
        """

        self.decision_level += 1
        self.trlim.append(len(self.trail))

    def on_backtrack(self, to):
        """
            Cancel all the decisions up to a certain level.
        """

        # undoing the assignments
        while len(self.trlim) > to:
            while len(self.trail) > self.trlim[-1]:
                lit = self.trail.pop()
                var = abs(lit)

                if self.value[var] is not None and not self.fixed[var]:
                    # informing all the constraints
                    for cs in self.wlst[lit]:
                        cs.unassign(lit)

                    self.value[var] = None

                self.level[var] = None

                # cleaning all the consequences
                for l in self.props[lit]:
                    self.origin[l].abandon(l)
                    self.origin[l] = None
                self.props[lit] = []

            self.trlim.pop()

        # updating decision level
        self.decision_level = to

        # updating queue head
        self.qhead = None

    def check_model(self, model):
        """
            Check if a given model satisfies all the constraints.
        """

        st = True  # no falsified constraints by default

        # checking all constraints one by one
        for cs in self.cons:
            if cs.falsified_by(model):
                self.falsified = cs
                st = False
                break

        if self.is_adaptive:
            self.adaptive_update(st)

        return st

    def adaptive_update(self, satisfied):
        """
            Update adaptive mode: either enable or disable the engine. This
            depends on the statistics accumulated in the current run and
            whether or not the previous assignment found by the solver
            satisfied the constraints.
        """

        # decaying increment
        self.pratio = self.pratio / self.pdecay + (self.nprops / self.ncalls if self.ncalls else 0)

        # taking into account whether the current model falsified something
        self.mratio = self.mratio / self.mdecay + (0 if satisfied else 1)

        if satisfied and self.is_active():
            # we are currently active and it does not pay off
            # in terms of propagation; should we slack off a bit?
            if self.pratio < self.pbound:
                self.disable()
        elif not satisfied and not self.is_active():
            # we are currently passive and there are many conflicts
            # let's put more effort into propagation to avoid them?
            if self.mratio > self.mbound:
                self.enable()

        # resetting the moving average stats
        self.nprops = self.ncalls = 0

    def propagate(self):
        """
            Run the propagator given the current assignment.
        """

        result = []

        if self.qhead is not None:
            while self.qhead < len(self.trail):
                lit = self.trail[self.qhead]

                # if we have just propagated an opposite value,
                # we stop and expect conflict analysis to be performed
                if self.origin[-lit] is not None:
                    break

                self.value[abs(lit)] = lit  # actually setting the value

                watched_holes = []
                for csid, cs in enumerate(self.wlst[lit]):
                    # checking the constraint
                    propagated = cs.propagate(lit)

                    # extracting the reason
                    for l in propagated:
                        if self.origin[l] is None:
                            # this literal is currently unknown
                            self.origin[l] = cs

                            # augment the list of entailed literals to return
                            result.append(l)

                            # recording all the dependencies
                            self.props[lit].append(l)

                    # checking whether or not this cs is still watched
                    if self.wlst[lit][csid] is None or type(self.wlst[lit][csid]) == int:
                        # instead of cs, we have None or an integer, i.e. we
                        # removed cs from the watched list for this literal
                        watched_holes.append((csid, self.wlst[lit][csid]))

                # cleaning up watches, should be more-or-less cheap,
                # doing so for +lit but also for -lit if it is affected
                if watched_holes:
                    self.cleanup_watched(lit, watched_holes)

                self.qhead += 1

            if self.is_adaptive:
                # collecting the stats
                self.nprops += len(result)
                self.ncalls += 1
        else:
            # propagating without an assignment
            for cs in self.cons:
                propagated = cs.propagate()

                # extracting the (empty) reason
                for l in propagated:
                    if self.origin[l] is None:
                        # this literal is currently unknown
                        self.origin[l] = cs

                        # augment the list of entailed literals to return
                        result.append(l)

        return result

    def cleanup_watched(self, lit, garbage):
        """
            Garbage collect holes in the watched list for +lit
            (and potentially for -lit).
        """

        otherside = []

        # going backwards, to make it work
        for i in range(len(garbage) - 1, -1, -1):
            pid, nid = garbage[i]

            self.wlst[lit][pid] = self.wlst[lit][-1]
            self.wlst[lit].pop()

            if nid is not None:
                # this one has a negative counterpart
                if pid < len(self.wlst[lit]):
                    # and it's affected
                    self.wlst[lit][pid].wopp[-lit] = pid

                otherside.append(nid)

        # taking care of the negative counterparts (if those are affected)
        for nid in sorted(otherside, reverse=True):
            self.wlst[-lit][nid] = self.wlst[-lit][-1]
            self.wlst[-lit].pop()

            if nid < len(self.wlst[-lit]):
                self.wlst[-lit][nid].wopp[lit] = nid

    def provide_reason(self, lit):
        """
            Return the reason clause for a given literal.
        """

        return [lit] + self.origin[lit].justify(lit)

    def add_clause(self):
        """
            Extract a new clause to add to the solver if one exists; return an
            empty clause ``[]`` otherwise.
        """

        if self.falsified is None:
            return []

        to_add = self.falsified.explain_failure()

        # cleaning the previous failure (currently being added)
        # technically, we should clean self.falsified.fmod too
        # but it should be safe enough not to do so
        self.falsified = None

        return to_add
