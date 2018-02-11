/*
 * seqcounter.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef SEQCOUNTER_HH_
#define SEQCOUNTER_HH_

#include <cmath>
#include "common.hh"
#include "ptypes.hh"
#include "utils.hh"

//
//=============================================================================
inline void seqcounter_encode_atmost1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	if (vars.empty())
		return;

	int cid  = ++top_id;
	int xlit = -vars[0];

	vector<int> cl; cl.push_back(xlit); cl.push_back(cid);
	clset.create_clause(cl); cl.clear();

	for (size_t j = 1; j < vars.size(); ++j) {
		xlit = -vars[j];
		cl.push_back(xlit);
		cl.push_back(-cid);
		clset.create_clause(cl); cl.clear();

		int nid = ++top_id;
		cl.push_back(xlit);
		cl.push_back(nid);
		clset.create_clause(cl); cl.clear();

		cl.push_back(-cid);
		cl.push_back(nid);
		clset.create_clause(cl); cl.clear();

		cid = nid;
	}

	xlit = -vars[vars.size()];
	cl.push_back(xlit);
	cl.push_back(-cid);
	clset.create_clause(cl);
}

//
//=============================================================================
inline void seqcounter_encode_atleast1(ClauseSet& clset, vector<int>& vars)
{
	common_encode_atleast1(clset, vars);
}

//
//=============================================================================
inline void seqcounter_encode_equals1(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars
)
{
	seqcounter_encode_atleast1(        clset, vars);
	seqcounter_encode_atmost1 (top_id, clset, vars);
}

//
//=============================================================================
void seqcounter_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int tval
)
{
	if ((size_t)tval >= vars.size())
		return;

	if ((size_t)tval == vars.size() - 1) {
		common_encode_atmostNm1(clset, vars);
		return;
	}

	if (tval == 0) {
		common_encode_atmost0(clset, vars);
		return;
	}

	// initialize the map
	Pair2IntMap p2i_map;

	// phase 1
	int s11 = mk_yvar(top_id, p2i_map, make_pair(1, 1));
	clset.create_binary_clause(s11, -vars[0]);

	// phase 2
	for (int j = 2; j <= tval; j++) {
		int s1j = mk_yvar(top_id, p2i_map, make_pair(1, j));
		clset.create_unit_clause(-s1j);
	}

	// phase 3
	for (unsigned int i = 2; i < vars.size(); i++) {
		// phase 3.1
		int si1 = mk_yvar(top_id, p2i_map, make_pair(i, 1));
		clset.create_binary_clause(-vars[i - 1], si1);

		int sim11 = mk_yvar(top_id, p2i_map, make_pair(i - 1, 1));
		clset.create_binary_clause(-sim11, si1);

		// phase 3.2
		for (int j = 2; j <= tval; j++) {
			int sim1jm1 = mk_yvar(top_id, p2i_map, make_pair(i - 1, j - 1));
			int sij = mk_yvar(top_id, p2i_map, make_pair(i, j));
			clset.create_ternary_clause(-vars[i - 1], -sim1jm1, sij);
			int sim1j = mk_yvar(top_id, p2i_map, make_pair(i - 1, j));
			clset.create_binary_clause(-sim1j, sij);
		}

		// phase 3.3
		int sim1k = mk_yvar(top_id, p2i_map, make_pair(i - 1, tval));
		clset.create_binary_clause(-vars[i - 1], -sim1k);
	}

	// fourth phase
	int n = vars.size();
	int snm1k = mk_yvar(top_id, p2i_map, make_pair(n - 1, tval));
	clset.create_binary_clause(-vars[n - 1], -snm1k);
	p2i_map.clear();
}

//
//=============================================================================
void seqcounter_encode_atleastN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int tval
)
{
	vector<int> ps;
	int nrhs = -tval;

	for (size_t i = 0; i < vars.size(); i++) {
		nrhs += 1;  // the weight in fact
		ps.push_back(-vars[i]);
	}

	seqcounter_encode_atmostN(top_id, clset, ps, nrhs);
}

#endif // SEQCOUNTER_HH_
