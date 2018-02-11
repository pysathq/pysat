/*
 * common.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef CARDCOMMON_HH_
#define CARDCOMMON_HH_

#include "clset.hh"

using namespace std;

//
//=============================================================================
inline void common_encode_atleast1(ClauseSet& clset, vector<int>& vars)
{
	vector<int> cl;

	for (size_t i = 0; i < vars.size(); ++i)
		cl.push_back(vars[i]);

	clset.create_clause(cl);
}

//
//=============================================================================
inline void common_encode_atleastN(ClauseSet& clset, vector<int>& vars)
{
	for (size_t i = 0; i < vars.size(); ++i) {
		vector<int> cl(1, vars[i]);
		clset.create_clause(cl);
	}
}

//
//=============================================================================
inline void common_encode_atmost0(ClauseSet& clset, vector<int>& vars)
{
	for (size_t i = 0; i < vars.size(); ++i) {
		vector<int> cl(1, -vars[i]);
		clset.create_clause(cl);
	}
}

//
//=============================================================================
inline void common_encode_atmostNm1(ClauseSet& clset, vector<int>& vars)
{
	vector<int> cl;

	for (size_t i = 0; i < vars.size(); ++i)
		cl.push_back(-vars[i]);

	clset.create_clause(cl);
}

#endif // CARDCOMMON_HH_
