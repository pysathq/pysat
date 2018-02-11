/*
 * pairwise.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef PAIRWISE_HH_
#define PAIRWISE_HH_

#include "common.hh"

//
//=============================================================================
inline void pairwise_encode_atmost1(ClauseSet& clset, vector<int>& vars)
{
	vector<int> cl; cl.resize(2);

	for (size_t i = 0; i < vars.size(); ++i) {
		for (size_t j = i + 1; j< vars.size(); ++j) {
			cl[0] = -vars[i];
			cl[1] = -vars[j];

			clset.create_clause(cl);
		}
	}
}

//
//=============================================================================
inline void pairwise_encode_atleast1(ClauseSet& clset, vector<int>& vars)
{
	common_encode_atleast1(clset, vars);
}

//
//=============================================================================
inline void pairwise_encode_equals1(ClauseSet& clset, vector<int>& vars)
{
	pairwise_encode_atleast1(clset, vars);
	pairwise_encode_atmost1 (clset, vars);
}

#endif // PAIRWISE_HH_
