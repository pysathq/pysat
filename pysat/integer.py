#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## integer.py
##
##  Created on: Jan 27, 2026
##      Author: Alexey Ignatiev
##      E-mail: alexey.ignatiev@monash.edu
##

"""
    ===============
    List of classes
    ===============

    .. autosummary::
        :nosignatures:

        Integer
        LinearExpr
        IntegerEngine

    ==================
    Module description
    ==================

    This module provides a small set of *experimental modelling and solving
    techniques* for finite-domain integer variables and linear constraints,
    implemented on top of :class:`.BooleanEngine`. Integer variables are
    encoded into Boolean literals, while integer linear constraints are
    translated into Boolean linear (pseudo-Boolean) constraints with
    non-negative weights. Domain constraints are clausified into CNF clauses
    and can be added directly to the SAT solver; the propagator is used only
    for the remaining linear constraints.

    The implementation is intentionally lightweight and aims to be *simple*
    and *illustrative*, providing working solutions that can be extended over
    time. It is **not** a full-featured CP solver and is not meant to be
    competitive with state-of-the-art CP or SMT tooling. It can serve
    educational and prototyping purposes and may evolve into a more complete
    front-end as (and if) additional constraints and encodings are added.

    Given an integer variable :math:`x \\in D`, the supported encodings of
    integer domains are:

    -  Direct (value / one-hot) encoding [1]_ where a Boolean literal
       :math:`d_i \\triangleq (x=i)` is introduced for each value :math:`i
       \\in D`. Exactly one value is allowed to be true.

    -  Order (bound) encoding [2]_ [3]_ introduces Boolean literals :math:`o_i
       \\triangleq (x \\geq i)` for each value :math:`i \\in D` representing
       the corresponding thresholds, with monotonicity constraints :math:`o_i
       \\rightarrow o_{i-1}`.

    -  Coupled encoding: both direct and order encodings are present with
       *channeling* clauses :math:`d_i \\leftrightarrow (o_i \\land
       \\neg{o_{i+1}})` linking them [4]_ [5]_, and *no separate one-hot
       constraints* are added for :math:`d_i` because the order chain and
       channeling suffice to imply exactly one value (cf. constraints (3)–(7)
       in [4]_).

    .. [1] T. Walsh. *SAT v CSP*. CP 2000. pp. 441-456

    .. [2] N. Tamura, A. Taga, S. Kitagawa, M. Banbara. *Compiling Finite
        Linear CSP into SAT*. Constraints 2009. vol. 14(2). pp. 254-272

    .. [3] C. Ansótegui and F. Manyà. *Mapping Problems with Finite-Domain
        Variables into Problems with Boolean Variables*. SAT (Selected
        Papers) 2004. pp. 1-15

    .. [4] A. Ignatiev, Y. Izza, P. J. Stuckey, and J. Marques-Silva.
        *Using MaxSAT for Efficient Explanations of Tree Ensembles*.
        AAAI 2022. pp. 3776-3785

    .. [5] T. Walsh. *Permutation Problems and Channelling Constraints*.
        LPAR 2001. pp. 377-391

    .. [6] F. Ulrich-Oltean, P. Nightingale, J. A. Walker. *Learning to
        select SAT encodings for pseudo-Boolean and linear integer
        constraints*. Constraints 2023. vol. 28(3). pp. 397-426

    Encodings can be mixed across variables (and even within the same linear
    constraint), as each variable :math:`x` provides its own translation of a
    term :math:`c \\cdot x`. Assuming the domain of variable :math:`x` is
    :math:`D`, in the case of direct encoding, we have :math:`x = \\sum_{i\\in
    D}{i \\cdot d_i}` and so :math:`c \\cdot x = \\sum_{i\\in D}{c \\cdot i
    \\cdot d_i}`. In the case of order encoding, it holds that :math:`x =
    \\min(D) + \\sum_{i=\\min(D)+1}^{\\max(D)}{o_i}`, so :math:`c \\cdot x = c
    \\cdot \\min(D) + \\sum_{i=\\min(D)+1}^{\\max(D)}{c \\cdot o_i}`. Next, we
    apply the same rule to compute an offset value :math:`shift=-\\min_{i\\in
    D}{(c \\cdot i)}` such that each coefficient is incremented by
    :math:`shift`.

    **Translation of linear constraints** over integer variables roughly
    follows the ideas described in [6]_. Consider a linear constraint over
    integer variables :math:`x_j` with numeric coefficients and the right-hand
    side: :math:`\\sum_j c_j \\cdot x_j \\leq b`. The aim of the
    transformation is to *booleanize* each term :math:`c_j \\cdot x_j` of this
    expression (see the paragraph above) so the whole constraint becomes a
    pseudo-Boolean (PB) constraint: a sum of *non-negative* weights on
    *positive* Boolean literals. The flow is as follows:

    1. Express each integer variable as a Boolean sum using variables \
        :math:`d_i` or :math:`o_i`, depending on the encoding of the \
        domain of :math:`x_j`, i.e. either direct or order.
    2. Multiply the resulting sum by the coefficient :math:`c_j`.
    3. If any resulting weights are negative, which happens when \
        :math:`c_j<0`, add a constant shift so that all weights become \
        non-negative.
    4. Drop all zero-weight literals (there is one per integer variable).

    The final Boolean linear constraint has the form: :math:`\\sum_k w_k
    \\cdot l_k \\leq b'`, where :math:`l_k` are Boolean literals representing
    the integers involved, :math:`w_k > 0` are weights, and :math:`b'` is the
    *shifted* bound.

    Consider an example constraint :math:`x - y \\le 2` with :math:`x` and
    :math:`y` sharing the domain :math:`\\{1,2,3\\}` and assume *direct*
    encoding. Assume Boolean variables :math:`x_i` and :math:`y_i` play the
    role of direct encoding variables :math:`d_i` from above. Observe that
    :math:`x = 1 \\cdot x_1 + 2 \\cdot x_2 + 3 \\cdot x_3` while :math:`-y =
    -1 \\cdot y_1 - 2 \\cdot y_2 - 3 \\cdot y_3`. The shifts for :math:`x` and
    :math:`y` are :math:`-1` and :math:`3`, respectively. The total shift is
    :math:`-1 + 3 = 2`, to be added to the right-hand side. The expressions
    for the terms are updated as follows: :math:`x = 0 \\cdot x_1 + 1 \\cdot
    x_2 + 2 \\cdot x_3` and :math:`-y = 2 \\cdot y_1 + 1 \\cdot y_2 + 0 \\cdot
    y_3`. Removing zero-weight literals results in the final PB constraint:
    :math:`x_2 + 2\\cdot x_3 + 2\\cdot y_1 + y_2 \\leq 4`.

    Consider another example, this time with an order encoding: :math:`x + y
    \\leq 2` with the domain of both :math:`x` and :math:`y` being
    :math:`[1,2]`. Assuming :math:`x_i` and :math:`y_i` play the role of order
    encoding variables :math:`o_i` from above, we have: :math:`x=1 + x_2` and
    :math:`y=1 + y_2`. The shift in both cases is calculated to be :math:`-1`
    totalling to :math:`-2`, to be added to both sides of the inequality.
    Therefore, the final PB constraint is :math:`x_2 + y_2 \\leq 0`.

    The module also includes a minimal expression DSL (see
    :class:`.LinearExpr`) so that constraints can be written in a natural form
    (e.g. ``X + Y <= 4``). Supported syntactic sugar includes ``+``, ``-``,
    unary negation, scalar ``*`` by numeric constants, and comparisons ``<=``,
    ``>=``, ``<``, ``>``, ``==``, ``!=``. Notably **unsupported** are
    variable-variable multiplication, division, modulus, absolute values, and
    reification.

    Integer variables can be declared to operate with either ``'float'`` or
    ``'decimal'`` coefficients, which is handled by the ``numeric``
    parameter. Integer coefficients can be mixed with either mode. However,
    float and decimal coefficients must not be mixed in the same constraints,
    hence one cannot mix integers with float and decimal numeric modes.

    Below is a compact 4x4 Sudoku example (digits 1..4). It demonstrates
    direct-encoded integer variables, AllDifferent constraints, and the use
    of the propagator. This is intentionally lightweight and meant to be
    illustrative.

    .. code-block:: python

        >>> from pysat.integer import Integer, IntegerEngine
        >>> from pysat.solvers import Cadical195
        >>>
        >>> # 4x4 Sudoku (2x2 blocks), 0 denotes empty
        >>> givens = [
        ...     [0, 0, 2, 0],
        ...     [0, 0, 0, 3],
        ...     [0, 1, 0, 0],
        ...     [4, 0, 0, 0],
        ... ]
        >>>
        >>> X = [[Integer(f'x{r}{c}', 1, 4, encoding='direct')
        ...       for c in range(4)] for r in range(4)]
        >>>
        >>> eng = IntegerEngine([v for row in X for v in row], adaptive=False)
        >>>
        >>> # rows and columns
        >>> for r in range(4):
        ...     eng.add_alldifferent(X[r])
        >>> for c in range(4):
        ...     eng.add_alldifferent([X[r][c] for r in range(4)])
        >>>
        >>> # 2x2 blocks
        >>> for br in (0, 2):
        ...     for bc in (0, 2):
        ...         block = [X[r][c] for r in range(br, br + 2)
        ...                           for c in range(bc, bc + 2)]
        ...         eng.add_alldifferent(block)
        >>>
        >>> # clues
        >>> for r in range(4):
        ...     for c in range(4):
        ...         if givens[r][c]:
        ...             eng.add_linear(X[r][c] == givens[r][c])
        >>>
        >>> with Cadical195() as solver:
        ...     solver.connect_propagator(eng)
        ...     eng.setup_observe(solver)
        ...     if solver.solve():
        ...         model = solver.get_model()
        ...         values = eng.decode_model(model)
        ...         for r in range(4):
        ...             row = [values[X[r][c]] for c in range(4)]
        ...             print(row)
        [1, 3, 2, 4]
        [2, 4, 1, 3]
        [3, 1, 4, 2]
        [4, 2, 3, 1]

    ==============
    Module details
    ==============
"""

#
#==============================================================================
from collections import defaultdict
from decimal import Decimal
import math
import numbers

from pysat.card import CardEnc, EncType as CardEncType
from pysat.engines import BooleanEngine
from pysat.formula import CNF, Formula
from pysat.pb import PBEnc, EncType as PBEncType


# importable components
#==============================================================================
__all__ = ['Integer', 'Int', 'LinearExpr', 'IntegerEngine']


#
#==============================================================================
class Integer:
    """
        Finite-domain integer variable with a configurable CNF encoding.

        Supported encodings are:

        - ``'direct'``: one-hot / value encoding
        - ``'order'``: order / bound encoding
        - ``'coupled'``: both encodings with channeling clauses

        Direct encoding uses Boolean literals :math:`d_i \\triangleq (x=i)`
        for each value :math:`i` in the domain and a cardinality encoding to
        enforce that exactly one value is chosen. Order encoding introduces
        Boolean literals :math:`o_i \\triangleq (x\\ge i)` and adds
        monotonicity implications between them. Coupled encoding mixes the two
        types of literals but **omits** explicit one-hot constraints for
        :math:`d_i` since the order chain plus channeling already imply
        exactly one value.

        :param name: variable name
        :param lb: lower bound
        :param ub: upper bound
        :param encoding: domain encoding ('direct', 'order', or 'coupled')
        :param card_enc: cardinality encoding for the direct encoding (ignored for coupled encoding)
        :param vpool: external variable pool (optional)
        :param numeric: numeric mode ('float' or 'decimal')

        :type name: str
        :type lb: int
        :type ub: int
        :type encoding: str
        :type card_enc: int
        :type vpool: :class:`pysat.formula.IDPool` or None
        :type numeric: str

        Example:

        .. code-block:: python

            >>> from pysat.integer import Integer
            >>> X = Integer('X', 0, 3, encoding='direct')
            >>> Y = Integer('Y', 0, 3, encoding='order')
            >>> c1 = X + Y <= 4
            >>> c2 = X - Y >= 1
            >>> print(c1)
            ('linear', [[2, 3, 4, 5, 6, 7], 4, {2: 1, 3: 2, 4: 3, 5: 1, 6: 1, 7: 1}])
            >>> print(c2)
            ('linear', [[1, 2, 3, 5, 6, 7], 2, {1: 3, 2: 2, 3: 1, 5: 1, 6: 1, 7: 1}])

        .. note::

            Integer coefficients attached to the variables can be mixed with
            either numeric mode. Mixing floats with decimals raises
            ``TypeError``.
    """

    def __init__(self, name, lb, ub, encoding='direct',
                 card_enc=CardEncType.seqcounter, vpool=None,
                 numeric='float'):
        """
            Constructor.
        """

        # some common-sense assumptions
        assert lb <= ub, 'Lower bound cannot be greater than upper bound'
        assert encoding in ('direct', 'order', 'coupled'), f'Unknown encoding {encoding}'
        assert numeric in ('float', 'decimal'), f'Unknown numeric mode {numeric}'

        self.name = name
        self.lb = lb
        self.ub = ub
        self.domain = list(range(lb, ub + 1))
        self.encoding = encoding
        self.card_enc = card_enc
        self.numeric = numeric
        self.clauses = None

        # deciding which IDPool to use
        self.vpool = vpool if vpool is not None else Formula.export_vpool()

        # ensure IDs are registered upfront to keep vpool stable
        if encoding in ('direct', 'coupled'):
            for v in self.domain:
                self.vpool.id((self, 'eq', v))
        if encoding in ('order', 'coupled'):
            for k in range(lb + 1, ub + 1):
                self.vpool.id((self, 'ge', k))

    def _coerce_number(self, value):
        """
            Coerce a numeric (coefficient) value to the variable's numeric
            mode.

            Integers are accepted in both modes. Mixing floats with decimals
            is not allowed and raises ``TypeError``.
        """

        if self.numeric == 'decimal':
            if isinstance(value, Decimal):
                return value
            if isinstance(value, numbers.Integral):
                return Decimal(value)
            raise TypeError('Decimal mode does not accept non-decimal values')

        if isinstance(value, Decimal):
            raise TypeError('Float mode does not accept Decimal values')
        if isinstance(value, numbers.Real):
            return value
        raise TypeError('Numeric value expected')

    def equals(self, value):
        """
            Return the Boolean literal corresponding to :math:`x = value`.

            Only available with the direct (or coupled) encoding.

            :param value: domain value
            :type value: int

            :rtype: int
        """

        assert self.encoding in ('direct', 'coupled'), 'Direct encoding is disabled'
        assert self.lb <= value <= self.ub, 'Value is outside the domain'
        return self.vpool.id((self, 'eq', value))

    def ge(self, value):
        """
            Return the literal representing :math:`x \\geq value`.

            Only available with the order (or coupled) encoding.

            :param value: lower bound value
            :type value: int

            :rtype: int
        """

        assert self.encoding in ('order', 'coupled'), 'Order encoding is disabled'
        assert self.lb + 1 <= value <= self.ub, 'Value is outside the order domain'
        return self.vpool.id((self, 'ge', value))

    def atleast(self, value):
        """
            Return the literal representing :math:`x \\geq value`. Same as
            :meth:`ge`.
        """

        return self.ge(value)

    def le(self, value):
        """
            Return the literal representing :math:`x \\leq value`.

            Only available with the order (or coupled) encoding.

            :param value: upper bound value
            :type value: int

            :rtype: int
        """

        assert self.encoding in ('order', 'coupled'), 'Order encoding is disabled'
        assert self.lb <= value <= self.ub - 1, 'Value is outside the order domain'

        # X <= value  <=>  not (X >= value + 1)
        return -self.vpool.id((self, 'ge', value + 1))

    def atmost(self, value):
        """
            Return the literal representing :math:`X \\leq value`.
        """

        return self.le(value)

    def __repr__(self):
        """
            String representation of the variable.
        """

        return f'{self.__class__.__name__}({self.name}, {self.lb}..{self.ub})'

    def __str__(self):
        """
            String representation of the variable.
        """

        return f'{self.name}'

    def __hash__(self):
        """
            Hash by identity to keep Integer usable as dict keys.
        """

        return object.__hash__(self)

    def _as_expr(self):
        """
            Convert the variable to a linear expression.
        """

        return LinearExpr({self: 1}, 0, numeric=self.numeric)

    def __add__(self, other):
        """
            Add a variable to another expression or numeric value.
        """

        return self._as_expr() + other

    def __radd__(self, other):
        """
            Right-add for numeric values and expressions.
        """

        return other + self._as_expr()

    def __sub__(self, other):
        """
            Subtract another expression or numeric value.
        """

        return self._as_expr() - other

    def __rsub__(self, other):
        """
            Right-subtract for numeric values and expressions.
        """

        return other - self._as_expr()

    def __mul__(self, other):
        """
            Multiply by a numeric coefficient.
        """

        try:
            coeff = self._coerce_number(other)
        except TypeError:
            return NotImplemented
        return LinearExpr({self: coeff}, 0, numeric=self.numeric)

    def __rmul__(self, other):
        """
            Right-multiply by a numeric coefficient.
        """

        return self.__mul__(other)

    def __le__(self, other):
        """
            Build a <= constraint against a numeric value.
        """

        return self._as_expr() <= other

    def __ge__(self, other):
        """
            Build a >= constraint against a numeric value.
        """

        return self._as_expr() >= other

    def __lt__(self, other):
        """
            Build a < constraint against a numeric value.
        """

        return self._as_expr() < other

    def __gt__(self, other):
        """
            Build a > constraint against a numeric value.
        """

        return self._as_expr() > other

    def __eq__(self, other):
        """
            Equality comparison against a numeric value or identity check.
        """

        if isinstance(other, Integer):
            return self is other

        return self._as_expr() == other

    def __ne__(self, other):
        """
            Inequality comparison against another Integer variable.
        """

        if isinstance(other, Integer):
            return ('ne', self, other)
        return self._as_expr().__ne__(other)

    def decode(self, model):
        """
            Decode the integer value of the variable given a SAT model
            assigning the Boolean variables encoding the domain.

            :param model: SAT model (list of literals)
            :type model: list(int)

            :rtype: int or None
        """

        def is_satisfied(lit):
            return model[abs(lit) - 1] == lit

        if self.encoding == 'direct':
            for value in self.domain:
                if is_satisfied(self.vpool.id((self, 'eq', value))):
                    return value
            return None

        # for order or coupled encodings,
        # applying binary search, due to monotonicity
        lo, hi = self.lb + 1, self.ub
        value = self.lb

        while lo <= hi:
            mid = (lo + hi) // 2
            if is_satisfied(self.vpool.id((self, 'ge', mid))):
                value = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return value

    def encode(self, value):
        """
            Encode an integer value as a list of true literals.

            For direct encoding, the list contains a single Boolean literal
            :math:`d_i` such that :math:`d_i \\triangleq (x=i)`.

            For order encoding, the list contains at most two Boolean literals
            :math:`o_i` and :math:`\\neg{o_{i+1}}` such that :math:`o_i
            \\triangleq (x \\ge i)` and :math:`o_{i+1} \\triangleq (x \\ge
            i+1)`. For the bound values, only one literal is used.

            :param value: domain value
            :type value: int or None

            :rtype: list(int)
        """

        if value is None:
            return []

        if self.encoding in ('direct', 'coupled'):
            return [self.equals(value)]

        # order encoding: pin value with adjacent bounds
        if self.lb == self.ub:
            # variable has a singleton domain - no variables are created at all
            return []
        if value == self.lb:
            return [-self.ge(self.lb + 1)]
        if value == self.ub:
            return [self.ge(self.ub)]
        return [self.ge(value), -self.ge(value + 1)]

    def domain_clauses(self):
        """
            Return CNF clauses encoding the variable's domain.

            Example:

            .. code-block:: python

                >>> from pysat.integer import Integer
                >>> X = Integer('X', 1, 3, encoding='direct')
                >>> cnf = X.domain_clauses()
                >>> print(cnf)
                [[1, 2, 3], [-1, 4], [-4, 5], [-2, -4], [-2, 5], [-3, -5]]

            :rtype: list(list(int))
        """

        if self.clauses is not None:
            return self.clauses

        # we are going to keep our clauses here
        self.clauses = []

        if self.encoding == 'direct':
            lits = [self.equals(val) for val in self.domain]
            cnf = CardEnc.equals(lits=lits, bound=1, vpool=self.vpool,
                                 encoding=self.card_enc)
            self.clauses.extend(cnf.clauses)

        if self.encoding in ('order', 'coupled'):
            for val in range(self.lb + 2, self.ub + 1):
                self.clauses.append([-self.ge(val), +self.ge(val - 1)])

        if self.encoding == 'coupled':
            self._add_channeling()

        return self.clauses

    def linearize(self, coeff):
        """
            Return a pair (weights, shift) encoding ``coeff * X`` using
            Boolean literals. The sum of weights for a satisfying assignment
            equals ``coeff * X + shift``.

            The shift is the **negative of the minimum value** of ``coeff *
            X`` over the variable's domain. This normalization ensures all
            weights are non-negative (required by :mod:`pysat.pb` and
            :class:`.BooleanEngine`) while preserving equivalence by adjusting
            the bound by the same constant. When the minimum term is 0 (e.g.,
            domain includes 0 with a non-negative coefficient), the shift is 0
            and no adjustment occurs. For order encoding this corresponds to
            ``-coeff * lb`` when ``coeff >= 0`` and ``-coeff * ub`` when
            ``coeff < 0``, derived from the threshold identity for ``X``.

            For direct encoding, this is simply a per-value weight map. For
            example, if :math:`x \\in \\{0, 1, 2\\}` and :math:`2x` is
            requested, then literals for values 0, 1, 2 get weights 0, 2, 4,
            respectively. For order encoding, we use the identity :math:`x =
            lb + \\sum_{k=lb+1}^{ub} (x \\geq k)`.

            :param coeff: coefficient
            :type coeff: int, float, or Decimal

            :rtype: (dict, number)

            Consider an example (direct encoding, :math:`x \\in \\{0,1,2\\}`):

            .. code-block:: python

                >>> x = Integer('X', 0, 2, encoding='direct')
                >>> wmap, shift = x.linearize(-3)
                >>> print(shift)
                6
                >>> # weights correspond to literals [x=0], [x=1], [x=2]
                >>> print([wmap[x.equals(v)] for v in x.domain])
                [6, 3, 0]

            Here the minimum term is ``-3 * 2 = -6``, so the shift is ``6``,
            which makes all weights in the final expression non-negative.

            Consider another example, this time with a negative coefficient:

            .. code-block:: python

                >>> y = Integer('y', 1, 3, encoding='direct')
                >>> wmap, shift = y.linearize(-4)
                >>> print(shift)
                12
                >>> # weights correspond to literals [y=1], [y=2], [y=3]
                >>> print([wmap[y.equals(v)] for v in y.domain])
                [8, 4, 0]

            The minimum term is ``-4 * 3 = -12``, so the shift is ``12``.
        """

        # first, making sure we are using a *compatible* coefficient
        coeff = self._coerce_number(coeff)

        # weights map is going to be stored here
        wmap = defaultdict(lambda: 0)

        if self.encoding in ('order', 'coupled'):
            if coeff >= 0:
                shift = -coeff * self.lb
                for k in range(self.lb + 1, self.ub + 1):
                    wmap[self.ge(k)] += +coeff
            else:
                shift = -coeff * self.ub
                for k in range(self.lb, self.ub):
                    wmap[self.le(k)] += -coeff

        else:  # direct encoding
            shift = -coeff * (self.lb if coeff >= 0 else self.ub)
            for v in self.domain:
                wmap[self.equals(v)] += coeff * v + shift

        return wmap, shift

    def _add_channeling(self):
        """
            Clauses linking direct and order encodings.

            Let :math:`d_i` denote :math:`x=i` and :math:`o_i` denote
            :math:`x \\ge i`. We add the endpoint equivalences

            - :math:`d_{lb} \\leftrightarrow \\neg o_{lb+1}`
            - :math:`d_{ub} \\leftrightarrow o_{ub}`

            and for each interior value :math:`i` in :math:`(lb, ub)`:

            - :math:`d_i \\leftrightarrow (o_i \\land \\neg o_{i+1})`.

            Together with the order chain, these clauses imply that exactly
            one value literal is true, i.e. such a constraint is not
            explicitly added.
        """

        # if the domain is a singleton, we need to
        # make sure the direct variable is set to true
        if self.lb == self.ub:
            self.clauses.append([self.equals(self.lb)])
            return

        # lower end-point
        self.clauses.append([-self.equals(self.lb), -self.ge(self.lb + 1)])
        self.clauses.append([+self.ge(self.lb + 1), +self.equals(self.lb)])

        # upper end-point
        self.clauses.append([-self.equals(self.ub), +self.ge(self.ub)])
        self.clauses.append([-self.ge(self.ub), +self.equals(self.ub)])

        # interior values
        for v in range(self.lb + 1, self.ub):
            self.clauses.append([-self.equals(v), +self.ge(v)])
            self.clauses.append([-self.equals(v), -self.ge(v + 1)])
            self.clauses.append([-self.ge(v), +self.ge(v + 1), +self.equals(v)])


#
#==============================================================================
class Int(Integer):
    """
        This is just an alias for the Integer class.
    """

    pass


#
#==============================================================================
class LinearExpr:
    """
        Minimal linear expression builder for :class:`Integer` with numeric
        coefficients. Supports comparisons against numeric values.

        The resulting comparisons return :class:`.BooleanEngine`-style
        constraints (tuples) that can be passed to
        :meth:`.IntegerEngine.add_linear`. Syntactic sugar supports ``+``,
        ``-``, unary negation, scalar ``*`` by numeric constants, and
        comparisons. Variable-variable multiplication, division, modulus,
        absolute values, and reification are not supported.

        Example:

        .. code-block:: python

            >>> from pysat.integer import Integer
            >>> X = Integer('X', 0, 3)
            >>> Y = Integer('Y', 0, 3, encoding='order')
            >>> c1 = X + Y <= 4
            >>> c2 = 2 * X - Y >= 1
            >>> print(c1)
            ('linear', [[2, 3, 4, 5, 6, 7], 4, {2: 1, 3: 2, 4: 3, 5: 1, 6: 1, 7: 1}])
            >>> print(c2)
            ('linear', [[1, 2, 3, 5, 6, 7], 5, {1: 6, 2: 4, 3: 2, 5: 1, 6: 1, 7: 1}])

        .. note::

            Integer constants (coefficients) can be mixed with either numeric
            mode. Mixing floats with decimals raises ``TypeError``.
    """

    def __init__(self, terms=None, const=0, numeric='float'):
        """
            Constructor.
        """

        self.terms = terms or {}
        self.const = const

        # mode
        self.numeric = numeric

    def _check_numeric(self, numeric):
        """
            Check if the numeric mode is consistent with the current mode.
        """

        if self.numeric != numeric:
            raise ValueError('Mixed numeric modes in linear expression')

    def _coerce_number(self, value):
        """
            Convert a given value to the appropriate numeric type.
        """

        if self.numeric == 'decimal':
            if isinstance(value, Decimal):
                return value
            if isinstance(value, numbers.Integral):
                return Decimal(value)
            raise TypeError('Decimal mode does not accept non-decimal values')

        # float
        if isinstance(value, Decimal):
            raise TypeError('Float mode does not accept Decimal values')
        if isinstance(value, numbers.Real):
            return value

        # well, it's neither decimal not float
        raise TypeError('Numeric value expected')

    def _add_term(self, var, coeff):
        """
            Add a term ``coeff * var`` to the expression.
        """

        if coeff == 0:
            # nothing to add
            return

        # updating the coefficient of this variable
        self.terms[var] = self.terms.get(var, 0) + coeff

        # if we canceled the term by this update
        if self.terms[var] == 0:
            del self.terms[var]

    def bounds(self):
        """
            Compute a (min, max) pair for the expression over variable domains.
        """

        # taking into account the constant term
        minv = self.const
        maxv = self.const

        # computing both ming and max values
        for var, coeff in self.terms.items():
            if coeff >= 0:
                minv += coeff * var.lb
                maxv += coeff * var.ub
            else:
                minv += coeff * var.ub
                maxv += coeff * var.lb

        return minv, maxv

    def __add__(self, other):
        """
            Add a numeric value, variable, or expression.
        """

        # constant numeric value
        try:
            value = self._coerce_number(other)
        except TypeError:
            value = None
        if value is not None:
            return LinearExpr(dict(self.terms), self.const + value,
                              numeric=self.numeric)

        # another Integer
        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            other = other._as_expr()

        # another LinearExpr
        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            res = LinearExpr(dict(self.terms), self.const + other.const,
                             numeric=self.numeric)
            for v, c in other.terms.items():
                res._add_term(v, c)
            return res

        return NotImplemented

    def __radd__(self, other):
        """
            Right-add for numeric values and expressions.
        """

        return self.__add__(other)

    def __sub__(self, other):
        """
            Subtract a numeric value, variable, or expression.
        """

        # constant numeric value
        try:
            value = self._coerce_number(other)
        except TypeError:
            value = None
        if value is not None:
            return LinearExpr(dict(self.terms), self.const - value,
                              numeric=self.numeric)

        # another Integer
        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            other = other._as_expr()

        # another LinearExpr
        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            res = LinearExpr(dict(self.terms), self.const - other.const,
                             numeric=self.numeric)
            for v, c in other.terms.items():
                res._add_term(v, -c)
            return res

        return NotImplemented

    def __rsub__(self, other):
        """
            Right-subtract for numeric values and expressions.
        """

        return (-1) * self + other

    def __mul__(self, other):
        """
            Multiply by a numeric coefficient.
        """

        try:
            value = self._coerce_number(other)
        except TypeError:
            return NotImplemented
        if value == 1:
            return self

        # general case of multiplying by a constant numeric value
        res = LinearExpr({}, self.const * value, numeric=self.numeric)
        for v, c in self.terms.items():
            res.terms[v] = c * value
        return res

    def __rmul__(self, other):
        """
            Right-multiply by a numeric coefficient.
        """

        return self.__mul__(other)

    def __neg__(self):
        """
            Unary negation.
        """

        return (-1) * self

    def __le__(self, other):
        """
            Build a <= constraint against a numeric value.
        """

        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            return (self - other) <= 0

        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            return (self - other) <= 0
        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        terms = [(c, v) for v, c in self.terms.items()]
        return LinearExpr.pb_linear_leq(terms, bound - self.const)

    def __ge__(self, other):
        """
            Build a >= constraint against a numeric value.
        """

        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            return (self - other) >= 0

        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            return (self - other) >= 0
        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        return (-self) <= (-bound)

    def __lt__(self, other):
        """
            Build a < constraint against a numeric value.
        """

        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            return (self - other) <= -1

        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            return (self - other) <= -1
        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        if self.numeric == 'decimal':
            return self <= bound.next_minus()

        return self <= math.nextafter(float(bound), float('-inf'))

    def __gt__(self, other):
        """
            Build a > constraint against a numeric value.
        """

        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            return (self - other) >= 1

        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            return (self - other) >= 1
        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        if self.numeric == 'decimal':
            return self >= bound.next_plus()

        return self >= math.nextafter(float(bound), float('inf'))

    def __eq__(self, other):
        """
            Build an == constraint against a numeric value.

            Returns a list with two inequalities.
        """

        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        return [self <= bound, self >= bound]

    def __ne__(self, other):
        """
            Build a != constraint against another expression or numeric value.
        """

        # other is an integer variable
        if isinstance(other, Integer):
            self._check_numeric(other.numeric)
            other = other._as_expr()

        # other is a linear expression
        if isinstance(other, LinearExpr):
            self._check_numeric(other.numeric)
            return ('ne_linear', self, other)

        # other is a constant number
        try:
            bound = self._coerce_number(other)
        except TypeError:
            return NotImplemented

        return ('ne_linear', self, LinearExpr({}, bound, numeric=self.numeric))

    @staticmethod
    def pb_linear_leq(terms, bound):
        """
            Build a PySAT ``'linear'`` constraint over Boolean variables
            (cardinality / pseudo-Boolean) representing:

                sum_i coeff_i * X_i <= bound

            where the left-hand side of the constraint signifies a list of
            pairs ``(coeff_i, X_i)`` with ``coeff_i`` being a number and
            ``X_i`` being :class:`Integer` and ``bound`` is a number.

            :param terms: terms of the left-hand side
            :param bound: right-hand side

            :type terms: list of pairs ``(coeff, Integer)``
            :type bound: number

            Example:

            .. code-block:: python

                >>> from pysat.integer import Integer, LinearExpr
                >>> X = Integer('X', 0, 2)
                >>> Y = Integer('Y', 0, 2, encoding='order')
                >>> c = LinearExpr.pb_linear_leq([(1, X), (2, Y)], 2)
                >>> print(c)
                ('linear', [[2, 3, 4, 5], 2, {2: 1, 3: 2, 4: 2, 5: 2}])

            :rtype: tuple
        """

        # do nothing if there are no terms
        terms = terms or []

        if terms:
            # checking all the numeric types
            var0 = terms[0][1]
            numeric = var0.numeric
            for _, var in terms:
                if var.numeric != numeric:
                    raise ValueError('Mixed numeric modes in linear expression')
            bound = var0._coerce_number(bound)

        # resulting stuff
        lits, weights, shift = [], {}, 0

        # applying linearization for each term
        for coeff, var in terms:
            wmap, sh = var.linearize(coeff)
            shift += sh

            for lit, wght in wmap.items():
                weights[lit] = weights.get(lit, 0) + wght
                lits.append(lit)

        # dropping zero-weight literals,
        # as they do not affect PB reasoning
        weights = {lit: wght for lit, wght in weights.items() if wght != 0}
        lits = sorted(weights.keys())

        return ('linear', [lits, bound + shift, weights])


#
#==============================================================================
class IntegerEngine(BooleanEngine):
    """
        Thin wrapper around :class:`.BooleanEngine`: converts integer
        constraints to pseudo-Boolean linear constraints and delegates
        reasoning to :class:`.BooleanEngine`.

        This is a somewhat experimental, simple and illustrative
        implementation rather than a performance-optimized CP solver.

        Example:

        .. code-block:: python

            >>> from pysat.integer import Integer, IntegerEngine
            >>> from pysat.solvers import Solver
            >>> X = Integer('X', 0, 3)
            >>> Y = Integer('Y', 0, 3)
            >>> eng = IntegerEngine([X, Y], adaptive=True)
            >>> eng.add_linear(X + Y <= 4)
            >>> eng.add_linear(X != Y)
            >>> with Solver(name='cd195') as solver:
            ...     solver.connect_propagator(eng)
            ...     eng.setup_observe(solver)
            ...     while solver.solve():
            ...         model = solver.get_model()
            ...         vals = eng.decode_model(model)
            ...         print('model:', {var.name: value for var, value in vals.items()})
            ...         blits = eng.encode_model(vals)
            ...         solver.add_clause([-l for l in blits])
            model: {'X': 1, 'Y': 0}
            model: {'X': 2, 'Y': 0}
            model: {'X': 0, 'Y': 1}
            model: {'X': 2, 'Y': 1}
            model: {'X': 1, 'Y': 2}
            model: {'X': 0, 'Y': 2}
    """

    def __init__(self, vars=None, constraints=None, adaptive=True, vpool=None):
        """
            Constructor.

            :param vars: :class:`.Integer` variables
            :param constraints: optional constraints to bootstrap with
            :param adaptive: enable adaptive mode in the Boolean engine
            :param vpool: optional shared IDPool for auxiliary variables

            :type vars: list of :class:`.Integer`
            :type constraints: list of :class:`.LinearExpr`
            :type adaptive: bool
            :type vpool: :class:`.IDPool` or None
        """

        # sets for storing encoded and attached variables
        self._venc, self._vatt = set(), set()

        # cache of linear constraints and reified constraints
        self._lcons = []

        # flag to determine whether we've already done setup_observe()
        self._attached = False

        # variables, if any, and their domain clauses
        self.integers, self.clauses = vars or [], []

        # variable manager
        self.vpool = vpool

        # checking related to the vpool
        if self.integers and self.vpool is None:
            self.vpool = self.integers[0].vpool
        if self.vpool is not None:
            for var in self.integers:
                if var.vpool is not self.vpool:
                    raise ValueError('All variables must share the same IDPool')

        # processing all the variables known so far
        for var in self.integers:
            self._encode_domain(var)

        # BooleanEngine's constructor
        super().__init__(bootstrap_with=[], adaptive=adaptive)

        # adding constraints, if any
        for constr in constraints or []:
            self.add_linear(constr)

    def add_var(self, var):
        """
            Add a new integer variable and its domain clauses.

            :param var: integer variable
            :type var: :class:`Integer`
        """

        # first, we need to make sure all variables share the same IDPool
        if self.vpool is None:
            self.vpool = var.vpool
        elif var.vpool is not self.vpool:
            raise ValueError('All variables must share the same IDPool')

        self.integers.append(var)
        self._encode_domain(var)

    def _encode_domain(self, var):
        """
            Cache and add domain clauses for a variable once per engine.
        """

        # do nothing if this variable is already encoded
        if var in self._venc:
            return

        # marking the variable as encoded
        self._venc.add(var)

        # encoding process
        clauses = var.domain_clauses()
        self.clauses.extend(clauses)

        # if we are attached, pass the variable and its clauses to the solver
        if self._attached:
            for cl in clauses:
                self.solver.add_clause(cl)

            self._vatt.add(var)

    def add_linear(self, constraint):
        """
            Add a constraint or a bundle of constraints to the engine.

            Accepts a single :class:`.LinearExpr`-style constraint (e.g. ``X +
            Y <= 4``), a list of such constraints (from ``==``), or a
            :class:`.BooleanEngine`'s ``'linear'`` constraint tuple (or a list
            of them). The ``!=`` operator is supported between Integer
            variables and between linear expressions (via auxiliary Boolean
            variables).

            Note that in the case of variants of :class:`.LinearExpr`
            constraints, those are internally transformed into
            :class:`.BooleanEngine`-style PB constraint first.

            :param constraint: constraint or list of constraints
            :type constraint: LinearExpr | tuple | list
        """

        # it's a '!=' constraint on two Integer variables
        if isinstance(constraint, tuple) and constraint and constraint[0] == 'ne':
            self.add_not_equal(constraint[1], constraint[2])
            return

        # it's a '!=' constraint on two LinearExpr objects
        if isinstance(constraint, tuple) and constraint and constraint[0] == 'ne_linear':
            left, right = constraint[1], constraint[2]
            if not isinstance(left, LinearExpr) or not isinstance(right, LinearExpr):
                raise TypeError('Linear != requires LinearExpr arguments')

            # reified disjunction: (left-right <= -1) or (left-right >= 1)
            diff = left - right
            c1, c2 = diff <= -1, diff >= 1
            s1, s2 = self._reify_linear(c1), self._reify_linear(c2)
            if s1 is None or s2 is None:
                # one side is tautological => disjunction always true
                return

            # enforce the disjunction of s1 or s2
            self.clauses.append([s1, s2])
            if self._attached:
                self.solver.add_clause([s1, s2])

            return

        # a linear constraint or a collection of those
        if isinstance(constraint, (list, tuple)):
            # empty constraint
            if not constraint:
                return

            # a single constraint
            if constraint and isinstance(constraint[0], str):
                self._record_linear(constraint)
                self._add_constraint_internal(constraint)
                return

            # a collection of constraints
            if constraint and all(
                isinstance(c, (list, tuple)) and c and isinstance(c[0], str)
                for c in constraint
            ):
                for c in constraint:
                    self._record_linear(c)
                    self._add_constraint_internal(c)
                return

        raise TypeError('Unsupported constraint type; expected linear tuple or list of tuples')

    def _record_linear(self, constraint):
        """
            Store a linear constraint for later clausification.
        """

        if isinstance(constraint, (list, tuple)) and constraint and constraint[0] == 'linear':
            self._lcons.append(constraint)

    def add_alldifferent(self, vars):
        """
            Add an AllDifferent constraint over variables (for direct/coupled
            encoding only).

            :param vars: variables to be all-different
            :type vars: list(:class:`Integer`)
        """

        # no variables -> nothing to do
        if not vars:
            return

        # every variable must share the same IDPool,
        # and its domainencoding must not be 'order'
        vpool = vars[0].vpool
        for var in vars:
            if var.vpool is not vpool:
                raise ValueError('AllDifferent variables must share the same IDPool')
            if var.encoding not in ('direct', 'coupled'):
                raise ValueError('AllDifferent requires direct or coupled encoding')

        # we care only about the intersection of all domains
        values = set()
        for var in vars:
            values.update(var.domain)

        # modelling all-differents are a bunch of AtMost1 constraints
        for v in values:
            lits = [var.equals(v) for var in vars if v in var.domain]
            if len(lits) > 1:
                self.add_linear(('linear', [lits, 1]))

    def _reify_linear(self, constraint):
        """
            Reify a :class:`.BooleanEngine`'s ``'linear'`` constraint.

            Returns a selector literal ``b`` such that ``b -> constraint``.
            Returns ``None`` if the constraint is tautological.
        """

        # we can verify only BooleanEngine's linears
        if not (isinstance(constraint, tuple) and constraint and constraint[0] == 'linear'):
            raise TypeError('Expected a BooleanEngine linear constraint')

        lits, bound = constraint[1][0], constraint[1][1]
        weights = {} if len(constraint[1]) == 2 else constraint[1][2]

        if not weights:
            weights = {l: 1 for l in lits}
        if any(l not in weights for l in lits):
            raise ValueError('PB encoding requires explicit weights for all literals')

        # computing the key
        ltup = tuple(sorted(lits))
        wtup = tuple(weights[lit] for lit in ltup)
        key = (ltup, wtup, bound)

        max_sum = sum(wtup)
        if bound >= max_sum:
            # the contraint is trivially satisfiable
            return None

        # first, checking if we actually have an IDPool to work with!
        if self.vpool is None:
            self.vpool = Formula.export_vpool()

        if (self, '_reif', key) not in self.vpool.obj2id:
            selv = self.vpool.id((self, '_reif', key))

            if bound < 0:
                # constraint unsatisfiable => selv must be false
                self.clauses.append([-selv])
                if self._attached:
                    self.solver.add_clause([-selv])
                return selv

            # computing selector's weight and recording the literal
            wght = max_sum - bound
            rweights = dict(weights)
            rweights[selv] = wght
            rlits = list(lits) + [selv]

            # creating the actual constraint
            rcons = ('linear', [rlits, bound + wght, rweights])
            self._record_linear(rcons)
            self._add_constraint_internal(rcons)

        return self.vpool.id((self, '_reif', key))

    def add_not_equal(self, left, right):
        """
            Add a not-equal constraint on two :class:`Integer` variables: left
            != right (for direct/coupled encodings only).

            :param left: left variable
            :param right: right variable
            :type left: :class:`Integer`
            :type right: :class:`Integer`
        """

        # common-sense checks first
        if left.vpool is not right.vpool:
            raise ValueError('NotEqual variables must share the same IDPool')
        if left.encoding not in ('direct', 'coupled'):
            raise ValueError('NotEqual requires direct or coupled encoding on left')
        if right.encoding not in ('direct', 'coupled'):
            raise ValueError('NotEqual requires direct or coupled encoding on right')

        # adding CNF clauses for value inequality
        values = set(left.domain).intersection(right.domain)
        for v in values:
            cl = [-left.equals(v), -right.equals(v)]
            self.clauses.append(cl)
            if self._attached:
                self.solver.add_clause(cl)

    def clausify(self, cardenc=CardEncType.seqcounter, pbenc=PBEncType.best):
        """
            Clausify all constraints and return a CNF encoding. All linear
            constraints are converted using the user-specified cardinality and
            pseudo-Boolean encoding. The former are utilized for unweighted
            constraints, while the latter are utilized for weighted
            constraints.

            Note that parameters ``cardenc`` and ``pbenc`` default to
            :attr:`.card.EncType.seqcounter` and
            :class:`pysat.pb.EncType.best`, respectively.

            :param cardenc: cardinality encoding for unweighted constraints
            :param pbenc: PB encoding for weighted constraints
            :type cardenc: int
            :type pbenc: int

            :rtype: :class:`pysat.formula.CNF`
        """

        # we are going to store the resulting formula here
        res = CNF()

        # first, checking if there is work to do
        if not self.integers:
            if self._lcons:
                # it should not happen that we've got constraints but no vars
                raise ValueError('Cannot clausify linear constraints without integer variables')

            # returning an empty formula
            return res

        # making sure all variables share the same IDPool
        vpool = self.integers[0].vpool
        for i in range(1, len(self.integers)):
            if self.integers[i].vpool is not vpool:
                raise ValueError('All variables must share the same IDPool')

        # extracting domain clauses for all the variables
        for var in self.integers:
            res.extend(var.domain_clauses())

        # include any extra CNF clauses (e.g., reified disjunctions)
        res.extend(self.clauses)

        # the main part is to encode all linear constraints
        for cs in self._lcons:
            lits, bound = cs[1][0], cs[1][1]
            weights = {} if len(cs[1]) == 2 else cs[1][2]

            if not weights:
                wght = 1
            else:
                wvals = list(weights.values())
                if len(set(wvals)) == 1:
                    wght = wvals[0]
                else:
                    wght = None

            # we have a common weight wght => cardinality constraint
            if wght is not None:
                new_bound = bound // wght
                if isinstance(new_bound, Decimal):
                    new_bound = int(new_bound)
                elif isinstance(new_bound, float):
                    new_bound = int(math.floor(new_bound))
                else:
                    new_bound = int(new_bound)

                if new_bound < 0:
                    # the bound is negative => constraint is unsatisfiable
                    res.append([])
                    continue
                if new_bound >= len(lits):
                    # the constraint is unfalsifiable
                    continue

                enc = CardEnc.atmost(lits=lits, bound=new_bound, vpool=vpool,
                                     encoding=cardenc)
                res.extend(enc.clauses)
                continue

            # the weights are not all the same => PB constraint
            # first checking the bound and literal weights for being int-like
            if not self._intlike(bound):
                raise ValueError('PB encoding requires integer bound')
            if any(l not in weights for l in lits):
                raise ValueError('PB encoding requires explicit weights for all literals')
            wlist = [weights[l] for l in lits]
            if not all(self._intlike(w) for w in wlist):
                raise ValueError('PB encoding requires integer weights')

            bound_int = int(bound) if not isinstance(bound, Decimal) else int(bound)
            wlist = [int(w) if not isinstance(w, Decimal) else int(w)
                            for w in wlist]

            enc = PBEnc.atmost(lits=lits, weights=wlist, bound=bound_int,
                               vpool=vpool, encoding=pbenc)
            res.extend(enc.clauses)

        return res

    @staticmethod
    def _intlike(value):
        """
            Checking if the value can be converted to integer.
        """

        # yes, nothing to do
        if isinstance(value, numbers.Integral):
            return True

        # yes, it's a convertable decimal
        if isinstance(value, Decimal):
            return value == value.to_integral_value()

        # yes, it's a convertable float
        if isinstance(value, float):
            return value.is_integer()

        # no, we can't convert it
        return False

    def _add_constraint_internal(self, constraint):
        """
            Add a constraint regardless of whether the solver is connected.
        """

        if self.solver is None:
            # the solver does not exist yet, we can't do setup_observe()
            cs = self._add_constraint(constraint)
            cs.register_watched(self.wlst)

            for lit in cs.lits:
                var = abs(lit)
                if var not in self.vset:
                    self.vset.add(var)
                    self.value[var] = None
                    self.level[var] = None
                    self.fixed[var] = False

            # keep the observed variable list in sync before setup_observe()
            self.vars = sorted(self.vset)

            cs.attach_values(self.value)
        else:
            # all good, resorting to BooleanEngine's add_constraint()
            super().add_constraint(constraint)

    @staticmethod
    def pb_linear_leq(terms, bound):
        """
            Convenience wrapper for building a PySAT ``'linear'`` constraint
            (cardinality / pseudo-Boolean) from integer terms. Calls
            :meth:`.LinearExpr.pb_linear_leq`.
        """

        return LinearExpr.pb_linear_leq(terms, bound)

    def setup_observe(self, solver):
        """
            Inform the solver about observed variables and add domain clauses.

            :param solver: SAT solver instance
            :type solver: :class:`pysat.solvers.Cadical195`
        """

        # first, calling BooleanEngine's setup_observe()
        # this is required for registering more Boolean self.vars variables
        # if we managed to create them since last time the method was called
        # note that self.vars is populated by collecting
        # variables appearing in linear constraints only
        super().setup_observe(solver)

        # next, adding domain clauses for all the known variables
        # setup_observe() is to be called once but more
        # variables can be added later through add_var()
        if not self._attached:
            for var in self._venc:
                if var in self._vatt:
                    continue

                for cl in var.domain_clauses():
                    self.solver.add_clause(cl)

                self._vatt.add(var)

            for cl in self.clauses:
                self.solver.add_clause(cl)

            # flagging that setup_observe() has been called
            self._attached = True

    def decode_model(self, model, vars=None):
        """
            Given a SAT model (list of int identifiers), return a mapping
            ``{Integer: integer_value}`` for the engine's integer variables.

            If ``vars`` is provided, decode only those variables.

            Example:

            .. code-block:: python

                >>> model = solver.get_model()
                >>> values = eng.decode_model(model, vars=[X, Y])
                >>> print(values)

            :param model: SAT model (list of literals)
            :param vars: subset of variables to decode (optional)
            :type model: list(int)
            :type vars: list(:class:`Integer`) or None

            :rtype: dict
        """

        res = {}

        # resorting to variables' own ability to derive their values
        for var in vars if vars is not None else self.integers:
            res[var] = var.decode(model)

        return res

    def encode_model(self, model, vars=None):
        """
            Given an integer-level model, return a list of true literals.

            ``model`` can be a dict mapping :class:`Integer` objects
            (preferred) or variable names to values, or a list/tuple of values
            corresponding to ``vars`` (or ``self.integers`` if ``vars`` is
            None).

            This is the inverse of :meth:`.decode_model` at the integer level.

            :param model: integer-level model
            :param vars: variable order for list/tuple models (optional)
            :type model: dict or list
            :type vars: list(:class:`Integer`) or None

            :rtype: list(int)
        """

        # if no target is given, using all variables
        if vars is None:
            vars = self.integers

        # preparing the values list
        if isinstance(model, dict):
            values = []
            for var in vars:
                if var in model:
                    values.append(model[var])
                else:
                    values.append(model.get(var.name))
        else:
            values = list(model)
            if len(values) != len(vars):
                raise ValueError('Model length does not match variables list')

        # the actual translation is done by variables themselves
        lits = []
        for var, value in zip(vars, values):
            lits.extend(var.encode(value))

        return lits

    def decode_assignment(self, lits, vars=None):
        """
            Given a list of assigned Boolean literals, return a mapping
            ``{Integer: integer_value}`` for those variables whose value is
            fixed by the assignment alone. Unlike :meth:`.decode_model`, this
            method does not require a full model and only looks at literals
            present in ``lits``. Also note that the method does not require
            the input literals to be in any particular order.

            If multiple inconsistent *equality* literals are present for the
            same variable, the value is reported as a list of all observed
            values, which (if an issue) can be used to find the culprit in the
            encoding. For order-based literals, if the inferred bounds fix the
            value, the value is reported as an integer; otherwise, the value
            is reported as the list of all values within the inferred bounds.
            If order-based bounds are contradictory (lower bound exceeds upper
            bound), the value is reported as an empty list.

            Example:

            .. code-block:: python

                >>> st, props = solver.propagate(assumptions=clues)
                >>> vals = eng.decode_assignment(props)
                >>> # vals[i] is an int if the value is fixed,
                >>> # a list if conflicting if multiple values are present,
                >>> # or [] if contradictory bounds were derived.

            :param lits: literals in the assignment
            :param vars: subset of variables to decode (optional)
            :type lits: iterable(int)
            :type vars: list(:class:`Integer`) or None

            :rtype: dict
        """

        # don't anything about any variables!
        if self.vpool is None:
            return {}

        # optional filtering by a subset of variables
        allowed = None if vars is None else set(vars)

        # per-variable state tracked only when we see relevant literals
        eq_true, lbounds, ubounds = {}, {}, {}

        seen = set()
        for lit in lits:
            if lit == 0:
                # literal '0' makes no sense
                raise ValueError('Literal 0 is not allowed')

            if lit not in seen:
                seen.add(lit)

                # getting the object given a literal
                obj = self.vpool.obj(abs(lit))

                # we expect a tuple of (var, 'kind', value)
                if not obj or not isinstance(obj, tuple) or len(obj) != 3:
                    # not a variable we know!
                    continue

                var, kind, value = obj
                if not isinstance(var, Integer) or kind not in ('eq', 'ge'):
                    # still not our variable!
                    continue

                # checking if the variable is among those we are interested in
                if allowed is not None and var not in allowed:
                    continue

                if kind == 'eq':
                    if lit > 0:
                        eq_true.setdefault(var, set()).add(value)
                else:  # kind == 'ge'
                    if var not in lbounds:
                        lbounds[var] = var.lb
                        ubounds[var] = var.ub

                    # refining the bounds if we can
                    if lit > 0:
                        if value > lbounds[var]:
                            lbounds[var] = value
                    else:
                        bound = value - 1
                        if bound < ubounds[var]:
                            ubounds[var] = bound

        # now, we are going to collate the data and put it here
        res = {}

        # direct/coupled encodings expose equality literals
        for var, values in eq_true.items():
            if len(values) == 1:
                # taking the concrete value we found
                res[var] = next(iter(values))
            else:
                # multiple values are found
                res[var] = sorted(values)

        # order/coupled encodings may be fixed by bounds alone
        for var in lbounds:
            if var in res:
                # well, we already have a concrete value for this variable
                continue

            if lbounds[var] == ubounds[var]:
                # concrete value defined from the bounds
                res[var] = lbounds[var]

            elif lbounds[var] < ubounds[var]:
                # the bounds represent a valid range
                res[var] = list(range(lbounds[var], ubounds[var] + 1))
            else:
                # conflicting bounds detected; report as an empty list
                # to signal contradiction without raising
                res[var] = []

        return res


# example usage
#==============================================================================
if __name__ == '__main__':
    # example 1: satisfiable, mixed encodings, all constraint types, enumeration
    from decimal import Decimal
    from pysat.solvers import Solver

    X = Integer('X', 0, 3)  # direct
    Y = Integer('Y', 0, 3, encoding='direct')  # direct
    Z = Integer('Z', 0, 3, encoding='coupled') # coupled
    D = Integer('D', 0, 3, numeric='decimal')  # decimal
    E = Integer('E', 0, 3, numeric='decimal')  # decimal

    eng = IntegerEngine([X, Y, Z, D, E], adaptive=False)

    # linear constraints
    eng.add_linear(X + Y <= 4 - Z)
    eng.add_linear(X + Y >= 3)
    eng.add_linear(Z - X <= 1)
    eng.add_linear(X - Z <= 1)

    # not equal and AllDifferent (direct/coupled only)
    eng.add_linear(X != Z)
    eng.add_alldifferent([X, Y, Z])

    # decimal linear constraint
    eng.add_linear(Decimal('1') * D + Decimal('2') * E <= Decimal('3'))
    eng.add_linear(Decimal('1') * D + Decimal('1') * E == Decimal('2'))

    # model enumeration using integer-level blocking
    with Solver(name='cd19', bootstrap_with=None) as solver:
        solver.connect_propagator(eng)
        eng.setup_observe(solver)
        while solver.solve():
            model = solver.get_model()
            vals = eng.decode_model(model)
            print('ENG example:', {var.name: value for var, value in vals.items()})
            blits = eng.encode_model(vals)
            solver.add_clause([-l for l in blits])

    print('')

    # example 2: satisfiable, clausified (same model set as example 1)
    cnf = eng.clausify()
    with Solver(name='g3', bootstrap_with=cnf.clauses) as solver:
        while solver.solve():
            model = solver.get_model()
            vals = eng.decode_model(model)
            print('CNF example:', {var.name: value for var, value in vals.items()})
            blits = eng.encode_model(vals)
            solver.add_clause([-l for l in blits])

    # example 3: should be unsatisfiable
    A = Integer('A', 0, 2)
    B = Integer('B', 0, 2)
    eng2 = IntegerEngine([A, B], adaptive=False)
    eng2.add_linear(A + B <= 1)
    eng2.add_linear(A - B >= 2)

    with Solver(name='cd19', bootstrap_with=None) as solver:
        solver.connect_propagator(eng2)
        eng2.setup_observe(solver)
        sat = solver.solve()
        if sat:
            model = solver.get_model()
            vals = eng2.decode_model(model)
            print('UNSAT example (wrong!):', {var.name: value for var, value in vals.items()})
        else:
            print('UNSAT example: UNSAT')
