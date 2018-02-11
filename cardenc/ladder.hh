/*
 * ladder.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef LADDER_HH_
#define LADDER_HH_

#include <cmath>
#include "common.hh"

//
//=============================================================================
inline void ladder_encode_equals1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	size_t n = vars.size();
	size_t p = n - 1;

	if (n == 1) {
		vector<int> cl(1, vars[0]);
		clset.create_clause(cl);
		return;
	}

	if (n == 2) {
		vector<int> cl(2);
		cl[0] = vars[0]; cl[1] = vars[1];
		clset.create_clause(cl);

		cl[0] = -vars[0]; cl[1] = -vars[1];
		clset.create_clause(cl);
		return;
	}

	vector<int> auxvars;
	auxvars.push_back(0);

	for (size_t j = 1; j <= p; ++j)
		auxvars.push_back(++top_id);

	vector<int> cl(2);

	// validity clauses (-aux[i+1] v aux[i]) i:1..p-1
	for (size_t i = 1; i < p; i++) {
		cl[0] = -auxvars[i + 1];
		cl[1] =  auxvars[i];
		clset.create_clause(cl);
	}

	// channelling clauses ((aux[i-1] and not aux[i]) <=> x[i])
	// i = 1
	cl[0] = auxvars[1];
	cl[1] = vars[0];
	clset.create_clause(cl);

	cl[0] = -vars[0];
	cl[1] = -auxvars[1];
	clset.create_clause(cl);

	// 1 < i < n
	for (size_t i = 2; i < n; i++) {
		cl.resize(3);
		cl[0] = -auxvars[i - 1];
		cl[1] =  auxvars[i];
		cl[2] =  vars   [i - 1];
		clset.create_clause(cl);

		cl.resize(2);
		cl[0] =  auxvars[i - 1];
		cl[1] = -vars   [i - 1];
		clset.create_clause(cl);

		cl[0] = -vars   [i - 1];
		cl[1] = -auxvars[i];
		clset.create_clause(cl);
	}

	// i = n
	cl[0] = -auxvars[n - 1];
	cl[1] =  vars   [n - 1];
	clset.create_clause(cl);

	cl[0] = -vars   [n - 1];
	cl[1] =  auxvars[n - 1];
	clset.create_clause(cl);
}

//
//=============================================================================
inline void ladder_encode_atmost1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	int extra = ++top_id;

	vector<int> new_vars;
	new_vars.resize(vars.size() + 1);

	for (size_t i = 0; i < vars.size(); i++)
		new_vars[i] = vars[i];

	new_vars[vars.size()] = extra;
	ladder_encode_equals1(top_id, clset, new_vars);
}

//
//=============================================================================
inline void ladder_encode_atleast1(ClauseSet& clset, vector<int>& vars)
{
	common_encode_atleast1(clset, vars);
}

#endif // LADDER_HH_
