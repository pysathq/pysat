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
        A minimum/minimal hitting set enumerator.
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
            Initialize the hitting set solver.
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
            Explicit destructor.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

    def get(self):
        """
            Compute and return a hitting set.
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
            Add a new set to hit.
        """

        # translating objects to variables
        to_hit = list(map(lambda obj: self.idpool.id(obj), to_hit))

        # a soft clause should be added for each new object
        new_obj = filter(lambda vid: vid not in self.oracle.vmap.e2i, to_hit)

        # new hard clause
        self.oracle.add_clause(to_hit)

        # new soft clauses
        for vid in new_obj:
            self.oracle.add_clause([-vid], 1)

    def block(self, to_block):
        """
            Block a set.
        """

        # translating objects to variables
        to_block = list(map(lambda obj: self.idpool.id(obj), to_block))

        # a soft clause should be added for each new object
        new_obj = filter(lambda vid: vid not in self.oracle.vmap.e2i, to_block)

        # new hard clause
        self.oracle.add_clause([-vid for vid in to_block])

        # new soft clauses
        for vid in new_obj:
            self.oracle.add_clause([-vid], 1)

    def enumerate(self):
        """
            Iterator for enumerating hitting sets.
        """

        done = False
        while not done:
            hset = self.get()

            if hset != None:
                self.block(hset)
                yield hset
            else:
                done = True
