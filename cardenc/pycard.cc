/*
 * pycard.cc
 *
 *  Created on: Sep 25, 2017
 *      Author: Alexey S. Ignatiev
 *      E-mail: aignatiev@ciencias.ulisboa.pt
 */

#define PY_SSIZE_T_CLEAN

#include <setjmp.h>
#include <signal.h>
#include <stdio.h>
#include <Python.h>

#include "card.hh"
#include "itot.hh"

using namespace std;

// docstrings
//=============================================================================
static char   module_docstring[] = "This module provides an interface for "
                                   "encoding a few types of cardinality "
                                   "constraints";
static char   atmost_docstring[] = "Create an AtMost(k) constraint.";
static char  atleast_docstring[] = "Create an AtLeast(k) constraint.";
static char itot_new_docstring[] = "Create an iterative totalizer object for "
                                   "an AtMost(k) constraint.";
static char itot_inc_docstring[] = "Increase bound in an iterative totalizer "
				   "object.";
static char itot_ext_docstring[] = "Extends the set of inputs in an iterative"
				   " totalizer object.";
static char itot_mrg_docstring[] = "Merge two totalizer objects into one.";
static char itot_del_docstring[] = "Delete an iterative totalizer object";

static PyObject *CardError;
static jmp_buf env;

// function declaration for functions available in module
//=============================================================================
extern "C" {
	static PyObject *py_encode_atmost  (PyObject *, PyObject *);
	static PyObject *py_encode_atleast (PyObject *, PyObject *);
	static PyObject *py_itot_new       (PyObject *, PyObject *);
	static PyObject *py_itot_inc       (PyObject *, PyObject *);
	static PyObject *py_itot_ext       (PyObject *, PyObject *);
	static PyObject *py_itot_mrg       (PyObject *, PyObject *);
	static PyObject *py_itot_del       (PyObject *, PyObject *);
}

// module specification
//=============================================================================
static PyMethodDef module_methods[] = {
	{ "encode_atmost",  py_encode_atmost,  METH_VARARGS,   atmost_docstring },
	{ "encode_atleast", py_encode_atleast, METH_VARARGS,  atleast_docstring },
	{ "itot_new",       py_itot_new,       METH_VARARGS, itot_new_docstring },
	{ "itot_inc",       py_itot_inc,       METH_VARARGS, itot_inc_docstring },
	{ "itot_ext",       py_itot_ext,       METH_VARARGS, itot_ext_docstring },
	{ "itot_mrg",       py_itot_mrg,       METH_VARARGS, itot_mrg_docstring },
	{ "itot_del",       py_itot_del,       METH_VARARGS, itot_del_docstring },

	{ NULL, NULL, 0, NULL }
};

extern "C" {

// signal handler for SIGINT
//=============================================================================
static void sigint_handler(int signum)
{
	longjmp(env, -1);
}

#if PY_MAJOR_VERSION >= 3  // for Python3
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

// PyInt_Check()
//=============================================================================
static int pyint_check(PyObject *i_obj)
{
	return PyLong_Check(i_obj);
}

// module initialization
//=============================================================================
static struct PyModuleDef module_def = {
	PyModuleDef_HEAD_INIT,
	"pycard",          /* m_name */
	module_docstring,  /* m_doc */
	-1,                /* m_size */
	module_methods,    /* m_methods */
	NULL,              /* m_reload */
	NULL,              /* m_traverse */
	NULL,              /* m_clear */
	NULL,              /* m_free */
};

PyMODINIT_FUNC PyInit_pycard(void)
{
	PyObject *m = PyModule_Create(&module_def);

	if (m == NULL)
		return NULL;

	CardError = PyErr_NewException((char *)"pycard.error", NULL, NULL);
	Py_INCREF(CardError);

	if (PyModule_AddObject(m, "error", CardError) < 0) {
		Py_DECREF(CardError);
		return NULL;
	}

	return m;
}
#else  // for Python2
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

// PyInt_Check()
//=============================================================================
static int pyint_check(PyObject *i_obj)
{
	return PyInt_Check(i_obj);
}

// module initialization
//=============================================================================
PyMODINIT_FUNC initpycard(void)
{
	PyObject *m = Py_InitModule3("pycard", module_methods,
			module_docstring);

	if (m == NULL)
		return;

	CardError = PyErr_NewException((char *)"pycard.error", NULL, NULL);
	Py_INCREF(CardError);
	PyModule_AddObject(m, "error", CardError);
}
#endif

// auxiliary function for translating an iterable to a vector<int>
//=============================================================================
static bool pyiter_to_vector(PyObject *obj, vector<int>& vect)
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
	}

	Py_DECREF(i_obj);
	return true;
}

//
//=============================================================================
static PyObject *py_encode_atmost(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *lhs_obj;
	int rhs;
	int top;
	int enc;

	if (!PyArg_ParseTuple(args, "Oiii", &lhs_obj, &rhs, &top, &enc))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	// calling encoder
	ClauseSet dest;
	_encode_atmost(dest, lhs, rhs, top, enc);

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

	if (dest.size()) {
		PyObject *ret = Py_BuildValue("On", dest_obj, (Py_ssize_t)top);
		Py_DECREF(dest_obj);
		return ret;
	}
	else {
		Py_DECREF(dest_obj);
		Py_RETURN_NONE;
	}
}

//
//=============================================================================
static PyObject *py_encode_atleast(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *lhs_obj;
	int rhs;
	int top;
	int enc;

	if (!PyArg_ParseTuple(args, "Oiii", &lhs_obj, &rhs, &top, &enc))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	// calling encoder
	ClauseSet dest;
	_encode_atleast(dest, lhs, rhs, top, enc);

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

	if (dest.size()) {
		PyObject *ret = Py_BuildValue("On", dest_obj, (Py_ssize_t)top);
		Py_DECREF(dest_obj);
		return ret;

	}
	else {
		Py_DECREF(dest_obj);
		Py_RETURN_NONE;
	}

}

//
//=============================================================================
static PyObject *py_itot_new(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *lhs_obj;
	int rhs;
	int top;

	if (!PyArg_ParseTuple(args, "Oii", &lhs_obj, &rhs, &top))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	// calling encoder
	ClauseSet dest;
	TotTree *tree = itot_new(dest, lhs, rhs, top);

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

	// creating the upper-bounds (right-hand side)
	PyObject *ubs_obj = PyList_New(tree->vars.size());
	for (size_t i = 0; i < tree->vars.size(); ++i) {
		PyObject *ub_obj = pyint_from_cint(tree->vars[i]);
		PyList_SetItem(ubs_obj, i, ub_obj);
	}

	PyObject *ret = Py_BuildValue("OOOn", void_to_pyobj((void *)tree),
				dest_obj, ubs_obj, (Py_ssize_t)top);

	Py_DECREF(dest_obj);
	Py_DECREF( ubs_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_inc(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *t_obj;
	int rhs;
	int top;

	if (!PyArg_ParseTuple(args, "Oii", &t_obj, &rhs, &top))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	// get pointer to tree
	TotTree *tree = (TotTree *)pyobj_to_void(t_obj);

	// calling encoder
	ClauseSet dest;
	itot_increase(tree, dest, rhs, top);

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

	// creating the upper-bounds (right-hand side)
	PyObject *ubs_obj = PyList_New(tree->vars.size());
	for (size_t i = 0; i < tree->vars.size(); ++i) {
		PyObject *ub_obj = pyint_from_cint(tree->vars[i]);
		PyList_SetItem(ubs_obj, i, ub_obj);
	}

	PyObject *ret = Py_BuildValue("OOn", dest_obj, ubs_obj, (Py_ssize_t)top);

	Py_DECREF(dest_obj);
	Py_DECREF( ubs_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_ext(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *t_obj;
	PyObject *lhs_obj;
	int rhs;
	int top;

	if (!PyArg_ParseTuple(args, "OOii", &t_obj, &lhs_obj, &rhs, &top))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	// get pointer to tree
	TotTree *tree = (TotTree *)pyobj_to_void(t_obj);

	// calling encoder
	ClauseSet dest;
	tree = itot_extend(lhs, tree, dest, rhs, top);

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

	// creating the upper-bounds (right-hand side)
	PyObject *ubs_obj = PyList_New(tree->vars.size());
	for (size_t i = 0; i < tree->vars.size(); ++i) {
		PyObject *ub_obj = pyint_from_cint(tree->vars[i]);
		PyList_SetItem(ubs_obj, i, ub_obj);
	}

	PyObject *ret = Py_BuildValue("OOOn", void_to_pyobj((void *)tree),
				dest_obj, ubs_obj, (Py_ssize_t)top);

	Py_DECREF(dest_obj);
	Py_DECREF( ubs_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_mrg(PyObject *self, PyObject *args)
{
	signal(SIGINT, sigint_handler);

	PyObject *t1_obj;
	PyObject *t2_obj;
	int rhs;
	int top;

	if (!PyArg_ParseTuple(args, "OOii", &t1_obj, &t2_obj, &rhs, &top))
		return NULL;

	if (setjmp(env) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	// get pointer to tree
	TotTree *tree1 = (TotTree *)pyobj_to_void(t1_obj);
	TotTree *tree2 = (TotTree *)pyobj_to_void(t2_obj);

	// calling encoder
	ClauseSet dest;
	tree1 = itot_merge(tree1, tree2, dest, rhs, top);

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

	// creating the upper-bounds (right-hand side)
	PyObject *ubs_obj = PyList_New(tree1->vars.size());
	for (size_t i = 0; i < tree1->vars.size(); ++i) {
		PyObject *ub_obj = pyint_from_cint(tree1->vars[i]);
		PyList_SetItem(ubs_obj, i, ub_obj);
	}

	if (dest.size()) {
		PyObject *ret = Py_BuildValue("OOOn", void_to_pyobj((void *)tree1),
				dest_obj, ubs_obj, (Py_ssize_t)top);
		Py_DECREF(dest_obj);
		Py_DECREF( ubs_obj);
		return ret;
	}
	else {
		Py_DECREF(dest_obj);
		Py_DECREF( ubs_obj);
		Py_RETURN_NONE;
	}

}

//
//=============================================================================
static PyObject *py_itot_del(PyObject *self, PyObject *args)
{
	PyObject *t_obj;

	if (!PyArg_ParseTuple(args, "O", &t_obj))
		return NULL;

	// get pointer to tree
	TotTree *tree = (TotTree *)pyobj_to_void(t_obj);

	// delete
	itot_destroy(tree);

	PyObject *ret = Py_BuildValue("");
	return ret;
}

}  // extern "C"
