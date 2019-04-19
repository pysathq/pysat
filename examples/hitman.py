#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## hitman.py
##
##      A minimum/minimal hitting set enumerator based on MaxSAT solving
##      and also MCS enumeration (LBX- or CLD-like). MaxSAT-based hitting
##      set enumeration computes hitting sets in a sorted manner, e.g. from
##      smallest size to largest size. MCS-based hitting set solver computes
##      arbitrary hitting sets, with no respect to their size.
##
##  Created on: Aug 23, 2018
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Hitman

    ==================
    Module description
    ==================

    A SAT-based implementation of an implicit minimal hitting set [1]_
    enumerator. The implementation is capable of computing/enumerating
    cardinality- and subset-minimal hitting sets of a given set of sets.
    Cardinality-minimal hitting set enumeration can be seen as ordered (sorted
    by size) subset-minimal hitting enumeration.

    The minimal hitting set problem is trivially formulated as a MaxSAT formula
    in WCNF, as follows. Assume :math:`E=\{e_1,\ldots,e_n\}` to be a universe
    of elements. Also assume there are :math:`k` sets to hit:
    :math:`s_i=\{e_{i,1},\ldots,e_{i,j_i}\}` s.t. :math:`e_{i,l}\in E`. Every
    set :math:`s_i=\{e_{i,1},\ldots,e_{i,j_i}\}` is translated into a hard
    clause :math:`(e_{i,1} \\vee \ldots \\vee e_{i,j_i})`. This results in the
    set of hard clauses having size :math:`k`. The set of soft clauses
    comprises unit clauses of the form :math:`(\\neg{e_{j}})` s.t.
    :math:`e_{j}\in E`, each having weight 1.

    Taking into account this problem formulation as MaxSAT, ordered hitting
    enumeration is done with the use of the state-of-the-art MaxSAT solver
    called :class:`.RC2` [2]_ [3]_ [4]_ while unordered hitting set enumeration
    is done through the *minimal correction subset* (MCS) enumeration, e.g.
    using the :class:`.LBX`- [5]_ or :class:`.MCSls`-like [6]_ MCS enumerators.

    .. [1] Erick Moreno-Centeno, Richard M. Karp. *The Implicit Hitting Set
        Approach to Solve Combinatorial Optimization Problems with an
        Application to Multigenome Alignment*. Operations Research 61(2). 2013.
        pp. 453-468

    .. [2] António Morgado, Carmine Dodaro, Joao Marques-Silva. *Core-Guided
        MaxSAT with Soft Cardinality Constraints*. CP 2014. pp. 564-573

    .. [3] António Morgado, Alexey Ignatiev, Joao Marques-Silva. *MSCG: Robust
        Core-Guided MaxSAT Solving*. JSAT 9. 2014. pp. 129-134

    .. [4] Alexey Ignatiev, António Morgado, Joao Marques-Silva. *RC2: a
        Python-based MaxSAT Solver*. MaxSAT Evaluation 2018. p. 22

    .. [5] Carlos Mencía, Alessandro Previti, Joao Marques-Silva.
        *Literal-Based MCS Extraction*. IJCAI. 2015. pp. 1973-1979

    .. [6] Joao Marques-Silva, Federico Heras, Mikolás Janota,
        Alessandro Previti, Anton Belov. *On Computing Minimal Correction
        Subsets*. IJCAI. 2013. pp. 615-622

    :class:`Hitman` supports hitting set enumeration in the *implicit* manner,
    i.e. when sets to hit can be added on the fly as well as hitting sets can
    be blocked on demand.

    An example usage of :class:`Hitman` through the Python ``import`` interface
    is shown below. Here we target unordered subset-minimal hitting set
    enumeration.

    .. code-block:: python

        >>> from pysat.examples.hitman import Hitman
        >>>
        >>> h = Hitman(solver='m22', htype='lbx')
        >>> # adding sets to hit
        >>> h.hit([1, 2, 3])
        >>> h.hit([1, 4])
        >>> h.hit([5, 6, 7])
        >>>
        >>> h.get()
        [1, 5]
        >>>
        >>> h.block([1, 5])
        >>>
        >>> h.get()
        [2, 4, 5]
        >>>
        >>> h.delete()

    Enumerating cardinality-minimal hitting sets can be done as follows:

    .. code-block:: python

        >>> from pysat.examples.hitman import Hitman
        >>>
        >>> sets = [[1, 2, 3], [1, 4], [5, 6, 7]]
        >>> with Hitman(bootstrap_with=sets, htype='sorted') as hitman:
        ...     for hs in hitman.enumerate():
        ...         print hs
        ...
        [1, 5]
        [1, 6]
        [1, 7]
        [3, 4, 7]
        [2, 4, 7]
        [3, 4, 6]
        [3, 4, 5]
        [2, 4, 6]
        [2, 4, 5]

    Finally, implicit hitting set enumeration can be used in practical problem
    solving. As an example, let us show the basic flow of a MaxHS-like [7]_
    algorithm for MaxSAT:

    .. code-block:: python

        >>> from pysat.examples.hitman import Hitman
        >>> from pysat.solvers import Solver
        >>>
        >>> hitman = Hitman(htype='sorted')
        >>> oracle = Solver()
        >>>
        >>> # here we assume that the SAT oracle
        >>> # is initialized with a MaxSAT formula,
        >>> # whose soft clauses are extended with
        >>> # selector literals stored in "sels"
        >>> while True:
        ...     hs = hitman.get()  # hitting the set of unsatisfiable cores
        ...     ts = set(sels).difference(set(hs))  # soft clauses to try
        ...
        ...     if oracle.solve(assumptions=ts):
        ...         print 's OPTIMUM FOUND'
        ...         print 'o', len(hs)
        ...         break
        ...     else:
        ...         core = oracle.get_core()
        ...         hitman.hit(core)

    .. [7] Jessica Davies, Fahiem Bacchus. *Solving MAXSAT by Solving a
        Sequence of Simpler SAT Instances*. CP 2011. pp. 225-239

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from pysat.formula import IDPool, WCNF
from pysat.examples.rc2 import RC2
from pysat.examples.lbx import LBX
from pysat.examples.mcsls import MCSls
import six


#
#==============================================================================
class Hitman(object):
    """
        A cardinality-/subset-minimal hitting set enumerator. The enumerator
        can be set up to use either a MaxSAT solver :class:`.RC2` or an MCS
        enumerator (either :class:`.LBX` or :class:`.MCSls`). In the former
        case, the hitting sets enumerated are ordered by size (smallest size
        hitting sets are computed first), i.e. *sorted*. In the latter case,
        subset-minimal hitting are enumerated in an arbitrary order, i.e.
        *unsorted*.

        This is handled with the use of parameter ``htype``, which is set to be
        ``'sorted'`` by default. The MaxSAT-based enumerator can be chosen by
        setting ``htype`` to one of the following values: ``'maxsat'``,
        ``'mxsat'``, or ``'rc2'``. Alternatively, by setting it to ``'mcs'`` or
        ``'lbx'``, a user can enforce using the :class:`.LBX` MCS enumerator.
        If ``htype`` is set to ``'mcsls'``, the :class:`.MCSls` enumerator is
        used.

        In either case, an underlying problem solver can use a SAT oracle
        specified as an input parameter ``solver``. The default SAT solver is
        Glucose3 (specified as ``g3``, see :class:`.SolverNames` for details).

        Objects of class :class:`Hitman` can be bootstrapped with an iterable
        of iterables, e.g. a list of lists. This is handled using the
        ``bootstrap_with`` parameter. Each set to hit can comprise elements of
        any type, e.g. integers, strings or objects of any Python class, as
        well as their combinations. The bootstrapping phase is done in
        :func:`init`.

        :param bootstrap_with: input set of sets to hit
        :param solver: name of SAT solver
        :param htype: enumerator type

        :type bootstrap_with: iterable(iterable(obj))
        :type solver: str
        :type htype: str
    """

    def __init__(self, bootstrap_with=[], solver='g3', htype='sorted'):
        """
            Constructor.
        """

        # hitting set solver
        self.oracle = None

        # name of SAT solver
        self.solver = solver

        # hitman type: either a MaxSAT solver or an MCS enumerator
        if htype in ('maxsat', 'mxsat', 'rc2', 'sorted'):
            self.htype = 'rc2'
        elif htype in ('mcs', 'lbx'):
            self.htype = 'lbx'
        else:  # 'mcsls'
            self.htype = 'mcsls'

        # pool of variable identifiers (for objects to hit)
        self.idpool = IDPool()

        # initialize hitting set solver
        self.init(bootstrap_with)

    def __del__(self):
        """
            Destructor.
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

    def init(self, bootstrap_with):
        """
            This method serves for initializing the hitting set solver with a
            given list of sets to hit. Concretely, the hitting set problem is
            encoded into partial MaxSAT as outlined above, which is then fed
            either to a MaxSAT solver or an MCS enumerator.

            :param bootstrap_with: input set of sets to hit
            :type bootstrap_with: iterable(iterable(obj))
        """

        # formula encoding the sets to hit
        formula = WCNF()

        # hard clauses
        for to_hit in bootstrap_with:
            to_hit = list(map(lambda obj: self.idpool.id(obj), to_hit))

            formula.append(to_hit)

        # soft clauses
        for obj_id in six.iterkeys(self.idpool.id2obj):
            formula.append([-obj_id], weight=1)

        if self.htype == 'rc2':
            # using the RC2-A options from MaxSAT evaluation 2018
            self.oracle = RC2(formula, solver=self.solver, adapt=False,
                    exhaust=True, trim=5)
        elif self.htype == 'lbx':
            self.oracle = LBX(formula, solver_name=self.solver, use_cld=True)
        else:
            self.oracle = MCSls(formula, solver_name=self.solver, use_cld=True)

    def delete(self):
        """
            Explicit destructor of the internal hitting set oracle.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

    def get(self):
        """
            This method computes and returns a hitting set. The hitting set is
            obtained using the underlying oracle operating the MaxSAT problem
            formulation. The computed solution is mapped back to objects of the
            problem domain.

            :rtype: list(obj)
        """

        model = self.oracle.compute()

        if model:
            if self.htype == 'rc2':
                # extracting a hitting set
                self.hset = filter(lambda v: v > 0, model)
            else:
                self.hset = model

            return list(map(lambda vid: self.idpool.id2obj[vid], self.hset))

    def hit(self, to_hit):
        """
            This method adds a new set to hit to the hitting set solver. This
            is done by translating the input iterable of objects into a list of
            Boolean variables in the MaxSAT problem formulation.

            :param to_hit: a new set to hit
            :type to_hit: iterable(obj)
        """

        # translating objects to variables
        to_hit = list(map(lambda obj: self.idpool.id(obj), to_hit))

        # a soft clause should be added for each new object
        new_obj = list(filter(lambda vid: vid not in self.oracle.vmap.e2i, to_hit))

        # new hard clause
        self.oracle.add_clause(to_hit)

        # new soft clauses
        for vid in new_obj:
            self.oracle.add_clause([-vid], 1)

    def block(self, to_block):
        """
            The method serves for imposing a constraint forbidding the hitting
            set solver to compute a given hitting set. Each set to block is
            encoded as a hard clause in the MaxSAT problem formulation, which
            is then added to the underlying oracle.

            :param to_block: a set to block
            :type to_block: iterable(obj)
        """

        # translating objects to variables
        to_block = list(map(lambda obj: self.idpool.id(obj), to_block))

        # a soft clause should be added for each new object
        new_obj = list(filter(lambda vid: vid not in self.oracle.vmap.e2i, to_block))

        # new hard clause
        self.oracle.add_clause([-vid for vid in to_block])

        # new soft clauses
        for vid in new_obj:
            self.oracle.add_clause([-vid], 1)

    def enumerate(self):
        """
            The method can be used as a simple iterator computing and blocking
            the hitting sets on the fly. It essentially calls :func:`get`
            followed by :func:`block`. Each hitting set is reported as a list
            of objects in the original problem domain, i.e. it is mapped back
            from the solutions over Boolean variables computed by the
            underlying oracle.

            :rtype: list(obj)
        """

        done = False
        while not done:
            hset = self.get()

            if hset != None:
                self.block(hset)
                yield hset
            else:
                done = True
