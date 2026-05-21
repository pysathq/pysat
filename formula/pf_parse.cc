/*
 * pf_parse.cc
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

// parse a full DIMACS CNF text buffer
//=============================================================================
PyObject *parse_cnf_impl(PyObject *txt_obj, PyObject *comment_lead)
{
	const char *buf;
	Py_ssize_t len;
	if (!get_text_view(txt_obj, &buf, &len))
		return NULL;

	bool comment_mask[256];
	init_comment_mask(comment_lead, comment_mask);

	PyObject *clauses = PyList_New(0);
	PyObject *comments = PyList_New(0);
	if (clauses == NULL || comments == NULL) {
		Py_XDECREF(clauses);
		Py_XDECREF(comments);
		return NULL;
	}

	int_cache cache = {};
	long long nv = 0;
	PyObject *ret = NULL;
	vector<long long> lits;
	lits.reserve(16);

	const char *p = buf;
	const char *end = buf + len;
	const char *beg, *lend;

	while (next_line(p, end, beg, lend)) {
		if (line_empty(beg, lend))
			continue;

		if (comment_mask[(unsigned char)beg[0]]) {
			if (!line_starts(beg, lend, "p cnf ")) {
				if (!append_comment(comments, beg, lend))
					goto fail;
			}
			continue;
		}

		if (!parse_clause_body(beg, lend, lits))
			goto fail;

		PyObject *cl = mk_llist(lits, &cache, &nv);
		if (cl == NULL)
			goto fail;

		if (PyList_Append(clauses, cl) < 0) {
			Py_DECREF(cl);
			goto fail;
		}

		Py_DECREF(cl);
	}

	pyint_cache_clear(&cache);
	ret = PyTuple_New(3);
	if (ret == NULL) {
		Py_DECREF(clauses);
		Py_DECREF(comments);
		return NULL;
	}

	PyTuple_SET_ITEM(ret, 0, PyLong_FromLongLong(nv));
	PyTuple_SET_ITEM(ret, 1, clauses);
	PyTuple_SET_ITEM(ret, 2, comments);
	return ret;

fail:
	pyint_cache_clear(&cache);
	Py_DECREF(clauses);
	Py_DECREF(comments);
	return NULL;
}

// parse a full DIMACS WCNF text buffer
//=============================================================================
PyObject *parse_wcnf_impl(PyObject *txt_obj, PyObject *comment_lead)
{
	const char *buf;
	Py_ssize_t len;
	if (!get_text_view(txt_obj, &buf, &len))
		return NULL;

	bool comment_mask[256];
	init_comment_mask(comment_lead, comment_mask);

	PyObject *hard = PyList_New(0);
	PyObject *soft = PyList_New(0);
	PyObject *wght = PyList_New(0);
	PyObject *comments = PyList_New(0);
	PyObject *negs = PyList_New(0);
	if (!hard || !soft || !wght || !comments || !negs) {
		Py_XDECREF(hard);
		Py_XDECREF(soft);
		Py_XDECREF(wght);
		Py_XDECREF(comments);
		Py_XDECREF(negs);
		return NULL;
	}

	PyObject *topw = dec_inf;
	Py_INCREF(topw);
	PyObject *zero = PyLong_FromLong(0);
	PyObject *ret = NULL;
	if (zero == NULL) {
		Py_DECREF(hard);
		Py_DECREF(soft);
		Py_DECREF(wght);
		Py_DECREF(comments);
		Py_DECREF(negs);
		Py_DECREF(topw);
		return NULL;
	}

	int_cache cache = {};
	long long nv = 0;
	vector<long long> lits;
	lits.reserve(16);

	const char *p = buf;
	const char *end = buf + len;
	const char *beg, *lend;

	while (next_line(p, end, beg, lend)) {
		if (line_empty(beg, lend))
			continue;

		if (comment_mask[(unsigned char)beg[0]]) {
			if (!line_starts(beg, lend, "p wcnf ")) {
				if (!append_comment(comments, beg, lend))
					goto fail;
			}
			else {
				if (!parse_weight_preamble(beg, lend, "wcnf",
						"invalid WCNF preamble", &topw))
					goto fail;
			}
			continue;
		}

		const char *lp = beg;
		const char *wbeg, *wend;
		if (!read_span(lp, lend, wbeg, wend))
			continue;

		PyObject *wt = parse_wght_span(wbeg, wend);
		if (wt == NULL)
			goto fail;

		if (!parse_clause_body(lp, lend, lits)) {
			Py_DECREF(wt);
			goto fail;
		}

		PyObject *cl = mk_llist(lits, &cache, &nv);
		if (cl == NULL) {
			Py_DECREF(wt);
			goto fail;
		}

		if (!append_weighted_clause(hard, soft, wght, negs, topw, zero, cl, wt)) {
			Py_DECREF(cl);
			Py_DECREF(wt);
			goto fail;
		}

		Py_DECREF(cl);
		Py_DECREF(wt);
	}

	pyint_cache_clear(&cache);
	Py_DECREF(zero);
	ret = PyTuple_New(7);
	if (ret == NULL)
		goto fail_nocache;

	PyTuple_SET_ITEM(ret, 0, PyLong_FromLongLong(nv));
	PyTuple_SET_ITEM(ret, 1, hard);
	PyTuple_SET_ITEM(ret, 2, soft);
	PyTuple_SET_ITEM(ret, 3, wght);
	PyTuple_SET_ITEM(ret, 4, topw);
	PyTuple_SET_ITEM(ret, 5, comments);
	PyTuple_SET_ITEM(ret, 6, negs);
	return ret;

fail:
	pyint_cache_clear(&cache);
	Py_DECREF(zero);
fail_nocache:
	Py_DECREF(hard);
	Py_DECREF(soft);
	Py_DECREF(wght);
	Py_DECREF(comments);
	Py_DECREF(negs);
	Py_DECREF(topw);
	return NULL;
}

// parse a full DIMACS CNF+ text buffer
//=============================================================================
PyObject *parse_cnfplus_impl(PyObject *txt_obj, PyObject *comment_lead)
{
	const char *buf;
	Py_ssize_t len;
	if (!get_text_view(txt_obj, &buf, &len))
		return NULL;

	bool comment_mask[256];
	init_comment_mask(comment_lead, comment_mask);

	PyObject *clauses = PyList_New(0);
	PyObject *atmosts = PyList_New(0);
	PyObject *comments = PyList_New(0);
	if (!clauses || !atmosts || !comments) {
		Py_XDECREF(clauses);
		Py_XDECREF(atmosts);
		Py_XDECREF(comments);
		return NULL;
	}

	int_cache cache = {};
	long long nv = 0;
	PyObject *ret = NULL;
	plus_body body;

	const char *p = buf;
	const char *end = buf + len;
	const char *beg, *lend;

	while (next_line(p, end, beg, lend)) {
		if (line_empty(beg, lend))
			continue;

		if (comment_mask[(unsigned char)beg[0]]) {
			if (!line_starts(beg, lend, "p cnf+")) {
				if (!append_comment(comments, beg, lend))
					goto fail;
			}
			continue;
		}

		const char *lp = beg;
		const char *tbeg, *tend;
		if (!read_span(lp, lend, tbeg, tend))
			continue;

		if (!parse_plus_body(tbeg, tend, lp, lend, body))
			goto fail;

		if (body.clause) {
			PyObject *cl = mk_llist(body.lits, &cache, &nv);
			if (cl == NULL)
				goto fail;

			if (PyList_Append(clauses, cl) < 0) {
				Py_DECREF(cl);
				goto fail;
			}

			Py_DECREF(cl);
		}
		else {
			PyObject *atm = mk_atm(body, &cache, nv);
			if (atm == NULL)
				goto fail;

			if (PyList_Append(atmosts, atm) < 0) {
				Py_DECREF(atm);
				goto fail;
			}

			Py_DECREF(atm);
		}
	}

	pyint_cache_clear(&cache);
	ret = PyTuple_New(4);
	if (ret == NULL)
		goto fail_nocache;

	PyTuple_SET_ITEM(ret, 0, PyLong_FromLongLong(nv));
	PyTuple_SET_ITEM(ret, 1, clauses);
	PyTuple_SET_ITEM(ret, 2, atmosts);
	PyTuple_SET_ITEM(ret, 3, comments);
	return ret;

fail:
	pyint_cache_clear(&cache);
fail_nocache:
	Py_DECREF(clauses);
	Py_DECREF(atmosts);
	Py_DECREF(comments);
	return NULL;
}

// parse a full DIMACS WCNF+ text buffer
//=============================================================================
PyObject *parse_wcnfplus_impl(PyObject *txt_obj, PyObject *comment_lead)
{
	const char *buf;
	Py_ssize_t len;
	if (!get_text_view(txt_obj, &buf, &len))
		return NULL;

	bool comment_mask[256];
	init_comment_mask(comment_lead, comment_mask);

	PyObject *hard = PyList_New(0);
	PyObject *soft = PyList_New(0);
	PyObject *wght = PyList_New(0);
	PyObject *atms = PyList_New(0);
	PyObject *comments = PyList_New(0);
	PyObject *negs = PyList_New(0);
	if (!hard || !soft || !wght || !atms || !comments || !negs) {
		Py_XDECREF(hard);
		Py_XDECREF(soft);
		Py_XDECREF(wght);
		Py_XDECREF(atms);
		Py_XDECREF(comments);
		Py_XDECREF(negs);
		return NULL;
	}

	PyObject *topw = dec_inf;
	Py_INCREF(topw);
	PyObject *zero = PyLong_FromLong(0);
	PyObject *ret = NULL;
	if (zero == NULL) {
		Py_DECREF(hard);
		Py_DECREF(soft);
		Py_DECREF(wght);
		Py_DECREF(atms);
		Py_DECREF(comments);
		Py_DECREF(negs);
		Py_DECREF(topw);
		return NULL;
	}

	int_cache cache = {};
	long long nv = 0;
	plus_body body;

	const char *p = buf;
	const char *end = buf + len;
	const char *beg, *lend;

	while (next_line(p, end, beg, lend)) {
		if (line_empty(beg, lend))
			continue;

		if (comment_mask[(unsigned char)beg[0]]) {
			if (!line_starts(beg, lend, "p wcnf+")) {
				if (!append_comment(comments, beg, lend))
					goto fail;
			}
			else {
				if (!parse_weight_preamble(beg, lend, "wcnf+",
						"invalid WCNF+ preamble", &topw))
					goto fail;
			}
			continue;
		}

		const char *lp = beg;
		const char *wbeg, *wend;
		if (!read_span(lp, lend, wbeg, wend))
			continue;

		PyObject *wt = parse_wght_span(wbeg, wend);
		if (wt == NULL)
			goto fail;

		const char *tbeg, *tend;
		if (!read_span(lp, lend, tbeg, tend)) {
			Py_DECREF(wt);
			PyErr_SetString(PyExc_ValueError,
					"missing clause or constraint body");
			goto fail;
		}

		if (!parse_plus_body(tbeg, tend, lp, lend, body)) {
			Py_DECREF(wt);
			goto fail;
		}

		if (body.clause) {
			PyObject *cl = mk_llist(body.lits, &cache, &nv);
			if (cl == NULL) {
				Py_DECREF(wt);
				goto fail;
			}

			if (!append_weighted_clause(hard, soft, wght, negs, topw, zero,
						cl, wt)) {
				Py_DECREF(cl);
				Py_DECREF(wt);
				goto fail;
			}

			Py_DECREF(cl);
			Py_DECREF(wt);
		}
		else {
			PyObject *atm = mk_atm(body, &cache, nv);
			if (atm == NULL) {
				Py_DECREF(wt);
				goto fail;
			}

			if (PyList_Append(atms, atm) < 0) {
				Py_DECREF(atm);
				Py_DECREF(wt);
				goto fail;
			}

			Py_DECREF(atm);
			Py_DECREF(wt);
		}
	}

	pyint_cache_clear(&cache);
	Py_DECREF(zero);
	ret = PyTuple_New(8);
	if (ret == NULL)
		goto fail_nocache;

	PyTuple_SET_ITEM(ret, 0, PyLong_FromLongLong(nv));
	PyTuple_SET_ITEM(ret, 1, hard);
	PyTuple_SET_ITEM(ret, 2, soft);
	PyTuple_SET_ITEM(ret, 3, wght);
	PyTuple_SET_ITEM(ret, 4, atms);
	PyTuple_SET_ITEM(ret, 5, topw);
	PyTuple_SET_ITEM(ret, 6, comments);
	PyTuple_SET_ITEM(ret, 7, negs);
	return ret;

fail:
	pyint_cache_clear(&cache);
	Py_DECREF(zero);
fail_nocache:
	Py_DECREF(hard);
	Py_DECREF(soft);
	Py_DECREF(wght);
	Py_DECREF(atms);
	Py_DECREF(comments);
	Py_DECREF(negs);
	Py_DECREF(topw);
	return NULL;
}
