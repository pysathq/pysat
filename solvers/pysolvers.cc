/*
 * pysolvers.cc
 *
 *  Created on: Nov 26, 2016
 *      Author: aign
 */

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <vector>

#ifdef WITH_GLUCOSE30
#include "glucose30/core/Solver.h"
#endif

#ifdef WITH_GLUCOSE41
#include "glucose41/core/Solver.h"
#endif

#ifdef WITH_LINGELING
#include "lingeling/lglib.h"
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
static char  module_docstring[] = "This module provides a wrapper interface "
				  "for several SAT solvers.";
static char     new_docstring[] = "Create a new solver object.";
static char   addcl_docstring[] = "Add a clause to formula.";
static char   addam_docstring[] = "Add an atmost constraint to formula "
				  "(for Minicard only).";
static char   solve_docstring[] = "Solve a given CNF instance.";
static char     lim_docstring[] = "Solve a given CNF instance within a budget.";
static char    prop_docstring[] = "Propagate a given set of literals.";
static char cbudget_docstring[] = "Set limit on the number of conflicts.";
static char pbudget_docstring[] = "Set limit on the number of propagations.";
static char setincr_docstring[] = "Set incremental mode (for Glucose3 only).";
static char tracepr_docstring[] = "Trace resolution proof.";
static char    core_docstring[] = "Get an unsatisfiable core if formula is UNSAT.";
static char   model_docstring[] = "Get a model if formula is SAT.";
static char   nvars_docstring[] = "Get number of variables used by the solver.";
static char    ncls_docstring[] = "Get number of clauses used by the solver.";
static char     del_docstring[] = "Delete a previously created solver object.";

static PyObject *SATError;
static jmp_buf env;

// function declaration for functions available in module
//=============================================================================
extern "C" {
#ifdef WITH_GLUCOSE30
	static PyObject *py_glucose3_new       (PyObject *, PyObject *);
	static PyObject *py_glucose3_add_cl    (PyObject *, PyObject *);
	static PyObject *py_glucose3_solve     (PyObject *, PyObject *);
	static PyObject *py_glucose3_solve_lim (PyObject *, PyObject *);
	static PyObject *py_glucose3_propagate (PyObject *, PyObject *);
	static PyObject *py_glucose3_cbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose3_pbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose3_setincr   (PyObject *, PyObject *);
	static PyObject *py_glucose3_tracepr   (PyObject *, PyObject *);
	static PyObject *py_glucose3_core      (PyObject *, PyObject *);
	static PyObject *py_glucose3_model     (PyObject *, PyObject *);
	static PyObject *py_glucose3_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_glucose3_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_glucose3_del       (PyObject *, PyObject *);
#endif
#ifdef WITH_GLUCOSE41
	static PyObject *py_glucose41_new       (PyObject *, PyObject *);
	static PyObject *py_glucose41_add_cl    (PyObject *, PyObject *);
	static PyObject *py_glucose41_solve     (PyObject *, PyObject *);
	static PyObject *py_glucose41_solve_lim (PyObject *, PyObject *);
	static PyObject *py_glucose41_propagate (PyObject *, PyObject *);
	static PyObject *py_glucose41_cbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose41_pbudget   (PyObject *, PyObject *);
	static PyObject *py_glucose41_setincr   (PyObject *, PyObject *);
	static PyObject *py_glucose41_tracepr   (PyObject *, PyObject *);
	static PyObject *py_glucose41_core      (PyObject *, PyObject *);
	static PyObject *py_glucose41_model     (PyObject *, PyObject *);
	static PyObject *py_glucose41_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_glucose41_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_glucose41_del       (PyObject *, PyObject *);
#endif
#ifdef WITH_LINGELING
	static PyObject *py_lingeling_new       (PyObject *, PyObject *);
	static PyObject *py_lingeling_add_cl    (PyObject *, PyObject *);
	static PyObject *py_lingeling_solve     (PyObject *, PyObject *);
	static PyObject *py_lingeling_tracepr   (PyObject *, PyObject *);
	static PyObject *py_lingeling_core      (PyObject *, PyObject *);
	static PyObject *py_lingeling_model     (PyObject *, PyObject *);
	static PyObject *py_lingeling_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_lingeling_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_lingeling_del       (PyObject *, PyObject *);
#endif
#ifdef WITH_MINICARD
	static PyObject *py_minicard_new       (PyObject *, PyObject *);
	static PyObject *py_minicard_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minicard_add_am    (PyObject *, PyObject *);
	static PyObject *py_minicard_solve     (PyObject *, PyObject *);
	static PyObject *py_minicard_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minicard_propagate (PyObject *, PyObject *);
	static PyObject *py_minicard_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minicard_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minicard_core      (PyObject *, PyObject *);
	static PyObject *py_minicard_model     (PyObject *, PyObject *);
	static PyObject *py_minicard_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minicard_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minicard_del       (PyObject *, PyObject *);
#endif
#ifdef WITH_MINISAT22
	static PyObject *py_minisat22_new       (PyObject *, PyObject *);
	static PyObject *py_minisat22_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minisat22_solve     (PyObject *, PyObject *);
	static PyObject *py_minisat22_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minisat22_propagate (PyObject *, PyObject *);
	static PyObject *py_minisat22_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minisat22_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minisat22_core      (PyObject *, PyObject *);
	static PyObject *py_minisat22_model     (PyObject *, PyObject *);
	static PyObject *py_minisat22_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minisat22_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minisat22_del       (PyObject *, PyObject *);
#endif
#ifdef WITH_MINISATGH
	static PyObject *py_minisatgh_new       (PyObject *, PyObject *);
	static PyObject *py_minisatgh_add_cl    (PyObject *, PyObject *);
	static PyObject *py_minisatgh_solve     (PyObject *, PyObject *);
	static PyObject *py_minisatgh_solve_lim (PyObject *, PyObject *);
	static PyObject *py_minisatgh_propagate (PyObject *, PyObject *);
	static PyObject *py_minisatgh_cbudget   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_pbudget   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_core      (PyObject *, PyObject *);
	static PyObject *py_minisatgh_model     (PyObject *, PyObject *);
	static PyObject *py_minisatgh_nof_vars  (PyObject *, PyObject *);
	static PyObject *py_minisatgh_nof_cls   (PyObject *, PyObject *);
	static PyObject *py_minisatgh_del       (PyObject *, PyObject *);
#endif
}

// module specification
//=============================================================================
static PyMethodDef module_methods[] = {
#ifdef WITH_GLUCOSE30
	{ "glucose3_new",       py_glucose3_new,       METH_VARARGS,     new_docstring },
        { "glucose3_add_cl",    py_glucose3_add_cl,    METH_VARARGS,   addcl_docstring },
        { "glucose3_solve",     py_glucose3_solve,     METH_VARARGS,   solve_docstring },
        { "glucose3_solve_lim", py_glucose3_solve_lim, METH_VARARGS,     lim_docstring },
        { "glucose3_propagate", py_glucose3_propagate, METH_VARARGS,    prop_docstring },
        { "glucose3_cbudget",   py_glucose3_cbudget,   METH_VARARGS, cbudget_docstring },
        { "glucose3_pbudget",   py_glucose3_pbudget,   METH_VARARGS, pbudget_docstring },
        { "glucose3_setincr",   py_glucose3_setincr,   METH_VARARGS, setincr_docstring },
        { "glucose3_tracepr",   py_glucose3_tracepr,   METH_VARARGS, tracepr_docstring },
        { "glucose3_core",      py_glucose3_core,      METH_VARARGS,    core_docstring },
        { "glucose3_model",     py_glucose3_model,     METH_VARARGS,   model_docstring },
        { "glucose3_nof_vars",  py_glucose3_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "glucose3_nof_cls",   py_glucose3_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "glucose3_del",       py_glucose3_del,       METH_VARARGS,     del_docstring },
#endif
#ifdef WITH_GLUCOSE41
	{ "glucose41_new",       py_glucose41_new,       METH_VARARGS,     new_docstring },
        { "glucose41_add_cl",    py_glucose41_add_cl,    METH_VARARGS,   addcl_docstring },
        { "glucose41_solve",     py_glucose41_solve,     METH_VARARGS,   solve_docstring },
        { "glucose41_solve_lim", py_glucose41_solve_lim, METH_VARARGS,     lim_docstring },
        { "glucose41_propagate", py_glucose41_propagate, METH_VARARGS,    prop_docstring },
        { "glucose41_cbudget",   py_glucose41_cbudget,   METH_VARARGS, cbudget_docstring },
        { "glucose41_pbudget",   py_glucose41_pbudget,   METH_VARARGS, pbudget_docstring },
        { "glucose41_setincr",   py_glucose41_setincr,   METH_VARARGS, setincr_docstring },
        { "glucose41_tracepr",   py_glucose41_tracepr,   METH_VARARGS, tracepr_docstring },
        { "glucose41_core",      py_glucose41_core,      METH_VARARGS,    core_docstring },
        { "glucose41_model",     py_glucose41_model,     METH_VARARGS,   model_docstring },
        { "glucose41_nof_vars",  py_glucose41_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "glucose41_nof_cls",   py_glucose41_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "glucose41_del",       py_glucose41_del,       METH_VARARGS,     del_docstring },
#endif
#ifdef WITH_LINGELING
	{ "lingeling_new",       py_lingeling_new,       METH_VARARGS,     new_docstring },
        { "lingeling_add_cl",    py_lingeling_add_cl,    METH_VARARGS,   addcl_docstring },
        { "lingeling_solve",     py_lingeling_solve,     METH_VARARGS,   solve_docstring },
        { "lingeling_tracepr",   py_lingeling_tracepr,   METH_VARARGS, tracepr_docstring },
        { "lingeling_core",      py_lingeling_core,      METH_VARARGS,    core_docstring },
        { "lingeling_model",     py_lingeling_model,     METH_VARARGS,   model_docstring },
        { "lingeling_nof_vars",  py_lingeling_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "lingeling_nof_cls",   py_lingeling_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "lingeling_del",       py_lingeling_del,       METH_VARARGS,     del_docstring },
#endif
#ifdef WITH_MINICARD
	{ "minicard_new",       py_minicard_new,       METH_VARARGS,     new_docstring },
        { "minicard_add_cl",    py_minicard_add_cl,    METH_VARARGS,   addcl_docstring },
        { "minicard_solve",     py_minicard_solve,     METH_VARARGS,   solve_docstring },
        { "minicard_solve_lim", py_minicard_solve_lim, METH_VARARGS,     lim_docstring },
        { "minicard_propagate", py_minicard_propagate, METH_VARARGS,    prop_docstring },
        { "minicard_cbudget",   py_minicard_cbudget,   METH_VARARGS, cbudget_docstring },
        { "minicard_pbudget",   py_minicard_pbudget,   METH_VARARGS, pbudget_docstring },
        { "minicard_core",      py_minicard_core,      METH_VARARGS,    core_docstring },
        { "minicard_model",     py_minicard_model,     METH_VARARGS,   model_docstring },
        { "minicard_nof_vars",  py_minicard_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "minicard_nof_cls",   py_minicard_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "minicard_del",       py_minicard_del,       METH_VARARGS,     del_docstring },
        { "minicard_add_am",    py_minicard_add_am,    METH_VARARGS,   addam_docstring },
#endif
#ifdef WITH_MINISAT22
	{ "minisat22_new",       py_minisat22_new,       METH_VARARGS,     new_docstring },
        { "minisat22_add_cl",    py_minisat22_add_cl,    METH_VARARGS,   addcl_docstring },
        { "minisat22_solve",     py_minisat22_solve,     METH_VARARGS,   solve_docstring },
        { "minisat22_solve_lim", py_minisat22_solve_lim, METH_VARARGS,     lim_docstring },
        { "minisat22_propagate", py_minisat22_propagate, METH_VARARGS,    prop_docstring },
        { "minisat22_cbudget",   py_minisat22_cbudget,   METH_VARARGS, cbudget_docstring },
        { "minisat22_pbudget",   py_minisat22_pbudget,   METH_VARARGS, pbudget_docstring },
        { "minisat22_core",      py_minisat22_core,      METH_VARARGS,    core_docstring },
        { "minisat22_model",     py_minisat22_model,     METH_VARARGS,   model_docstring },
        { "minisat22_nof_vars",  py_minisat22_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "minisat22_nof_cls",   py_minisat22_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "minisat22_del",       py_minisat22_del,       METH_VARARGS,     del_docstring },
#endif
#ifdef WITH_MINISATGH
	{ "minisatgh_new",       py_minisatgh_new,       METH_VARARGS,     new_docstring },
        { "minisatgh_add_cl",    py_minisatgh_add_cl,    METH_VARARGS,   addcl_docstring },
        { "minisatgh_solve",     py_minisatgh_solve,     METH_VARARGS,   solve_docstring },
        { "minisatgh_solve_lim", py_minisatgh_solve_lim, METH_VARARGS,     lim_docstring },
        { "minisatgh_propagate", py_minisatgh_propagate, METH_VARARGS,    prop_docstring },
        { "minisatgh_cbudget",   py_minisatgh_cbudget,   METH_VARARGS, cbudget_docstring },
        { "minisatgh_pbudget",   py_minisatgh_pbudget,   METH_VARARGS, pbudget_docstring },
        { "minisatgh_core",      py_minisatgh_core,      METH_VARARGS,    core_docstring },
        { "minisatgh_model",     py_minisatgh_model,     METH_VARARGS,   model_docstring },
        { "minisatgh_nof_vars",  py_minisatgh_nof_vars,  METH_VARARGS,   nvars_docstring },
        { "minisatgh_nof_cls",   py_minisatgh_nof_cls,   METH_VARARGS,    ncls_docstring },
	{ "minisatgh_del",       py_minisatgh_del,       METH_VARARGS,     del_docstring },
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

	int size = (int)PyList_Size(c_obj);
	Glucose30::vec<Glucose30::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? Glucose30::mkLit(l, false) : Glucose30::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose30::vec<Glucose30::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose30::mkLit(l, false) : Glucose30::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = s->solve(a);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_solve_lim(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose30::vec<Glucose30::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose30::mkLit(l, false) : Glucose30::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Glucose30::lbool res = s->solveLimited(a);

	PyObject *ret;
	if (res != Glucose30::lbool((uint8_t)2))  // l_Undef
		ret = PyBool_FromLong((long)!(Glucose30::toInt(res)));
	else
		ret = Py_BuildValue("");  // return Python's None if l_Undef

	return ret;
}

//
//=============================================================================
static PyObject *py_glucose3_propagate(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose30::Solver *s = (Glucose30::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose30::vec<Glucose30::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose30::mkLit(l, false) : Glucose30::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose3_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Glucose30::vec<Glucose30::Lit> p;
	bool res = s->prop_check(a, p);

	PyObject *ret = Py_None;

	if (p.size()) {
		PyObject *propagated = PyList_New(p.size());
		for (int i = 0; i < p.size(); ++i) {
			int l = Glucose30::var(p[i]) * (Glucose30::sign(p[i]) ? -1 : 1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(propagated, i, lit);
		}

		ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
		Py_DECREF(propagated);
	}

	return ret;
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

	s->setConfBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	s->setPropBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_None;

	if (c->size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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

	Glucose30::vec<Glucose30::lbool> *m = &(s->model);  // minisat's model
	Glucose30::lbool True = Glucose30::lbool((uint8_t)0);  // l_True fails to work

	PyObject *model = PyList_New(m->size() - 1);
	for (int i = 1; i < m->size(); ++i) {
		int l = i * ((*m)[i] == True ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (m->size())
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	int size = (int)PyList_Size(c_obj);
	Glucose41::vec<Glucose41::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? Glucose41::mkLit(l, false) : Glucose41::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose41::vec<Glucose41::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose41::mkLit(l, false) : Glucose41::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = s->solve(a);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_solve_lim(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose41::vec<Glucose41::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose41::mkLit(l, false) : Glucose41::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Glucose41::lbool res = s->solveLimited(a);

	PyObject *ret;
	if (res != Glucose41::lbool((uint8_t)2))  // l_Undef
		ret = PyBool_FromLong((long)!(Glucose41::toInt(res)));
	else
		ret = Py_BuildValue("");  // return Python's None if l_Undef

	return ret;
}

//
//=============================================================================
static PyObject *py_glucose41_propagate(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Glucose41::Solver *s = (Glucose41::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Glucose41::vec<Glucose41::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Glucose41::mkLit(l, false) : Glucose41::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		glucose41_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Glucose41::vec<Glucose41::Lit> p;
	bool res = s->prop_check(a, p);

	PyObject *ret = Py_None;

	if (p.size()) {
		PyObject *propagated = PyList_New(p.size());
		for (int i = 0; i < p.size(); ++i) {
			int l = Glucose41::var(p[i]) * (Glucose41::sign(p[i]) ? -1 : 1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(propagated, i, lit);
		}

		ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
		Py_DECREF(propagated);
	}

	return ret;
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

	s->setConfBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	s->setPropBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_None;

	if (c->size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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

	Glucose41::vec<Glucose41::lbool> *m = &(s->model);  // minisat's model
	Glucose41::lbool True = Glucose41::lbool((uint8_t)0);  // l_True fails to work

	PyObject *model = PyList_New(m->size() - 1);
	for (int i = 1; i < m->size(); ++i) {
		int l = i * ((*m)[i] == True ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (m->size())
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
}
#endif  // WITH_GLUCOSE41

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

	int size = (int)PyList_Size(c_obj);

	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		lgladd(s, l);
		lglfreeze(s, abs(l));
	}

	lgladd(s, 0);

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

	PyObject *ret = Py_BuildValue("");
	return ret;
}

//
//=============================================================================
static PyObject *py_lingeling_solve(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	LGL *s = (LGL *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);

	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);

		lglassume(s, l);
	}

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = lglsat(s) == 10 ? true : false;

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
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

	PyObject *ret = Py_None;

	if (c.size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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
	PyObject *model = PyList_New(maxvar);
	for (int i = 1; i <= maxvar; ++i) {
		int l = lglderef(s, i) > 0 ? i : -i;

		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (maxvar)
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
}
#endif  // WITH_LINGELING

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

	int size = (int)PyList_Size(c_obj);
	Minicard::vec<Minicard::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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

	int size = (int)PyList_Size(c_obj);
	Minicard::vec<Minicard::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minicard::vec<Minicard::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = s->solve(a);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_solve_lim(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minicard::vec<Minicard::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Minicard::lbool res = s->solveLimited(a);

	PyObject *ret;
	if (res != Minicard::lbool((uint8_t)2))  // l_Undef
		ret = PyBool_FromLong((long)!(Minicard::toInt(res)));
	else
		ret = Py_BuildValue("");  // return Python's None if l_Undef

	return ret;
}

//
//=============================================================================
static PyObject *py_minicard_propagate(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minicard::Solver *s = (Minicard::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minicard::vec<Minicard::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minicard::mkLit(l, false) : Minicard::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minicard_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Minicard::vec<Minicard::Lit> p;
	bool res = s->prop_check(a, p);

	PyObject *ret = Py_None;

	if (p.size()) {
		PyObject *propagated = PyList_New(p.size());
		for (int i = 0; i < p.size(); ++i) {
			int l = Minicard::var(p[i]) * (Minicard::sign(p[i]) ? -1 : 1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(propagated, i, lit);
		}

		ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
		Py_DECREF(propagated);
	}

	return ret;
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

	s->setConfBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	s->setPropBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_None;

	if (c->size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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

	Minicard::vec<Minicard::lbool> *m = &(s->model);  // minisat's model
	Minicard::lbool True = Minicard::lbool((uint8_t)0);  // l_True fails to work

	PyObject *model = PyList_New(m->size() - 1);
	for (int i = 1; i < m->size(); ++i) {
		int l = i * ((*m)[i] == True ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (m->size())
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	int size = (int)PyList_Size(c_obj);
	Minisat22::vec<Minisat22::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? Minisat22::mkLit(l, false) : Minisat22::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minisat22::vec<Minisat22::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minisat22::mkLit(l, false) : Minisat22::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = s->solve(a);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_solve_lim(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minisat22::vec<Minisat22::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minisat22::mkLit(l, false) : Minisat22::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Minisat22::lbool res = s->solveLimited(a);

	PyObject *ret;
	if (res != Minisat22::lbool((uint8_t)2))  // l_Undef
		ret = PyBool_FromLong((long)!(Minisat22::toInt(res)));
	else
		ret = Py_BuildValue("");  // return Python's None if l_Undef

	return ret;
}

//
//=============================================================================
static PyObject *py_minisat22_propagate(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	Minisat22::Solver *s = (Minisat22::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	Minisat22::vec<Minisat22::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? Minisat22::mkLit(l, false) : Minisat22::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisat22_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	Minisat22::vec<Minisat22::Lit> p;
	bool res = s->prop_check(a, p);

	PyObject *ret = Py_None;

	if (p.size()) {
		PyObject *propagated = PyList_New(p.size());
		for (int i = 0; i < p.size(); ++i) {
			int l = Minisat22::var(p[i]) * (Minisat22::sign(p[i]) ? -1 : 1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(propagated, i, lit);
		}

		ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
		Py_DECREF(propagated);
	}

	return ret;
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

	s->setConfBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	s->setPropBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_None;

	if (c->size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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

	Minisat22::vec<Minisat22::lbool> *m = &(s->model);  // minisat's model
	Minisat22::lbool True = Minisat22::lbool((uint8_t)0);  // l_True fails to work

	PyObject *model = PyList_New(m->size() - 1);
	for (int i = 1; i < m->size(); ++i) {
		int l = i * ((*m)[i] == True ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (m->size())
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	int size = (int)PyList_Size(c_obj);
	MinisatGH::vec<MinisatGH::Lit> cl((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(c_obj, i);
		int l = pyint_to_cint(l_obj);
		cl[i] = (l > 0) ? MinisatGH::mkLit(l, false) : MinisatGH::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

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
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	MinisatGH::vec<MinisatGH::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? MinisatGH::mkLit(l, false) : MinisatGH::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	bool res = s->solve(a);

	PyObject *ret = PyBool_FromLong((long)res);
	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_solve_lim(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	MinisatGH::vec<MinisatGH::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? MinisatGH::mkLit(l, false) : MinisatGH::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	MinisatGH::lbool res = s->solveLimited(a);

	PyObject *ret;
	if (res != MinisatGH::lbool((uint8_t)2))  // l_Undef
		ret = PyBool_FromLong((long)!(MinisatGH::toInt(res)));
	else
		ret = Py_BuildValue("");  // return Python's None if l_Undef

	return ret;
}

//
//=============================================================================
static PyObject *py_minisatgh_propagate(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *s_obj;
	PyObject *a_obj;  // assumptions

	if (!PyArg_ParseTuple(args, "OO", &s_obj, &a_obj))
		return NULL;

	// get pointer to solver
	MinisatGH::Solver *s = (MinisatGH::Solver *)pyobj_to_void(s_obj);

	int size = (int)PyList_Size(a_obj);
	MinisatGH::vec<MinisatGH::Lit> a((int)size);

	int max_var = -1;
	for (int i = 0; i < size; ++i) {
		PyObject *l_obj = PyList_GetItem(a_obj, i);
		int l = pyint_to_cint(l_obj);
		a[i] = (l > 0) ? MinisatGH::mkLit(l, false) : MinisatGH::mkLit(-l, true);

		if (abs(l) > max_var)
			max_var = abs(l);
	}

	if (max_var > 0)
		minisatgh_declare_vars(s, max_var);

	if (setjmp(env) != 0) {
		PyErr_SetString(SATError, "Caught keyboard interrupt");
		return NULL;
	}

	MinisatGH::vec<MinisatGH::Lit> p;
	bool res = s->prop_check(a, p);

	PyObject *ret = Py_None;

	if (p.size()) {
		PyObject *propagated = PyList_New(p.size());
		for (int i = 0; i < p.size(); ++i) {
			int l = MinisatGH::var(p[i]) * (MinisatGH::sign(p[i]) ? -1 : 1);
			PyObject *lit = pyint_from_cint(l);
			PyList_SetItem(propagated, i, lit);
		}

		ret = Py_BuildValue("nO", (Py_ssize_t)res, propagated);
		Py_DECREF(propagated);
	}

	return ret;
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

	s->setConfBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	s->setPropBudget(budget);

	PyObject *ret = Py_BuildValue("");
	return ret;
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

	PyObject *ret = Py_None;

	if (c->size())
		ret = Py_BuildValue("O", core);

	Py_DECREF(core);
	return ret;
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

	MinisatGH::vec<MinisatGH::lbool> *m = &(s->model);  // minisat's model
	MinisatGH::lbool True = MinisatGH::lbool((uint8_t)0);  // l_True fails to work

	PyObject *model = PyList_New(m->size() - 1);
	for (int i = 1; i < m->size(); ++i) {
		int l = i * ((*m)[i] == True ? 1 : -1);
		PyObject *lit = pyint_from_cint(l);
		PyList_SetItem(model, i - 1, lit);
	}

	PyObject *ret = Py_None;

	if (m->size())
		ret = Py_BuildValue("O", model);

	Py_DECREF(model);
	return ret;
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

	PyObject *ret = Py_BuildValue("");
	return ret;
}
#endif  // WITH_MINISATGH

}  // extern "C"
