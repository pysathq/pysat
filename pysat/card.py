#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## card.py
##
##  Created on: Sep 26, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from pysat.formula import CNF, CNFPlus
import pycard
import signal

#
#==============================================================================
class NoSuchEncodingError(Exception):
    pass


#
#==============================================================================
class EncType(object):
    """
        Encoding types.
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
        Create a CNF formula encoding a cardinality constraint.
    """

    @classmethod
    def atmost(cls, lits, bound=1, top_id=None, encoding=EncType.seqcounter):
        """
            Create an AtMostK constraint.
        """

        assert 0 <= encoding <= 9, 'Wrong encoding type'

        if not top_id:
            top_id = max(map(lambda x: abs(x), lits))

        # we are going to return this formula
        ret = CNFPlus()

        # Minicard's native representation is handled separately
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
            Create an AtLeastK constraint.
        """

        assert 0 <= encoding <= 9, 'Wrong encoding type'

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
            Create an EqualsK constraint.
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
        Iterative totalizer.
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

        # this newly created totalizer object is not yet merged in any other
        self._merged = False

        if lits:
            self.new(lits=lits, ubound=ubound, top_id=top_id)

    def new(self, lits=[], ubound=1, top_id=None):
        """
            Create a new totalizer object.
        """

        self.lits = lits
        self.ubound = ubound
        self.top_id = max(map(lambda x: abs(x), self.lits + [top_id]))

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
            Destroy a totalizer object.
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
            Increase a possible upper bound (right-hand side) in an existing
            totalizer object.
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
            Add more input literals to an existing totalizer object.
        """

        # preparing a new list of distinct input literals
        lits = list(set(lits).difference(set(self.lits)))

        if not lits:
            # nothing to merge with -> just increase the bound
            if ubound:
                self.increase(ubound=ubound, top_id=top_id)

            return

        self.top_id = max(self.top_id, top_id)
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
            Merge with another totalizer tree.
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
