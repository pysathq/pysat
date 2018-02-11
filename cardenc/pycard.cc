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

using namespace std;

// docstrings
//=============================================================================
static char  module_docstring[] = "This module provides an interface for "
                                  "encoding a few types of cardinality "
                                  "constraints";
static char  atmost_docstring[] = "Create an AtMost(k) constraint.";
static char atleast_docstring[] = "Create an AtLeast(k) constraint.";

static PyObject *CardError;
static sigjmp_buf env;

// function declaration for functions available in module
//=============================================================================
extern "C" {
	static PyObject *py_encode_atmost  (PyObject *, PyObject *);
	static PyObject *py_encode_atleast (PyObject *, PyObject *);
}

// module specification
//=============================================================================
static PyMethodDef module_methods[] = {
	{ "encode_atmost",  py_encode_atmost,  METH_VARARGS, atmost_docstring  },
	{ "encode_atleast", py_encode_atleast, METH_VARARGS, atleast_docstring },

	{ NULL, NULL, 0, NULL }
};

extern "C" {

// signal handler for SIGINT
//=============================================================================
static void sigint_handler(int signum)
{
	siglongjmp(env, -1);
}

// module initialization
//=============================================================================
#if PY_MAJOR_VERSION >= 3  // for Python3
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

	if (sigsetjmp(env, 0) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	// reading arguments
	size_t lhs_sz = (size_t)PyList_Size(lhs_obj);
	vector<int> lhs((size_t)lhs_sz);

	for (size_t i = 0; i < lhs_sz; ++i) {
		PyObject *l_entry = PyList_GetItem(lhs_obj, i);
#if PY_MAJOR_VERSION >= 3
		lhs[i] = PyLong_AsLong(l_entry);
#else
		lhs[i] = PyInt_AsLong(l_entry);
#endif
	}

	// calling encoder
	ClauseSet dest;
	_encode_atmost(dest, lhs, rhs, top, enc);

	// creating the resulting clause set
	PyObject *dest_obj = PyList_New(dest.size());
	for (size_t i = 0; i < dest.size(); ++i) {
		PyObject *cl_obj = PyList_New(dest[i].size());

		for (size_t j = 0; j < dest[i].size(); ++j) {
#if PY_MAJOR_VERSION >= 3
			PyObject *lit_obj = PyLong_FromLong(dest[i][j]);
#else
			PyObject *lit_obj = PyInt_FromLong(dest[i][j]);
#endif
			PyList_SetItem(cl_obj, j, lit_obj);
		}

		PyList_SetItem(dest_obj, i, cl_obj);
	}

	PyObject *ret = Py_None;

	if (dest.size())
		ret = Py_BuildValue("On", dest_obj, (Py_ssize_t)top);

	Py_DECREF(dest_obj);
	return ret;
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

	if (sigsetjmp(env, 0) != 0) {
		PyErr_SetString(CardError, "Caught keyboard interrupt");
		return NULL;
	}

	// reading arguments
	size_t lhs_sz = (size_t)PyList_Size(lhs_obj);
	vector<int> lhs((size_t)lhs_sz);

	for (size_t i = 0; i < lhs_sz; ++i) {
		PyObject *l_entry = PyList_GetItem(lhs_obj, i);
#if PY_MAJOR_VERSION >= 3
		lhs[i] = PyLong_AsLong(l_entry);
#else
		lhs[i] = PyInt_AsLong(l_entry);
#endif
	}

	// calling encoder
	ClauseSet dest;
	_encode_atleast(dest, lhs, rhs, top, enc);

	// creating the resulting clause set
	PyObject *dest_obj = PyList_New(dest.size());
	for (size_t i = 0; i < dest.size(); ++i) {
		PyObject *cl_obj = PyList_New(dest[i].size());

		for (size_t j = 0; j < dest[i].size(); ++j) {
#if PY_MAJOR_VERSION >= 3
			PyObject *lit_obj = PyLong_FromLong(dest[i][j]);
#else
			PyObject *lit_obj = PyInt_FromLong(dest[i][j]);
#endif
			PyList_SetItem(cl_obj, j, lit_obj);
		}

		PyList_SetItem(dest_obj, i, cl_obj);
	}

	PyObject *ret = Py_None;

	if (dest.size())
		ret = Py_BuildValue("On", dest_obj, (Py_ssize_t)top);

	Py_DECREF(dest_obj);
	return ret;
}

}  // extern "C"
