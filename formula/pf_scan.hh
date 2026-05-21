/*
 * pf_scan.hh
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#ifndef __PF_SCAN_HH__
#define __PF_SCAN_HH__

#include "pyformula.hh"

// low-level cursor helpers
//=============================================================================
// skip inline whitespace while advancing the cursor
static inline void skip_ws(const char * &p, const char *end)
{
	while (p < end && ((*p >= 9 && *p <= 13) || *p == 32))
		++p;
}

// check whether a bounded span matches a C string exactly
//=============================================================================
static inline bool span_eq(const char *beg, const char *end, const char *s)
{
	size_t n = strlen(s);
	return (Py_ssize_t)n == end - beg && memcmp(beg, s, n) == 0;
}

// check whether a line starts with a fixed prefix
//=============================================================================
static inline bool line_starts(const char *beg, const char *end,
		const char *prefix)
{
	size_t n = strlen(prefix);
	return (Py_ssize_t)n <= end - beg && memcmp(beg, prefix, n) == 0;
}

// test whether a trimmed line is empty
//=============================================================================
static inline bool line_empty(const char *beg, const char *end)
{
	return end <= beg;
}

// split the input into trimmed logical lines
//=============================================================================
static inline bool next_line(const char * &p, const char *end,
		const char * &beg, const char * &lend)
{
	if (p >= end)
		return false;

	beg = p;
	while (p < end && *p != '\n')
		++p;

	lend = p;
	if (p < end)
		++p;

	while (lend > beg && isspace((unsigned char)lend[-1]))
		--lend;

	return true;
}

// read the next whitespace-delimited token span
//=============================================================================
static inline bool read_span(const char * &p, const char *end,
		const char * &beg, const char * &tend)
{
	skip_ws(p, end);
	if (p >= end)
		return false;

	beg = p;
	while (p < end && !isspace((unsigned char)*p))
		++p;

	tend = p;
	return true;
}

// check whether a span has the syntax of a signed integer
//=============================================================================
static inline bool span_is_integer_like(const char *beg, const char *end)
{
	if (beg >= end)
		return false;

	if (*beg == '+' || *beg == '-')
		++beg;
	if (beg >= end)
		return false;

	for (; beg < end; ++beg) {
		if (*beg < '0' || *beg > '9')
			return false;
	}

	return true;
}

// parse a bounded signed integer without copying
//=============================================================================
static inline bool parse_ll_span(const char *beg, const char *end,
		long long &out)
{
	if (beg >= end)
		return false;

	bool neg = false;
	if (*beg == '+' || *beg == '-') {
		neg = (*beg == '-');
		++beg;
	}
	if (beg >= end)
		return false;

	unsigned long long lim = neg ? (unsigned long long)LLONG_MAX + 1ULL
					     : (unsigned long long)LLONG_MAX;
	unsigned long long val = 0;

	for (; beg < end; ++beg) {
		unsigned char ch = (unsigned char)*beg;
		if (ch < '0' || ch > '9')
			return false;

		unsigned long long dig = (unsigned long long)(ch - '0');
		if (val > (lim - dig) / 10ULL)
			return false;

		val = val * 10ULL + dig;
	}

	if (neg) {
		if (val == (unsigned long long)LLONG_MAX + 1ULL)
			out = LLONG_MIN;
		else
			out = -(long long)val;
	}
	else {
		out = (long long)val;
	}

	return true;
}

// parse the next integer directly from the cursor
//=============================================================================
static inline bool read_int(const char *&p, const char *end, long long &out)
{
	skip_ws(p, end);
	if (p >= end) {
		PyErr_SetString(PyExc_ValueError,
				"unexpected end of input while parsing integer");
		return false;
	}

	const char *beg = p;
	if (*p == '+' || *p == '-')
		++p;
	if (p >= end || *p < '0' || *p > '9') {
		PyErr_SetString(PyExc_ValueError, "invalid integer token");
		return false;
	}

	while (p < end && *p >= '0' && *p <= '9')
		++p;

	if (!parse_ll_span(beg, p, out)) {
		PyErr_SetString(PyExc_ValueError, "invalid integer token");
		return false;
	}

	return true;
}

#endif
