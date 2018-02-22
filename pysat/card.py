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
from pysat.formula import CNFPlus
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

        return res1


#
#==============================================================================
class ITotalizer(object):
    pass
