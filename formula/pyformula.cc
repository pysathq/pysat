/*
 * pyformula.cc
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#include "pyformula.hh"

// module docstrings
//=============================================================================
static char    module_docstring[] = "Fast DIMACS parsers for PySAT formula "
				    "objects.";
static char      pcnf_docstring[] = "Parse a DIMACS CNF.";
static char     pwcnf_docstring[] = "Parse a DIMACS WCNF.";
static char  pcnfplus_docstring[] = "Parse a DIMACS CNF+.";
static char pwcnfplus_docstring[] = "Parse a DIMACS WCNF+.";

// module-level objects
//=============================================================================
PyObject *formula_err;
PyObject *dec_cls;
PyObject *dec_inf;

// Python wrapper for CNF parsing
//=============================================================================
static PyObject *py_parse_cnf(PyObject *self, PyObject *args)
{
	PyObject *text;
	PyObject *comment_lead;

	if (!PyArg_ParseTuple(args, "OO", &text, &comment_lead))
		return NULL;

	return parse_cnf_impl(text, comment_lead);
}

// Python wrapper for WCNF parsing
//=============================================================================
static PyObject *py_parse_wcnf(PyObject *self, PyObject *args)
{
	PyObject *text;
	PyObject *comment_lead;

	if (!PyArg_ParseTuple(args, "OO", &text, &comment_lead))
		return NULL;

	return parse_wcnf_impl(text, comment_lead);
}

// Python wrapper for CNF+ parsing
//=============================================================================
static PyObject *py_parse_cnfplus(PyObject *self, PyObject *args)
{
	PyObject *text;
	PyObject *comment_lead;

	if (!PyArg_ParseTuple(args, "OO", &text, &comment_lead))
		return NULL;

	return parse_cnfplus_impl(text, comment_lead);
}

// Python wrapper for WCNF+ parsing
//=============================================================================
static PyObject *py_parse_wcnfplus(PyObject *self, PyObject *args)
{
	PyObject *text;
	PyObject *comment_lead;

	if (!PyArg_ParseTuple(args, "OO", &text, &comment_lead))
		return NULL;

	return parse_wcnfplus_impl(text, comment_lead);
}

// module specification
//=============================================================================
static PyMethodDef module_methods[] = {
	{ "parse_cnf",      py_parse_cnf,      METH_VARARGS,      pcnf_docstring },
	{ "parse_wcnf",     py_parse_wcnf,     METH_VARARGS,     pwcnf_docstring },
	{ "parse_cnfplus",  py_parse_cnfplus,  METH_VARARGS,  pcnfplus_docstring },
	{ "parse_wcnfplus", py_parse_wcnfplus, METH_VARARGS, pwcnfplus_docstring },
	{ NULL, NULL, 0, NULL }
};

//
//=============================================================================
static struct PyModuleDef module_def = {
	PyModuleDef_HEAD_INIT,
	"pyformula",       /* m_name */
	module_docstring,   /* m_doc */
	-1,                 /* m_size */
	module_methods,     /* m_methods */
	NULL,               /* m_reload */
	NULL,               /* m_traverse */
	NULL,               /* m_clear */
	NULL,               /* m_free */
};

// module initialization
//=============================================================================

// initialize the native pyformula module and also Decimal helpers
//=============================================================================
PyMODINIT_FUNC PyInit_pyformula(void)
{
	PyObject *m = PyModule_Create(&module_def);
	if (m == NULL)
		return NULL;

	formula_err = PyErr_NewException((char *)"pyformula.error", NULL, NULL);
	if (formula_err == NULL) {
		Py_DECREF(m);
		return NULL;
	}

	Py_INCREF(formula_err);
	if (PyModule_AddObject(m, "error", formula_err) < 0) {
		Py_DECREF(formula_err);
		Py_DECREF(m);
		return NULL;
	}

	PyObject *decmod = PyImport_ImportModule("decimal");
	if (decmod == NULL) {
		Py_DECREF(m);
		return NULL;
	}

	dec_cls = PyObject_GetAttrString(decmod, "Decimal");
	Py_DECREF(decmod);
	if (dec_cls == NULL) {
		Py_DECREF(m);
		return NULL;
	}

	PyObject *infstr = PyUnicode_FromString("+inf");
	if (infstr == NULL) {
		Py_DECREF(m);
		return NULL;
	}

	dec_inf = PyObject_CallFunctionObjArgs(dec_cls, infstr, NULL);
	Py_DECREF(infstr);
	if (dec_inf == NULL) {
		Py_DECREF(m);
		return NULL;
	}

	return m;
}
