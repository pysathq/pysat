/*
 * pf_weight.cc
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#include "pyformula.hh"
#include "pf_scan.hh"
#include "pf_weight.hh"

// parse only the weighted preamble fields relevant to the native parser
//=============================================================================
bool parse_weight_preamble(const char *beg, const char *end,
		const char *errmsg, PyObject **topw)
{
	const char *p = beg;
	const char *tbeg, *tend;

	if (!read_span(p, end, tbeg, tend) || !span_eq(tbeg, tend, "p") ||
			!read_span(p, end, tbeg, tend) ||
			!(span_eq(tbeg, tend, "wcnf") || span_eq(tbeg, tend, "wcnf+")) ||
			!read_span(p, end, tbeg, tend) ||
			!read_span(p, end, tbeg, tend)) {
		PyErr_SetString(PyExc_ValueError, errmsg);
		return false;
	}

	if (read_span(p, end, tbeg, tend)) {
		PyObject *nw = parse_wght_span(tbeg, tend);
		if (nw == NULL)
			return false;

		Py_DECREF(*topw);
		*topw = nw;
	}

	skip_ws(p, end);
	if (p != end) {
		PyErr_SetString(PyExc_ValueError, errmsg);
		return false;
	}

	return true;
}
