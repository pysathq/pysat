/*
 * utils.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef CARDUTILS_HH_
#define CARDUTILS_HH_

#include <vector>
#include "clset.hh"
#include "ptypes.hh"

//
//=============================================================================
template <class PT>
inline PT make_pair(int v1, int v2)
{
	return (PT) std::make_pair(v1, v2);
}

//
//=============================================================================
template <class PH, class PT>
inline int mk_yvar(int& top_id, PH& vset, PT np)
{
	typename PH::iterator ppos = vset.find(np);
	int nid = -1;

	if (ppos == vset.end()) {
		nid = ++top_id;
		vset.insert(make_pair(np, nid));
	}
	else
		nid = ppos->second;

	return nid;
}

//
//=============================================================================
inline void encode_ite(ClauseSet& clset, int ov, int sv, int x1, int x0)
{
	clset.create_ternary_clause(-sv,  x1, -ov);
	clset.create_ternary_clause(-sv, -x1,  ov);
	clset.create_ternary_clause( sv,  x0, -ov);
	clset.create_ternary_clause( sv, -x0,  ov);
	clset.create_ternary_clause( ov, -x0, -x1);
	clset.create_ternary_clause(-ov,  x0,  x1);
}

//
//=============================================================================
inline void encode_and(ClauseSet& clset, int ov, int x1, int x0)
{
	clset.create_binary_clause ( x0,     -ov);
	clset.create_binary_clause ( x1,     -ov);
	clset.create_ternary_clause(-x0, -x1, ov);
}

//
//=============================================================================
inline void encode_or(ClauseSet& clset, int ov, int x1, int x0)
{
	clset.create_binary_clause (-x0,      ov);
	clset.create_binary_clause (-x1,      ov);
	clset.create_ternary_clause( x0, x1, -ov);
}

//
//=============================================================================
inline void encode_2equiv(ClauseSet& clset, int ov, int iv)
{
	clset.create_binary_clause(-iv,  ov);
	clset.create_binary_clause( iv, -ov);
}

//
//=============================================================================
inline void encode_comparator(ClauseSet& clset,
	int omx,
	int omn,
	int x0,
	int x1
)
{
	encode_and(clset, omn, x0, x1);
	encode_and(clset, omx, x0, x1);
}

//
//=============================================================================
inline void encode_implic_pos_ite(
	ClauseSet& clset,
	int ov,
	int sv,
	int x1,
	int x0
)
{
	// generate CNF for ITE (positive polarity)
	clset.create_ternary_clause(-sv, x1, -ov);
	clset.create_ternary_clause( sv, x0, -ov);
}

//
//=============================================================================
inline void encode_implic_pos_and(ClauseSet& clset, int ov, int x1, int x0)
{
	// generate CNF for AND (positive polarity)
	clset.create_binary_clause(x1, -ov);
	clset.create_binary_clause(x0, -ov);
}

//
//=============================================================================
inline void encode_implic_pos_or(ClauseSet& clset, int ov, int x1, int x0)
{
	// generate CNF for OR (positive polarity)
	clset.create_ternary_clause(x1, x0, -ov);
}

//
//=============================================================================
inline void encode_implic_pos_2equiv(ClauseSet& clset, int ov, int iv)
{
	// generate CNF for equiv vars
	clset.create_binary_clause(-iv,  ov);
	clset.create_binary_clause( iv, -ov);
}

//
//=============================================================================
inline void create_vvect(int& top_id, vector<int>& ov, size_t nvars)
{
	assert(nvars > 0);

	size_t refnv = ov.size();
	size_t tvars = refnv + nvars;
	ov.resize(tvars, 0);

	for (size_t k = refnv; k < tvars; ++k)
		ov[k] = ++top_id;

	assert(ov.size() > 0);
}

//
//=============================================================================
inline void copy_vvect(int& top_id, vector<int>& ov, vector<int>& iv)
{
	size_t refnv = ov.size();
	ov.resize(refnv + iv.size(), 0);

	for (size_t k = 0; k < iv.size(); ++k)
		ov[refnv + k] = iv[k];

	assert(ov.size() > 0);
}

//
//=============================================================================
inline void mk_half_vect(vector<int>& ov, vector<int>& iv, size_t offset)
{
	assert(iv.size() > 0);

	size_t ns = iv.size() / 2;
	ov.resize(ns, 0);

	for (size_t k = 0; k < ns; ++k)
		ov[k] = iv[offset + k];
}

//
//=============================================================================
inline void mk_ksize_vect(
	vector<int>& ov,
	vector<int>& iv,
	size_t sz,
	size_t offset
)
{
	ov.resize(sz, 0);

	for (size_t k = 0; k < sz; ++k)
		ov[k] = iv[offset + k];
}

//
//=============================================================================
inline void mk_odd_vect(vector<int>& ov, vector<int>& iv)
{
	assert(iv.size() > 0);

	size_t ns = iv.size() / 2;
	ov.resize(ns, 0);

	for (size_t k = 0; k < ns; ++k)
		ov[k] = iv[k * 2];
}

//
//=============================================================================
inline void mk_even_vect(vector<int>& ov, vector<int>& iv)
{
	assert(iv.size() > 0);

	size_t ns = iv.size() / 2;
	ov.resize(ns, 0);

	for (size_t k = 0; k < ns; ++k)
		ov[k] = iv[k * 2 + 1];
}

#endif // CARDUTILS_HH_
