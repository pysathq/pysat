/*
 * pf_weight.hh
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#ifndef __PF_WEIGHT_HH__
#define __PF_WEIGHT_HH__

#include "pyformula.hh"
#include "pf_scan.hh"

// weights and preambles
//=============================================================================
// parse a clause or top weight as h, int, or decimal.Decimal
static inline PyObject *parse_wght_span(const char *beg, const char *end)
{
	if (span_eq(beg, end, "h")) {
		Py_RETURN_NONE;
	}

	if (span_is_integer_like(beg, end)) {
		long long val;
		if (!parse_ll_span(beg, end, val)) {
			PyErr_SetString(PyExc_ValueError, "invalid integer weight");
			return NULL;
		}

		return PyLong_FromLongLong(val);
	}

	PyObject *text = PyUnicode_FromStringAndSize(beg, end - beg);
	if (text == NULL)
		return NULL;

	PyObject *d = PyObject_CallFunctionObjArgs(dec_cls, text, NULL);
	Py_DECREF(text);
	if (d == NULL)
		return NULL;

	PyObject *inf = PyObject_CallMethod(d, (char *)"is_infinite", NULL);
	if (inf == NULL) {
		Py_DECREF(d);
		return NULL;
	}

	int is_inf = PyObject_IsTrue(inf);
	Py_DECREF(inf);
	if (is_inf < 0) {
		Py_DECREF(d);
		return NULL;
	}
	if (is_inf)
		return d;

	PyObject *ival = PyObject_CallMethod(d, (char *)"to_integral_value", NULL);
	if (ival == NULL) {
		Py_DECREF(d);
		return NULL;
	}

	int is_eq = PyObject_RichCompareBool(d, ival, Py_EQ);
	Py_DECREF(ival);
	if (is_eq < 0) {
		Py_DECREF(d);
		return NULL;
	}

	if (is_eq) {
		PyObject *res = PyNumber_Long(d);
		Py_DECREF(d);
		return res;
	}

	return d;
}

// parse a weighted literal of the form w*l
//=============================================================================
static inline bool parse_wlit_span(const char *beg, const char *end,
		long long &w, long long &l)
{
	const char *star = (const char *)memchr(beg, '*', (size_t)(end - beg));
	if (star == NULL)
		return false;

	return parse_ll_span(beg, star, w) &&
		parse_ll_span(star + 1, end, l) && l != 0;
}

#endif
