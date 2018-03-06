#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## formula.py
##
##  Created on: Dec 7, 2016
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
from __future__ import print_function
import collections
import copy
import itertools
import os
import sys

try:  # for Python2
    from cStringIO import StringIO
except ImportError:  # for Python3
    from io import StringIO


#
#==============================================================================
class IDPool(object):
    """
        A simple manager of variable IDs.
    """

    def __init__(self, start_from=1):
        """
            Constructor.
        """

        self.restart(start_from=start_from)

    def restart(self, start_from=1):
        """
            Restart the manager from scratch.
        """

        # initial ID
        self.start_from = start_from

        # this is how we get the current ID
        self.counter = itertools.count(start=self.start_from)

        # main dictionary storing the mapping from objects to variable IDs
        self.obj2id = collections.defaultdict(lambda: next(self.counter))

        # mapping back from variable IDs to objects
        # (if for whatever reason necessary)
        self.id2obj = {}

    def id(self, obj):
        """
            Return an integer variable ID for a given object, which
            can be a a variable name. Assign a new ID if necessary.
        """

        vid = self.obj2id[obj]

        if vid not in self.id2obj:
            self.id2obj[vid] = obj

        return vid

    def obj(self, vid):
        """
            Given a variable ID, get the corresponding object.
        """

        if vid in self.id2obj:
            return self.id2obj[vid]

        return None

    def top(self):
        """
            Return current top variable ID.
        """

        return len(self.obj2id) + self.start_from - 1


#
#==============================================================================
class CNF(object):
    """
        CNF formula class.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None, from_clauses=[], comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.clauses = []
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead)
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)
        elif from_clauses:
            self.from_clauses(from_clauses)

    def from_file(self, fname, comment_lead=['c']):
        """
            Read CNF formula from a file in DIMACS format.
        """

        with open(fname, 'r') as fp:
            self.from_fp(fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read CNF formula from a file pointer.
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
            Read CNF formula from a DIMACS string.
        """

        self.from_fp(StringIO(string), comment_lead)

    def from_clauses(self, clauses):
        """
            Copy CNF formula from clauses.
        """

        self.clauses = clauses[:]

        for cl in self.clauses:
            self.nv = max([abs(l) for l in cl] + [self.nv])

    def copy(self):
        """
            Creates a copy of the formula.
        """

        cnf = CNF()
        cnf.nv = self.nv
        cnf.clauses = copy.deepcopy(self.clauses)
        cnf.comments = copy.deepcopy(self.comments)

        return cnf

    def to_file(self, fname, comments=None):
        """
            Save CNF formula to a file in DIMACS format.
        """

        with open(fname, 'w') as fp:
            self.to_fp(fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            Save CNF formula to a file pointer.
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
            Add one more clause to CNF formula.
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])
        self.clauses.append(clause)

    def extend(self, clauses):
        """
            Add more clauses to CNF formula.
        """

        for cl in clauses:
            self.append(cl)

    def weighted(self):
        """
            Create and return a weighted copy of the formula.
        """

        wcnf = WCNF()

        wcnf.nv = self.nv
        wcnf.hard = []
        wcnf.soft = self.clauses[:]
        wcnf.wght = [1 for cl in wcnf.soft]
        self.topw = len(wcnf.wght) + 1
        wcnf.comments = self.comments[:]

        return wcnf

    def negate(self, topv=None):
        """
            Returns an object of class CNF, which is the Tseitin-encoded
            negation of the given CNF.
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
        Weighted CNF formula class.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None, comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.hard = []
        self.soft = []
        self.wght = []
        self.topw = 0
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead)
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)

    def from_file(self, fname, comment_lead=['c']):
        """
            Read WCNF formula from a file in DIMACS format.
        """

        with open(fname, 'r') as fp:
            self.from_fp(fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read WCNF formula from a file pointer.
        """

        self.nv = 0
        self.hard = []
        self.soft = []
        self.wght = []
        self.topw = 0
        self.comments = []
        comment_lead = tuple('p') + tuple(comment_lead)

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    cl = [int(l) for l in line.split()[:-1]]
                    w = cl.pop(0)
                    self.nv = max([abs(l) for l in cl] + [self.nv])

                    if w >= self.topw:
                        self.hard.append(cl)
                    else:
                        self.soft.append(cl)
                        self.wght.append(w)
                elif not line.startswith('p wcnf '):
                    self.comments.append(line)
                else:  # expecting the preamble
                    self.topw = int(line.rsplit(' ', 1)[1])

    def from_string(self, string, comment_lead=['c']):
        """
            Read WCNF formula from a DIMACS string.
        """

        self.from_fp(StringIO(string), comment_lead)

    def copy(self):
        """
            Creates a copy of the formula.
        """

        wcnf = WCNF()
        wcnf.nv = self.nv
        wcnf.topw = self.topw
        wcnf.hard = copy.deepcopy(self.hard)
        wcnf.soft = copy.deepcopy(self.soft)
        wcnf.wght = copy.deepcopy(self.wght)
        wcnf.comments = copy.deepcopy(self.comments)

        return wcnf

    def to_file(self, fname, comments=None):
        """
            Save WCNF formula to a file in DIMACS format.
        """

        with open(fname, 'w') as fp:
            self.to_fp(fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            Save WCNF formula to a file pointer.
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
            Add one more clause to WCNF formula.
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])

        if weight:
            self.soft.append(clause)
            self.wght.append(weight)
        else:
            self.hard.append(clause)

    def extend(self, clauses, weights=None):
        """
            Add more clauses to WCNF formula.
        """

        if weights:
            # clauses are soft
            for i, cl in enumerate(clauses):
                self.append(cl, weight=weights[i])
        else:
            # clauses are hard
            for cl in clauses:
                self.append(cl)

    def unweigh(self):
        """
            Create a simple CNF formula by removing weights.
        """

        cnf = CNF()

        cnf.nv = self.nv
        cnf.clauses = self.hard + self.soft
        cnf.commends = self.comments[:]

        return cnf


#
#==============================================================================
class CNFPlus(object):
    """
        CNF+ formula class.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None, comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.clauses = []
        self.atmosts = []
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead)
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)

    def from_file(self, fname, comment_lead=['c']):
        """
            Read CNF+ formula from a file in DIMACS format.
        """

        with open(fname, 'r') as fp:
            self.from_fp(fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read CNF+ formula from a file pointer.
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
                    if line[-1] == '0':  # normal clause
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
                elif not line.startswith('p cnf+ '):
                    self.comments.append(line)

    def from_string(self, string, comment_lead=['c']):
        """
            Read CNF+ formula from a DIMACS string.
        """

        self.from_fp(StringIO(string), comment_lead)

    def to_file(self, fname, comments=None):
        """
            Save CNF+ formula to a file in DIMACS format.
        """

        with open(fname, 'w') as fp:
            self.to_fp(fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            Save CNF+ formula to a file pointer.
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        ftype = 'cnf+' if self.atmosts else 'cnf'
        print('p', ftype, self.nv, len(self.clauses), file=file_pointer)

        for cl in self.clauses:
            print(' '.join(str(l) for l in cl), '0', file=file_pointer)

        for am in self.atmosts:
            print(' '.join(str(l) for l in am[0]), '<=', am[1], file=file_pointer)

    def append(self, clause, is_atmost=False):
        """
            Add one more clause or atmost constraint to CNF+ formula.
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])

        if not is_atmost:
            self.clauses.append(clause)
        else:
            self.atmosts.append(clause)

    def extend(self, clauses):
        """
            Add more clauses to CNF+ formula.
        """

        for cl in clauses:
            self.append(cl)


#
#==============================================================================
class WCNFPlus(object):
    """
        Weighted CNF+ formula class.
    """

    def __init__(self, from_file=None, from_fp=None, from_string=None, comment_lead=['c']):
        """
            Constructor.
        """

        self.nv = 0
        self.hard = []
        self.atms = []
        self.soft = []
        self.wght = []
        self.topw = 0
        self.comments = []

        if from_file:
            self.from_file(from_file, comment_lead)
        elif from_fp:
            self.from_fp(from_fp, comment_lead)
        elif from_string:
            self.from_string(from_string, comment_lead)

    def from_file(self, fname, comment_lead=['c']):
        """
            Read WCNF+ formula from a file in DIMACS format.
        """

        with open(fname, 'r') as fp:
            self.from_fp(fp, comment_lead)

    def from_fp(self, file_pointer, comment_lead=['c']):
        """
            Read WCNF+ formula from a file pointer.
        """

        self.nv = 0
        self.hard = []
        self.atms = []
        self.soft = []
        self.wght = []
        self.topw = 0
        self.comments = []
        comment_lead = tuple('p') + tuple(comment_lead)

        for line in file_pointer:
            line = line.strip()
            if line:
                if line[0] not in comment_lead:
                    if line[-1] == '0':  # normal clause
                        cl = [int(l) for l in line.split()[:-1]]
                        w = cl.pop(0)
                        self.nv = max([abs(l) for l in cl] + [self.nv])

                        if w >= self.topw:
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
                elif not line.startswith('p wcnf+ '):
                    self.comments.append(line)
                else:  # expecting the preamble
                    self.topw = int(line.rsplit(' ', 1)[1])

    def from_string(self, string, comment_lead=['c']):
        """
            Read WCNF+ formula from a DIMACS string.
        """

        self.from_fp(StringIO(string), comment_lead)

    def to_file(self, fname, comments=None):
        """
            Save WCNF+ formula to a file in DIMACS format.
        """

        with open(fname, 'w') as fp:
            self.to_fp(fp, comments)

    def to_fp(self, file_pointer, comments=None):
        """
            Save WCNF+ formula to a file pointer.
        """

        # saving formula's internal comments
        for c in self.comments:
            print(c, file=file_pointer)

        # saving externally specified comments
        if comments:
            for c in comments:
                print(c, file=file_pointer)

        ftype = 'wcnf+' if self.atms else 'wcnf'
        print('p', ftype, self.nv, len(self.hard) + len(self.soft), self.topw, file=file_pointer)

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
            Add one more clause to WCNF+ formula.
        """

        self.nv = max([abs(l) for l in clause] + [self.nv])

        if weight:
            self.soft.append(clause)
            self.wght.append(weight)
        elif not is_atmost:
            self.hard.append(clause)
        else:
            self.atms.append(clause)

    def extend(self, clauses, weights=None):
        """
            Add more clauses to WCNF+ formula.
        """

        if weights:
            # clauses are soft
            for i, cl in enumerate(clauses):
                self.append(cl, weight=weights[i])
        else:
            # clauses are hard
            for cl in clauses:
                self.append(cl)
