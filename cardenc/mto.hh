/*
 * mto.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef MTO_HH_
#define MTO_HH_

#include <cmath>
#include "common.hh"
#include "ptypes.hh"
#include "utils.hh"

// totalizer
//=============================================================================
inline void to_UA(
	int& top_id,
	ClauseSet& clset,
	vector<int>& outlst,
	vector<int>& alst,
	vector<int>& blst
)
{
	size_t m = alst.size();
	size_t n = blst.size();

	// add the constraints
	for (size_t j = 0; j < n; j++)
		clset.create_binary_clause(-blst[j], outlst[j]);

	for (size_t i = 0; i < m; i++)
		clset.create_binary_clause(-alst[i], outlst[i]);

	for (size_t i = 1; i <= m; i++) {
		for (size_t j = 1; j <= n; j++)
			clset.create_ternary_clause(-alst[i - 1], -blst[j - 1], outlst[i + j - 1]);
	}
}

//
//=============================================================================
inline void to_TO(
	int& top_id,
	ClauseSet& clset,
	vector<int>& outvars,
	vector<int>& invars
)
{
	size_t n = invars.size();

	if (n < 2) {
		outvars.resize(n);
		for (size_t i = 0; i < n; i++)
			outvars[i] = invars[i];

		return;
	}

	outvars.resize(n);
	for (size_t i = 0; i < n; i++)
		outvars[i] = ++top_id;

	vector<pair<vector<int> *, vector<int> *> > stack;

	vector<int> *ilst = new vector<int>; ilst->resize(n);
	vector<int> *olst = new vector<int>; olst->resize(n);
	for (size_t i = 0; i < n; i++) {
		(*ilst)[i] =  invars[i];
		(*olst)[i] = outvars[i];
	}

	pair<vector<int> *, vector<int> *> bottom (ilst, olst);
	stack.push_back(bottom);

	while (!stack.empty()) {
		ilst = stack.back().first;
		olst = stack.back().second;
		stack.pop_back();

		n = ilst->size();
		size_t half = n - (n >> 1);

		vector<int> *fsthalf = new vector<int>(half);
		for (size_t i = 0; i < half; i++)
			(*fsthalf)[i] = (*ilst)[i];

		vector<int> *outfsthalf = new vector<int>(half);
		if (half < 2)
			for (size_t i = 0; i < half; i++)
				(*outfsthalf)[i] = (*fsthalf)[i];
		else {
			for (unsigned i = 0; i < half; i++)
				(*outfsthalf)[i] = ++top_id;
			pair<vector<int> *, vector<int> *> next(fsthalf, outfsthalf);
			stack.push_back(next);
		}

		vector<int> *sndhalf = new vector<int>(n - half);
		for (size_t i = 0; i < n - half; i++)
			(*sndhalf)[i] = (*ilst)[half + i];

		vector<int> *outsndhalf= new vector<int>(n - half);
		if (n - half < 2) {
			for (size_t i = 0; i < n - half; i++)
				(*outsndhalf)[i] = (*sndhalf)[i];
		}
		else {
			for (size_t i = 0; i < n - half; i++)
				(*outsndhalf)[i] = ++top_id;

			pair<vector<int> *, vector<int> *> next(sndhalf, outsndhalf);
			stack.push_back(next);
		}

		to_UA(top_id, clset, *olst, *outfsthalf, *outsndhalf);

		delete ilst;
		delete olst;
	}
}

//
//=============================================================================
inline void to_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int k
)
{
	size_t n = vars.size();

	if ((size_t)k >= n)
		return;

	if (k == 0) {
		common_encode_atmost0(clset, vars);
		return;
	}

	vector<int> outvars;
	to_TO(top_id, clset, outvars, vars);
	clset.create_unit_clause(-outvars[k]);
}

//
//=============================================================================
inline void to_encode_atleastN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int tval
)
{
	vector<int> ps;
	int nrhs = -tval;

	for(size_t i = 0; i < vars.size(); i++) {
		nrhs += 1; // The weight in fact
		ps.push_back(-vars[i]);
	}

	to_encode_atmostN(top_id, clset, ps, nrhs);
}

// modulo totalizer
//=============================================================================
inline void mto_MUA_A(
	int& top_id,
	ClauseSet& clset,
	vector<int>& hs,
	vector<int>& rs,
	vector<int>& fs,
	vector<int>& as,
	vector<int>& gs,
	vector<int>& bs,
	size_t p
)
{
	size_t sigma = hs.size();
	size_t alfa  = fs.size();
	size_t m     = as.size();
	size_t beta  = gs.size();
	size_t n     = bs.size();

	int c = ++top_id;

	// phi 1
	// i = 0 (n < p necessarily)
	for (size_t j = 1; j <= n; j++)
		clset.create_ternary_clause(-bs[j - 1], rs[j - 1], c);

	// j = 0 (m < p necessarily)
	for (size_t i = 1; i <= m; i++)
		clset.create_ternary_clause(-as[i - 1], rs[i - 1], c);

	// i, j != 0
	for (size_t i = 1; i <= m; i++) {
		for (size_t j = 1; j <= n; j++) {
			if (i + j < p) {
				vector<int> lits(4);
				lits[0] = -as[i - 1];
				lits[1] = -bs[j - 1];
				lits[2] =  rs[i + j - 1];
				lits[3] = c;
				clset.create_clause(lits);
			}
			else if (i + j > p)
				clset.create_ternary_clause(-as[i - 1], -bs[j - 1], rs[((i + j) % p) - 1]);
			else
				clset.create_ternary_clause(-as[i - 1], -bs[j - 1], c);
		}
	}

	// phi 2
	// i = 0 j = 0
	if (sigma == 0)
		clset.create_unit_clause(-c);
	else
		clset.create_binary_clause(-c, hs[0]);

	// i = 0
	for (size_t j = 1; j <= beta; j++) {
		if (j <= sigma)
			clset.create_binary_clause(-gs[j - 1], hs[j - 1]);
		else
			clset.create_unit_clause  (-gs[j - 1]);

		if (j < sigma)
			clset.create_ternary_clause(-c, -gs[j - 1], hs[j]);
		else
			clset.create_binary_clause (-c, -gs[j - 1]);
	}

	// j = 0
	for (size_t i = 1; i <= alfa; i++) {
		if (i <= sigma)
			clset.create_binary_clause(-fs[i - 1], hs[i - 1]);
		else
			clset.create_unit_clause  (-fs[i - 1]);

		if (i < sigma)
			clset.create_ternary_clause(-c, -fs[i - 1], hs[i]);
		else
			clset.create_binary_clause (-c, -fs[i - 1]);
	}

	// i, j != 0
	for (size_t i = 1; i <= alfa; i++) {
		for (size_t j = 1; j <= beta; j++) {
			if (i + j <= sigma)
				clset.create_ternary_clause(-fs[i - 1], -gs[j - 1], hs[i + j - 1]);
			else
				clset.create_binary_clause (-fs[i - 1], -gs[j - 1]);

			vector<int> lits(3);
			lits[0] = -c;
			lits[1] = -fs[i - 1];
			lits[2] = -gs[j - 1];

			if (i + j < sigma)
				lits.push_back(hs[i + j]);

			clset.create_clause(lits);
		}
	}
}

//
//=============================================================================
inline void mto_MTO_A(
	int& top_id,
	ClauseSet& clset,
	vector<int>& us,
	vector<int>& ls,
	vector<int>& is,
	size_t p,
	int k = -1)
{
	if (is.size() < p) {
		us.resize(0);
		to_TO(top_id, clset, ls, is);
		return;
	}

	size_t un = is.size() / p;
	if (k >= 0 && k / p < un)
		un = k / p;

	us.resize(un);
	for (size_t i = 0; i < un; i++)
		us[i] = ++top_id;

	ls.resize(p - 1);
	for (size_t i = 0; i < p - 1; i++)
		ls[i] = ++top_id;

	vector<int> *ilst = new vector<int>(is);
	vector<int> *ulst = new vector<int>(us);
	vector<int> *llst = new vector<int>(ls);

	pair<vector<int> *, pair<vector<int> *, vector<int> *> > bottom;
	bottom.first = ilst;
	bottom.second.first  = ulst;
	bottom.second.second = llst;

	vector<pair<vector<int> *, pair<vector<int> *, vector<int> *> > > stack;
	stack.push_back(bottom);

	while (!stack.empty()) {
		ilst = stack.back().first;
		ulst = stack.back().second.first;
		llst = stack.back().second.second;
		stack.pop_back();

		vector<int> *ufsthalf;
		vector<int> *lfsthalf;
		vector<int> *usndhalf;
		vector<int> *lsndhalf;

		size_t ni   = ilst->size();
		size_t half = ni - (ni >> 1);

		vector<int> *fsthalf = new vector<int>(half);
		for (size_t i = 0; i < half; i++)
			(*fsthalf)[i] = (*ilst)[i];

		if (half < p) {
			ufsthalf = new vector<int>(0);
			lfsthalf = new vector<int>();

			to_TO(top_id, clset, *lfsthalf, *fsthalf);
		}
		else {
			un = half / p;
			if (k >= 0 && k / p < un)
				un = k / p;

			ufsthalf = new vector<int>(un);
			for (size_t i = 0; i < un; i++)
				(*ufsthalf)[i] = ++top_id;

			lfsthalf = new vector<int>(p - 1);
			for (size_t i = 0; i < p - 1; i++)
				(*lfsthalf)[i] = ++top_id;

			pair<vector<int> *, pair<vector<int> *, vector<int> *> > next;
			next.first = fsthalf;
			next.second.first  = ufsthalf;
			next.second.second = lfsthalf;

			stack.push_back(next);
		}

		vector<int> *sndhalf = new vector<int>(ni - half);
		for (size_t i = 0; i < ni - half; i++)
			(*sndhalf)[i] = (*ilst)[i + half];

		if (ni - half < p) {
			usndhalf = new vector<int>(0);
			lsndhalf = new vector<int>();

			to_TO(top_id, clset, *lsndhalf, *sndhalf);
		}
		else {
			un = (ni - half) / p;
			if (k >= 0 && k / p < un)
				un = k / p;

			usndhalf = new vector<int>(un);
			for (size_t i = 0; i < un; i++)
				(*usndhalf)[i] = ++top_id;

			lsndhalf = new vector<int>(p - 1);
			for (size_t i = 0; i < p - 1; i++)
				(*lsndhalf)[i] = ++top_id;

			pair<vector<int> *, pair<vector<int> *, vector<int> *> > next;
			next.first = sndhalf;
			next.second.first  = usndhalf;
			next.second.second = lsndhalf;
			stack.push_back(next);
		}

		mto_MUA_A(top_id, clset, *ulst, *llst, *ufsthalf, *lfsthalf,
				*usndhalf, *lsndhalf, p);

		delete ilst;
		delete ulst;
		delete llst;
	}
}

//
//=============================================================================
inline void mto_comparator(
	int& top_id,
	ClauseSet& clset,
	vector<int>& upper,
	vector<int>& lower,
	size_t p,
	int k
)
{
	size_t ro = k / p;
	size_t nu = k % p;

	// upper
	for (size_t i = ro + 1; i <= upper.size(); i++)
		clset.create_unit_clause(-upper[i - 1]);

	// lower
	for (size_t i = nu + 1; i < p; i++) {
		if (ro > 0) {
			if (ro - 1 < upper.size())
				clset.create_binary_clause(-upper[ro - 1], -lower[i - 1]);
		}
		else
			clset.create_unit_clause(-lower[i - 1]);
	};
}

//
//=============================================================================
inline void mto_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int k
)
{
	size_t n = vars.size();

	if ((size_t)k >= n)
		return;

	if (k == 0) {
		// generate \sum x <= 0
		common_encode_atmost0(clset, vars);
		return;
	}

	size_t p = (size_t)floor(sqrt((double)n));
	if (p < 2)
		p = 2;

	vector<int> uvars, lvars;
	mto_MTO_A(top_id, clset, uvars, lvars, vars, p);
	mto_comparator(top_id, clset, uvars, lvars, p, k);
}

//
//=============================================================================
inline void mto_encode_atleastN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int tval
)
{
	vector<int> ps;
	int nrhs = -tval;
	for (size_t i = 0; i < vars.size(); i++) {
		nrhs += 1; // the weight in fact
		ps.push_back(-vars[i]);
	}

	mto_encode_atmostN(top_id, clset, ps, nrhs);
}

// approximation of k modulo totalizer
//=============================================================================
inline void kmto_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int k
)
{
	size_t n = vars.size();

	if ((size_t)k >= n)
		return;

	if (k == 0) {
		// generate \sum x <= 0
		common_encode_atmost0(clset, vars);
		return;
	}

	size_t p = (size_t)floor(sqrt((double)k));
	if (p < 2)
		p = 2;

	vector<int> uvars, lvars;
	mto_MTO_A(top_id, clset, uvars, lvars, vars, p, k);
	mto_comparator(top_id, clset, uvars, lvars, p, k);
}

//
//=============================================================================
inline void kmto_encode_atleastN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int tval
)
{
	vector<int> ps;
	int nrhs = -tval;

	for (size_t i = 0; i < vars.size(); i++) {
		nrhs += 1; // the weight in fact
		ps.push_back(-vars[i]);
	}

	kmto_encode_atmostN(top_id, clset, ps, nrhs);
}

//
//=============================================================================
inline void kmto_encode_equalsN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int k
)
{
	kmto_encode_atmostN (top_id, clset, vars, k);
	kmto_encode_atleastN(top_id, clset, vars, k);
}

#endif // MTO_HH_
