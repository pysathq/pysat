#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## process.py
##
##  Created on: Jan 17, 2023
##      Author: Christos Karamanos
##      E-mail: karamanos.christos@gmail.com
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Processor

    ==================
    Module description
    ==================

    This module provides access to the preprocessor functionality of `CaDiCaL
    1.5.3 <https://github.com/arminbiere/cadical>`__. It can be used to
    process [1]_ (also see references therein) a given CNF formula and output
    a another formula, which is guaranteed to be *equisatisfiable* with the
    original formula. The processor can be invoked for a user-provided number
    of rounds. Also, the following preprocessing techniques can be used when
    running the processor:

    -  blocked clause elimination
    -  covered clause elimination
    -  globally-blocked clause elimination
    -  equivalent literal substitution
    -  bounded variable elimination
    -  failed literal probing
    -  hyper binary resolution
    -  clause subsumption
    -  clause vivification

    .. [1] Armin Biere, Matti Järvisalo, Benjamin Kiesl. *Preprocessing in SAT
        Solving*. In *Handbook of Satisfiability - Second Edition*. pp. 391-435

    Importantly, the module provides a user with a possibility to freeze some
    of the formula's variables so that they aren't eliminated, which may be
    useful when unsatisfiability preserving processing is required - usable in
    MCS and MUS enumeration as well as MaxSAT solving.

    Note that the numerous parameters used in CaDiCaL for tweaking the
    preprocessor's behavior are currently unavailable here. (Default values
    are used.)

    .. code-block:: python

        >>> from pysat.formula import CNF
        >>> from pysat.process import Processor
        >>> from pysat.solvers import Solver
        >>>
        >>> cnf = CNF(from_clauses=[[1, 2], [3, 2], [-1, 4, -2], [3, -2], [3, 4]])
        >>> processor = Processor(bootstrap_with=cnf)
        >>>
        >>> processed = processor.process()
        >>> print(processed.clauses)
        []
        >>> print(processed.status)
        True
        >>>
        >>> with Solver(bootstrap_with=processed) as solver:
        ...     solver.solve()
        True
        ...     print('proc model:', solver.get_model())
        proc model: []
        ...     print('orig model:', processor.restore(solver.get_model()))
        orig model: [1, -2, 3, -4]
        >>>
        >>> processor.delete()

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from pysat.formula import CNF
from pysat.solvers import Cadical153


#
#==============================================================================
class Processor(object):
    """
        This class provides interface to CaDiCaL's preprocessor. The only
        input parameter is ``bootstrap_with``, which is expected to be a
        :class:`.CNF` formula or a list (or iterable) of clauses.

        :param bootstrap_with: a list of clauses for processor initialization.
        :type bootstrap_with: :class:`.CNF` or iterable(iterable(int))

        Once created and used, a processor must be deleted with the
        :meth:`delete` method. Alternatively, if created using the ``with``
        statement, deletion is done automatically when the end of the ``with``
        block is reached. It is *important* to keep the processor if a user
        wants to restore a model of the original formula.

        The main methods of this class are :meth:`process` and
        :meth:`restore`. The former calls CaDiCaL's preprocessor while the
        latter can be used to reconstruct a model of the original formula
        given a model for the processed formula as illustrated below.

        Note how keeping the :class:`Processor` object is needed for model
        restoration. (If it is deleted, the information needed for model
        reconstruction is lost.)

        .. code-block:: python

            >>> from pysat.process import Processor
            >>> from pysat.solvers import Solver
            >>>
            >>> processor = Processor(bootstrap_with=[[-1, 2], [1, -2]])
            >>> processor.append_formula([[-2, 3], [1]])
            >>> processor.add_clause([-3, 4])
            >>>
            >>> processed = processor.process()
            >>> print(processed.clauses)
            []
            >>> print(processed.status)
            True
            >>>
            >>> with Solver(bootstrap_with=processed) as solver:
            ...     solver.solve()
            True
            ...     print('proc model:', solver.get_model())
            proc model: []
            ...     print('orig model:', processor.restore(solver.get_model()))
            orig model: [1, 2, 3, 4]
            >>>
            >>> processor.delete()
    """

    def __init__(self, bootstrap_with=None):
        """
            Basic constructor.
        """

        # immediately creating a CaDiCaL object
        self.cadical = Cadical153()

        # status of processor is True by default meaning
        # that the input formula *is not* unsatisfiable
        self.status = True

        if bootstrap_with:
            self.append_formula(bootstrap_with)

    def __del__(self):
        """
            Default destructor.
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
            Actual destructor.
        """

        if self.cadical:
            self.cadical.delete()
            self.cadical = None

    def add_clause(self, clause):
        """
            Add a single clause to the processor.

            :param clause: a clause to add
            :type clause: list(int) or any iterable(int)

            .. code-block:: python

                >>> processor = Processor()
                >>> processor.add_clause([-1, 2, 3])
        """

        if self.cadical:
            self.cadical.add_clause(clause)

    def append_formula(self, formula):
        """
            Add a given list of clauses into the solver.

            :param formula: a list of clauses.
            :type formula: iterable(iterable(int)), or :class:`.CNF`

            .. code-block:: python

                >>> cnf = CNF()
                ... # assume the formula contains clauses
                >>> processor = Processor()
                >>> processor.append_formula(cnf)
        """

        if self.cadical:
            self.cadical.append_formula(formula)

    def process(self, rounds=1, block=False, cover=False, condition=False,
                decompose=True, elim=True, probe=True, probehbr=True,
                subsume=True, vivify=True, freeze=[]):
        """
            Runs CaDiCaL's preprocessor for the internal formula for a given
            number of rounds and using the techniques specified in the
            arguments. Note that the default values of all the arguments used
            are set as in the default configuration of CaDiCaL 1.5.3.

            As the result, the method returns a :class:`.CNF` object
            containing the processed formula. Additionally to the clauses, the
            formula contains a ``status`` variable, which is set to ``False``
            if the preprocessor found the original formula to be unsatisfiable
            (and ``True`` otherwise). The same status value is set to the
            ``status`` variable of the processor itself.

            It is important to note that activation of some of the
            preprocessing techniques conditionally depends on the activation
            of other preprocessing techniques. For instance, subsumed, blocked
            and covered clause elimination is invoked only if bounded variable
            elimination is active. Subsumption elimination in turn may trigger
            vivification and transitive reduction if the corresponding flags
            are set.

            Finally, note that the ``freeze`` argument can be used to keep
            some of the variables of the original formula unchanged during
            preprocessing. If convenient, the list may contain literals too
            (negative integers).

            :param rounds: number of preprocessing rounds
            :type rounds: int

            :param block: apply blocked clause elimination
            :type block: bool

            :param cover: apply covered clause elimination
            :type cover: bool

            :param condition: detect conditional autarkies and apply globally-blocked clause elimination
            :type condition: bool

            :param decompose: detect strongly connected components (SCCs) in the binary implication graph (BIG) and apply equivalent literal substitution (ELS)
            :type decompose: bool

            :param elim: apply bounded variable elimination
            :type elim: bool

            :param probe: apply failed literal probing
            :type probe: bool

            :param probehbr: learn hyper binary resolvents while probing
            :type probehbr: bool

            :param subsume: apply global forward clause subsumption
            :type subsume: bool

            :param vivify: apply clause vivification
            :type vivify: bool

            :param freeze: a list of variables / literals to be kept during preprocessing
            :type freeze: list(int) or any iterable(int)

            :return: processed formula
            :rtype: :class:`.CNF`

            .. code-block:: python

                >>> from pysat.process import Processor
                >>>
                >>> processor = Processor(bootstrap_with=[[-1, 2], [-2, 3], [-1, -3]])
                >>> processor.add_clause([1])
                >>>
                >>> processed = processor.process()
                >>> print(processed.clauses)
                [[]]
                >>> print(processed.status)
                False  # this means the processor decided the formula to be unsatisfiable
                >>>
                >>> with Solver(bootstrap_with=processed) as solver:
                ...     solver.solve()
                False
                >>> processor.delete()
        """

        if self.cadical:
            self.status, result = self.cadical.process(rounds, block, cover,
                                                       condition, decompose,
                                                       elim, probe, probehbr,
                                                       subsume, vivify,
                                                       freeze)

            # making the status Boolean
            self.status = False if self.status == 20 else True

            # saving it in the output formula
            result = CNF(from_clauses=result)
            result.status = self.status

            return result

    def get_status(self):
        """
            Preprocessor's status as the result of the previous call to
            :meth:`process()`. A ``False`` status indicates that the formula
            is found to be unsatisfiable by the preprocessor. Otherwise, the
            status equals ``True``.

            :rtype: bool
        """

        return self.status

    def restore(self, model):
        """
            Reconstruct a model for the original formula given a model for the
            processed formula. Done by using CaDiCaL's extend() and
            reconstruction stack functionality.

            :param model: a model for the preprocessed formula
            :type model: iterable(int)

            :return: extended model satisfying the original formula
            :rtype: list(int)

            .. code-block:: python

                >>> from pysat.process import Processor
                >>>
                >>> with Processor(bootstrap_with=[[-1, 2], [-2, 3]]) as proc:
                ...     proc.add_clause([1])
                ...     processed = proc.process()
                ...     with Solver(bootstrap_with=processed) as solver:
                ...         solver.solve()
                ...         print('model:', proc.restore(solver.get_model()))
                ...
                model: [1, 2, 3]
        """

        assert self.status, 'Cannot restore a model for an unsatisfiable formula!'

        if self.cadical:
            return self.cadical.restore(model)
