/*
 * pyformula.hh
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#ifndef __PYFORMULA_HH__
#define __PYFORMULA_HH__

#define PY_SSIZE_T_CLEAN

#include <Python.h>
#include <ctype.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>
#include <vector>

using namespace std;

// parser overview
//=============================================================================
// The code below follows one cursor-based parsing style throughout.
// The aim is to replicate the former PySAT's parsers for all *CNF? formats.
//
// Generic path:
//   next_line()      -> split the input into trimmed lines
//   read_span()      -> scan the next token on a line
//   parse_ll_span()  -> parse a bounded integer token/span
//   read_int()       -> parse the next integer directly from a cursor
//
// Formula-specific path:
//   CNF      : parse_clause_body() -> mk_llist()
//   WCNF     : read weight with parse_wght_span(), parse clause body,
//              classify with append_weighted_clause()
//   CNF+     : parse_plus_body() -> clause or AtMost/PB constraint
//   WCNF+    : parse weight with parse_wght_span(), then parse_plus_body(),
//              then route either to append_weighted_clause() or mk_atm()
//
// Weight parsing:
//   parse_wght_span() parses clause/top weights as hard-marker 'h', integer,
//   or decimal.Decimal; parse_wlit_span() parses weighted PB literals w*l.
//
// Public wrappers are py_parse_*(); parse_*_impl() contain the actual parser
// implementations used by those wrappers.
//
// Note that preambles are only recognized enough to distinguish the format
// and, for weighted formats, extract the optional top weight.

#define PYINT_CACHE_SIZE (1u << 10)

extern PyObject *formula_err;
extern PyObject *dec_cls;
extern PyObject *dec_inf;

typedef struct {
	long long key;
	PyObject *obj;
	unsigned char used;
} int_cache_ent;

typedef struct {
	int_cache_ent slots[PYINT_CACHE_SIZE];
	uint16_t   used_idx[PYINT_CACHE_SIZE];
	size_t used_count;
} int_cache;

typedef struct {
	bool weighted;
	bool clause;
	long long rhs;
	long long sumw;
	vector<long long> lits;
	vector<long long> wght;
} plus_body;

bool parse_weight_preamble(const char *beg, const char *end,
		const char *errmsg, PyObject **topw);

bool parse_clause_body(const char *p, const char *end,
		vector<long long> &lits);

bool parse_plus_body(const char *first_beg, const char *first_end,
		const char *p, const char *end, plus_body &body);

PyObject *mk_atm(const plus_body &body, int_cache *cache, long long &nv);

bool append_weighted_clause(PyObject *hard, PyObject *soft, PyObject *wght,
		PyObject *negs, PyObject *topw, PyObject *zero, PyObject *cl,
		PyObject *wt);

PyObject *parse_cnf_impl     (PyObject *txt_obj, PyObject *comment_lead);
PyObject *parse_wcnf_impl    (PyObject *txt_obj, PyObject *comment_lead);
PyObject *parse_cnfplus_impl (PyObject *txt_obj, PyObject *comment_lead);
PyObject *parse_wcnfplus_impl(PyObject *txt_obj, PyObject *comment_lead);

#endif
