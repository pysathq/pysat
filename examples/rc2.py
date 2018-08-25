#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## rc2.py
##
##      Python-based implementation of the OLLITI/RC2 algorithm described in:
##      1. A. Morgado, J. Marques-Silva. CP 2014
##      2. A. Morgado, A. Ignatiev, J. Marques-Silva. JSAT 2015
##      This implementation roughly follows the one of MSCG15.
##
##  Created on: Dec 2, 2017
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import collections
import getopt
import itertools
from math import copysign
import os
from pysat.formula import CNF, WCNF
from pysat.card import ITotalizer
from pysat.solvers import Solver
import re
import six
from six.moves import range
import sys


#
#==============================================================================
class RC2(object):
    """
        MaxSAT algorithm based on relaxable cardinality constraints (RC2/OLL).
    """

    def __init__(self, formula, solver='g3', adapt=False, exhaust=False,
            incr=False, minz=False, trim=0, verbose=0):
        """
            Constructor.
        """

        # saving verbosity level and other options
        self.verbose = verbose
        self.exhaust = exhaust
        self.solver = solver
        self.adapt = adapt
        self.minz = minz
        self.trim = trim

        # clause selectors and mapping from selectors to clause ids
        self.sels, self.smap = [], {}

        # other MaxSAT related stuff
        self.topv = formula.nv
        self.wght = {}  # weights of soft clauses
        self.sums = []  # totalizer sum assumptions
        self.bnds = {}  # a mapping from sum assumptions to totalizer bounds
        self.tobj = {}  # a mapping from sum assumptions to totalizer objects
        self.cost = 0

        # mappings between internal and external variables
        VariableMap = collections.namedtuple('VariableMap', ['e2i', 'i2e'])
        self.vmap = VariableMap(e2i={}, i2e={})

        # initialize SAT oracle with hard clauses only
        self.init(formula, incr=incr)

        # core minimization is going to be extremely expensive
        # for large plain formulas, and so we turn it off here
        wght = self.wght.values()
        if not formula.hard and len(self.sels) > 100000 and min(wght) == max(wght):
            self.minz = False

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

    def init(self, formula, incr=False):
        """
            Initialize the SAT solver.
        """

        # creating a solver object
        self.oracle = Solver(name=self.solver, bootstrap_with=formula.hard,
                incr=incr, use_timer=True)

        # adding soft clauses to oracle
        for i, cl in enumerate(formula.soft):
            selv = cl[0]  # if clause is unit, selector variable is its literal

            if len(cl) > 1:
                self.topv += 1
                selv = self.topv

                cl.append(-self.topv)
                self.oracle.add_clause(cl)

            if selv not in self.wght:
                # record selector and its weight
                self.sels.append(selv)
                self.wght[selv] = formula.wght[i]
                self.smap[selv] = i
            else:
                # selector is not new; increment its weight
                self.wght[selv] += formula.wght[i]

        # storing the set of selectors
        self.sels_set = set(self.sels)

        # at this point internal and external variables are the same
        for v in range(1, formula.nv + 1):
            self.vmap.e2i[v] = v
            self.vmap.i2e[v] = v

        if self.verbose > 1:
            print('c formula: {0} vars, {1} hard, {2} soft'.format(formula.nv,
                len(formula.hard), len(formula.soft)))

    def add_clause(self, clause, weight=None):
        """
            Add a new clause (needed for incremental MaxSAT solving).
        """

        # first, map external literals to internal literals
        # introduce new variables if necessary
        cl = list(map(lambda l: self._map_extlit(l), clause))

        if not weight:
            # the clause is hard, and so we simply add it to the SAT oracle
            self.oracle.add_clause(cl)
        else:
            # soft clauses should be augmented with a selector
            selv = cl[0]  # for a unit clause, no selector is needed

            if len(cl) > 1:
                self.topv += 1
                selv = self.topv

                cl.append(-self.topv)
                self.oracle.add_clause(cl)

            if selv not in self.wght:
                # record selector and its weight
                self.sels.append(selv)
                self.wght[selv] = weight
                self.smap[selv] = len(self.sels) - 1
            else:
                # selector is not new; increment its weight
                self.wght[selv] += weight

            self.sels_set.add(selv)

    def delete(self):
        """
            Explicit destructor.
        """

        if self.oracle:
            self.oracle.delete()
            self.oracle = None

            if self.solver != 'mc':  # for minicard, there is nothing to free
                for t in six.itervalues(self.tobj):
                    t.delete()

    def compute(self):
        """
            Compute and return a solution.
        """

        # simply apply MaxSAT only once
        res = self.compute_()

        if res:
            # extracting a model
            self.model = self.oracle.get_model()
            self.model = filter(lambda l: abs(l) in self.vmap.i2e, self.model)
            self.model = map(lambda l: int(copysign(self.vmap.i2e[abs(l)], l)), self.model)
            self.model = sorted(self.model, key=lambda l: abs(l))

            return self.model

    def enumerate(self):
        """
            Enumerate MaxSAT solutions (from best to worst).
        """

        done = False
        while not done:
            model = self.compute()

            if model != None:
                self.oracle.add_clause([-l for l in model])
                yield model
            else:
                done = True

    def compute_(self):
        """
            Compute a MaxSAT solution with RC2.
        """

        # trying to adapt (simplify) the formula
        # by detecting and using atmost1 constraints
        if self.adapt:
            self.adapt_am1()

        # main solving loop
        while not self.oracle.solve(assumptions=self.sels + self.sums):
            self.get_core()

            if not self.core:
                # core is empty, i.e. hard part is unsatisfiable
                return False

            self.process_core()

            if self.verbose > 1:
                print('c cost: {0}; core sz: {1}; soft sz: {2}'.format(self.cost,
                    len(self.core), len(self.sels) + len(self.sums)))

        return True

    def get_core(self):
        """
            Extract unsatisfiable core.
        """

        # extracting the core
        self.core = self.oracle.get_core()

        if self.core:
            # try to reduce the core by trimming
            self.trim_core()

            # and by heuristic minimization
            self.minimize_core()

            # core weight
            self.minw = min(map(lambda l: self.wght[l], self.core))

            # dividing the core into two parts
            iter1, iter2 = itertools.tee(self.core)
            self.core_sels = list(l for l in iter1 if l in self.sels_set)
            self.core_sums = list(l for l in iter2 if l not in self.sels_set)

    def process_core(self):
        """
            Deal with a core found in the main loop.
        """

        # updating the cost
        self.cost += self.minw

        # assumptions to remove
        self.garbage = set()

        if len(self.core_sels) != 1 or len(self.core_sums) > 0:
            # process selectors in the core
            self.process_sels()

            # process previously introducded sums in the core
            self.process_sums()

            if len(self.rels) > 1:
                # create a new cardunality constraint
                t = self.create_sum()

                # apply core exhaustion if required
                b = self.exhaust_core(t) if self.exhaust else 1

                if b:
                    # save the info about this sum and
                    # add its assumption literal
                    self.set_bound(t, b)
                else:
                    # impossible to satisfy any of these clauses
                    # they must become hard
                    for relv in self.rels:
                        self.oracle.add_clause([relv])
        else:
            # unit cores are treated differently
            # (their negation is added to the hard part)
            self.oracle.add_clause([-self.core_sels[0]])
            self.garbage.add(self.core_sels[0])

        # remove unnecessary assumptions
        self.filter_assumps()

    def adapt_am1(self):
        """
            Try to detect atmost1 constraints involving soft literals.
        """

        # literal connections
        conns = collections.defaultdict(lambda: set([]))
        confl = []

        # prepare connections
        for l1 in self.sels:
            st, props = self.oracle.propagate(assumptions=[l1], phase_saving=2)
            if st:
                for l2 in props:
                    if -l2 in self.sels_set:
                        conns[l1].add(-l2)
                        conns[-l2].add(l1)
            else:
                # propagating this literal results in a conflict
                confl.append(l1)

        if confl:  # filtering out unnecessary connections
            ccopy = {}
            confl = set(confl)

            for l in conns:
                if l not in confl:
                    cc = conns[l].difference(confl)
                    if cc:
                        ccopy[l] = cc

            conns = ccopy
            confl = list(confl)

            # processing unit size cores
            for l in confl:
                self.core, self.minw = [l], self.wght[l]
                self.core_sels, self.core_sums = [l], []
                self.process_core()

            if self.verbose > 1:
                print('c unit cores found: {0}; cost: {1}'.format(len(confl),
                    self.cost))

        nof_am1 = 0
        len_am1 = []
        lits = set(conns.keys())
        while lits:
            am1 = [min(lits, key=lambda l: len(conns[l]))]

            for l in sorted(conns[am1[0]], key=lambda l: len(conns[l])):
                if l in lits:
                    for l_added in am1[1:]:
                        if l_added not in conns[l]:
                            break
                    else:
                        am1.append(l)

            # updating remaining lits and connections
            lits.difference_update(set(am1))
            for l in conns:
                conns[l] = conns[l].difference(set(am1))

            if len(am1) > 1:
                # treat the new atmost1 relation
                self.process_am1(am1)
                nof_am1 += 1
                len_am1.append(len(am1))

        # updating the set of selectors
        self.sels_set = set(self.sels)

        if self.verbose > 1 and nof_am1:
            print('c am1s found: {0}; avgsz: {1:.1f}; cost: {2}'.format(nof_am1,
                sum(len_am1) / float(nof_am1), self.cost))

    def process_am1(self, am1):
        """
            Process an atmost1 relation detected (treat as a core).
        """

        # computing am1's weight
        self.minw = min(map(lambda l: self.wght[l], am1))

        # pretending am1 to be a core, and the bound is its size - 1
        self.core_sels, b = am1, len(am1) - 1

        # incrementing the cost
        self.cost += b * self.minw

        # assumptions to remove
        self.garbage = set()

        # splitting and relaxing if needed
        self.process_sels()

        # new selector
        self.topv += 1
        selv = self.topv

        self.oracle.add_clause([-l for l in self.rels] + [-selv])

        # integrating the new selector
        self.sels.append(selv)
        self.wght[selv] = self.minw
        self.smap[selv] = len(self.wght) - 1

        # removing unnecessary assumptions
        self.filter_assumps()

    def trim_core(self):
        """
            Trim unsatisfiable core at most a given number of times.
        """

        for i in range(self.trim):
            # call solver with core assumption only
            # it must return 'unsatisfiable'
            self.oracle.solve(assumptions=self.core)

            # extract a new core
            new_core = self.oracle.get_core()

            if len(new_core) == len(self.core):
                # stop if new core is not better than the previous one
                break

            # otherwise, update core
            self.core = new_core

    def minimize_core(self):
        """
            Try to minimize a core and compute an approximation of an MUS.
            Simple deletion-based MUS extraction.
        """

        if self.minz and len(self.core) > 1:
            self.core = sorted(self.core, key=lambda l: self.wght[l])
            self.oracle.conf_budget(1000)

            i = 0
            while i < len(self.core):
                to_test = self.core[:i] + self.core[(i + 1):]

                if self.oracle.solve_limited(assumptions=to_test) == False:
                    self.core = to_test
                else:
                    i += 1

    def exhaust_core(self, tobj):
        """
            Exhaust core by increasing its bound as much as possible.
        """

        # the first case is simpler
        if self.oracle.solve(assumptions=[-tobj.rhs[1]]):
            return 1
        else:
            self.cost += self.minw

        for i in range(2, len(self.rels)):
            # saving the previous bound
            self.tobj[-tobj.rhs[i - 1]] = tobj
            self.bnds[-tobj.rhs[i - 1]] = i - 1

            # increasing the bound
            self.update_sum(-tobj.rhs[i - 1])

            if self.oracle.solve(assumptions=[-tobj.rhs[i]]):
                # the bound should be equal to i
                return i

            # the cost should increase further
            self.cost += self.minw

        return None

    def process_sels(self):
        """
            Process soft clause selectors participating in a new core.
        """

        # new relaxation variables
        self.rels = []

        for l in self.core_sels:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)

                # reuse assumption variable as relaxation
                self.rels.append(-l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # it is an unrelaxed soft clause,
                # a new relaxed copy of which we add to the solver
                self.topv += 1
                self.oracle.add_clause([l, self.topv])
                self.rels.append(self.topv)

    def process_sums(self):
        """
            Process cardinality sums participating in a new core.
        """

        for l in self.core_sums:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

            # increase bound for the sum
            t, b = self.update_sum(l)

            # updating bounds and weights
            if b < len(t.rhs):
                lnew = -t.rhs[b]
                if lnew in self.garbage:
                    self.garbage.remove(lnew)
                    self.wght[lnew] = 0

                if lnew not in self.wght:
                    self.set_bound(t, b)
                else:
                    self.wght[lnew] += self.minw

            # put this assumption to relaxation vars
            self.rels.append(-l)

    def create_sum(self, bound=1):
        """
            Create a totalizer object encoding a new cardinality constraint.
            For Minicard, native atmostb constraints is used instead.
        """

        if self.solver != 'mc':  # standard totalizer-based encoding
            # new totalizer sum
            t = ITotalizer(lits=self.rels, ubound=bound, top_id=self.topv)

            # updating top variable id
            self.topv = t.top_id

            # adding its clauses to oracle
            for cl in t.cnf.clauses:
                self.oracle.add_clause(cl)
        else:
            # for minicard, use native cardinality constraints instead of the
            # standard totalizer, i.e. create a new (empty) totalizer sum and
            # fill it with the necessary data supported by minicard
            t = ITotalizer()
            t.lits = self.rels

            self.topv += 1  # a new variable will represent the bound

            # proper initial bound
            t.rhs = [None] * (len(t.lits))
            t.rhs[bound] = self.topv

            # new atmostb constraint instrumented with
            # an implication and represented natively
            rhs = len(t.lits)
            amb = [[-self.topv] * (rhs - bound) + t.lits, rhs]

            # add constraint to the solver
            self.oracle.add_atmost(*amb)

        return t

    def update_sum(self, assump):
        """
            Increase the bound for a given totalizer object.
        """

        # getting a totalizer object corresponding to assumption
        t = self.tobj[assump]

        # increment the current bound
        b = self.bnds[assump] + 1

        if self.solver != 'mc':  # the case of standard totalizer encoding
            # increasing its bound
            t.increase(ubound=b, top_id=self.topv)

            # updating top variable id
            self.topv = t.top_id

            # adding its clauses to oracle
            if t.nof_new:
                for cl in t.cnf.clauses[-t.nof_new:]:
                    self.oracle.add_clause(cl)
        else:  # the case of cardinality constraints represented natively
            # right-hand side is always equal to the number of input literals
            rhs = len(t.lits)

            if b < rhs:
                # creating an additional bound
                if not t.rhs[b]:
                    self.topv += 1
                    t.rhs[b] = self.topv

                # a new at-most-b constraint
                amb = [[-t.rhs[b]] * (rhs - b) + t.lits, rhs]
                self.oracle.add_atmost(*amb)

        return t, b

    def set_bound(self, tobj, rhs):
        """
            Set a bound for a given totalizer object.
        """

        # saving the sum and its weight in a mapping
        self.tobj[-tobj.rhs[rhs]] = tobj
        self.bnds[-tobj.rhs[rhs]] = rhs
        self.wght[-tobj.rhs[rhs]] = self.minw

        # adding a new assumption to force the sum to be at most rhs
        self.sums.append(-tobj.rhs[rhs])

    def filter_assumps(self):
        """
            Filter out both unnecessary selectors and sums.
        """

        self.sels = list(filter(lambda x: x not in self.garbage, self.sels))
        self.sums = list(filter(lambda x: x not in self.garbage, self.sums))

        self.bnds = {l: b for l, b in six.iteritems(self.bnds) if l not in self.garbage}
        self.wght = {l: w for l, w in six.iteritems(self.wght) if l not in self.garbage}

        self.garbage.clear()

    def oracle_time(self):
        """
            Report the total SAT solving time.
        """

        return self.oracle.time_accum()

    def _map_extlit(self, l):
        """
            Map an external variable to an internal one if necessary.
        """

        v = abs(l)

        if v in self.vmap.e2i:
            return int(copysign(self.vmap.e2i[v], l))
        else:
            self.topv += 1

            self.vmap.e2i[v] = self.topv
            self.vmap.i2e[self.topv] = v

            return int(copysign(self.topv, l))


#
#==============================================================================
class RC2Stratified(RC2, object):
    """
        Stratified version of RC2 exploiting Boolean lexicographic optimization
        and stratification.
    """

    def __init__(self, formula, solver='g3', adapt=False, exhaust=False,
            incr=False, minz=False, trim=0, verbose=0):
        """
            Constructor.
        """

        # calling the constructor for the basic version
        super(RC2Stratified, self).__init__(formula, solver=solver,
                adapt=adapt, exhaust=exhaust, incr=incr, minz=minz, trim=trim,
                verbose=verbose)

        self.levl = 0   # initial optimization level
        self.blop = []  # a list of blo levels

        # backing up selectors
        self.bckp, self.bckp_set = self.sels, self.sels_set
        self.sels = []

        # initialize Boolean lexicographic optimization
        if sum(self.wght.values()) > len(self.bckp):
            self.init_wstr()

    def init_wstr(self):
        """
            Compute and initialize optimization levels for BLO.
        """

        # a mapping for stratified problem solving,
        # i.e. from a weight to a list of selectors
        self.wstr = collections.defaultdict(lambda: [])

        for s, w in six.iteritems(self.wght):
            self.wstr[w].append(s)

        # sorted list of distinct weight levels
        self.blop = sorted([w for w in self.wstr], reverse=True)

        # diversity parameter for stratification
        self.sdiv = len(self.blop) / 2.0

    def compute(self):
        """
            Exploit Boolean lexicographic optimization when solving.
        """

        done = 0  # levels done

        # first attempt to get an optimization level
        self.next_level()

        while self.levl != None and done < len(self.blop):
            # add more clauses
            done = self.activate_clauses(done)

            if self.verbose > 1:
                print('c wght str:', self.blop[self.levl])

            # call RC2
            if self.compute_() == False:
                return

            # updating the list of distinct weight levels
            self.blop = sorted([w for w in self.wstr], reverse=True)

            if done < len(self.blop):
                if self.verbose > 1:
                    print('c curr opt:', self.cost)

                # done with this level
                self.finish_level()

                self.levl += 1

                # get another level
                self.next_level()

                if self.verbose > 1:
                    print('c')

        # extracting a model
        self.model = self.oracle.get_model()
        self.model = filter(lambda l: abs(l) in self.vmap.i2e, self.model)
        self.model = map(lambda l: int(copysign(self.vmap.i2e[abs(l)], l)), self.model)
        self.model = sorted(self.model, key=lambda l: abs(l))

        return self.model

    def next_level(self):
        """
            Get next weight to use in BLO.
        """

        if self.levl >= len(self.blop):
            self.levl = None

        while self.levl < len(self.blop) - 1:
            # number of selectors with weight less than current weight
            numc = sum([len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

            # sum of their weights
            sumw = sum([w * len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

            # partial BLO
            if self.blop[self.levl] > sumw and sumw != 0:
                break

            # stratification
            if numc / float(len(self.blop) - self.levl - 1) > self.sdiv:
                break

            self.levl += 1

    def activate_clauses(self, beg):
        """
            Add more soft clauses to the problem.
        """

        end = min(self.levl + 1, len(self.blop))

        for l in range(beg, end):
            for sel in self.wstr[self.blop[l]]:
                if sel in self.bckp_set:
                    self.sels.append(sel)
                else:
                    self.sums.append(sel)

        # updating set of selectors
        self.sels_set = set(self.sels)

        return end

    def finish_level(self):
        """
            Postprocess the current optimization level: harden clauses
            depending on their remaining weights.
        """

        # assumptions to remove
        self.garbage = set()

        # sum of weights of the remaining levels
        sumw = sum([w * len(self.wstr[w]) for w in self.blop[(self.levl + 1):]])

        # trying to harden selectors and sums
        for s in self.sels + self.sums:
            if self.wght[s] > sumw:
                self.oracle.add_clause([s])
                self.garbage.add(s)

        if self.verbose > 1:
            print('c hardened:', len(self.garbage))

        # remove unnecessary assumptions
        self.filter_assumps()

    def process_am1(self, am1):
        """
            Process an atmost1 relation detected (treat as a core).
        """

        # computing am1's weight
        self.minw = min(map(lambda l: self.wght[l], am1))

        # pretending am1 to be a core, and the bound is its size - 1
        self.core_sels, b = am1, len(am1) - 1

        # incrementing the cost
        self.cost += b * self.minw

        # assumptions to remove
        self.garbage = set()

        # splitting and relaxing if needed
        self.process_sels()

        # new selector
        self.topv += 1
        selv = self.topv

        self.oracle.add_clause([-l for l in self.rels] + [-selv])

        # integrating the new selector
        self.sels.append(selv)
        self.wght[selv] = self.minw
        self.smap[selv] = len(self.wght) - 1

        # do not forget this newly selector!
        self.bckp_set.add(selv)

        # removing unnecessary assumptions
        self.filter_assumps()

    def process_sels(self):
        """
            Process soft clause selectors participating in a new core.
        """

        # new relaxation variables
        self.rels = []

        # selectors that should be deactivated (but not removed completely)
        to_deactivate = set([])

        for l in self.core_sels:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)

                # reuse assumption variable as relaxation
                self.rels.append(-l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # deactivate this assumption and put at a lower level
                if self.wght[l] < self.blop[self.levl]:
                    self.wstr[self.wght[l]].append(l)
                    to_deactivate.add(l)

                # it is an unrelaxed soft clause,
                # a new relaxed copy of which we add to the solver
                self.topv += 1
                self.oracle.add_clause([l, self.topv])
                self.rels.append(self.topv)

        # deactivating unnecessary selectors
        self.sels = list(filter(lambda x: x not in to_deactivate, self.sels))

    def process_sums(self):
        """
            Process cardinality sums participating in a new core.
        """

        # sums that should be deactivated (but not removed completely)
        to_deactivate = set([])

        for l in self.core_sums:
            if self.wght[l] == self.minw:
                # marking variable as being a part of the core
                # so that next time it is not used as an assump
                self.garbage.add(l)
            else:
                # do not remove this variable from assumps
                # since it has a remaining non-zero weight
                self.wght[l] -= self.minw

                # deactivate this assumption and put at a lower level
                if self.wght[l] < self.blop[self.levl]:
                    self.wstr[self.wght[l]].append(l)
                    to_deactivate.add(l)

            # increase bound for the sum
            t, b = self.update_sum(l)

            # updating bounds and weights
            if b < len(t.rhs):
                lnew = -t.rhs[b]
                if lnew in self.garbage:
                    self.garbage.remove(lnew)
                    self.wght[lnew] = 0

                if lnew not in self.wght:
                    self.set_bound(t, b)
                else:
                    self.wght[lnew] += self.minw

            # put this assumption to relaxation vars
            self.rels.append(-l)

        # deactivating unnecessary sums
        self.sums = list(filter(lambda x: x not in to_deactivate, self.sums))


#
#==============================================================================
def parse_options():
    """
        Parses command-line option
    """

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'ac:e:hilms:t:vx',
                ['adapt', 'comp=', 'enum=', 'exhaust', 'help', 'incr', 'blo',
                    'minimize', 'solver=', 'trim=', 'verbose'])
    except getopt.GetoptError as err:
        sys.stderr.write(str(err).capitalize())
        usage()
        sys.exit(1)

    adapt = False
    exhaust = False
    cmode = None
    to_enum = 1
    incr = False
    blo = False
    minz = False
    solver = 'g3'
    trim = 0
    verbose = 1

    for opt, arg in opts:
        if opt in ('-a', '--adapt'):
            adapt = True
        elif opt in ('-c', '--comp'):
            cmode = str(arg)
        elif opt in ('-e', '--enum'):
            to_enum = str(arg)
            if to_enum != 'all':
                to_enum = int(to_enum)
            else:
                to_enum = 0
        elif opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif opt in ('-i', '--incr'):
            incr = True
        elif opt in ('-l', '--blo'):
            blo = True
        elif opt in ('-m', '--minimize'):
            minz = True
        elif opt in ('-s', '--solver'):
            solver = str(arg)
        elif opt in ('-t', '--trim'):
            trim = int(arg)
        elif opt in ('-v', '--verbose'):
            verbose += 1
        elif opt in ('-x', '--exhaust'):
            exhaust = True
        else:
            assert False, 'Unhandled option: {0} {1}'.format(opt, arg)

    return adapt, blo, cmode, to_enum, exhaust, incr, minz, solver, trim, \
            verbose, args


#==============================================================================
def usage():
    """
        Prints usage message.
        """

    print('Usage:', os.path.basename(sys.argv[0]), '[options] dimacs-file')
    print('Options:')
    print('        -a, --adapt              Try to adapt (simplify) input formula')
    print('        -c, --comp=<string>      Enable one of the MSE18 configurations')
    print('                                 Available values: a, b, none (default = none)')
    print('        -e, --enum=<int>         Number of MaxSAT models to compute')
    print('                                 Available values: [1 .. INT_MAX], all (default = 1)')
    print('        -h, --help               Show this message')
    print('        -i, --incr               Use SAT solver incrementally (only for g3 and g4)')
    print('        -l, --blo                Use BLO and stratification')
    print('        -m, --minimize           Use a heuristic unsatisfiable core minimizer')
    print('        -s, --solver=<string>    SAT solver to use')
    print('                                 Available values: g3, g4, lgl, mc, m22, mgh (default = g3)')
    print('        -t, --trim=<int>         How many times to trim unsatisfiable cores')
    print('                                 Available values: [0 .. INT_MAX] (default = 0)')
    print('        -v, --verbose            Be verbose')
    print('        -x, --exhaust            Exhaust new unsatisfiable cores')


#
#==============================================================================
if __name__ == '__main__':
    adapt, blo, cmode, to_enum, exhaust, incr, minz, solver, trim, verbose, \
            files = parse_options()

    if files:
        # parsing the input formula
        if re.search('\.wcnf(\.(gz|bz2|lzma|xz))?$', files[0]):
            formula = WCNF(from_file=files[0])
        else:  # expecting '*.cnf'
            formula = CNF(from_file=files[0]).weighted()

        # enabling the competition mode
        if cmode:
            assert cmode in ('a', 'b'), 'Wrong MSE18 mode chosen: {0}'.format(cmode)
            adapt, blo, exhaust, solver, verbose = True, True, True, 'g3', 3

            if cmode == 'a':
                trim = 5 if max(formula.wght) > min(formula.wght) else 0
                minz = False
            else:
                trim, minz = 0, True

            # trying to use unbuffered standard output
            if sys.version_info.major == 2:
                sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

        # deciding whether or not to stratify
        if blo and max(formula.wght) > min(formula.wght):
            assert to_enum == 1, 'Stratified solving is incompatible with model enumeration'
            MXS = RC2Stratified
        else:
            MXS = RC2

        # starting the solver
        with MXS(formula, solver=solver, adapt=adapt, exhaust=exhaust,
                incr=incr, minz=minz, trim=trim, verbose=verbose) as rc2:

            optimum_found = False
            for i, model in enumerate(rc2.enumerate(), 1):
                optimum_found = True

                if verbose:
                    if i == 1:
                        print('s OPTIMUM FOUND')
                        print('o {0}'.format(rc2.cost))

                    if verbose > 2:
                        print('v', ' '.join([str(l) for l in model]))

                if i == to_enum:
                    break

            if verbose:
                if not optimum_found:
                    print('s UNSATISFIABLE')
                elif to_enum != 1:
                    print('c models found:', i)

                if verbose > 1:
                    print('c oracle time: {0:.4f}'.format(rc2.oracle_time()))
