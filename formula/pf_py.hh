/*
 * pf_py.hh
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#ifndef __PF_PY_HH__
#define __PF_PY_HH__

#include "pyformula.hh"
#include "pf_scan.hh"

// tiny integer cache for repeated literals/weights
//=============================================================================
// hash an integer for the tiny object cache
static inline uint32_t pyint_cache_hash(long long v)
{
	return ((uint32_t)v * 2654435761u) & (PYINT_CACHE_SIZE - 1u);
}

// fetch a cached Python integer or create it on demand
//=============================================================================
static inline PyObject *pyint_cache_get_or_make(int_cache *cache, long long v)
{
	uint32_t idx = pyint_cache_hash(v);
	int_cache_ent *e = &cache->slots[idx];
	if (e->used && e->key == v) {
		Py_INCREF(e->obj);
		return e->obj;
	}

	PyObject *obj = PyLong_FromLongLong(v);
	if (obj == NULL)
		return NULL;

	if (e->used)
		Py_DECREF(e->obj);
	else
		cache->used_idx[cache->used_count++] = (uint16_t)idx;

	e->used = 1;
	e->key  = v;
	e->obj  = obj;

	Py_INCREF(obj);
	return obj;
}

// release all Python integers stored in the cache
//=============================================================================
static inline void pyint_cache_clear(int_cache *cache)
{
	for (size_t i = 0; i < cache->used_count; ++i) {
		int_cache_ent *e = &cache->slots[cache->used_idx[i]];
		if (e->used) {
			Py_DECREF(e->obj);
			e->obj = NULL;
			e->used = 0;
		}
	}

	cache->used_count = 0;
}

// generic helpers
//=============================================================================
// build a fast lookup table for comment lead characters
static inline void init_comment_mask(PyObject *comment_lead, bool mask[256])
{
	memset(mask, 0, sizeof(bool) * 256);
	mask[(unsigned char)'p'] = true;

	if (comment_lead == NULL)
		return;

	PyObject *iter = PyObject_GetIter(comment_lead);
	if (iter == NULL) {
		PyErr_Clear();
		return;
	}

	PyObject *item;
	while ((item = PyIter_Next(iter)) != NULL) {
		if (PyUnicode_Check(item)) {
			Py_ssize_t size = 0;
			const char *s = PyUnicode_AsUTF8AndSize(item, &size);
			if (s && size > 0)
				mask[(unsigned char)s[0]] = true;
		}
#if PY_MAJOR_VERSION < 3
		else if (PyString_Check(item)) {
			char *s = NULL;
			Py_ssize_t size = 0;
			if (PyString_AsStringAndSize(item, &s, &size) == 0 && s && size > 0)
				mask[(unsigned char)s[0]] = true;
		}
#endif
		Py_DECREF(item);
	}

	Py_DECREF(iter);
	PyErr_Clear();
}

// expose a Python string/bytes object as a contiguous text buffer
//=============================================================================
static inline bool get_text_view(PyObject *obj, const char **ptr,
		Py_ssize_t *len)
{
	if (PyUnicode_Check(obj)) {
		*ptr = PyUnicode_AsUTF8AndSize(obj, len);
		return *ptr != NULL;
	}
	else if (PyBytes_Check(obj)) {
		return PyBytes_AsStringAndSize(obj, (char **)ptr, len) == 0;
	}
#if PY_MAJOR_VERSION < 3
	else if (PyString_Check(obj)) {
		return PyString_AsStringAndSize(obj, (char **)ptr, len) == 0;
	}
#endif

	PyErr_SetString(PyExc_TypeError, "string or bytes expected");
	return false;
}

// create a Python string from a line span
//=============================================================================
static inline PyObject *mk_line(const char *beg, const char *end)
{
	return PyUnicode_FromStringAndSize(beg, end - beg);
}

// append a raw comment line to the comments list
//=============================================================================
static inline bool append_comment(PyObject *comments, const char *beg,
		const char *end)
{
	PyObject *line = mk_line(beg, end);
	if (line == NULL)
		return false;

	int ok = PyList_Append(comments, line);
	Py_DECREF(line);
	return ok >= 0;
}

// update the current maximum variable identifier
//=============================================================================
static inline void update_nv(long long lit, long long &nv)
{
	long long a = lit < 0 ? -lit : lit;
	if (a > nv)
		nv = a;
}

// convert a vector of integers into a Python list
//=============================================================================
static inline PyObject *mk_llist(const vector<long long> &vals,
		int_cache *cache, long long *nv)
{
	PyObject *lst = PyList_New((Py_ssize_t)vals.size());
	if (lst == NULL)
		return NULL;

	for (Py_ssize_t i = 0; i < (Py_ssize_t)vals.size(); ++i) {
		long long v = vals[(size_t)i];
		if (nv)
			update_nv(v, *nv);

		PyObject *obj = pyint_cache_get_or_make(cache, v);
		if (obj == NULL) {
			Py_DECREF(lst);
			return NULL;
		}

		PyList_SET_ITEM(lst, i, obj);
	}

	return lst;
}

#endif
