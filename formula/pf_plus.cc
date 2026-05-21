/*
 * pf_plus.cc
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#include "pyformula.hh"
#include "pf_scan.hh"
#include "pf_py.hh"
#include "pf_weight.hh"
#include "pf_plus.hh"

// parse a zero-terminated clause body into a vector of literals
//=============================================================================
bool parse_clause_body(const char *p, const char *end,
		vector<long long> &lits)
{
	lits.clear();

	long long lit;
	while (true) {
		if (!read_int(p, end, lit))
			return false;
		if (lit == 0)
			break;

		lits.push_back(lit);
	}

	skip_ws(p, end);
	if (p != end) {
		PyErr_SetString(PyExc_ValueError,
				"unexpected trailing characters after clause terminator");
		return false;
	}

	return true;
}

// parse a CNF+/WCNF+ clause, cardinality, or PB body
//=============================================================================
bool parse_plus_body(const char *first_beg, const char *first_end,
		const char *p, const char *end, plus_body &body)
{
	const char *tbeg = first_beg;
	const char *tend = first_end;
	init_plus_body(body);

	body.weighted = span_eq(tbeg, tend, "w");
	bool is_ge = false;
	bool have_cmp = false;

	if (body.weighted) {
		while (read_span(p, end, tbeg, tend)) {
			if (span_eq(tbeg, tend, "<=") || span_eq(tbeg, tend, ">=")) {
				have_cmp = true;
				is_ge = (*tbeg == '>');
				break;
			}

			long long w, l;
			if (!parse_wlit_span(tbeg, tend, w, l)) {
				PyErr_SetString(PyExc_ValueError, "invalid weighted literal");
				return false;
			}

			body.wght.push_back(w);
			body.lits.push_back(l);
			body.sumw += w;
		}

		if (!have_cmp || !read_span(p, end, tbeg, tend) ||
				!parse_ll_span(tbeg, tend, body.rhs)) {
			PyErr_SetString(PyExc_ValueError, "invalid right-hand side");
			return false;
		}
	}
	else {
		while (true) {
			if (span_eq(tbeg, tend, "<=") || span_eq(tbeg, tend, ">=")) {
				have_cmp = true;
				is_ge = (*tbeg == '>');
				break;
			}

			long long lit;
			if (!parse_ll_span(tbeg, tend, lit)) {
				PyErr_SetString(PyExc_ValueError, "invalid literal");
				return false;
			}

			if (lit == 0) {
				body.clause = true;
				break;
			}

			body.lits.push_back(lit);
			++body.sumw;

			if (!read_span(p, end, tbeg, tend)) {
				PyErr_SetString(PyExc_ValueError,
						"unterminated clause/constraint");
				return false;
			}
		}

		if (!body.clause) {
			if (!have_cmp || !read_span(p, end, tbeg, tend) ||
					!parse_ll_span(tbeg, tend, body.rhs)) {
				PyErr_SetString(PyExc_ValueError, "invalid right-hand side");
				return false;
			}
		}
	}

	if (read_span(p, end, tbeg, tend)) {
		PyErr_SetString(PyExc_ValueError, "unexpected trailing tokens");
		return false;
	}

	if (!body.clause && is_ge)
		normalize_ge(body);

	return true;
}

// build a Python AtMost/PB object from a parsed CNF+ body
//=============================================================================
PyObject *mk_atm(const plus_body &body, int_cache *cache, long long &nv)
{
	PyObject *lits = mk_llist(body.lits, cache, &nv);
	PyObject *rhs = NULL;
	PyObject *wobj = NULL;
	PyObject *atm = NULL;

	if (lits == NULL)
		return NULL;

	rhs = pyint_cache_get_or_make(cache, body.rhs);
	if (rhs == NULL) {
		Py_DECREF(lits);
		return NULL;
	}

	if (body.weighted) {
		wobj = mk_llist(body.wght, cache, NULL);
		if (wobj == NULL) {
			Py_DECREF(lits);
			Py_DECREF(rhs);
			return NULL;
		}
	}

	atm = PyList_New(body.weighted ? 3 : 2);
	if (atm == NULL) {
		Py_DECREF(lits);
		Py_DECREF(rhs);
		Py_XDECREF(wobj);
		return NULL;
	}

	PyList_SET_ITEM(atm, 0, lits);
	PyList_SET_ITEM(atm, 1, rhs);
	if (body.weighted)
		PyList_SET_ITEM(atm, 2, wobj);

	return atm;
}

// route a weighted clause to hard, soft, or negative-soft storage
//=============================================================================
bool append_weighted_clause(PyObject *hard, PyObject *soft,
		PyObject *wght, PyObject *negs, PyObject *topw, PyObject *zero,
		PyObject *cl, PyObject *wt)
{
	int is_hard = (wt == Py_None);
	if (!is_hard) {
		int ge_top = PyObject_RichCompareBool(wt, topw, Py_GE);
		if (ge_top < 0)
			return false;
		is_hard = ge_top;
	}

	if (is_hard)
		return PyList_Append(hard, cl) >= 0;

	int gt_zero = PyObject_RichCompareBool(wt, zero, Py_GT);
	if (gt_zero < 0)
		return false;

	if (gt_zero)
		return PyList_Append(soft, cl) >= 0 && PyList_Append(wght, wt) >= 0;

	PyObject *posw = PyNumber_Negative(wt);
	if (posw == NULL)
		return false;

	PyObject *pair = PyTuple_New(2);
	if (pair == NULL) {
		Py_DECREF(posw);
		return false;
	}

	Py_INCREF(cl);
	PyTuple_SET_ITEM(pair, 0, cl);
	PyTuple_SET_ITEM(pair, 1, posw);

	int ok = PyList_Append(negs, pair) >= 0;
	Py_DECREF(pair);
	return ok;
}
