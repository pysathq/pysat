#!/usr/bin/env python
#-*- coding:utf-8 -*-
##
## solvers.py
##
##  Created on: Nov 27, 2016
##      Author: Alexey S. Ignatiev
##      E-mail: aignatiev@ciencias.ulisboa.pt
##

#
#==============================================================================
import pysolvers
import signal
import tempfile
import time


#
#==============================================================================
class NoSuchSolverError(Exception):
    pass

#
#==============================================================================
class Solver(object):
    """
        Abstract SAT solver class.
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
            Constructor.
        """

        if not self.solver:
            if name in ('g3', 'glucose3'):
                self.solver = Glucose3(bootstrap_with, use_timer, **kwargs)
            elif name in ('lgl', 'lingeling'):
                self.solver = Lingeling(bootstrap_with, use_timer, **kwargs)
            elif name in ('mc', 'mcard', 'minicard'):
                self.solver = Minicard(bootstrap_with, use_timer)
            elif name in ('m22', 'msat22', 'minisat22'):
                self.solver = Minisat22(bootstrap_with, use_timer)
            elif name in ('mgh', 'msat-gh', 'minisat-gh'):
                self.solver = MinisatGH(bootstrap_with, use_timer)
            else:
                raise(NoSuchSolverError(name))

    def delete(self):
        """
            Destructor.
        """

        if self.solver:
            self.solver.delete()
            self.solver = None

    def solve(self, assumptions=[]):
        """
            Solve internal formula.
        """

        if self.solver:
            return self.solver.solve(assumptions)

    def solve_limited(self, assumptions=[]):
        """
            Solve internal formula using given budgets for conflicts and
            propagations.
        """

        if self.solver:
            return self.solver.solve_limited(assumptions)

    def conf_budget(self, budget):
        """
            Set limit on the number of conflicts.
        """

        if self.solver:
            self.solver.conf_budget(budget)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.solver:
            self.solver.prop_budget(budget)

    def get_status(self):
        """
            Returns solver's status.
        """

        if self.solver:
            return self.solver.get_status()

    def get_model(self):
        """
            Get a model if the formula was previously satisfied.
        """

        if self.solver:
            return self.solver.get_model()

    def get_core(self):
        """
            Get an unsatisfiable core if the formula was previously
            unsatisfied.
        """

        if self.solver:
            return self.solver.get_core()

    def get_proof(self):
        """
            Get a proof produced while deciding the formula.
        """

        if self.solver:
            return self.solver.get_proof()

    def time(self):
        """
            Get time spent for the last call to oracle.
        """

        if self.solver:
            return self.solver.time()

    def time_accum(self):
        """
            Get time accumulated for all calls to oracle.
        """

        if self.solver:
            return self.solver.time_accum()

    def nof_vars(self):
        """
            Get number of variables currently used by the solver.
        """

        if self.solver:
            return self.solver.nof_vars()

    def nof_clauses(self):
        """
            Get number of clauses currently used by the solver.
        """

        if self.solver:
            return self.solver.nof_clauses()

    def enum_models(self, assumptions=[]):
        """
            Iterate over models of the internal formula.
        """

        if self.solver:
            return self.solver.enum_models(assumptions)

    def add_clause(self, clause, no_return=True):
        """
            Add a new clause to solver's internal formula.
        """

        if self.solver:
            res = self.solver.add_clause(clause, no_return)
            if not no_return:
                return res

    def add_atmost(self, lits, k, no_return=True):
        """
            Add a new atmost constraint to solver's internal formula.
            Note: works only with Minicard!
        """

        if self.solver:
            res = self.solver.add_atmost(lits, k, no_return)
            if not no_return:
                return res

    def append_formula(self, formula, no_return=True):
        """
            Appends list of clauses to solver's internal formula.
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
            pysolvers.glucose3_cbudget(self.glucose)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.glucose:
            pysolvers.glucose3_pbudget(self.glucose)

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
            return pysolvers.glucose3_model(self.glucose)

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
class Lingeling(object):
    """
        Lingeling SAT solver.
    """

    def __init__(self, bootstrap_with=None, use_timer=False, with_proof=False):
        """
            Basic constructor.
        """

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
            return pysolvers.lingeling_model(self.lingeling)

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
            pysolvers.minicard_cbudget(self.minicard)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minicard:
            pysolvers.minicard_pbudget(self.minicard)

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
            return pysolvers.minicard_model(self.minicard)

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
            pysolvers.minisat22_cbudget(self.minisat)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minisat:
            pysolvers.minisat22_pbudget(self.minisat)

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
            return pysolvers.minisat22_model(self.minisat)

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
            pysolvers.minisatgh_cbudget(self.minisat)

    def prop_budget(self, budget):
        """
            Set limit on the number of propagations.
        """

        if self.minisat:
            pysolvers.minisatgh_pbudget(self.minisat)

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
            return pysolvers.minisatgh_model(self.minisat)

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
