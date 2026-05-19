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
#include <stdint.h>
#include <Python.h>

#include "card.hh"
#include "itot.hh"

using namespace std;

#ifndef PYCARD_ENABLE_PYINT_CACHE
#define PYCARD_ENABLE_PYINT_CACHE 1
#endif

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

// forward declaration (implemented in Python2/Python3 branches below)
extern "C" {
	static PyObject *pyint_from_cint(int i);
}

#define PYINT_CACHE_SIZE (1u << 8)

typedef struct {
	int key;
	PyObject *obj;  // cache-owned reference
	unsigned char used;
} PyIntCacheEntry;

typedef struct {
	PyIntCacheEntry slots[PYINT_CACHE_SIZE];
	uint16_t used_idx[PYINT_CACHE_SIZE];
	size_t used_count;
} PyIntCache;

static inline uint32_t pyint_cache_hash(int v)
{
	return ((uint32_t)v * 2654435761u) & (PYINT_CACHE_SIZE - 1u);
}

static PyObject *pyint_cache_get_or_make(PyIntCache *cache, int v)
{
#if PYCARD_ENABLE_PYINT_CACHE
	uint32_t idx = pyint_cache_hash(v);
	PyIntCacheEntry *e = &cache->slots[idx];
	if (e->used && e->key == v) {
		Py_INCREF(e->obj);  // caller gets one ref
		return e->obj;
	}

	PyObject *obj = pyint_from_cint(v);
	if (obj == NULL)
		return NULL;

	if (e->used)
		Py_DECREF(e->obj);
	else
		cache->used_idx[cache->used_count++] = (uint16_t)idx;

	e->used = 1;
	e->key = v;
	e->obj = obj;      // cache keeps one ref

	Py_INCREF(obj);    // caller gets one ref
	return obj;
#else
	(void)cache;
	return pyint_from_cint(v);
#endif
}

static void pyint_cache_clear(PyIntCache *cache)
{
#if PYCARD_ENABLE_PYINT_CACHE
	for (size_t i = 0; i < cache->used_count; ++i) {
		PyIntCacheEntry *e = &cache->slots[cache->used_idx[i]];
		if (e->used) {
			Py_DECREF(e->obj);
			e->obj = NULL;
			e->used = 0;
		}
	}
	cache->used_count = 0;
#else
	(void)cache;
#endif
}

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
	// Fast path for sequences (list/tuple and sequence-like objects).
	// This avoids iterator protocol overhead and allows up-front reservation.
	PyObject *seq = PySequence_Fast(obj, NULL);
	if (seq != NULL) {
		Py_ssize_t n = PySequence_Fast_GET_SIZE(seq);
		if (n > 0)
			vect.reserve(vect.size() + (size_t)n);

		PyObject **items = PySequence_Fast_ITEMS(seq);
		for (Py_ssize_t i = 0; i < n; ++i) {
			PyObject *l_obj = items[i];
			if (!pyint_check(l_obj)) {
				Py_DECREF(seq);
				PyErr_SetString(PyExc_TypeError, "integer expected");
				return false;
			}

			int l = pyint_to_cint(l_obj);
			if (l == 0) {
				Py_DECREF(seq);
				PyErr_SetString(PyExc_ValueError, "non-zero integer expected");
				return false;
			}

			vect.push_back(l);
		}

		Py_DECREF(seq);
		return true;
	}

	// If this failed because object is not a sequence, continue with iterator path.
	PyErr_Clear();

	PyObject *i_obj = PyObject_GetIter(obj);

	if (i_obj == NULL) {
		PyErr_SetString(PyExc_RuntimeError,
				"Object does not seem to be an iterable.");
		return false;
	}

	PyObject *hint_obj = PyObject_CallMethod(i_obj, "__length_hint__", NULL);
	if (hint_obj != NULL) {
		if (pyint_check(hint_obj)) {
			int hint = pyint_to_cint(hint_obj);
			if (hint > 0)
				vect.reserve(vect.size() + (size_t)hint);
		}
		Py_DECREF(hint_obj);
	}
	else {
		PyErr_Clear();
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

	if (PyErr_Occurred()) {
		Py_DECREF(i_obj);
		return false;
	}

	Py_DECREF(i_obj);
	return true;
}

// Auxiliary function for translating ClauseSet to Python list of lists
//=============================================================================
static PyObject *clauseset_to_pylist(ClauseSet& dest, PyIntCache *cache)
{
	Py_ssize_t ncls = (Py_ssize_t)dest.size();
	PyObject *dest_obj = PyList_New(ncls);
	if (dest_obj == NULL)
		return NULL;

	for (Py_ssize_t i = 0; i < ncls; ++i) {
		const vector<int> &cl = dest[(size_t)i];
		Py_ssize_t nlit = (Py_ssize_t)cl.size();
		PyObject *cl_obj = PyList_New(nlit);
		if (cl_obj == NULL) {
			Py_DECREF(dest_obj);
			return NULL;
		}

		for (Py_ssize_t j = 0; j < nlit; ++j) {
			PyObject *lit_obj = pyint_cache_get_or_make(cache, cl[(size_t)j]);
			if (lit_obj == NULL) {
				Py_DECREF(cl_obj);
				Py_DECREF(dest_obj);
				return NULL;
			}

			PyList_SET_ITEM(cl_obj, j, lit_obj);
		}

		PyList_SET_ITEM(dest_obj, i, cl_obj);
	}

	return dest_obj;
}

// Auxiliary function for translating vector<int> to Python list
//=============================================================================
static PyObject *vector_to_pylist(const vector<int>& vals)
{
	Py_ssize_t n = (Py_ssize_t)vals.size();
	PyObject *lst = PyList_New(n);
	if (lst == NULL)
		return NULL;

	for (Py_ssize_t i = 0; i < n; ++i) {
		PyObject *v_obj = pyint_from_cint(vals[(size_t)i]);
		if (v_obj == NULL) {
			Py_DECREF(lst);
			return NULL;
		}

		PyList_SET_ITEM(lst, i, v_obj);
	}

	return lst;
}

//
//=============================================================================
static PyObject *py_encode_atmost(PyObject *self, PyObject *args)
{
	PyObject *lhs_obj;
	int rhs;
	int top;
	int enc;
	int main_thread;

	if (!PyArg_ParseTuple(args, "Oiiii", &lhs_obj, &rhs, &top, &enc,
				&main_thread))
		return NULL;

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	_encode_atmost(dest, lhs, rhs, top, enc);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	if (dest.size()) {
		PyObject *ret = PyTuple_New(2);
		if (ret == NULL) {
			Py_DECREF(dest_obj);
			return NULL;
		}

		PyObject *top_obj = pyint_from_cint(top);
		if (top_obj == NULL) {
			Py_DECREF(dest_obj);
			Py_DECREF(ret);
			return NULL;
		}

		PyTuple_SET_ITEM(ret, 0, dest_obj);
		PyTuple_SET_ITEM(ret, 1, top_obj);
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
	PyObject *lhs_obj;
	int rhs;
	int top;
	int enc;
	int main_thread;

	if (!PyArg_ParseTuple(args, "Oiiii", &lhs_obj, &rhs, &top, &enc,
				&main_thread))
		return NULL;

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	_encode_atleast(dest, lhs, rhs, top, enc);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	if (dest.size()) {
		PyObject *ret = PyTuple_New(2);
		if (ret == NULL) {
			Py_DECREF(dest_obj);
			return NULL;
		}

		PyObject *top_obj = pyint_from_cint(top);
		if (top_obj == NULL) {
			Py_DECREF(dest_obj);
			Py_DECREF(ret);
			return NULL;
		}

		PyTuple_SET_ITEM(ret, 0, dest_obj);
		PyTuple_SET_ITEM(ret, 1, top_obj);
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
	PyObject *lhs_obj;
	int rhs;
	int top;
	int main_thread;

	if (!PyArg_ParseTuple(args, "Oiii", &lhs_obj, &rhs, &top, &main_thread))
		return NULL;

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	TotTree *tree = itot_new(dest, lhs, rhs, top);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	PyObject *ubs_obj = vector_to_pylist(tree->vars);
	if (ubs_obj == NULL) {
		Py_DECREF(dest_obj);
		return NULL;
	}
	PyObject *tree_obj = void_to_pyobj((void *)tree);
	if (tree_obj == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		return NULL;
	}
	PyObject *top_obj = pyint_from_cint(top);
	if (top_obj == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		Py_DECREF(tree_obj);
		return NULL;
	}

	PyObject *ret = PyTuple_New(4);
	if (ret == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		Py_DECREF(tree_obj);
		Py_DECREF(top_obj);
		return NULL;
	}
	PyTuple_SET_ITEM(ret, 0, tree_obj);
	PyTuple_SET_ITEM(ret, 1, dest_obj);
	PyTuple_SET_ITEM(ret, 2, ubs_obj);
	PyTuple_SET_ITEM(ret, 3, top_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_inc(PyObject *self, PyObject *args)
{
	PyObject *t_obj;
	int rhs;
	int top;
	int main_thread;

	if (!PyArg_ParseTuple(args, "Oiii", &t_obj, &rhs, &top, &main_thread))
		return NULL;

	// get pointer to tree
	TotTree *tree = (TotTree *)pyobj_to_void(t_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	itot_increase(tree, dest, rhs, top);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	PyObject *ubs_obj = vector_to_pylist(tree->vars);
	if (ubs_obj == NULL) {
		Py_DECREF(dest_obj);
		return NULL;
	}
	PyObject *top_obj = pyint_from_cint(top);
	if (top_obj == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		return NULL;
	}

	PyObject *ret = PyTuple_New(3);
	if (ret == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		Py_DECREF(top_obj);
		return NULL;
	}
	PyTuple_SET_ITEM(ret, 0, dest_obj);
	PyTuple_SET_ITEM(ret, 1, ubs_obj);
	PyTuple_SET_ITEM(ret, 2, top_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_ext(PyObject *self, PyObject *args)
{
	PyObject *t_obj;
	PyObject *lhs_obj;
	int rhs;
	int top;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOiii", &t_obj, &lhs_obj, &rhs, &top,
				&main_thread))
		return NULL;

	vector<int> lhs;
	if (pyiter_to_vector(lhs_obj, lhs) == false)
		return NULL;

	// get pointer to tree
	TotTree *tree = (TotTree *)pyobj_to_void(t_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	tree = itot_extend(lhs, tree, dest, rhs, top);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	PyObject *ubs_obj = vector_to_pylist(tree->vars);
	if (ubs_obj == NULL) {
		Py_DECREF(dest_obj);
		return NULL;
	}
	PyObject *tree_obj = void_to_pyobj((void *)tree);
	if (tree_obj == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		return NULL;
	}
	PyObject *top_obj = pyint_from_cint(top);
	if (top_obj == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		Py_DECREF(tree_obj);
		return NULL;
	}

	PyObject *ret = PyTuple_New(4);
	if (ret == NULL) {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
		Py_DECREF(tree_obj);
		Py_DECREF(top_obj);
		return NULL;
	}
	PyTuple_SET_ITEM(ret, 0, tree_obj);
	PyTuple_SET_ITEM(ret, 1, dest_obj);
	PyTuple_SET_ITEM(ret, 2, ubs_obj);
	PyTuple_SET_ITEM(ret, 3, top_obj);
	return ret;
}

//
//=============================================================================
static PyObject *py_itot_mrg(PyObject *self, PyObject *args)
{
	PyObject *t1_obj;
	PyObject *t2_obj;
	int rhs;
	int top;
	int main_thread;

	if (!PyArg_ParseTuple(args, "OOiii", &t1_obj, &t2_obj, &rhs, &top,
				&main_thread))
		return NULL;

	// get pointer to tree
	TotTree *tree1 = (TotTree *)pyobj_to_void(t1_obj);
	TotTree *tree2 = (TotTree *)pyobj_to_void(t2_obj);

	PyOS_sighandler_t sig_save;
	if (main_thread) {
		sig_save = PyOS_setsig(SIGINT, sigint_handler);

		if (setjmp(env) != 0) {
			PyErr_SetString(CardError, "Caught keyboard interrupt");
			return NULL;
		}
	}

	// calling encoder
	ClauseSet dest;
	tree1 = itot_merge(tree1, tree2, dest, rhs, top);

	if (main_thread)
		PyOS_setsig(SIGINT, sig_save);

	PyIntCache cache = {};
	PyObject *dest_obj = clauseset_to_pylist(dest, &cache);
	pyint_cache_clear(&cache);
	if (dest_obj == NULL)
		return NULL;

	PyObject *ubs_obj = vector_to_pylist(tree1->vars);
	if (ubs_obj == NULL) {
		Py_DECREF(dest_obj);
		return NULL;
	}

	if (dest.size()) {
		PyObject *tree_obj = void_to_pyobj((void *)tree1);
		if (tree_obj == NULL) {
			Py_DECREF(dest_obj);
			Py_DECREF(ubs_obj);
			return NULL;
		}
		PyObject *top_obj = pyint_from_cint(top);
		if (top_obj == NULL) {
			Py_DECREF(dest_obj);
			Py_DECREF(ubs_obj);
			Py_DECREF(tree_obj);
			return NULL;
		}

		PyObject *ret = PyTuple_New(4);
		if (ret == NULL) {
			Py_DECREF(dest_obj);
			Py_DECREF(ubs_obj);
			Py_DECREF(tree_obj);
			Py_DECREF(top_obj);
			return NULL;
		}
		PyTuple_SET_ITEM(ret, 0, tree_obj);
		PyTuple_SET_ITEM(ret, 1, dest_obj);
		PyTuple_SET_ITEM(ret, 2, ubs_obj);
		PyTuple_SET_ITEM(ret, 3, top_obj);
		return ret;
	}
	else {
		Py_DECREF(dest_obj);
		Py_DECREF(ubs_obj);
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
