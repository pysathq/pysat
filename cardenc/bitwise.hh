/*
 * bitwise.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef BITWISE_HH_
#define BITWISE_HH_

#include <cmath>
#include "common.hh"

//
//=============================================================================
inline void bitwise_encode_atmost1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	size_t naux = ceil(log(1.0 * vars.size()) / log(2.0));

	vector<int> togs, vids, cl;

	for (size_t j = 0; j < naux; ++j) {
		togs.push_back(0);
		vids.push_back(++top_id);
	}

	for (size_t i = 0; i < vars.size(); ++i) {
		for (size_t j = 0; j < naux; ++j) {
			cl.push_back(-vars[i]);
			cl.push_back(togs[j] ? vids[j] : -vids[j]);

			clset.create_clause(cl);
			cl.clear();
		}

		for (int j = naux - 1; j >= 0; ) {
			if (togs[j] == 0) {
				togs[j] = 1;
				break;
			}
			else
				togs[j--] = 0;
		}
	}
}

//
//=============================================================================
inline void bitwise_encode_atleast1(ClauseSet& clset, vector<int>& vars)
{
	common_encode_atleast1(clset, vars);
}

//
//=============================================================================
inline void bitwise_encode_equals1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	bitwise_encode_atleast1(        clset, vars);
	bitwise_encode_atmost1 (top_id, clset, vars);
}

#endif // BITWISE_HH_
