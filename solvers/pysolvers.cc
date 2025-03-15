/*
 * pysolvers.cc
 *
 *  Created on: Nov 26, 2016
 *      Author: aign
 */

#ifdef _MSC_VER
#define setlinebuf(a)
#endif

#define PY_SSIZE_T_CLEAN

#include <algorithm>
#include <Python.h>
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <vector>

#ifdef WITH_CADICAL103
#include "cadical103/cadical.hpp"
#endif

#ifdef WITH_CADICAL153
#include "cadical153/cadical.hpp"
#endif

#ifdef WITH_CADICAL195
#include "cadical195/cadical.hpp"
#endif

#ifdef WITH_GLUECARD30
#include "gluecard30/core/Solver.h"
#endif

#ifdef WITH_GLUECARD41
#include "gluecard41/core/Solver.h"
#endif

#ifdef WITH_GLUCOSE30
#include "glucose30/core/Solver.h"
#endif

#ifdef WITH_GLUCOSE41
#include "glucose41/core/Solver.h"
#endif

#ifdef WITH_GLUCOSE421
#include "glucose421/core/Solver.h"
#endif

#ifdef WITH_LINGELING
#include "lingeling/lglib.h"
#endif

#ifdef WITH_MAPLECHRONO
#include "maplechrono/core/Solver.h"
#endif

#ifdef WITH_MAPLECM
#include "maplecm/core/Solver.h"
#endif

#ifdef WITH_MAPLESAT
#include "maplesat/core/Solver.h"
#endif

#ifdef WITH_MERGESAT3
#include "mergesat3/core/Solver.h"
#endif

#ifdef WITH_MINICARD
#include "minicard/core/Solver.h"
#endif

#ifdef WITH_MINISAT22
#include "minisat22/core/Solver.h"
#endif

#ifdef WITH_MINISATGH
#include "minisatgh/core/Solver.h"
#endif

using namespace std;

// docstrings
//=============================================================================
static char    module_docstring[] = "This module provides a wrapper interface "
                                    "for several SAT solvers.";
static char       new_docstring[] = "Create a new solver object.";
static char       set_docstring[] = "Set a value of a solver's parameter "
                                    "(for CaDiCaL 153 only).";
static char     addcl_docstring[] = "Add a clause to formula.";
static char     addam_docstring[] = "Add an atmost constraint to formula "
                                    "(for Minicard only).";
static char     solve_docstring[] = "Solve a given CNF instance.";
static char       lim_docstring[] = "Solve a given CNF instance within a budget.";
static char   process_docstring[] = "(Pre)process a given CNF formula using "
                                    "the CaDiCaL 1.5.3 preprocessor";
static char   restore_docstring[] = "Reconstruct the model to a CNF formula "
                                    "from the model for its processed version";
static char      prop_docstring[] = "Propagate a given set of literals.";
static char    phases_docstring[] = "Set variable polarities.";
static char   cbudget_docstring[] = "Set limit on the number of conflicts.";
static char   pbudget_docstring[] = "Set limit on the number of propagations.";
static char   dbudget_docstring[] = "Set limit on the number of decisions "
                                    "(CaDiCaL only).";
static char interrupt_docstring[] = "Interrupt SAT solver execution "
                                    "(not supported by lingeling and CaDiCaL).";
static char  clearint_docstring[] = "Clear interrupt indicator flag.";
static char   setincr_docstring[] = "Set incremental mode (for Glucose3 only).";
static char   tracepr_docstring[] = "Trace resolution proof.";
static char      core_docstring[] = "Get an unsatisfiable core if formula is UNSAT.";
static char     model_docstring[] = "Get a model if formula is SAT.";
static char     nvars_docstring[] = "Get number of variables used by the solver.";
static char      ncls_docstring[] = "Get number of clauses used by the solver.";
static char       del_docstring[] = "Delete a previously created solver object.";
static char  acc_stat_docstring[] = "Get accumulated stats from the solver.";
static char  setstart_docstring[] = "Set (warm) start mode for the solver.";
static char     pconn_docstring[] = "Attach an external propagator "
                                    "(CaDiCaL 1.9.5 only).";
static char  pdisconn_docstring[] = "Disconnect external propagator, which also resets of 'observed' flags "
                                    "(CaDiCaL 1.9.5 only).";
static char   penable_docstring[] = "Enable an external propagator "
                                    "(CaDiCaL 1.9.5 only).";
static char  pdisable_docstring[] = "Disable an external propagator "
                                    "(CaDiCaL 1.9.5 only).";
static char   pactive_docstring[] = "Return the status of external propagator "
                                    "(CaDiCaL 1.9.5 only).";
static char  vobserve_docstring[] = "Mark a variable as 'observed' "
                                    "(CaDiCaL 1.9.5 only).";
static char   vignore_docstring[] = "Remove the 'observed' flag for a variable "
                                    "(CaDiCaL 1.9.5 only).";
static char    vreset_docstring[] = "Remove all the 'observed' variable flags"
                                    "(CaDiCaL 1.9.5 only).";
static char  isdeclit_docstring[] = "Get reason of valid observed literal "
                                    "(CaDiCaL 1.9.5 only).";
static char  set_rnd_seed_docstring[] =          "Set PNRG seed "
                                                 "(Glucose 4.2.1 only).";
static char  set_rnd_freq_docstring[] =          "Set frequency of random decisions "
                                                 "(Glucose 4.2.1 only).";
static char  set_rnd_pol_docstring[] =           "Randomize polarities on branching "
                                                 "(Glucose 4.2.1 only).";
static char  set_rnd_init_act_docstring[] =      "Randomize initial activities "
                                                 "(Glucose 4.2.1 only).";
static char  set_rnd_first_descent_docstring[] = "Randomize decisions until first conflict "
                                                 "(Glucose 4.2.1 only).";




static PyObject *SATError;
static jmp_buf env;

// function declaration for functions available in module
//=============================================================================
extern "C" {
#ifdef WITH_CADICAL103
	static PyObject *py_cadical103_new       (PyObject *, PyObject *);
	static PyObject *py_cadical103_add_cl    (PyObject *, PyObject *);
	static PyObject *py_cadical103_solve     (PyObject *, PyObject *);
	static PyObject *py_cadical103_solve_lim (PyObject *, PyObject *);
	static PyObject *py_cadical103_cbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical103_dbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical103_tracepr   (PyObject *, PyObject *);
	static PyObject *py_cadical103_core      (PyObject *, PyObject *);
	static PyObject *py_cadical103_model     (PyObject *, PyObject *);
	static PyObject *py_cadical103_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_cadical103_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_cadical103_del       (PyObject *, PyObject *);
	static PyObject *py_cadical103_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_CADICAL153
	static PyObject *py_cadical153_new       (PyObject *, PyObject *);
	static PyObject *py_cadical153_set       (PyObject *, PyObject *);
	static PyObject *py_cadical153_add_cl    (PyObject *, PyObject *);
	static PyObject *py_cadical153_process   (PyObject *, PyObject *);
	static PyObject *py_cadical153_restore   (PyObject *, PyObject *);
	static PyObject *py_cadical153_solve     (PyObject *, PyObject *);
	static PyObject *py_cadical153_solve_lim (PyObject *, PyObject *);
	static PyObject *py_cadical153_propagate (PyObject *, PyObject *);
	static PyObject *py_cadical153_setphases (PyObject *, PyObject *);
	static PyObject *py_cadical153_cbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical153_dbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical153_tracepr   (PyObject *, PyObject *);
	static PyObject *py_cadical153_core      (PyObject *, PyObject *);
	static PyObject *py_cadical153_model     (PyObject *, PyObject *);
	static PyObject *py_cadical153_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_cadical153_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_cadical153_del       (PyObject *, PyObject *);
	static PyObject *py_cadical153_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_CADICAL195
	static PyObject *py_cadical195_new       (PyObject *, PyObject *);
	static PyObject *py_cadical195_set       (PyObject *, PyObject *);
	static PyObject *py_cadical195_add_cl    (PyObject *, PyObject *);
	static PyObject *py_cadical195_process   (PyObject *, PyObject *);
	static PyObject *py_cadical195_restore   (PyObject *, PyObject *);
	static PyObject *py_cadical195_solve     (PyObject *, PyObject *);
	static PyObject *py_cadical195_solve_lim (PyObject *, PyObject *);
	static PyObject *py_cadical195_propagate (PyObject *, PyObject *);
	static PyObject *py_cadical195_setphases (PyObject *, PyObject *);
	static PyObject *py_cadical195_cbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical195_dbudget   (PyObject *, PyObject *);
	static PyObject *py_cadical195_tracepr   (PyObject *, PyObject *);
	static PyObject *py_cadical195_core      (PyObject *, PyObject *);
	static PyObject *py_cadical195_model     (PyObject *, PyObject *);
	static PyObject *py_cadical195_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_cadical195_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_cadical195_del       (PyObject *, PyObject *);
	static PyObject *py_cadical195_acc_stats (PyObject *, PyObject *);
	static PyObject *py_cadical195_pconn     (PyObject *, PyObject *);
	static PyObject *py_cadical195_pdisconn  (PyObject *, PyObject *);
	static PyObject *py_cadical195_penable   (PyObject *, PyObject *);
	static PyObject *py_cadical195_pdisable  (PyObject *, PyObject *);
	static PyObject *py_cadical195_pactive   (PyObject *, PyObject *);
	static PyObject *py_cadical195_vobserve  (PyObject *, PyObject *);
	static PyObject *py_cadical195_vignore   (PyObject *, PyObject *);
	static PyObject *py_cadical195_vreset    (PyObject *, PyObject *);
	static PyObject *py_cadical195_isdeclit  (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUECARD30
	static PyObject *py_gluecard3_new       (PyObject *, PyObject *);
	static PyObject *py_gluecard3_set_start (PyObject *, PyObject *);
	static PyObject *py_gluecard3_add_cl    (PyObject *, PyObject *);
	static PyObject *py_gluecard3_add_am    (PyObject *, PyObject *);
	static PyObject *py_gluecard3_solve     (PyObject *, PyObject *);
	static PyObject *py_gluecard3_solve_lim (PyObject *, PyObject *);
	static PyObject *py_gluecard3_propagate (PyObject *, PyObject *);
	static PyObject *py_gluecard3_setphases (PyObject *, PyObject *);
	static PyObject *py_gluecard3_cbudget   (PyObject *, PyObject *);
	static PyObject *py_gluecard3_pbudget   (PyObject *, PyObject *);
	static PyObject *py_gluecard3_interrupt (PyObject *, PyObject *);
	static PyObject *py_gluecard3_clearint  (PyObject *, PyObject *);
	static PyObject *py_gluecard3_setincr   (PyObject *, PyObject *);
	static PyObject *py_gluecard3_tracepr   (PyObject *, PyObject *);
	static PyObject *py_gluecard3_core      (PyObject *, PyObject *);
	static PyObject *py_gluecard3_model     (PyObject *, PyObject *);
	static PyObject *py_gluecard3_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_gluecard3_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_gluecard3_del       (PyObject *, PyObject *);
	static PyObject *py_gluecard3_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUECARD41
	static PyObject *py_gluecard41_new       (PyObject *, PyObject *);
	static PyObject *py_gluecard41_set_start (PyObject *, PyObject *);
	static PyObject *py_gluecard41_add_cl    (PyObject *, PyObject *);
	static PyObject *py_gluecard41_add_am    (PyObject *, PyObject *);
	static PyObject *py_gluecard41_solve     (PyObject *, PyObject *);
	static PyObject *py_gluecard41_solve_lim (PyObject *, PyObject *);
	static PyObject *py_gluecard41_propagate (PyObject *, PyObject *);
	static PyObject *py_gluecard41_setphases (PyObject *, PyObject *);
	static PyObject *py_gluecard41_cbudget   (PyObject *, PyObject *);
	static PyObject *py_gluecard41_pbudget   (PyObject *, PyObject *);
	static PyObject *py_gluecard41_interrupt (PyObject *, PyObject *);
	static PyObject *py_gluecard41_clearint  (PyObject *, PyObject *);
	static PyObject *py_gluecard41_setincr   (PyObject *, PyObject *);
	static PyObject *py_gluecard41_tracepr   (PyObject *, PyObject *);
	static PyObject *py_gluecard41_core      (PyObject *, PyObject *);
	static PyObject *py_gluecard41_model     (PyObject *, PyObject *);
	static PyObject *py_gluecard41_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_gluecard41_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_gluecard41_del       (PyObject *, PyObject *);
	static PyObject *py_gluecard41_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUCOSE30
	static PyObject *py_glucose3_new       (PyObject *, PyObject *);
	static PyObject *py_glucose3_set_start (PyObject *, PyObject *);
	static PyObject *py_glucose3_add_cl    (PyObject *, PyObject *);
	static PyObject *py_glucose3_solve     (PyObject *, PyObject *);
	static PyObject *py_glucose3_solve_lim (PyObject *, PyObject *);
	static PyObject *py_glucose3_propagate (PyObject *, PyObject *);
	static PyObject *py_glucose3_setphases (PyObject *, PyObject *);
	static PyObject *py_glucose3_cbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose3_pbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose3_interrupt (PyObject *, PyObject *);
	static PyObject *py_glucose3_clearint  (PyObject *, PyObject *);
	static PyObject *py_glucose3_setincr   (PyObject *, PyObject *);
	static PyObject *py_glucose3_tracepr   (PyObject *, PyObject *);
	static PyObject *py_glucose3_core      (PyObject *, PyObject *);
	static PyObject *py_glucose3_model     (PyObject *, PyObject *);
	static PyObject *py_glucose3_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_glucose3_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_glucose3_del       (PyObject *, PyObject *);
	static PyObject *py_glucose3_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUCOSE41
	static PyObject *py_glucose41_new       (PyObject *, PyObject *);
	static PyObject *py_glucose41_set_start (PyObject *, PyObject *);
	static PyObject *py_glucose41_add_cl    (PyObject *, PyObject *);
	static PyObject *py_glucose41_solve     (PyObject *, PyObject *);
	static PyObject *py_glucose41_solve_lim (PyObject *, PyObject *);
	static PyObject *py_glucose41_propagate (PyObject *, PyObject *);
	static PyObject *py_glucose41_setphases (PyObject *, PyObject *);
	static PyObject *py_glucose41_cbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose41_pbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose41_interrupt (PyObject *, PyObject *);
	static PyObject *py_glucose41_clearint  (PyObject *, PyObject *);
	static PyObject *py_glucose41_setincr   (PyObject *, PyObject *);
	static PyObject *py_glucose41_tracepr   (PyObject *, PyObject *);
	static PyObject *py_glucose41_core      (PyObject *, PyObject *);
	static PyObject *py_glucose41_model     (PyObject *, PyObject *);
	static PyObject *py_glucose41_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_glucose41_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_glucose41_del       (PyObject *, PyObject *);
	static PyObject *py_glucose41_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUCOSE421
	static PyObject *py_glucose421_new                   (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_start             (PyObject *, PyObject *);
	static PyObject *py_glucose421_add_cl                (PyObject *, PyObject *);
	static PyObject *py_glucose421_solve                 (PyObject *, PyObject *);
	static PyObject *py_glucose421_solve_lim             (PyObject *, PyObject *);
	static PyObject *py_glucose421_propagate             (PyObject *, PyObject *);
	static PyObject *py_glucose421_setphases             (PyObject *, PyObject *);
	static PyObject *py_glucose421_cbudget               (PyObject *, PyObject *);
	static PyObject *py_glucose421_pbudget               (PyObject *, PyObject *);
	static PyObject *py_glucose421_interrupt             (PyObject *, PyObject *);
	static PyObject *py_glucose421_clearint              (PyObject *, PyObject *);
	static PyObject *py_glucose421_setincr               (PyObject *, PyObject *);
	static PyObject *py_glucose421_tracepr               (PyObject *, PyObject *);
	static PyObject *py_glucose421_core                  (PyObject *, PyObject *);
	static PyObject *py_glucose421_model                 (PyObject *, PyObject *);
	static PyObject *py_glucose421_nof_vars              (PyObject *, PyObject *);
	static PyObject *py_glucose421_nof_cls               (PyObject *, PyObject *);
	static PyObject *py_glucose421_del                   (PyObject *, PyObject *);
	static PyObject *py_glucose421_acc_stats             (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_rnd_seed          (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_rnd_freq          (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_rnd_pol           (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_rnd_init_act      (PyObject *, PyObject *);
	static PyObject *py_glucose421_set_rnd_first_descent (PyObject *, PyObject *);
#endif
#ifdef WITH_LINGELING
	static PyObject *py_lingeling_new       (PyObject *, PyObject *);
	static PyObject *py_lingeling_add_cl    (PyObject *, PyObject *);
	static PyObject *py_lingeling_solve     (PyObject *, PyObject *);
	static PyObject *py_lingeling_setphases (PyObject *, PyObject *);
	static PyObject *py_lingeling_tracepr   (PyObject *, PyObject *);
	static PyObject *py_lingeling_core      (PyObject *, PyObject *);
	static PyObject *py_lingeling_model     (PyObject *, PyObject *);
	static PyObject *py_lingeling_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_lingeling_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_lingeling_del       (PyObject *, PyObject *);
	static PyObject *py_lingeling_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MAPLECHRONO
	static PyObject *py_maplechrono_new       (PyObject *, PyObject *);
	static PyObject *py_maplechrono_add_cl    (PyObject *, PyObject *);
	static PyObject *py_maplechrono_solve     (PyObject *, PyObject *);
	static PyObject *py_maplechrono_solve_lim (PyObject *, PyObject *);
	static PyObject *py_maplechrono_propagate (PyObject *, PyObject *);
	static PyObject *py_maplechrono_setphases (PyObject *, PyObject *);
	static PyObject *py_maplechrono_cbudget   (PyObject *, PyObject *);
	static PyObject *py_maplechrono_pbudget   (PyObject *, PyObject *);
	static PyObject *py_maplechrono_interrupt (PyObject *, PyObject *);
	static PyObject *py_maplechrono_clearint  (PyObject *, PyObject *);
	static PyObject *py_maplechrono_tracepr   (PyObject *, PyObject *);
	static PyObject *py_maplechrono_core      (PyObject *, PyObject *);
	static PyObject *py_maplechrono_model     (PyObject *, PyObject *);
	static PyObject *py_maplechrono_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_maplechrono_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_maplechrono_del       (PyObject *, PyObject *);
	static PyObject *py_maplechrono_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MAPLECM
	static PyObject *py_maplecm_new       (PyObject *, PyObject *);
	static PyObject *py_maplecm_set_start (PyObject *, PyObject *);
	static PyObject *py_maplecm_add_cl    (PyObject *, PyObject *);
	static PyObject *py_maplecm_solve     (PyObject *, PyObject *);
	static PyObject *py_maplecm_solve_lim (PyObject *, PyObject *);
	static PyObject *py_maplecm_propagate (PyObject *, PyObject *);
	static PyObject *py_maplecm_setphases (PyObject *, PyObject *);
	static PyObject *py_maplecm_cbudget   (PyObject *, PyObject *);
	static PyObject *py_maplecm_pbudget   (PyObject *, PyObject *);
	static PyObject *py_maplecm_interrupt (PyObject *, PyObject *);
	static PyObject *py_maplecm_clearint  (PyObject *, PyObject *);
	static PyObject *py_maplecm_tracepr   (PyObject *, PyObject *);
	static PyObject *py_maplecm_core      (PyObject *, PyObject *);
	static PyObject *py_maplecm_model     (PyObject *, PyObject *);
	static PyObject *py_maplecm_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_maplecm_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_maplecm_del       (PyObject *, PyObject *);
	static PyObject *py_maplecm_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MAPLESAT
	static PyObject *py_maplesat_new       (PyObject *, PyObject *);
	static PyObject *py_maplesat_set_start (PyObject *, PyObject *);
	static PyObject *py_maplesat_add_cl    (PyObject *, PyObject *);
	static PyObject *py_maplesat_solve     (PyObject *, PyObject *);
	static PyObject *py_maplesat_solve_lim (PyObject *, PyObject *);
	static PyObject *py_maplesat_propagate (PyObject *, PyObject *);
	static PyObject *py_maplesat_setphases (PyObject *, PyObject *);
	static PyObject *py_maplesat_cbudget   (PyObject *, PyObject *);
	static PyObject *py_maplesat_pbudget   (PyObject *, PyObject *);
	static PyObject *py_maplesat_interrupt (PyObject *, PyObject *);
	static PyObject *py_maplesat_clearint  (PyObject *, PyObject *);
	static PyObject *py_maplesat_tracepr   (PyObject *, PyObject *);
	static PyObject *py_maplesat_core      (PyObject *, PyObject *);
	static PyObject *py_maplesat_model     (PyObject *, PyObject *);
	static PyObject *py_maplesat_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_maplesat_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_maplesat_del       (PyObject *, PyObject *);
	static PyObject *py_maplesat_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MERGESAT3
	static PyObject *py_mergesat3_new       (PyObject *, PyObject *);
	static PyObject *py_mergesat3_add_cl    (PyObject *, PyObject *);
	static PyObject *py_mergesat3_solve     (PyObject *, PyObject *);
	static PyObject *py_mergesat3_solve_lim (PyObject *, PyObject *);
	static PyObject *py_mergesat3_propagate (PyObject *, PyObject *);
	static PyObject *py_mergesat3_setphases (PyObject *, PyObject *);
	static PyObject *py_mergesat3_cbudget   (PyObject *, PyObject *);
	static PyObject *py_mergesat3_pbudget   (PyObject *, PyObject *);
	static PyObject *py_mergesat3_interrupt (PyObject *, PyObject *);
	static PyObject *py_mergesat3_clearint  (PyObject *, PyObject *);
	static PyObject *py_mergesat3_core      (PyObject *, PyObject *);
	static PyObject *py_mergesat3_model     (PyObject *, PyObject *);
	static PyObject *py_mergesat3_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_mergesat3_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_mergesat3_del       (PyObject *, PyObject *);
	static PyObject *py_mergesat3_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MINICARD
	static PyObject *py_minicard_new       (PyObject *, PyObject *);
	static PyObject *py_minicard_set_start (PyObject *, PyObject *);
	static PyObject *py_minicard_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minicard_add_am    (PyObject *, PyObject *);
	static PyObject *py_minicard_solve     (PyObject *, PyObject *);
	static PyObject *py_minicard_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minicard_propagate (PyObject *, PyObject *);
	static PyObject *py_minicard_setphases (PyObject *, PyObject *);
	static PyObject *py_minicard_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minicard_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minicard_interrupt (PyObject *, PyObject *);
	static PyObject *py_minicard_clearint  (PyObject *, PyObject *);
	static PyObject *py_minicard_core      (PyObject *, PyObject *);
	static PyObject *py_minicard_model     (PyObject *, PyObject *);
	static PyObject *py_minicard_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minicard_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minicard_del       (PyObject *, PyObject *);
	static PyObject *py_minicard_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MINISAT22
	static PyObject *py_minisat22_new       (PyObject *, PyObject *);
	static PyObject *py_minisat22_set_start (PyObject *, PyObject *);
	static PyObject *py_minisat22_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minisat22_solve     (PyObject *, PyObject *);
	static PyObject *py_minisat22_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minisat22_propagate (PyObject *, PyObject *);
	static PyObject *py_minisat22_setphases (PyObject *, PyObject *);
	static PyObject *py_minisat22_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minisat22_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minisat22_interrupt (PyObject *, PyObject *);
	static PyObject *py_minisat22_clearint  (PyObject *, PyObject *);
	static PyObject *py_minisat22_core      (PyObject *, PyObject *);
	static PyObject *py_minisat22_model     (PyObject *, PyObject *);
	static PyObject *py_minisat22_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minisat22_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minisat22_del       (PyObject *, PyObject *);
	static PyObject *py_minisat22_acc_stats (PyObject *, PyObject *);
#endif
#ifdef WITH_MINISATGH
	static PyObject *py_minisatgh_new       (PyObject *, PyObject *);
	static PyObject *py_minisatgh_set_start (PyObject *, PyObject *);
	static PyObject *py_minisatgh_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minisatgh_solve     (PyObject *, PyObject *);
	static PyObject *py_minisatgh_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minisatgh_propagate (PyObject *, PyObject *);
	static PyObject *py_minisatgh_setphases (PyObject *, PyObject *);
	static PyObject *py_minisatgh_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_interrupt (PyObject *, PyObject *);
	static PyObject *py_minisatgh_clearint  (PyObject *, PyObject *);
	static PyObject *py_minisatgh_core      (PyObject *, PyObject *);
	static PyObject *py_minisatgh_model     (PyObject *, PyObject *);
	static PyObject *py_minisatgh_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minisatgh_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_del       (PyObject *, PyObject *);
	static PyObject *py_minisatgh_acc_stats (PyObject *, PyObject *);
#endif
}

// module specification
//=============================================================================
static PyMethodDef module_methods[] = {
#ifdef WITH_CADICAL103
	{ "cadical103_new",       py_cadical103_new,       METH_VARARGS,      new_docstring },
	{ "cadical103_add_cl",    py_cadical103_add_cl,    METH_VARARGS,    addcl_docstring },
	{ "cadical103_solve",     py_cadical103_solve,     METH_VARARGS,    solve_docstring },
	{ "cadical103_solve_lim", py_cadical103_solve_lim, METH_VARARGS,      lim_docstring },
	{ "cadical103_cbudget",   py_cadical103_cbudget,   METH_VARARGS,  cbudget_docstring },
	{ "cadical103_dbudget",   py_cadical103_dbudget,   METH_VARARGS,  dbudget_docstring },
	{ "cadical103_tracepr",   py_cadical103_tracepr,   METH_VARARGS,  tracepr_docstring },
	{ "cadical103_core",      py_cadical103_core,      METH_VARARGS,     core_docstring },
	{ "cadical103_model",     py_cadical103_model,     METH_VARARGS,    model_docstring },
	{ "cadical103_nof_vars",  py_cadical103_nof_vars,  METH_VARARGS,    nvars_docstring },
	{ "cadical103_nof_cls",   py_cadical103_nof_cls,   METH_VARARGS,     ncls_docstring },
	{ "cadical103_del",       py_cadical103_del,       METH_VARARGS,      del_docstring },
	{ "cadical103_acc_stats", py_cadical103_acc_stats, METH_VARARGS, acc_stat_docstring },
#endif
#ifdef WITH_CADICAL153
	{ "cadical153_new",       py_cadical153_new,       METH_VARARGS,      new_docstring },
	{ "cadical153_set",       py_cadical153_set,       METH_VARARGS,      set_docstring },
	{ "cadical153_add_cl",    py_cadical153_add_cl,    METH_VARARGS,    addcl_docstring },
	{ "cadical153_solve",     py_cadical153_solve,     METH_VARARGS,    solve_docstring },
	{ "cadical153_solve_lim", py_cadical153_solve_lim, METH_VARARGS,      lim_docstring },
	{ "cadical153_propagate", py_cadical153_propagate, METH_VARARGS,     prop_docstring },
	{ "cadical153_setphases", py_cadical153_setphases, METH_VARARGS,   phases_docstring },
	{ "cadical153_cbudget",   py_cadical153_cbudget,   METH_VARARGS,  cbudget_docstring },
	{ "cadical153_dbudget",   py_cadical153_dbudget,   METH_VARARGS,  dbudget_docstring },
	{ "cadical153_process",   py_cadical153_process,   METH_VARARGS,  process_docstring },
	{ "cadical153_restore",   py_cadical153_restore,   METH_VARARGS,  restore_docstring },
	{ "cadical153_tracepr",   py_cadical153_tracepr,   METH_VARARGS,  tracepr_docstring },
	{ "cadical153_core",      py_cadical153_core,      METH_VARARGS,     core_docstring },
	{ "cadical153_model",     py_cadical153_model,     METH_VARARGS,    model_docstring },
	{ "cadical153_nof_vars",  py_cadical153_nof_vars,  METH_VARARGS,    nvars_docstring },
	{ "cadical153_nof_cls",   py_cadical153_nof_cls,   METH_VARARGS,     ncls_docstring },
	{ "cadical153_del",       py_cadical153_del,       METH_VARARGS,      del_docstring },
	{ "cadical153_acc_stats", py_cadical153_acc_stats, METH_VARARGS, acc_stat_docstring },
#endif
#ifdef WITH_CADICAL195
	{ "cadical195_new",       py_cadical195_new,       METH_VARARGS,      new_docstring },
	{ "cadical195_set",       py_cadical195_set,       METH_VARARGS,      set_docstring },
	{ "cadical195_add_cl",    py_cadical195_add_cl,    METH_VARARGS,    addcl_docstring },
	{ "cadical195_solve",     py_cadical195_solve,     METH_VARARGS,    solve_docstring },
	{ "cadical195_solve_lim", py_cadical195_solve_lim, METH_VARARGS,      lim_docstring },
	{ "cadical195_propagate", py_cadical195_propagate, METH_VARARGS,     prop_docstring },
	{ "cadical195_setphases", py_cadical195_setphases, METH_VARARGS,   phases_docstring },
	{ "cadical195_cbudget",   py_cadical195_cbudget,   METH_VARARGS,  cbudget_docstring },
	{ "cadical195_dbudget",   py_cadical195_dbudget,   METH_VARARGS,  dbudget_docstring },
	{ "cadical195_process",   py_cadical195_process,   METH_VARARGS,  process_docstring },
	{ "cadical195_restore",   py_cadical195_restore,   METH_VARARGS,  restore_docstring },
	{ "cadical195_tracepr",   py_cadical195_tracepr,   METH_VARARGS,  tracepr_docstring },
	{ "cadical195_core",      py_cadical195_core,      METH_VARARGS,     core_docstring },
	{ "cadical195_model",     py_cadical195_model,     METH_VARARGS,    model_docstring },
	{ "cadical195_nof_vars",  py_cadical195_nof_vars,  METH_VARARGS,    nvars_docstring },
	{ "cadical195_nof_cls",   py_cadical195_nof_cls,   METH_VARARGS,     ncls_docstring },
	{ "cadical195_del",       py_cadical195_del,       METH_VARARGS,      del_docstring },
	{ "cadical195_acc_stats", py_cadical195_acc_stats, METH_VARARGS, acc_stat_docstring },
	{ "cadical195_pconn",     py_cadical195_pconn,     METH_VARARGS,    pconn_docstring },
	{ "cadical195_pdisconn",  py_cadical195_pdisconn,  METH_VARARGS, pdisconn_docstring },
	{ "cadical195_penable",   py_cadical195_penable,   METH_VARARGS,  penable_docstring },
	{ "cadical195_pdisable",  py_cadical195_pdisable,  METH_VARARGS, pdisable_docstring },
	{ "cadical195_pactive",   py_cadical195_pactive,   METH_VARARGS,  pactive_docstring },
	{ "cadical195_vobserve",  py_cadical195_vobserve,  METH_VARARGS, vobserve_docstring },
	{ "cadical195_vignore",   py_cadical195_vignore,   METH_VARARGS,  vignore_docstring },
	{ "cadical195_vreset",    py_cadical195_vreset,    METH_VARARGS,   vreset_docstring },
	{ "cadical195_isdeclit",  py_cadical195_isdeclit,  METH_VARARGS, isdeclit_docstring },
#endif
#ifdef WITH_GLUECARD30
	{ "gluecard3_new",       py_gluecard3_new,       METH_VARARGS,       new_docstring },
	{ "gluecard3_set_start", py_gluecard3_set_start, METH_VARARGS,  setstart_docstring },
	{ "gluecard3_add_cl",    py_gluecard3_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "gluecard3_add_am",    py_gluecard3_add_am,    METH_VARARGS,     addam_docstring },
	{ "gluecard3_solve",     py_gluecard3_solve,     METH_VARARGS,     solve_docstring },
	{ "gluecard3_solve_lim", py_gluecard3_solve_lim, METH_VARARGS,       lim_docstring },
	{ "gluecard3_propagate", py_gluecard3_propagate, METH_VARARGS,      prop_docstring },
	{ "gluecard3_setphases", py_gluecard3_setphases, METH_VARARGS,    phases_docstring },
	{ "gluecard3_cbudget",   py_gluecard3_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "gluecard3_pbudget",   py_gluecard3_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "gluecard3_interrupt", py_gluecard3_interrupt, METH_VARARGS, interrupt_docstring },
	{ "gluecard3_clearint",  py_gluecard3_clearint,  METH_VARARGS,  clearint_docstring },
	{ "gluecard3_setincr",   py_gluecard3_setincr,   METH_VARARGS,   setincr_docstring },
	{ "gluecard3_tracepr",   py_gluecard3_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "gluecard3_core",      py_gluecard3_core,      METH_VARARGS,      core_docstring },
	{ "gluecard3_model",     py_gluecard3_model,     METH_VARARGS,     model_docstring },
	{ "gluecard3_nof_vars",  py_gluecard3_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "gluecard3_nof_cls",   py_gluecard3_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "gluecard3_del",       py_gluecard3_del,       METH_VARARGS,       del_docstring },
	{ "gluecard3_acc_stats", py_gluecard3_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_GLUECARD41
	{ "gluecard41_new",       py_gluecard41_new,       METH_VARARGS,       new_docstring },
	{ "gluecard41_set_start", py_gluecard41_set_start, METH_VARARGS,  setstart_docstring },
	{ "gluecard41_add_cl",    py_gluecard41_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "gluecard41_add_am",    py_gluecard41_add_am,    METH_VARARGS,     addam_docstring },
	{ "gluecard41_solve",     py_gluecard41_solve,     METH_VARARGS,     solve_docstring },
	{ "gluecard41_solve_lim", py_gluecard41_solve_lim, METH_VARARGS,       lim_docstring },
	{ "gluecard41_propagate", py_gluecard41_propagate, METH_VARARGS,      prop_docstring },
	{ "gluecard41_setphases", py_gluecard41_setphases, METH_VARARGS,    phases_docstring },
	{ "gluecard41_cbudget",   py_gluecard41_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "gluecard41_pbudget",   py_gluecard41_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "gluecard41_interrupt", py_gluecard41_interrupt, METH_VARARGS, interrupt_docstring },
	{ "gluecard41_clearint",  py_gluecard41_clearint,  METH_VARARGS,  clearint_docstring },
	{ "gluecard41_setincr",   py_gluecard41_setincr,   METH_VARARGS,   setincr_docstring },
	{ "gluecard41_tracepr",   py_gluecard41_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "gluecard41_core",      py_gluecard41_core,      METH_VARARGS,      core_docstring },
	{ "gluecard41_model",     py_gluecard41_model,     METH_VARARGS,     model_docstring },
	{ "gluecard41_nof_vars",  py_gluecard41_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "gluecard41_nof_cls",   py_gluecard41_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "gluecard41_del",       py_gluecard41_del,       METH_VARARGS,       del_docstring },
	{ "gluecard41_acc_stats", py_gluecard41_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_GLUCOSE30
	{ "glucose3_new",       py_glucose3_new,       METH_VARARGS,       new_docstring },
	{ "glucose3_set_start", py_glucose3_set_start, METH_VARARGS,  setstart_docstring },
	{ "glucose3_add_cl",    py_glucose3_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "glucose3_solve",     py_glucose3_solve,     METH_VARARGS,     solve_docstring },
	{ "glucose3_solve_lim", py_glucose3_solve_lim, METH_VARARGS,       lim_docstring },
	{ "glucose3_propagate", py_glucose3_propagate, METH_VARARGS,      prop_docstring },
	{ "glucose3_setphases", py_glucose3_setphases, METH_VARARGS,    phases_docstring },
	{ "glucose3_cbudget",   py_glucose3_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "glucose3_pbudget",   py_glucose3_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "glucose3_interrupt", py_glucose3_interrupt, METH_VARARGS, interrupt_docstring },
	{ "glucose3_clearint",  py_glucose3_clearint,  METH_VARARGS,  clearint_docstring },
	{ "glucose3_setincr",   py_glucose3_setincr,   METH_VARARGS,   setincr_docstring },
	{ "glucose3_tracepr",   py_glucose3_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "glucose3_core",      py_glucose3_core,      METH_VARARGS,      core_docstring },
	{ "glucose3_model",     py_glucose3_model,     METH_VARARGS,     model_docstring },
	{ "glucose3_nof_vars",  py_glucose3_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "glucose3_nof_cls",   py_glucose3_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "glucose3_del",       py_glucose3_del,       METH_VARARGS,       del_docstring },
	{ "glucose3_acc_stats", py_glucose3_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_GLUCOSE41
	{ "glucose41_new",       py_glucose41_new,       METH_VARARGS,       new_docstring },
	{ "glucose41_set_start", py_glucose41_set_start, METH_VARARGS,  setstart_docstring },
	{ "glucose41_add_cl",    py_glucose41_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "glucose41_solve",     py_glucose41_solve,     METH_VARARGS,     solve_docstring },
	{ "glucose41_solve_lim", py_glucose41_solve_lim, METH_VARARGS,       lim_docstring },
	{ "glucose41_propagate", py_glucose41_propagate, METH_VARARGS,      prop_docstring },
	{ "glucose41_setphases", py_glucose41_setphases, METH_VARARGS,    phases_docstring },
	{ "glucose41_cbudget",   py_glucose41_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "glucose41_pbudget",   py_glucose41_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "glucose41_interrupt", py_glucose41_interrupt, METH_VARARGS, interrupt_docstring },
	{ "glucose41_clearint",  py_glucose41_clearint,  METH_VARARGS,  clearint_docstring },
	{ "glucose41_setincr",   py_glucose41_setincr,   METH_VARARGS,   setincr_docstring },
	{ "glucose41_tracepr",   py_glucose41_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "glucose41_core",      py_glucose41_core,      METH_VARARGS,      core_docstring },
	{ "glucose41_model",     py_glucose41_model,     METH_VARARGS,     model_docstring },
	{ "glucose41_nof_vars",  py_glucose41_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "glucose41_nof_cls",   py_glucose41_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "glucose41_del",       py_glucose41_del,       METH_VARARGS,       del_docstring },
	{ "glucose41_acc_stats", py_glucose41_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_GLUCOSE421
	{ "glucose421_new",                   py_glucose421_new,                   METH_VARARGS,                    new_docstring },
	{ "glucose421_set_start",             py_glucose421_set_start,             METH_VARARGS,               setstart_docstring },
	{ "glucose421_add_cl",                py_glucose421_add_cl,                METH_VARARGS,                  addcl_docstring },
	{ "glucose421_solve",                 py_glucose421_solve,                 METH_VARARGS,                  solve_docstring },
	{ "glucose421_solve_lim",             py_glucose421_solve_lim,             METH_VARARGS,                    lim_docstring },
	{ "glucose421_propagate",             py_glucose421_propagate,             METH_VARARGS,                   prop_docstring },
	{ "glucose421_setphases",             py_glucose421_setphases,             METH_VARARGS,                 phases_docstring },
	{ "glucose421_cbudget",               py_glucose421_cbudget,               METH_VARARGS,                cbudget_docstring },
	{ "glucose421_pbudget",               py_glucose421_pbudget,               METH_VARARGS,                pbudget_docstring },
	{ "glucose421_interrupt",             py_glucose421_interrupt,             METH_VARARGS,              interrupt_docstring },
	{ "glucose421_clearint",              py_glucose421_clearint,              METH_VARARGS,               clearint_docstring },
	{ "glucose421_setincr",               py_glucose421_setincr,               METH_VARARGS,                setincr_docstring },
	{ "glucose421_tracepr",               py_glucose421_tracepr,               METH_VARARGS,                tracepr_docstring },
	{ "glucose421_core",                  py_glucose421_core,                  METH_VARARGS,                   core_docstring },
	{ "glucose421_model",                 py_glucose421_model,                 METH_VARARGS,                  model_docstring },
	{ "glucose421_nof_vars",              py_glucose421_nof_vars,              METH_VARARGS,                  nvars_docstring },
	{ "glucose421_nof_cls",               py_glucose421_nof_cls,               METH_VARARGS,                   ncls_docstring },
	{ "glucose421_del",                   py_glucose421_del,                   METH_VARARGS,                    del_docstring },
	{ "glucose421_acc_stats",             py_glucose421_acc_stats,             METH_VARARGS,               acc_stat_docstring },
	{ "glucose421_set_rnd_seed",          py_glucose421_set_rnd_seed,          METH_VARARGS,           set_rnd_seed_docstring },
	{ "glucose421_set_rnd_freq",          py_glucose421_set_rnd_freq,          METH_VARARGS,           set_rnd_freq_docstring },
	{ "glucose421_set_rnd_pol",           py_glucose421_set_rnd_pol,           METH_VARARGS,            set_rnd_pol_docstring },
	{ "glucose421_set_rnd_init_act",      py_glucose421_set_rnd_init_act,      METH_VARARGS,       set_rnd_init_act_docstring },
	{ "glucose421_set_rnd_first_descent", py_glucose421_set_rnd_first_descent, METH_VARARGS,  set_rnd_first_descent_docstring },
#endif
#ifdef WITH_LINGELING
	{ "lingeling_new",       py_lingeling_new,       METH_VARARGS,      new_docstring },
	{ "lingeling_add_cl",    py_lingeling_add_cl,    METH_VARARGS,    addcl_docstring },
	{ "lingeling_solve",     py_lingeling_solve,     METH_VARARGS,    solve_docstring },
	{ "lingeling_setphases", py_lingeling_setphases, METH_VARARGS,   phases_docstring },
	{ "lingeling_tracepr",   py_lingeling_tracepr,   METH_VARARGS,  tracepr_docstring },
	{ "lingeling_core",      py_lingeling_core,      METH_VARARGS,     core_docstring },
	{ "lingeling_model",     py_lingeling_model,     METH_VARARGS,    model_docstring },
	{ "lingeling_nof_vars",  py_lingeling_nof_vars,  METH_VARARGS,    nvars_docstring },
	{ "lingeling_nof_cls",   py_lingeling_nof_cls,   METH_VARARGS,     ncls_docstring },
	{ "lingeling_del",       py_lingeling_del,       METH_VARARGS,      del_docstring },
	{ "lingeling_acc_stats", py_lingeling_acc_stats, METH_VARARGS, acc_stat_docstring },
#endif
#ifdef WITH_MAPLECHRONO
	{ "maplechrono_new",       py_maplechrono_new,       METH_VARARGS,       new_docstring },
	{ "maplechrono_add_cl",    py_maplechrono_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "maplechrono_solve",     py_maplechrono_solve,     METH_VARARGS,     solve_docstring },
	{ "maplechrono_solve_lim", py_maplechrono_solve_lim, METH_VARARGS,       lim_docstring },
	{ "maplechrono_propagate", py_maplechrono_propagate, METH_VARARGS,      prop_docstring },
	{ "maplechrono_setphases", py_maplechrono_setphases, METH_VARARGS,    phases_docstring },
	{ "maplechrono_cbudget",   py_maplechrono_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "maplechrono_pbudget",   py_maplechrono_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "maplechrono_interrupt", py_maplechrono_interrupt, METH_VARARGS, interrupt_docstring },
	{ "maplechrono_clearint",  py_maplechrono_clearint,  METH_VARARGS,  clearint_docstring },
	{ "maplechrono_tracepr",   py_maplechrono_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "maplechrono_core",      py_maplechrono_core,      METH_VARARGS,      core_docstring },
	{ "maplechrono_model",     py_maplechrono_model,     METH_VARARGS,     model_docstring },
	{ "maplechrono_nof_vars",  py_maplechrono_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "maplechrono_nof_cls",   py_maplechrono_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "maplechrono_del",       py_maplechrono_del,       METH_VARARGS,       del_docstring },
	{ "maplechrono_acc_stats", py_maplechrono_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MAPLECM
	{ "maplecm_new",       py_maplecm_new,       METH_VARARGS,       new_docstring },
	{ "maplecm_set_start", py_maplecm_set_start, METH_VARARGS,  setstart_docstring },
	{ "maplecm_add_cl",    py_maplecm_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "maplecm_solve",     py_maplecm_solve,     METH_VARARGS,     solve_docstring },
	{ "maplecm_solve_lim", py_maplecm_solve_lim, METH_VARARGS,       lim_docstring },
	{ "maplecm_propagate", py_maplecm_propagate, METH_VARARGS,      prop_docstring },
	{ "maplecm_setphases", py_maplecm_setphases, METH_VARARGS,    phases_docstring },
	{ "maplecm_cbudget",   py_maplecm_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "maplecm_pbudget",   py_maplecm_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "maplecm_interrupt", py_maplecm_interrupt, METH_VARARGS, interrupt_docstring },
	{ "maplecm_clearint",  py_maplecm_clearint,  METH_VARARGS,  clearint_docstring },
	{ "maplecm_tracepr",   py_maplecm_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "maplecm_core",      py_maplecm_core,      METH_VARARGS,      core_docstring },
	{ "maplecm_model",     py_maplecm_model,     METH_VARARGS,     model_docstring },
	{ "maplecm_nof_vars",  py_maplecm_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "maplecm_nof_cls",   py_maplecm_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "maplecm_del",       py_maplecm_del,       METH_VARARGS,       del_docstring },
	{ "maplecm_acc_stats", py_maplecm_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MAPLESAT
	{ "maplesat_new",       py_maplesat_new,       METH_VARARGS,       new_docstring },
	{ "maplesat_set_start", py_maplesat_set_start, METH_VARARGS,  setstart_docstring },
	{ "maplesat_add_cl",    py_maplesat_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "maplesat_solve",     py_maplesat_solve,     METH_VARARGS,     solve_docstring },
	{ "maplesat_solve_lim", py_maplesat_solve_lim, METH_VARARGS,       lim_docstring },
	{ "maplesat_propagate", py_maplesat_propagate, METH_VARARGS,      prop_docstring },
	{ "maplesat_setphases", py_maplesat_setphases, METH_VARARGS,    phases_docstring },
	{ "maplesat_cbudget",   py_maplesat_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "maplesat_pbudget",   py_maplesat_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "maplesat_interrupt", py_maplesat_interrupt, METH_VARARGS, interrupt_docstring },
	{ "maplesat_clearint",  py_maplesat_clearint,  METH_VARARGS,  clearint_docstring },
	{ "maplesat_tracepr",   py_maplesat_tracepr,   METH_VARARGS,   tracepr_docstring },
	{ "maplesat_core",      py_maplesat_core,      METH_VARARGS,      core_docstring },
	{ "maplesat_model",     py_maplesat_model,     METH_VARARGS,     model_docstring },
	{ "maplesat_nof_vars",  py_maplesat_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "maplesat_nof_cls",   py_maplesat_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "maplesat_del",       py_maplesat_del,       METH_VARARGS,       del_docstring },
	{ "maplesat_acc_stats", py_maplesat_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MERGESAT3
	{ "mergesat3_new",       py_mergesat3_new,       METH_VARARGS,       new_docstring },
	{ "mergesat3_add_cl",    py_mergesat3_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "mergesat3_solve",     py_mergesat3_solve,     METH_VARARGS,     solve_docstring },
	{ "mergesat3_solve_lim", py_mergesat3_solve_lim, METH_VARARGS,       lim_docstring },
	{ "mergesat3_propagate", py_mergesat3_propagate, METH_VARARGS,      prop_docstring },
	{ "mergesat3_setphases", py_mergesat3_setphases, METH_VARARGS,    phases_docstring },
	{ "mergesat3_cbudget",   py_mergesat3_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "mergesat3_pbudget",   py_mergesat3_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "mergesat3_interrupt", py_mergesat3_interrupt, METH_VARARGS, interrupt_docstring },
	{ "mergesat3_clearint",  py_mergesat3_clearint,  METH_VARARGS,  clearint_docstring },
	{ "mergesat3_core",      py_mergesat3_core,      METH_VARARGS,      core_docstring },
	{ "mergesat3_model",     py_mergesat3_model,     METH_VARARGS,     model_docstring },
	{ "mergesat3_nof_vars",  py_mergesat3_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "mergesat3_nof_cls",   py_mergesat3_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "mergesat3_del",       py_mergesat3_del,       METH_VARARGS,       del_docstring },
	{ "mergesat3_acc_stats", py_mergesat3_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MINICARD
	{ "minicard_new",       py_minicard_new,       METH_VARARGS,       new_docstring },
	{ "minicard_set_start", py_minicard_set_start, METH_VARARGS,  setstart_docstring },
	{ "minicard_add_cl",    py_minicard_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "minicard_solve",     py_minicard_solve,     METH_VARARGS,     solve_docstring },
	{ "minicard_solve_lim", py_minicard_solve_lim, METH_VARARGS,       lim_docstring },
	{ "minicard_propagate", py_minicard_propagate, METH_VARARGS,      prop_docstring },
	{ "minicard_setphases", py_minicard_setphases, METH_VARARGS,    phases_docstring },
	{ "minicard_cbudget",   py_minicard_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "minicard_pbudget",   py_minicard_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "minicard_interrupt", py_minicard_interrupt, METH_VARARGS, interrupt_docstring },
	{ "minicard_clearint",  py_minicard_clearint,  METH_VARARGS,  clearint_docstring },
	{ "minicard_core",      py_minicard_core,      METH_VARARGS,      core_docstring },
	{ "minicard_model",     py_minicard_model,     METH_VARARGS,     model_docstring },
	{ "minicard_nof_vars",  py_minicard_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "minicard_nof_cls",   py_minicard_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "minicard_del",       py_minicard_del,       METH_VARARGS,       del_docstring },
	{ "minicard_add_am",    py_minicard_add_am,    METH_VARARGS,     addam_docstring },
	{ "minicard_acc_stats", py_minicard_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MINISAT22
	{ "minisat22_new",       py_minisat22_new,       METH_VARARGS,       new_docstring },
	{ "minisat22_set_start", py_minisat22_set_start, METH_VARARGS,  setstart_docstring },
	{ "minisat22_add_cl",    py_minisat22_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "minisat22_solve",     py_minisat22_solve,     METH_VARARGS,     solve_docstring },
	{ "minisat22_solve_lim", py_minisat22_solve_lim, METH_VARARGS,       lim_docstring },
	{ "minisat22_propagate", py_minisat22_propagate, METH_VARARGS,      prop_docstring },
	{ "minisat22_setphases", py_minisat22_setphases, METH_VARARGS,    phases_docstring },
	{ "minisat22_cbudget",   py_minisat22_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "minisat22_pbudget",   py_minisat22_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "minisat22_interrupt", py_minisat22_interrupt, METH_VARARGS, interrupt_docstring },
	{ "minisat22_clearint",  py_minisat22_clearint,  METH_VARARGS,  clearint_docstring },
	{ "minisat22_core",      py_minisat22_core,      METH_VARARGS,      core_docstring },
	{ "minisat22_model",     py_minisat22_model,     METH_VARARGS,     model_docstring },
	{ "minisat22_nof_vars",  py_minisat22_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "minisat22_nof_cls",   py_minisat22_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "minisat22_del",       py_minisat22_del,       METH_VARARGS,       del_docstring },
	{ "minisat22_acc_stats", py_minisat22_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
#ifdef WITH_MINISATGH
	{ "minisatgh_new",       py_minisatgh_new,       METH_VARARGS,       new_docstring },
	{ "minisatgh_set_start", py_minisatgh_set_start, METH_VARARGS,  setstart_docstring },
	{ "minisatgh_add_cl",    py_minisatgh_add_cl,    METH_VARARGS,     addcl_docstring },
	{ "minisatgh_solve",     py_minisatgh_solve,     METH_VARARGS,     solve_docstring },
	{ "minisatgh_solve_lim", py_minisatgh_solve_lim, METH_VARARGS,       lim_docstring },
	{ "minisatgh_propagate", py_minisatgh_propagate, METH_VARARGS,      prop_docstring },
	{ "minisatgh_setphases", py_minisatgh_setphases, METH_VARARGS,    phases_docstring },
	{ "minisatgh_cbudget",   py_minisatgh_cbudget,   METH_VARARGS,   cbudget_docstring },
	{ "minisatgh_pbudget",   py_minisatgh_pbudget,   METH_VARARGS,   pbudget_docstring },
	{ "minisatgh_interrupt", py_minisatgh_interrupt, METH_VARARGS, interrupt_docstring },
	{ "minisatgh_clearint",  py_minisatgh_clearint,  METH_VARARGS,  clearint_docstring },
	{ "minisatgh_core",      py_minisatgh_core,      METH_VARARGS,      core_docstring },
	{ "minisatgh_model",     py_minisatgh_model,     METH_VARARGS,     model_docstring },
	{ "minisatgh_nof_vars",  py_minisatgh_nof_vars,  METH_VARARGS,     nvars_docstring },
	{ "minisatgh_nof_cls",   py_minisatgh_nof_cls,   METH_VARARGS,      ncls_docstring },
	{ "minisatgh_del",       py_minisatgh_del,       METH_VARARGS,       del_docstring },
	{ "minisatgh_acc_stats", py_minisatgh_acc_stats, METH_VARARGS,  acc_stat_docstring },
#endif
	{ NULL, NULL, 0, NULL }
};

extern "C" {

// signal handler for SIGINT
//=============================================================================
static void sigint_handler(int signum)
{
	longjmp(env, -1);
}

#if PY_MAJOR_VERSION >= 3
// PyInt_asLong()
//=============================================================================
static int pyint_to_cint(PyObject *i_obj)
{
	return PyLong_AsLong(i_obj);
}

// PyInt_fromLong()
//=============================================================================
static PyObject *pyint_from_cint(int i)
{
	return PyLong_FromLong(i);
}

// PyInt_Check()
//=============================================================================
static int pyint_check(PyObject *i_obj)
{
	return PyLong_Check(i_obj);
}

// PyCapsule_New()
//=============================================================================
static PyObject *void_to_pyobj(void *ptr)
{
	return PyCapsule_New(ptr, NULL, NULL);
}

// PyCapsule_GetPointer()
//=============================================================================
static void *pyobj_to_void(PyObject *obj)
{
	return PyCapsule_GetPointer(obj, NULL);
}

// module initialization
//=============================================================================
static struct PyModuleDef module_def = {
	PyModuleDef_HEAD_INIT,
	"pysolvers",       /* m_name */
	module_docstring,  /* m_doc */
	-1,                /* m_size */
	module_methods,    /* m_methods */
	NULL,              /* m_reload */
	NULL,              /* m_traverse */
	NULL,              /* m_clear */
	NULL,              /* m_free */
};

PyMODINIT_FUNC PyInit_pysolvers(void)
{
	PyObject *m = PyModule_Create(&module_def);

	if (m == NULL)
		return NULL;

	SATError = PyErr_NewException((char *)"pysolvers.error", NULL, NULL);
	Py_INCREF(SATError);

	if (PyModule_AddObject(m, "error", SATError) < 0) {
		Py_DECREF(SATError);
		return NULL;
	}

	return m;
}
#else
// PyInt_asLong()
//=============================================================================
static int pyint_to_cint(PyObject *i_obj)
{
	return PyInt_AsLong(i_obj);
}

// PyInt_fromLong()
//=============================================================================
static PyObject *pyint_from_cint(int i)
{
	return PyInt_FromLong(i);
}

// PyInt_Check()
//=============================================================================
static int pyint_check(PyObject *i_obj)
{
	return PyInt_Check(i_obj);
}

// PyCObject_FromVoidPtr()
//=============================================================================
static PyObject *void_to_pyobj(void *ptr)
{
	return PyCObject_FromVoidPtr(ptr, NULL);
}

// PyCObject_AsVoidPtr()
//=============================================================================
static void *pyobj_to_void(PyObject *obj)
{
	return PyCObject_AsVoidPtr(obj);
}

// module initialization
//=============================================================================
PyMODINIT_FUNC initpysolvers(void)
{
	PyObject *m = Py_InitModule3("pysolvers", module_methods,
			module_docstring);

	if (m == NULL)
		return;

	SATError = PyErr_NewException((char *)"pysolvers.error", NULL, NULL);
	Py_INCREF(SATError);
	PyModule_AddObject(m, "error", SATError);
}
#endif

// auxiliary function for translating an iterable to a vector<int>
//=============================================================================
static bool pyiter_to_vector(PyObject *obj, vector<int>& vect, int& max_var)
{
	PyObject *i_obj = PyObject_GetIter(obj);

	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		vect.push_back(l);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}
// auxiliary function for translating an iterable to a vector<PyObject*>
//=============================================================================
static bool pyiter_to_pyitervector(PyObject *obj, vector<PyObject*>& vect)
{
	PyObject *i_obj = PyObject_GetIter(obj);

	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!PyList_Check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			// TODO also need to decref everything in vect
			PyErr_SetString(PyExc_TypeError, "list expected");
			return false;
		}
		Py_INCREF(l_obj); // TODO check if we need to do this
		vect.push_back(l_obj); // we don't decref it because we need to keep the reference to it
	}

	Py_DECREF(i_obj);
	return true;
}

// auxiliary function for converting a C++ vector to a Python list
// this might be inefficient as we construct a new list and
// populate it with the values of the vector
//=============================================================================
PyObject *vector_to_pylist(const std::vector<int> &vec) {
	PyObject *pylist = PyList_New(vec.size());
	if (pylist == NULL) {
		PyErr_SetString(PyExc_RuntimeError, "Could not create python list from vector.");
		return NULL;
	}

	Py_ssize_t index = 0;
	for (auto v = vec.cbegin(); v != vec.cend(); ++v) {
		PyObject *pyv = pyint_from_cint(*v);
		if (pyv == NULL) {
			Py_DECREF(pylist);
			PyErr_SetString(PyExc_RuntimeError, "Could not create python int from int in vector.");
			return NULL;
		}
		PyList_SET_ITEM(pylist, index, pyv);
		index++;
	}

	return pylist;
}

// API for CaDiCaL 1.0.3
//=============================================================================
#ifdef WITH_CADICAL103
static PyObject *py_cadical103_new(PyObject *self, PyObject *args)
{
	CaDiCaL103::Solver *s = new CaDiCaL103::Solver;

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

//
//=============================================================================
static PyObject *py_cadical103_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	// clause iterator
	PyObject *i_obj = PyObject_GetIter(c_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Clause does not seem to be an iterable object.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->add(l);
	}

	s->add(0);
	Py_DECREF(i_obj);

	PyObject *ret = PyBool_FromLong((long)true);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical103_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->trace_proof(PyFile_AsFile(p_obj), "<py_fobj>");
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	FILE *cd_trace_fp = fdopen(fd, "w+");
	if (cd_trace_fp == NULL) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(cd_trace_fp);
	s->trace_proof(cd_trace_fp, "<py_fobj>");
	Py_INCREF(p_obj);
#endif

	s->set("binary", 0);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve() == 10 ? true : false;

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical103_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	int res = s->solve();
	res = (res == 10 ? 1 : (res == 20 ? -1 : 0));

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = pyint_from_cint(res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical103_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("conflicts", (int)budget);
	else
		s->limit("conflicts", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_dbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("decisions", (int)budget);
	else
		s->limit("decisions", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);

	vector<int> c;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);

		if (s->failed(l))
			c.push_back(l);
	}

	PyObject *core = PyList_New(c.size());
	for (size_t i = 0; i < c.size(); ++i) {
		PyObject *lit = pyint_from_cint(c[i]);
		PyList_SetItem(core, i, lit);
	}

	if (c.size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	int maxvar = s->vars();
	if (maxvar) {
		PyObject *model = PyList_New(maxvar);
		for (int i = 1; i <= maxvar; ++i) {
			int l = s->val(i) > 0 ? i : -i;

			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->vars();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical103_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->irredundant() + s->redundant();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical103_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (p_obj != Py_None)
		PyFile_DecUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (p_obj != Py_None)
		Py_DECREF(p_obj);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical103_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	CaDiCaL103::Solver *s = (CaDiCaL103::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->restarts(),
		"conflicts", (Py_ssize_t)s->conflicts(),
		"decisions", (Py_ssize_t)s->decisions(),
		"propagations", (Py_ssize_t)s->propagations()
	);
}
#endif  // WITH_CADICAL103

// API for CaDiCaL 1.5.3
//=============================================================================
#ifdef WITH_CADICAL153
static PyObject *py_cadical153_new(PyObject *self, PyObject *args)
{
	CaDiCaL153::Solver *s = new CaDiCaL153::Solver;

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

//
//=============================================================================
static PyObject *py_cadical153_set(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	const char *name;
	int64_t value;

	if (!PyArg_ParseTuple(args, "Osl", &s_obj, &name, &value))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// set the parameter
	CaDiCaL153::State temp = s->state();
	s->set_state(CaDiCaL153::State::CONFIGURING); // temporarily set state to configuring to enable option setting
	s->set(name, value);
	s->set_state(temp); // restore the original state

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// clause iterator
	PyObject *i_obj = PyObject_GetIter(c_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Clause does not seem to be an iterable object.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->add(l);
	}

	s->add(0);
	Py_DECREF(i_obj);

	PyObject *ret = PyBool_FromLong((long)true);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->trace_proof(PyFile_AsFile(p_obj), "<py_fobj>");
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	FILE *cd_trace_fp = fdopen(fd, "w+");
	if (cd_trace_fp == NULL) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(cd_trace_fp);
	s->trace_proof(cd_trace_fp, "<py_fobj>");
	Py_INCREF(p_obj);
#endif

	s->set("binary", 0);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_process(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int rounds;
	int block;
	int cover;
	int condition;
	int decompose;
	int elim;
	int probe;
	int probehbr;
	int subsume;
	int vivify;
	int main_thread;

        if (!PyArg_ParseTuple(args, "Oiiiiiiiiiii", &s_obj, &rounds, &block,
                              &cover, &condition, &decompose, &elim, &probe,
                              &probehbr, &subsume, &vivify, &main_thread))
          return NULL;

        // get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// set the options
	CaDiCaL153::State temp = s->state();
	s->set_state(CaDiCaL153::State::CONFIGURING); // temporarily set state to configuring to enable option setting
	s->set("block",     block    );
	s->set("cover",     cover    );
	s->set("condition", condition);
	s->set("decompose", decompose);
	s->set("elim",      elim     );
	s->set("probe",     probe    );
	s->set("probehbr",  probehbr );
	s->set("subsume",   subsume  );
	s->set("vivify",    vivify   );
	s->set_state(temp);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	vector<vector<int>> dest;
	int st = s->simplify(rounds);
	s->get_dimacs(dest);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	// creating the resulting clause set
	PyObject *dest_obj = PyList_New(dest.size());
	for (size_t i = 0; i < dest.size(); ++i) {
		PyObject *cl_obj = PyList_New(dest[i].size());

		for (size_t j = 0; j < dest[i].size(); ++j) {
			PyObject *lit_obj = pyint_from_cint(dest[i][j]);
			PyList_SetItem(cl_obj, j, lit_obj);
		}

		PyList_SetItem(dest_obj, i, cl_obj);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)st, dest_obj);
	Py_DECREF(dest_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_restore(PyObject *self, PyObject *args)
{
	PyObject *s_obj;  // solver
	PyObject *m_obj;  // model for the processed formula

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &m_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// model for the processed formula
	vector<int> pmod; int dummy_max;
	if (pyiter_to_vector(m_obj, pmod, dummy_max) == false)
		return NULL;

	// model for the original formula
	std::vector<bool> omod = s->extend(pmod);

	// translating it to Python List
	PyObject *ret = PyList_New(s->vars());
	for (size_t i = 1; i < omod.size(); i++)
		PyList_SetItem(ret, i - 1, pyint_from_cint(omod[i] ? +i : -i));

	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve() == 10 ? true : false;

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	int res = s->solve();
	res = (res == 10 ? 1 : (res == 20 ? -1 : 0));

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = pyint_from_cint(res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);
	std::vector<int> a;
	int max_var = -1;

	if (pyiter_to_vector(a_obj, a, max_var) == false)
		return NULL;

	if (s->vars() < max_var)
		s->reserve(max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	std::vector<int> p;
	bool res = s->prop_check(a, p, save_phases);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = p[i];
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(p_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->phase(l);
	}

	Py_DECREF(i_obj);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("conflicts", (int)budget);
	else
		s->limit("conflicts", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_dbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("decisions", (int)budget);
	else
		s->limit("decisions", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);

	vector<int> c;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);

		if (s->failed(l))
			c.push_back(l);
	}

	PyObject *core = PyList_New(c.size());
	for (size_t i = 0; i < c.size(); ++i) {
		PyObject *lit = pyint_from_cint(c[i]);
		PyList_SetItem(core, i, lit);
	}

	if (c.size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	int maxvar = s->vars();
	if (maxvar) {
		PyObject *model = PyList_New(maxvar);
		for (int i = 1; i <= maxvar; ++i) {
			int l = s->val(i) > 0 ? i : -i;

			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->vars();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->irredundant() + s->redundant();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical153_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (p_obj != Py_None)
		PyFile_DecUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (p_obj != Py_None)
		Py_DECREF(p_obj);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical153_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	CaDiCaL153::Solver *s = (CaDiCaL153::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->restarts(),
		"conflicts", (Py_ssize_t)s->conflicts(),
		"decisions", (Py_ssize_t)s->decisions(),
		"propagations", (Py_ssize_t)s->propagations()
	);
}
#endif  // WITH_CADICAL153

// API for CaDiCaL 1.9.5
//=============================================================================
#ifdef WITH_CADICAL195
static PyObject *py_cadical195_new(PyObject *self, PyObject *args)
{
	CaDiCaL195::Solver *s = new CaDiCaL195::Solver;

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

//
//=============================================================================
static PyObject *py_cadical195_set(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	const char *name;
	int64_t value;

	if (!PyArg_ParseTuple(args, "Osl", &s_obj, &name, &value))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// set the parameter
	CaDiCaL195::State temp = s->state();
	s->set_state(CaDiCaL195::State::CONFIGURING); // temporarily set state to configuring to enable option setting
	s->set(name, value);
	s->set_state(temp); // restore the original state

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// clause iterator
	PyObject *i_obj = PyObject_GetIter(c_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Clause does not seem to be an iterable object.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->add(l);
	}

	s->add(0);
	Py_DECREF(i_obj);

	PyObject *ret = PyBool_FromLong((long)true);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->trace_proof(PyFile_AsFile(p_obj), "<py_fobj>");
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	FILE *cd_trace_fp = fdopen(fd, "w+");
	if (cd_trace_fp == NULL) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(cd_trace_fp);
	s->trace_proof(cd_trace_fp, "<py_fobj>");
	Py_INCREF(p_obj);
#endif

	s->set("binary", 0);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_process(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int rounds;
	int block;
	int cover;
	int condition;
	int decompose;
	int elim;
	int probe;
	int probehbr;
	int subsume;
	int vivify;
	int main_thread;

        if (!PyArg_ParseTuple(args, "Oiiiiiiiiiii", &s_obj, &rounds, &block,
                              &cover, &condition, &decompose, &elim, &probe,
                              &probehbr, &subsume, &vivify, &main_thread))
          return NULL;

        // get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// set the options
	CaDiCaL195::State temp = s->state();
	s->set_state(CaDiCaL195::State::CONFIGURING); // temporarily set state to configuring to enable option setting
	s->set("block",     block    );
	s->set("cover",     cover    );
	s->set("condition", condition);
	s->set("decompose", decompose);
	s->set("elim",      elim     );
	s->set("probe",     probe    );
	s->set("probehbr",  probehbr );
	s->set("subsume",   subsume  );
	s->set("vivify",    vivify   );
	s->set_state(temp);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	vector<vector<int>> dest;
	int st = s->simplify(rounds);
	s->get_dimacs(dest);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	// creating the resulting clause set
	PyObject *dest_obj = PyList_New(dest.size());
	for (size_t i = 0; i < dest.size(); ++i) {
		PyObject *cl_obj = PyList_New(dest[i].size());

		for (size_t j = 0; j < dest[i].size(); ++j) {
			PyObject *lit_obj = pyint_from_cint(dest[i][j]);
			PyList_SetItem(cl_obj, j, lit_obj);
		}

		PyList_SetItem(dest_obj, i, cl_obj);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)st, dest_obj);
	Py_DECREF(dest_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_restore(PyObject *self, PyObject *args)
{
	PyObject *s_obj;  // solver
	PyObject *m_obj;  // model for the processed formula

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &m_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// model for the processed formula
	vector<int> pmod; int dummy_max;
	if (pyiter_to_vector(m_obj, pmod, dummy_max) == false)
		return NULL;

	// model for the original formula
	std::vector<bool> omod = s->extend(pmod);

	// translating it to Python List
	PyObject *ret = PyList_New(s->vars());
	for (size_t i = 1; i < omod.size(); i++)
		PyList_SetItem(ret, i - 1, pyint_from_cint(omod[i] ? +i : -i));

	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve() == 10 ? true : false;

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->assume(l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	int res = s->solve();
	res = (res == 10 ? 1 : (res == 20 ? -1 : 0));

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = pyint_from_cint(res);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);
	std::vector<int> a;
	int max_var = -1;

	if (pyiter_to_vector(a_obj, a, max_var) == false)
		return NULL;

	if (s->vars() < max_var)
		s->reserve(max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	std::vector<int> p;
	bool res = s->prop_check(a, p, save_phases);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = p[i];
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(p_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		s->phase(l);
	}

	Py_DECREF(i_obj);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("conflicts", (int)budget);
	else
		s->limit("conflicts", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_dbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->limit("decisions", (int)budget);
	else
		s->limit("decisions", -1);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);

	vector<int> c;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);

		if (s->failed(l))
			c.push_back(l);
	}

	PyObject *core = PyList_New(c.size());
	for (size_t i = 0; i < c.size(); ++i) {
		PyObject *lit = pyint_from_cint(c[i]);
		PyList_SetItem(core, i, lit);
	}

	if (c.size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	int maxvar = s->vars();
	if (maxvar) {
		PyObject *model = PyList_New(maxvar);
		for (int i = 1; i <= maxvar; ++i) {
			int l = s->val(i) > 0 ? i : -i;

			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->vars();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->irredundant() + s->redundant();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_cadical195_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (p_obj != Py_None)
		PyFile_DecUseCount((PyFileObject *)p_obj);
#else
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (p_obj != Py_None)
		Py_DECREF(p_obj);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->restarts(),
		"conflicts", (Py_ssize_t)s->conflicts(),
		"decisions", (Py_ssize_t)s->decisions(),
		"propagations", (Py_ssize_t)s->propagations()
	);
}

//
//=============================================================================
class PyExternalPropagator : public CaDiCaL195::ExternalPropagator {
private:
	PyObject *py_prop;
	std::vector<int> provide_reason_queue;
	std::vector<int> add_clause_queue;
	std::vector<int> propagations_queue;
	std::vector<PyObject*> reason_clauses; // if propagate_gives_reason = true
	std::vector<PyObject*> ext_clauses; // if multi_clause = true
public:
	bool passive;
	bool enable;
	bool disable;
	int zero_level;
	bool combined_has_clause;
	bool multi_clause;
	bool propagate_gives_reason;
	PyExternalPropagator (PyObject *py_propagator) {
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		py_prop = py_propagator;
		passive = enable = disable = false;
		zero_level = true;
		combined_has_clause = true;
		multi_clause = false;
		propagate_gives_reason = false;
	}

	// dereference the python propagator
	bool pyprop_delete() {
		if (py_prop == NULL) {
			return false;
		}
		Py_DECREF(py_prop);
		py_prop = NULL;
		return true;
	}
	// check if a python propagator is attached
	bool pyprop_has() {
		if (py_prop == NULL) {
			return false;
		}
		return true;
	}
	// attach a python propagator (for use if we later want to implement something that
	// allows us to detach and reattach propagators on the fly)
	bool pyprop_reattach(PyObject *py_propagator) {
		if (py_prop == NULL) {
			pyprop_delete();
		}
		py_prop = py_propagator;
		return true; // TODO add error checking
	}
	// Notify the propagator about assignments to observed variables.
	// The notification is not necessarily eager. It usually happens before
	// the call of propagator callbacks and when a driving clause is leading
	// to an assignment.
	//
	void notify_assignment (int lit, bool is_fixed) {
		if (!zero_level && passive && !is_fixed)
			return;

		PyObject *status = PyObject_CallMethod(py_prop, "on_assignment", "(ii)", lit, is_fixed, NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'on_assignment' in attached propagator.");
			return;
		}
		Py_DECREF(status);
	}
	void notify_new_decision_level () {
		if (enable && zero_level) {
			/* enabling at level 0 only! */
			passive = false;
			enable  = false;
		}

		zero_level = false;

		if (passive)
			return;

		PyObject *status = PyObject_CallMethod(py_prop, "on_new_level", "()", NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'on_new_level' in attached propagator.");
			return;
		}
		Py_DECREF(status);
	}
	void notify_backtrack (size_t new_level) {
		if (!passive) {
			if (PyErr_Occurred()) {
				PyErr_Print();
			}
			propagations_queue.clear(); // we need to clear propagation
						// queue when backtracking!

			PyObject *status = PyObject_CallMethod(py_prop, "on_backtrack", "(i)", (int)new_level, NULL);
			if (status == NULL) {
				PyErr_SetString(PyExc_RuntimeError, "Could not access method 'on_backtrack' in attached propagator.");
				return;
			}
			Py_DECREF(status);
		}

		zero_level = (new_level == 0);

		if (disable && zero_level) {
			/* disable at level 0 only! */
			passive = true;
			disable = false;
		}
	}

	// Check by the external propagator the found complete solution (after
	// solution reconstruction). If it returns false, the propagator must
	// provide an external clause during the next callback.
	//
	bool cb_check_found_model (const std::vector<int> &model) {
		// convert to python list
		PyObject *pylist = vector_to_pylist(model);

		if (pylist == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not convert from vector to python list.");
			return NULL;
		}
		if (PyErr_Occurred() == NULL) {
		}
		PyObject *status = PyObject_CallMethod(py_prop, "check_model", "(O)", pylist, NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'check_model' in attached propagator.");
			return NULL;
		}
		int res = PyObject_IsTrue(status);
		if (res == -1) {
			Py_DECREF(pylist);
			Py_DECREF(status);
			PyErr_SetString(PyExc_RuntimeError, "Error converting check_model return to C boolean");
			return NULL;
		}
		Py_DECREF(pylist);
		Py_DECREF(status);
		return res;
	}

	// Ask the external propagator for the next decision literal. If it
	// returns 0, the solver makes its own choice.
	//
	int cb_decide () {
		if (passive)
			return 0;

		PyObject *status = PyObject_CallMethod(py_prop, "decide", "()", NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'decide' in attached propagator.");
			return NULL;
		}
		int result = pyint_to_cint(status);

		if (PyErr_Occurred() != NULL) {
			Py_DECREF(status);
			PyErr_SetString(PyExc_RuntimeError, "Could not construct integer from PyObject.");
			return NULL;
		}
		Py_DECREF(status);
		return result;
	}

	// Ask the external propagator if there is an external propagation to make
	// under the current assignment. It returns either a literal to be
	// propagated or 0, indicating that there is no external propagation under
	// the current assignment.
	//
	int cb_propagate () {
		if (!zero_level && passive)
			return 0;

		int res = 0;
		// if propagate gives reason, we use reason_clauses queue
		if (propagate_gives_reason) {
			// if queue is empty
			if (reason_clauses.empty()) {
				// call python method
				PyObject *status = PyObject_CallMethod(py_prop, "propagate", "()", NULL);
				if (PyErr_Occurred()) {
					PyErr_Print();
				}
				if (status == NULL) {
					PyErr_SetString(PyExc_RuntimeError, "Could not access method 'propagate' in attached propagator.");
					return NULL;
				}

				// put into queue
				//check if the list is empty
				if (PyList_Check(status)) {
					if (PyList_GET_SIZE(status) > 0) {
						bool succ = pyiter_to_pyitervector(status, reason_clauses);
						if (!succ) {
							PyErr_SetString(PyExc_RuntimeError, "Could not convert return value of 'propagate' to vector.");
							Py_DECREF(status);
							return NULL;
						}
						reverse(reason_clauses.begin(), reason_clauses.end());
					}
				} else {
					Py_DECREF(status);
					PyErr_SetString(PyExc_TypeError, "Python method 'provide reason' did not give a list return value.");
					return NULL;
				}
				Py_DECREF(status);
			}
			if (!reason_clauses.empty()) {
				// get item from queue
				PyObject *sel = *reason_clauses.rbegin();
				// pop item
				reason_clauses.pop_back();
				// get first literal and put all values into add_reason_queue
				provide_reason_queue.clear();
				if (!PyList_Check(sel)) {
					PyErr_SetString(PyExc_TypeError, "'propagate' gave something that isn't a pylist.");
					Py_DECREF(sel);
					return NULL;
				}
				int plist_size = PyList_GET_SIZE(sel);
				if (plist_size < 1) {
					PyErr_SetString(PyExc_ValueError, "Propagate gave an empty reason clause.");
					Py_DECREF(sel);
					return NULL;
				}
				PyObject *plit = PyList_GET_ITEM(sel, 0); // get first item
				if (!pyint_check(plit)) {
					PyErr_SetString(PyExc_ValueError, "Propagate has a non-integer in its clauses.");
					Py_DECREF(plit);
					Py_DECREF(sel);
					return NULL;
				}
				res = pyint_to_cint(plit);
				provide_reason_queue.reserve(plist_size);
				for (int i = plist_size-1; i > 0; i--) {
					plit = PyList_GET_ITEM(sel, i); // get item
					if (!pyint_check(plit)) {
						PyErr_SetString(PyExc_ValueError, "Propagate has a non-integer in its clauses.");
						Py_DECREF(plit);
						Py_DECREF(sel);
						return NULL;
					}
					provide_reason_queue.push_back(pyint_to_cint(plit)); // push
					Py_DECREF(plit);
				}
				provide_reason_queue.push_back(res);
			}

			return res;
		}
		// if queue is empty
		if (propagations_queue.empty()) {
			// call python method
			PyObject *status = PyObject_CallMethod(py_prop, "propagate", "()", NULL);
			if (PyErr_Occurred()) {
				PyErr_Print();
			}
			if (status == NULL) {
				PyErr_SetString(PyExc_RuntimeError, "Could not access method 'propagate' in attached propagator.");
				return NULL;
			}
			if (propagate_gives_reason) { // get propagate to give: [[reason_clauses]] where first literal in clause is propagated

			}
			// put into queue
			int dummy_max = 0;
			//check if the list is empty
			if (PyList_Check(status)) {
				if (PyList_GET_SIZE(status) > 0) {
					pyiter_to_vector(status, propagations_queue, dummy_max);
					reverse(propagations_queue.begin(), propagations_queue.end());
				}
			} else {
				Py_DECREF(status);
				PyErr_SetString(PyExc_TypeError, "Python method 'propagate' did not give a list return value.");
				return NULL;
			}
			Py_DECREF(status);
		}
		if (!propagations_queue.empty()) {
			// get item from queue
			res = *propagations_queue.rbegin();
			// pop item
			propagations_queue.pop_back();
			// ensure we end with a 0
			if (propagations_queue.empty() && res != 0) {
				propagations_queue.push_back(0);
			}
		}

		return res;
	}

	// Ask the external propagator for the reason clause of a previous
	// external propagation step (done by cb_propagate). The clause must be
	// added literal-by-literal closed with a 0. Further, the clause must
	// contain the propagated literal.
	//
	int cb_add_reason_clause_lit (int propagated_lit) {
		if (!zero_level && passive)
			return 0;

		int res = 0;
		// if queue is empty
		if (provide_reason_queue.empty()) {
			if (propagate_gives_reason) {
				// error?
				PyErr_SetString(PyExc_RuntimeError, "provide reason queue is empty, but it shouldn't be?");
				return NULL;
			}
			// call python method
			PyObject *status = PyObject_CallMethod(py_prop, "provide_reason", "(i)", propagated_lit, NULL);
			if (PyErr_Occurred()) {
				PyErr_Print();
			}
			if (status == NULL) {
				PyErr_SetString(PyExc_RuntimeError, "Could not access method 'provide_reason' in attached propagator.");
				return NULL;
			}
			// put into queue
			int dummy_max = 0;
			//check if the list is empty
			if (PyList_Check(status)) {
				if (PyList_GET_SIZE(status) > 0) {
					pyiter_to_vector(status, provide_reason_queue, dummy_max);
				}
			} else {
				Py_DECREF(status);
				PyErr_SetString(PyExc_TypeError, "Python method 'provide reason' did not give a list return value.");
				return NULL;
			}
			Py_DECREF(status);
		}
		if (!provide_reason_queue.empty()) {
			// get item from queue
			res = *provide_reason_queue.rbegin();
			// pop item
			provide_reason_queue.pop_back();
			// ensure we end with a 0
			if (provide_reason_queue.empty() && res != 0) {
				provide_reason_queue.push_back(0);
			}
		}

		return res;
	}

	// The following two functions are used to add external clauses to the
	// solver during the CDCL loop. The external clause is added
	// literal-by-literal and learned by the solver as an irredundant
	// (original) input clause. The clause can be arbitrary, but if it is
	// root-satisfied or tautology, the solver will ignore it without learning
	// it. Root-falsified literals are eagerly removed from the clause.
	// Falsified clauses trigger conflict analysis, propagating clauses
	// trigger propagation. In case chrono is 0, the solver backtracks to
	// propagate the new literal on the right decision level, otherwise it
	// potentially will be an out-of-order assignment on the current level.
	// Unit clauses always (unless root-satisfied, see above) trigger
	// backtracking (independently from the value of the chrono option and
	// independently from being falsified or satisfied or unassigned) to level
	// 0. Empty clause (or root falsified clause, see above) makes the problem
	// unsat and stops the search immediately. A literal 0 must close the
	// clause.
	//
	// The external propagator indicates that there is a clause to add.
	//
	// TODO check if this works and polish it up
	bool py_callmethod_to_vec (const char *name,std::vector<int>& outvect_int, std::vector<PyObject*>& outvect_pyobj) {
		PyObject *status = PyObject_CallMethod(py_prop, "add_clause", "()", NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'add_clause' in attached propagator.");
			return false;
		}
		// put into queue
		int dummy_max = 0;
		bool succ;
		if (!multi_clause) { //fill in add_clause_queue
			succ = pyiter_to_vector(status, outvect_int, dummy_max); // is a list of literals
		} else { // fill in ext_clauses
			succ = pyiter_to_pyitervector(status, outvect_pyobj); // is a list of clauses
		}
		if (!succ) {
			Py_DECREF(status);
			PyErr_SetString(PyExc_RuntimeError, "Could not convert python iterable to vector.");
			return false;
		}
		Py_DECREF(status);
		if (multi_clause) {
			if (outvect_pyobj.empty()) {
				return true;
			}
			// put a clause from outvect_pyobj into outvect_int if not empty
			PyObject *sel = *outvect_pyobj.rbegin();
			outvect_pyobj.pop_back();
			if (!pyiter_to_vector(sel, outvect_int, dummy_max)) {
				Py_DECREF(sel);
				PyErr_SetString(PyExc_RuntimeError, "Could not convert python iterable to vector.");
				return false;
			}
			Py_DECREF(sel);
		}
		return true;
	}
	bool cb_has_external_clause () {
		if (combined_has_clause) {
			if (!(add_clause_queue.empty())) {
				perror("Warning: calling has_external clause while clauses are still in queue");
				add_clause_queue.clear();
			}
			if ((!(ext_clauses.empty())) && multi_clause) { // add_clause_queue should be empty
				// put item from ext_clauses into add_clause_queue
				int dummy_max = 0;
				// put a clause from outvect_pyobj into outvect_int
				PyObject *sel = *ext_clauses.rbegin();
				ext_clauses.pop_back();
				if (!pyiter_to_vector(sel, add_clause_queue, dummy_max)) {
					Py_DECREF(sel);
					PyErr_SetString(PyExc_RuntimeError, "Could not convert python iterable to vector.");
					return NULL;
				}
				Py_DECREF(sel);
				// return
				return !(add_clause_queue.empty());
			}
			// query has_clause
			if (!py_callmethod_to_vec("add_clause",add_clause_queue,ext_clauses)) {
				PyErr_Print();
				return NULL;
			}
			// if no clause, return false
			// if has clause, return true
			return !(add_clause_queue.empty());
		}
		PyObject *status = PyObject_CallMethod(py_prop, "has_clause", "()", NULL);
		if (PyErr_Occurred()) {
			PyErr_Print();
		}
		if (status == NULL) {
			PyErr_SetString(PyExc_RuntimeError, "Could not access method 'has_clause' in attached propagator.");
			return NULL;
		}
		int res = PyObject_IsTrue(status);
		if (res == -1) {
			Py_DECREF(status);
			PyErr_SetString(PyExc_RuntimeError, "Error converting has_clause return to C boolean");
			return NULL;
		}
		Py_DECREF(status);
		return res;
	}

	// The actual function called to add the external clause.
	//
	int cb_add_external_clause_lit () {
		if (combined_has_clause) {
			int val;
			// if queue empty, return 0
			if (add_clause_queue.empty()) {
				return 0;
			}
			// else pop from queue
			val = *add_clause_queue.rbegin();
			add_clause_queue.pop_back();
			return val;
		}
		int res = 0;
		// if queue is empty
		if ((!(ext_clauses.empty())) && multi_clause && (add_clause_queue.empty())) { // first check if we have a clause queued up
			// put item from ext_clauses into add_clause_queue
			int dummy_max = 0;
			// put a clause from outvect_pyobj into outvect_int
			PyObject *sel = *ext_clauses.rbegin();
			ext_clauses.pop_back();
			if (!pyiter_to_vector(sel, add_clause_queue, dummy_max)) {
				Py_DECREF(sel);
				PyErr_SetString(PyExc_RuntimeError, "Could not convert python iterable to vector.");
				return NULL;
			}
			Py_DECREF(sel);
		} else if (add_clause_queue.empty()) { // otherwise, call add_clause
			if (!py_callmethod_to_vec("add_clause",add_clause_queue,ext_clauses)) { // this should already load a clause into add_clause_queue
				PyErr_Print();
				return NULL;
			}
		}

		if (!add_clause_queue.empty()) {
			// get item from queue
			res = *add_clause_queue.rbegin();
			// pop item
			add_clause_queue.pop_back();
			// some safety if user forgets to terminate with 0
			if (add_clause_queue.empty() && res != 0) {
				add_clause_queue.push_back(0);
			}
		}

		return res;
	}
};

static PyObject *py_cadical195_pconn(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *py_prop; // should be an already initialised version of the propagator
	if (!PyArg_ParseTuple(args, "OO", &s_obj, &py_prop))
		return NULL;

	Py_INCREF(py_prop);
	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	// create C class for the external propagator
	PyExternalPropagator *cprop = new PyExternalPropagator(py_prop);

	// attach propagator
	s->connect_external_propagator(cprop);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_pdisconn(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);
	// TODO get the external propagator and Py_DECREF it (will need to extend solver.cpp with patch) - done but need to test
	PyExternalPropagator *cprop = (PyExternalPropagator*)(s->get_external_propagator());
	s->disconnect_external_propagator();
	cprop->pyprop_delete();
	delete cprop;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_penable(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);
	// get external propagator
	PyExternalPropagator *cprop = (PyExternalPropagator*)(s->get_external_propagator());

	if (cprop->zero_level || !cprop->passive) {
		// we are at level 0 => enable it now
		// alternatively, it is already active so
		// we need to turn off the flag "enable"
		cprop->passive = false;
		cprop->enable  = false;
	}
	else  // otherwise, mark as to enable in the future if currently passive
		cprop->enable = true;

	// if there was previously a flag to disable, drop it
	cprop->disable = false;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_pdisable(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);
	// get external propagator
	PyExternalPropagator *cprop = (PyExternalPropagator*)(s->get_external_propagator());

	if (cprop->zero_level || cprop->passive) {
		// we are at level 0 => disable it now
		// alternatively, it is already passive and
		// we need to turn off the flag "disable"
		cprop->passive = true;
		cprop->disable = false;
	}
	else  // otherwise, mark as to disable in the future if currently active
		cprop->disable = true;

	// if there was previously a flag to enable, drop it
	cprop->enable = false;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_pactive(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);
	// get external propagator
	PyExternalPropagator *cprop = (PyExternalPropagator*)(s->get_external_propagator());

	if (cprop->passive)
		Py_RETURN_FALSE;
	else
		Py_RETURN_TRUE;
}

//
//=============================================================================
static PyObject *py_cadical195_vobserve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int var;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &var))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	s->add_observed_var(var);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_vignore(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int var;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &var))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	s->remove_observed_var(var);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_vreset(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	s->reset_observed_vars();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_cadical195_isdeclit(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int lit;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &lit))
		return NULL;

	// get pointer to solver
	CaDiCaL195::Solver *s = (CaDiCaL195::Solver *)pyobj_to_void(s_obj);

	if (s->is_decision(lit))
		return Py_True;
	else
		return Py_False;
}
#endif  // WITH_CADICAL195

// API for Gluecard 3.0
//=============================================================================
#ifdef WITH_GLUECARD30
static PyObject *py_gluecard3_new(PyObject *self, PyObject *args)
{
	Gluecard30::Solver *s = new Gluecard30::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void gluecard3_declare_vars(Gluecard30::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool gluecard3_iterate(
	PyObject *obj,
	Gluecard30::vec<Gluecard30::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Gluecard30::mkLit(l, false) : Gluecard30::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_gluecard3_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	Gluecard30::vec<Gluecard30::Lit> cl;
	int max_var = -1;

	if (gluecard3_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_add_am(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;
	int64_t rhs;

	if (!PyArg_ParseTuple(args, "OOl", &s_obj, &c_obj, &rhs))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	Gluecard30::vec<Gluecard30::Lit> cl;
	int max_var = -1;

	if (gluecard3_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	bool res = s->addAtMost(cl, rhs);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	Gluecard30::vec<Gluecard30::Lit> a;
	int max_var = -1;

	if (gluecard3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	Gluecard30::vec<Gluecard30::Lit> a;
	int max_var = -1;

	if (gluecard3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	Gluecard30::lbool res = Gluecard30::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Gluecard30::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Gluecard30::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_gluecard3_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	Gluecard30::vec<Gluecard30::Lit> a;
	int max_var = -1;

	if (gluecard3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Gluecard30::vec<Gluecard30::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Gluecard30::var(p[i]) * (Gluecard30::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard3_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_setincr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	s->setIncrementalMode();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->certifiedOutput = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->certifiedOutput = fdopen(fd, "w+");
	if (s->certifiedOutput == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->certifiedOutput);
	Py_INCREF(p_obj);
#endif

	s->certifiedUNSAT  = true;
	s->certifiedPyFile = (void *)p_obj;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	Gluecard30::vec<Gluecard30::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Gluecard30::var((*c)[i]) * (Gluecard30::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Gluecard30::vec<Gluecard30::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Gluecard30::lbool True = Gluecard30::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard30::Solver *s = (Gluecard30::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard3_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->certifiedUNSAT == true)
		PyFile_DecUseCount((PyFileObject *)(s->certifiedPyFile));
#else
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->certifiedUNSAT == true)
		Py_DECREF((PyObject *)s->certifiedPyFile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard3_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Gluecard30::Solver *s = (Gluecard30::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_GLUECARD30

// API for Gluecard 3.0
//=============================================================================
#ifdef WITH_GLUECARD41
static PyObject *py_gluecard41_new(PyObject *self, PyObject *args)
{
	Gluecard41::Solver *s = new Gluecard41::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void gluecard41_declare_vars(Gluecard41::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool gluecard41_iterate(
	PyObject *obj,
	Gluecard41::vec<Gluecard41::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Gluecard41::mkLit(l, false) : Gluecard41::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_gluecard41_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	Gluecard41::vec<Gluecard41::Lit> cl;
	int max_var = -1;

	if (gluecard41_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_add_am(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;
	int64_t rhs;

	if (!PyArg_ParseTuple(args, "OOl", &s_obj, &c_obj, &rhs))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	Gluecard41::vec<Gluecard41::Lit> cl;
	int max_var = -1;

	if (gluecard41_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	bool res = s->addAtMost(cl, rhs);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	Gluecard41::vec<Gluecard41::Lit> a;
	int max_var = -1;

	if (gluecard41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	Gluecard41::vec<Gluecard41::Lit> a;
	int max_var = -1;

	if (gluecard41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	Gluecard41::lbool res = Gluecard41::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Gluecard41::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Gluecard41::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_gluecard41_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	Gluecard41::vec<Gluecard41::Lit> a;
	int max_var = -1;

	if (gluecard41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Gluecard41::vec<Gluecard41::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Gluecard41::var(p[i]) * (Gluecard41::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		gluecard41_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_setincr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	s->setIncrementalMode();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->certifiedOutput = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->certifiedOutput = fdopen(fd, "w+");
	if (s->certifiedOutput == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->certifiedOutput);
	Py_INCREF(p_obj);
#endif

	s->certifiedUNSAT  = true;
	s->certifiedPyFile = (void *)p_obj;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	Gluecard41::vec<Gluecard41::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Gluecard41::var((*c)[i]) * (Gluecard41::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Gluecard41::vec<Gluecard41::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Gluecard41::lbool True = Gluecard41::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Gluecard41::Solver *s = (Gluecard41::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_gluecard41_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->certifiedUNSAT == true)
		PyFile_DecUseCount((PyFileObject *)(s->certifiedPyFile));
#else
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->certifiedUNSAT == true)
		Py_DECREF((PyObject *)s->certifiedPyFile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_gluecard41_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Gluecard41::Solver *s = (Gluecard41::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_GLUECARD41

// API for Glucose 3.0
//=============================================================================
#ifdef WITH_GLUCOSE30
static PyObject *py_glucose3_new(PyObject *self, PyObject *args)
{
	Glucose30::Solver *s = new Glucose30::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void glucose3_declare_vars(Glucose30::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool glucose3_iterate(
	PyObject *obj,
	Glucose30::vec<Glucose30::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Glucose30::mkLit(l, false) : Glucose30::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_glucose3_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);
	Glucose30::vec<Glucose30::Lit> cl;
	int max_var = -1;

	if (glucose3_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);
	Glucose30::vec<Glucose30::Lit> a;
	int max_var = -1;

	if (glucose3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);
	Glucose30::vec<Glucose30::Lit> a;
	int max_var = -1;

	if (glucose3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	Glucose30::lbool res = Glucose30::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Glucose30::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Glucose30::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_glucose3_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);
	Glucose30::vec<Glucose30::Lit> a;
	int max_var = -1;

	if (glucose3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Glucose30::vec<Glucose30::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Glucose30::var(p[i]) * (Glucose30::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_setincr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	s->setIncrementalMode();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose30::Solver *s = (Glucose30::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->certifiedOutput = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Glucose30::Solver *s = (Glucose30::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->certifiedOutput = fdopen(fd, "w+");
	if (s->certifiedOutput == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->certifiedOutput);
	Py_INCREF(p_obj);
#endif

	s->certifiedUNSAT  = true;
	s->certifiedPyFile = (void *)p_obj;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	Glucose30::vec<Glucose30::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Glucose30::var((*c)[i]) * (Glucose30::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Glucose30::vec<Glucose30::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Glucose30::lbool True = Glucose30::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose30::Solver *s = (Glucose30::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->certifiedUNSAT == true)
		PyFile_DecUseCount((PyFileObject *)(s->certifiedPyFile));
#else
	Glucose30::Solver *s = (Glucose30::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->certifiedUNSAT == true)
		Py_DECREF((PyObject *)s->certifiedPyFile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose3_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose30::Solver *s = (Glucose30::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Glucose30::Solver *s = (Glucose30::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_GLUCOSE30

// API for Glucose 4.1
//=============================================================================
#ifdef WITH_GLUCOSE41
static PyObject *py_glucose41_new(PyObject *self, PyObject *args)
{
	Glucose41::Solver *s = new Glucose41::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void glucose41_declare_vars(Glucose41::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool glucose41_iterate(
	PyObject *obj,
	Glucose41::vec<Glucose41::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Glucose41::mkLit(l, false) : Glucose41::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_glucose41_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);
	Glucose41::vec<Glucose41::Lit> cl;
	int max_var = -1;

	if (glucose41_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);
	Glucose41::vec<Glucose41::Lit> a;
	int max_var = -1;

	if (glucose41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);
	Glucose41::vec<Glucose41::Lit> a;
	int max_var = -1;

	if (glucose41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	Glucose41::lbool res = Glucose41::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Glucose41::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Glucose41::toInt(res)));

	Py_RETURN_NONE; // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_glucose41_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);
	Glucose41::vec<Glucose41::Lit> a;
	int max_var = -1;

	if (glucose41_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Glucose41::vec<Glucose41::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Glucose41::var(p[i]) * (Glucose41::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_setincr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	s->setIncrementalMode();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose41::Solver *s = (Glucose41::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->certifiedOutput = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Glucose41::Solver *s = (Glucose41::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->certifiedOutput = fdopen(fd, "w+");
	if (s->certifiedOutput == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->certifiedOutput);
	Py_INCREF(p_obj);
#endif

	s->certifiedUNSAT  = true;
	s->certifiedPyFile = (void *)p_obj;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	Glucose41::vec<Glucose41::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Glucose41::var((*c)[i]) * (Glucose41::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Glucose41::vec<Glucose41::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Glucose41::lbool True = Glucose41::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose41::Solver *s = (Glucose41::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->certifiedUNSAT == true)
		PyFile_DecUseCount((PyFileObject *)(s->certifiedPyFile));
#else
	Glucose41::Solver *s = (Glucose41::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->certifiedUNSAT == true)
		Py_DECREF((PyObject *)s->certifiedPyFile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose41_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose41::Solver *s = (Glucose41::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Glucose41::Solver *s = (Glucose41::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_GLUCOSE41


// API for Glucose 4.1
//=============================================================================
#ifdef WITH_GLUCOSE421
static PyObject *py_glucose421_new(PyObject *self, PyObject *args)
{
	Glucose421::Solver *s = new Glucose421::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}
	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void glucose421_declare_vars(Glucose421::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool glucose421_iterate(
	PyObject *obj,
	Glucose421::vec<Glucose421::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Glucose421::mkLit(l, false) : Glucose421::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_glucose421_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	Glucose421::vec<Glucose421::Lit> cl;
	int max_var = -1;

	if (glucose421_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose421_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose421_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	Glucose421::vec<Glucose421::Lit> a;
	int max_var = -1;

	if (glucose421_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose421_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose421_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	Glucose421::vec<Glucose421::Lit> a;
	int max_var = -1;

	if (glucose421_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose421_declare_vars(s, max_var);

	Glucose421::lbool res = Glucose421::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Glucose421::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Glucose421::toInt(res)));

	Py_RETURN_NONE; // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_glucose421_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	Glucose421::vec<Glucose421::Lit> a;
	int max_var = -1;

	if (glucose421_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose421_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Glucose421::vec<Glucose421::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Glucose421::var(p[i]) * (Glucose421::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_glucose421_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		glucose421_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_setincr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	s->setIncrementalMode();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_set_rnd_seed(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	double dbl;

	if (!PyArg_ParseTuple(args, "Od", &s_obj, &dbl))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	
	s->random_seed = dbl;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_set_rnd_freq(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	double dbl;

	if (!PyArg_ParseTuple(args, "Od", &s_obj, &dbl))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	
	s->random_var_freq = dbl;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_set_rnd_pol(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int b;

	if (!PyArg_ParseTuple(args, "Op", &s_obj, &b))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	
	s->rnd_pol = (bool) b;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_set_rnd_init_act(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int b;

	if (!PyArg_ParseTuple(args, "Op", &s_obj, &b))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	
	s->rnd_init_act = (bool) b;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_set_rnd_first_descent(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int b;

	if (!PyArg_ParseTuple(args, "Op", &s_obj, &b))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);
	
	s->randomizeFirstDescent = (bool) b;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose421::Solver *s = (Glucose421::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->certifiedOutput = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Glucose421::Solver *s = (Glucose421::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->certifiedOutput = fdopen(fd, "w+");
	if (s->certifiedOutput == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->certifiedOutput);
	Py_INCREF(p_obj);
#endif

	s->certifiedUNSAT  = true;
	s->certifiedPyFile = (void *)p_obj;

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	Glucose421::vec<Glucose421::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Glucose421::var((*c)[i]) * (Glucose421::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Glucose421::vec<Glucose421::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Glucose421::lbool True = Glucose421::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose421_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Glucose421::Solver *s = (Glucose421::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose421_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose421::Solver *s = (Glucose421::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->certifiedUNSAT == true)
		PyFile_DecUseCount((PyFileObject *)(s->certifiedPyFile));
#else
	Glucose421::Solver *s = (Glucose421::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->certifiedUNSAT == true)
		Py_DECREF((PyObject *)s->certifiedPyFile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_glucose421_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Glucose421::Solver *s = (Glucose421::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Glucose421::Solver *s = (Glucose421::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_GLUCOSE421

// API for Lingeling
//=============================================================================
#ifdef WITH_LINGELING
static PyObject *py_lingeling_new(PyObject *self, PyObject *args)
{
	LGL *s = lglinit();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	lglsetopt(s, "simplify", 0);

	return void_to_pyobj((void *)s);
}

//
//=============================================================================
static PyObject *py_lingeling_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	// clause iterator
	PyObject *i_obj = PyObject_GetIter(c_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Clause does not seem to be an iterable object.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		lgladd(s, l);
		lglfreeze(s, abs(l));
	}

	lgladd(s, 0);
	Py_DECREF(i_obj);

	PyObject *ret = PyBool_FromLong((long)true);
	return ret;
}

//
//=============================================================================
static PyObject *py_lingeling_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	LGL *s = (LGL *)PyCObject_AsVoidPtr(s_obj);

	lglsetrace(s, PyFile_AsFile(p_obj));
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	LGL *s = (LGL *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	FILE *lgl_trace_fp = fdopen(fd, "w+");
	if (lgl_trace_fp == NULL) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(lgl_trace_fp);
	lglsetrace(s, lgl_trace_fp);
	Py_INCREF(p_obj);
#endif

	lglsetopt (s, "druplig", 1);
	lglsetopt (s, "drupligtrace", 2);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_lingeling_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	// assumptions iterator
	PyObject *i_obj = PyObject_GetIter(a_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		lglassume(s, l);
	}

	Py_DECREF(i_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = lglsat(s) == 10 ? true : false;

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_lingeling_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	// phases iterator
	PyObject *i_obj = PyObject_GetIter(p_obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return NULL;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return NULL;
		}

		int lit = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (lit == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return NULL;
		}

		lglsetphase(s, lit);
	}

	Py_DECREF(i_obj);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_lingeling_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);

	vector<int> c;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);

		if (lglfailed(s, l))
			c.push_back(l);
	}

	PyObject *core = PyList_New(c.size());
	for (size_t i = 0; i < c.size(); ++i) {
		PyObject *lit = pyint_from_cint(c[i]);
		PyList_SetItem(core, i, lit);
	}

	if (c.size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_lingeling_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	int maxvar = lglmaxvar(s);
	if (maxvar) {
		PyObject *model = PyList_New(maxvar);
		for (int i = 1; i <= maxvar; ++i) {
			int l = lglderef(s, i) > 0 ? i : -i;

			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_lingeling_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	int nof_vars = lglmaxvar(s);

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_lingeling_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	int nof_cls = lglnclauses(s);

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_lingeling_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	LGL *s = (LGL *)PyCObject_AsVoidPtr(s_obj);

	if (p_obj != Py_None)
		PyFile_DecUseCount((PyFileObject *)p_obj);
#else
	LGL *s = (LGL *)PyCapsule_GetPointer(s_obj, NULL);

	if (p_obj != Py_None)
		Py_DECREF(p_obj);
#endif

	lglrelease(s);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_lingeling_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)lglgetrests(s),
		"conflicts", (Py_ssize_t)lglgetconfs(s),
		"decisions", (Py_ssize_t)lglgetdecs(s),
		"propagations", (Py_ssize_t)lglgetprops(s)
	);
}
#endif  // WITH_LINGELING

// API for MapleChrono
//=============================================================================
#ifdef WITH_MAPLECHRONO
static PyObject *py_maplechrono_new(PyObject *self, PyObject *args)
{
	MapleChrono::Solver *s = new MapleChrono::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void maplechrono_declare_vars(
	MapleChrono::Solver *s,
	const int max_id
)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool maplechrono_iterate(
	PyObject *obj,
	MapleChrono::vec<MapleChrono::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? MapleChrono::mkLit(l, false) : MapleChrono::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_maplechrono_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);
	MapleChrono::vec<MapleChrono::Lit> cl;
	int max_var = -1;

	if (maplechrono_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplechrono_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplechrono_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);
	MapleChrono::vec<MapleChrono::Lit> a;
	int max_var = -1;

	if (maplechrono_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplechrono_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplechrono_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);
	MapleChrono::vec<MapleChrono::Lit> a;
	int max_var = -1;

	if (maplechrono_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplechrono_declare_vars(s, max_var);

	MapleChrono::lbool res = MapleChrono::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != MapleChrono::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(MapleChrono::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_maplechrono_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);
	MapleChrono::vec<MapleChrono::Lit> a;
	int max_var = -1;

	if (maplechrono_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplechrono_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	MapleChrono::vec<MapleChrono::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = MapleChrono::var(p[i]) * (MapleChrono::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_maplechrono_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplechrono_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->drup_file = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->drup_file = fdopen(fd, "w+");
	if (s->drup_file == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->drup_file);
	Py_INCREF(p_obj);
#endif

	s->drup_pyfile = (void *)p_obj;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	MapleChrono::vec<MapleChrono::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = MapleChrono::var((*c)[i]) * (MapleChrono::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	MapleChrono::vec<MapleChrono::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		MapleChrono::lbool True = MapleChrono::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplechrono_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleChrono::Solver *s = (MapleChrono::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplechrono_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->drup_file)
		PyFile_DecUseCount((PyFileObject *)(s->drup_pyfile));
#else
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->drup_file)
		Py_DECREF((PyObject *)s->drup_pyfile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplechrono_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	MapleChrono::Solver *s = (MapleChrono::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MAPLECHRONO

// API for Maplesat
//=============================================================================
#ifdef WITH_MAPLESAT
static PyObject *py_maplesat_new(PyObject *self, PyObject *args)
{
	Maplesat::Solver *s = new Maplesat::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void maplesat_declare_vars(
	Maplesat::Solver *s,
	const int max_id
)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool maplesat_iterate(
	PyObject *obj,
	Maplesat::vec<Maplesat::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Maplesat::mkLit(l, false) : Maplesat::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_maplesat_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);
	Maplesat::vec<Maplesat::Lit> cl;
	int max_var = -1;

	if (maplesat_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplesat_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplesat_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);
	Maplesat::vec<Maplesat::Lit> a;
	int max_var = -1;

	if (maplesat_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplesat_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplesat_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);
	Maplesat::vec<Maplesat::Lit> a;
	int max_var = -1;

	if (maplesat_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplesat_declare_vars(s, max_var);

	Maplesat::lbool res = Maplesat::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Maplesat::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Maplesat::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_maplesat_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);
	Maplesat::vec<Maplesat::Lit> a;
	int max_var = -1;

	if (maplesat_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplesat_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Maplesat::vec<Maplesat::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Maplesat::var(p[i]) * (Maplesat::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_maplesat_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplesat_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Maplesat::Solver *s = (Maplesat::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->drup_file = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	Maplesat::Solver *s = (Maplesat::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->drup_file = fdopen(fd, "w+");
	if (s->drup_file == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->drup_file);
	Py_INCREF(p_obj);
#endif

	s->drup_pyfile = (void *)p_obj;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	Maplesat::vec<Maplesat::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Maplesat::var((*c)[i]) * (Maplesat::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Maplesat::vec<Maplesat::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Maplesat::lbool True = Maplesat::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplesat_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Maplesat::Solver *s = (Maplesat::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplesat_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Maplesat::Solver *s = (Maplesat::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->drup_file)
		PyFile_DecUseCount((PyFileObject *)(s->drup_pyfile));
#else
	Maplesat::Solver *s = (Maplesat::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->drup_file)
		Py_DECREF((PyObject *)s->drup_pyfile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplesat_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Maplesat::Solver *s = (Maplesat::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Maplesat::Solver *s = (Maplesat::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MAPLESAT

// API for MapleCM
//=============================================================================
#ifdef WITH_MAPLECM
static PyObject *py_maplecm_new(PyObject *self, PyObject *args)
{
	MapleCM::Solver *s = new MapleCM::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void maplecm_declare_vars(
	MapleCM::Solver *s,
	const int max_id
)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool maplecm_iterate(
	PyObject *obj,
	MapleCM::vec<MapleCM::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? MapleCM::mkLit(l, false) : MapleCM::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_maplecm_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);
	MapleCM::vec<MapleCM::Lit> cl;
	int max_var = -1;

	if (maplecm_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplecm_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplecm_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);
	MapleCM::vec<MapleCM::Lit> a;
	int max_var = -1;

	if (maplecm_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplecm_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplecm_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);
	MapleCM::vec<MapleCM::Lit> a;
	int max_var = -1;

	if (maplecm_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplecm_declare_vars(s, max_var);

	MapleCM::lbool res = MapleCM::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != MapleCM::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(MapleCM::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_maplecm_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);
	MapleCM::vec<MapleCM::Lit> a;
	int max_var = -1;

	if (maplecm_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplecm_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	MapleCM::vec<MapleCM::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = MapleCM::var(p[i]) * (MapleCM::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_maplecm_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		maplecm_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_tracepr(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleCM::Solver *s = (MapleCM::Solver *)PyCObject_AsVoidPtr(s_obj);

	s->drup_file = PyFile_AsFile(p_obj);
	PyFile_IncUseCount((PyFileObject *)p_obj);
#else
	MapleCM::Solver *s = (MapleCM::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	int fd = PyObject_AsFileDescriptor(p_obj);
	if (fd == -1) {
		PyErr_SetString(SATError, "Cannot create proof file descriptor!");
		return NULL;
	}

	s->drup_file = fdopen(fd, "w+");
	if (s->drup_file == 0) {
		PyErr_SetString(SATError, "Cannot create proof file pointer!");
		return NULL;
	}

	setlinebuf(s->drup_file);
	Py_INCREF(p_obj);
#endif

	s->drup_pyfile = (void *)p_obj;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	MapleCM::vec<MapleCM::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = MapleCM::var((*c)[i]) * (MapleCM::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	MapleCM::vec<MapleCM::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		MapleCM::lbool True = MapleCM::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplecm_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MapleCM::Solver *s = (MapleCM::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_maplecm_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleCM::Solver *s = (MapleCM::Solver *)PyCObject_AsVoidPtr(s_obj);

	if (s->drup_file)
		PyFile_DecUseCount((PyFileObject *)(s->drup_pyfile));
#else
	MapleCM::Solver *s = (MapleCM::Solver *)PyCapsule_GetPointer(s_obj, NULL);

	if (s->drup_file)
		Py_DECREF((PyObject *)s->drup_pyfile);
#endif

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_maplecm_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MapleCM::Solver *s = (MapleCM::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	MapleCM::Solver *s = (MapleCM::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MAPLECM

// API for MergeSat 3
//=============================================================================
#ifdef WITH_MERGESAT3
static PyObject *py_mergesat3_new(PyObject *self, PyObject *args)
{
	MergeSat3::Solver *s = new MergeSat3::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void mergesat3_declare_vars(MergeSat3::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool mergesat3_iterate(
	PyObject *obj,
	MergeSat3::vec<MergeSat3::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? MergeSat3::mkLit(l, false) : MergeSat3::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_mergesat3_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);
	MergeSat3::vec<MergeSat3::Lit> cl;
	int max_var = -1;

	if (mergesat3_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		mergesat3_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_mergesat3_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);
	MergeSat3::vec<MergeSat3::Lit> a;
	int max_var = -1;

	if (mergesat3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		mergesat3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_mergesat3_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);
	MergeSat3::vec<MergeSat3::Lit> a;
	int max_var = -1;

	if (mergesat3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		mergesat3_declare_vars(s, max_var);

	MergeSat3::lbool res = MergeSat3::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != MergeSat3::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(MergeSat3::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_mergesat3_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);
	MergeSat3::vec<MergeSat3::Lit> a;
	int max_var = -1;

	if (mergesat3_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		mergesat3_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	MergeSat3::vec<MergeSat3::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = MergeSat3::var(p[i]) * (MergeSat3::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_mergesat3_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		mergesat3_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	MergeSat3::vec<MergeSat3::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = MergeSat3::var((*c)[i]) * (MergeSat3::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	MergeSat3::vec<MergeSat3::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		MergeSat3::lbool True = MergeSat3::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_mergesat3_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_mergesat3_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MergeSat3::Solver *s = (MergeSat3::Solver *)pyobj_to_void(s_obj);

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_mergesat3_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MergeSat3::Solver *s = (MergeSat3::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	MergeSat3::Solver *s = (MergeSat3::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MERGESAT3

// API for Minicard
//=============================================================================
#ifdef WITH_MINICARD
static PyObject *py_minicard_new(PyObject *self, PyObject *args)
{
	Minicard::Solver *s = new Minicard::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void minicard_declare_vars(Minicard::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool minicard_iterate(
	PyObject *obj,
	Minicard::vec<Minicard::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_minicard_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	Minicard::vec<Minicard::Lit> cl;
	int max_var = -1;

	if (minicard_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_add_am(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;
	int64_t rhs;

	if (!PyArg_ParseTuple(args, "OOl", &s_obj, &c_obj, &rhs))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	Minicard::vec<Minicard::Lit> cl;
	int max_var = -1;

	if (minicard_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	bool res = s->addAtMost(cl, rhs);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	Minicard::vec<Minicard::Lit> a;
	int max_var = -1;

	if (minicard_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	Minicard::vec<Minicard::Lit> a;
	int max_var = -1;

	if (minicard_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	Minicard::lbool res = Minicard::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Minicard::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Minicard::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_minicard_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	Minicard::vec<Minicard::Lit> a;
	int max_var = -1;

	if (minicard_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Minicard::vec<Minicard::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Minicard::var(p[i]) * (Minicard::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	Minicard::vec<Minicard::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Minicard::var((*c)[i]) * (Minicard::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Minicard::vec<Minicard::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Minicard::lbool True = Minicard::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minicard_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Minicard::Solver *s = (Minicard::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Minicard::Solver *s = (Minicard::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MINICARD

// API for MiniSat 2.2
//=============================================================================
#ifdef WITH_MINISAT22
static PyObject *py_minisat22_new(PyObject *self, PyObject *args)
{
	Minisat22::Solver *s = new Minisat22::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void minisat22_declare_vars(Minisat22::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool minisat22_iterate(
	PyObject *obj,
	Minisat22::vec<Minisat22::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? Minisat22::mkLit(l, false) : Minisat22::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_minisat22_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);
	Minisat22::vec<Minisat22::Lit> cl;
	int max_var = -1;

	if (minisat22_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);
	Minisat22::vec<Minisat22::Lit> a;
	int max_var = -1;

	if (minisat22_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);
	Minisat22::vec<Minisat22::Lit> a;
	int max_var = -1;

	if (minisat22_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	Minisat22::lbool res = Minisat22::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != Minisat22::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(Minisat22::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_minisat22_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);
	Minisat22::vec<Minisat22::Lit> a;
	int max_var = -1;

	if (minisat22_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	Minisat22::vec<Minisat22::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = Minisat22::var(p[i]) * (Minisat22::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), p[i] < 0);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	Minisat22::vec<Minisat22::Lit> *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = Minisat22::var((*c)[i]) * (Minisat22::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	Minisat22::vec<Minisat22::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		Minisat22::lbool True = Minisat22::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisat22_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	Minisat22::Solver *s = (Minisat22::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	Minisat22::Solver *s = (Minisat22::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MINISAT22

// API for MiniSat from github
//=============================================================================
#ifdef WITH_MINISATGH
static PyObject *py_minisatgh_new(PyObject *self, PyObject *args)
{
	MinisatGH::Solver *s = new MinisatGH::Solver();

	if (s == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Cannot create a new solver.");
		return NULL;
	}

	return void_to_pyobj((void *)s);
}

// auxiliary function for declaring new variables
//=============================================================================
static inline void minisatgh_declare_vars(MinisatGH::Solver *s, const int max_id)
{
	while (s->nVars() < max_id + 1)
		s->newVar();
}

// translating an iterable to vec<Lit>
//=============================================================================
static inline bool minisatgh_iterate(
	PyObject *obj,
	MinisatGH::vec<MinisatGH::Lit>& v,
	int& max_var
)
{
	// iterator object
	PyObject *i_obj = PyObject_GetIter(obj);
	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *l_obj;
	while ((l_obj = PyIter_Next(i_obj)) != NULL) {
		if (!pyint_check(l_obj)) {
			Py_DECREF(l_obj);
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_TypeError, "integer expected");
			return false;
		}

		int l = pyint_to_cint(l_obj);
		Py_DECREF(l_obj);

		if (l == 0) {
			Py_DECREF(i_obj);
			PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
			return false;
		}

		v.push((l > 0) ? MinisatGH::mkLit(l, false) : MinisatGH::mkLit(-l, true));

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_minisatgh_set_start(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int warm_start;

	if (!PyArg_ParseTuple(args, "Oi", &s_obj, &warm_start))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	s->setStartMode((bool)warm_start);

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_add_cl(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *c_obj;

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &c_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);
	MinisatGH::vec<MinisatGH::Lit> cl;
	int max_var = -1;

	if (minisatgh_iterate(c_obj, cl, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	bool res = s->addClause(cl);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_solve(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOi", &s_obj, &a_obj, &main_thread))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);
	MinisatGH::vec<MinisatGH::Lit> a;
	int max_var = -1;

	if (minisatgh_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	bool res = s->solve(a);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_solve_lim(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int main_thread;
	int expect_interrupt;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &main_thread,
				&expect_interrupt))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);
	MinisatGH::vec<MinisatGH::Lit> a;
	int max_var = -1;

	if (minisatgh_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	MinisatGH::lbool res = MinisatGH::lbool((uint8_t)2);  // l_Undef
	if (expect_interrupt == 0) {
		PyOS_sighandler_t sig_save;
		if (main_thread) {
			sig_save = PyOS_setsig(SIGINT, sigint_handler);

			if (setjmp(env) != 0) {
				PyErr_SetString(SATError, "Caught keyboard interrupt");
				return NULL;
			}
		}

		res = s->solveLimited(a);

		if (main_thread)
			PyOS_setsig(SIGINT, sig_save);
	}
	else {
		Py_BEGIN_ALLOW_THREADS
		res = s->solveLimited(a);
		Py_END_ALLOW_THREADS
	}

	if (res != MinisatGH::lbool((uint8_t)2))  // l_Undef
		return PyBool_FromLong((long)!(MinisatGH::toInt(res)));

	Py_RETURN_NONE;  // return Python's None if l_Undef
}

//
//=============================================================================
static PyObject *py_minisatgh_propagate(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *a_obj;  // assumptions
	int save_phases;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOii", &s_obj, &a_obj, &save_phases,
				&main_thread))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);
	MinisatGH::vec<MinisatGH::Lit> a;
	int max_var = -1;

	if (minisatgh_iterate(a_obj, a, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(SATError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	MinisatGH::vec<MinisatGH::Lit> p;
	bool res = s->prop_check(a, p, save_phases);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyObject *propagated = PyList_New(p.size());
	for (int i = 0; i < p.size(); ++i) {
		int l = MinisatGH::var(p[i]) * (MinisatGH::sign(p[i]) ? -1 : 1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(propagated, i, lit);
	}

	PyObject *ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
	Py_DECREF(propagated);

	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_setphases(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	PyObject *p_obj;  // polarities given as a list of integer literals

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &p_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);
	vector<int> p;
	int max_var = -1;

	if (pyiter_to_vector(p_obj, p, max_var) == false)
		return NULL;

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	for (size_t i = 0; i < p.size(); ++i)
		s->setPolarity(abs(p[i]), MinisatGH::lbool(p[i] < 0));

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_cbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setConfBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_pbudget(PyObject *self, PyObject *args)
{
	PyObject *s_obj;
	int64_t budget;

	if (!PyArg_ParseTuple(args, "Ol", &s_obj, &budget))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	if (budget != 0 && budget != -1)  // it is 0 by default
		s->setPropBudget(budget);
	else
		s->budgetOff();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_interrupt(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	s->interrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_clearint(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	s->clearInterrupt();

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_core(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	MinisatGH::LSet *c = &(s->conflict);  // minisat's conflict

	PyObject *core = PyList_New(c->size());
	for (int i = 0; i < c->size(); ++i) {
		int l = MinisatGH::var((*c)[i]) * (MinisatGH::sign((*c)[i]) ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(core, i, lit);
	}

	if (c->size()) {
		PyObject *ret = Py_BuildValue("O", core);
		Py_DECREF(core);
		return ret;
	}

	Py_DECREF(core);
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_model(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	// minisat's model
	MinisatGH::vec<MinisatGH::lbool> *m = &(s->model);

	if (m->size()) {
		// l_True fails to work
		MinisatGH::lbool True = MinisatGH::lbool((uint8_t)0);

		PyObject *model = PyList_New(m->size() - 1);
		for (int i = 1; i < m->size(); ++i) {
			int l = i * ((*m)[i] == True ? 1 : -1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(model, i - 1, lit);
		}

		PyObject *ret = Py_BuildValue("O", model);
		Py_DECREF(model);
		return ret;
	}

	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_nof_vars(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	int nof_vars = s->nVars() - 1;  // 0 is a dummy variable

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_vars);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_nof_cls(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	int nof_cls = s->nClauses();

	PyObject *ret = Py_BuildValue("n", (Py_ssize_t)nof_cls);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_del(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	delete s;
	Py_RETURN_NONE;
}

//
//=============================================================================
static PyObject *py_minisatgh_acc_stats(PyObject *self, PyObject *args)
{
	PyObject *s_obj;

	if (!PyArg_ParseTuple(args, "O", &s_obj))
		return NULL;

	// get pointer to solver
#if PY_MAJOR_VERSION < 3
	MinisatGH::Solver *s = (MinisatGH::Solver *)PyCObject_AsVoidPtr(s_obj);
#else
	MinisatGH::Solver *s = (MinisatGH::Solver *)PyCapsule_GetPointer(s_obj, NULL);
#endif

	return Py_BuildValue("{s:n,s:n,s:n,s:n}",
		"restarts", (Py_ssize_t)s->starts,
		"conflicts", (Py_ssize_t)s->conflicts,
		"decisions", (Py_ssize_t)s->decisions,
		"propagations", (Py_ssize_t)s->propagations
	);
}
#endif  // WITH_MINISATGH

}  // extern "C"
