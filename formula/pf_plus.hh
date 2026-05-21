/*
 * pf_plus.hh
 *
 *  Created on: May 19, 2025
 *      Author: Alexey Ignatiev
 *      E-mail: alexey.ignatiev@monash.edu
 */

#ifndef __PF_PLUS_HH__
#define __PF_PLUS_HH__

#include "pyformula.hh"

// reset the temporary state used for CNF+/WCNF+ bodies
//=============================================================================
static inline void init_plus_body(plus_body &body)
{
	body.weighted = false;
	body.clause   = false;
	body.rhs      = 0;
	body.sumw     = 0;
	body.lits.clear();
	body.wght.clear();
}

// normalize a >= constraint into an equivalent <= form
//=============================================================================
static inline void normalize_ge(plus_body &body)
{
	for (size_t i = 0; i < body.lits.size(); ++i)
		body.lits[i] = -body.lits[i];

	body.rhs = body.sumw - body.rhs;
}

#endif
