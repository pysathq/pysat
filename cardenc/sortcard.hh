/*
 * sortcard.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef SORTCARD_HH_
#define SORTCARD_HH_

#include "common.hh"
#include "utils.hh"

#define NOPTCLS true

// sorting networks
//=============================================================================
inline void sortn_half_merge_recur(
	int& top_id,
	ClauseSet& clset,
	vector<int>& av,
	vector<int>& bv,
	vector<int>& cv,
	size_t zvar
)
{
	assert(bv.size() == av.size());

	if (av.size() == 1) { // vectors of size 1
		assert(av[0] != 0);
		if (NOPTCLS || (av[0] != zvar && bv[0] != zvar)) {
			create_vvect(top_id, cv, 2);
			clset.create_binary_clause (-av[0],  cv[0]);
			clset.create_binary_clause (-bv[0],  cv[0]);
			clset.create_ternary_clause(-av[0], -bv[0], cv[1]);
		}
		else {
			if (av[0] == zvar) {
				cv.push_back(bv[0]);
				cv.push_back(av[0]);
			}
			else {
				assert(bv[0] == zvar);
				cv.push_back(av[0]);
				cv.push_back(bv[0]);
			}
		}
	}
	else {
		if (NOPTCLS ||
				((av[0] != zvar || av[av.size() - 1] != zvar) &&
				 (bv[0] != zvar || bv[av.size() - 1] != zvar))) {
			vector<int> aodd, aeven, bodd, beven, dv, ev;

			mk_odd_vect(aodd, av); mk_even_vect(aeven, av);
			mk_odd_vect(bodd, bv); mk_even_vect(beven, bv);

			sortn_half_merge_recur(top_id, clset, aodd,  bodd,  dv, zvar);
			sortn_half_merge_recur(top_id, clset, aeven, beven, ev, zvar);

			assert(cv.size() == 0);
			cv.push_back(dv[0]);
			create_vvect(top_id, cv, 2 * av.size() - 2);
			cv.push_back(ev[ev.size() - 1]);

			for (size_t i = 0; i < av.size() - 1; ++i) {
				assert(i + 1 < dv.size());
				assert(i < ev.size());
				assert(2 * 1 + 1 < cv.size());

				clset.create_binary_clause (-dv[i + 1],  cv[2 * i + 1]);
				clset.create_binary_clause (-ev[i    ],  cv[2 * i + 1]);
				clset.create_ternary_clause(-dv[i + 1], -ev[i], cv[2 * i + 2]);
			}
		}
		else {
			if (av[0] == zvar && av[av.size() - 1] == zvar) {
				copy_vvect(top_id, cv, bv);
				copy_vvect(top_id, cv, av);
			}
			else {
				assert(bv[0] == zvar && bv[av.size() - 1] == zvar);
				copy_vvect(top_id, cv, av);
				copy_vvect(top_id, cv, bv);
			}
		}
	}

	assert(cv.size() > 0);
}

//
//=============================================================================
inline vector<int>& sortn_half_sorter_recur(
	int& top_id,
	ClauseSet& clset,
	vector<int>& av,
	vector<int>& cv,
	size_t zvar
)
{
	assert(av.size() > 1);

	if (av.size() == 2) {
		assert(av[0] != 0 && av[1] != 0);

		vector<int> xav, xbv; xav.push_back(av[0]); xbv.push_back(av[1]);
		sortn_half_merge_recur(top_id, clset, xav, xbv, cv, zvar);
	}
	else {
		vector<int> dv1, dv2, lav, uav;
		mk_half_vect(lav, av, 0);
		mk_half_vect(uav, av, av.size() / 2);

		assert(lav.size() == uav.size());
		sortn_half_sorter_recur(top_id, clset, lav, dv1, zvar); assert(dv1.size() > 0);
		sortn_half_sorter_recur(top_id, clset, uav, dv2, zvar); assert(dv2.size() > 0);
		sortn_half_merge_recur (top_id, clset, dv1, dv2, cv, zvar);
	}

	assert(cv.size() > 0);
	return cv;
}

//
//=============================================================================
inline void sortn_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int rhs
)
{
	int nvars = vars.size();

	if (rhs >= nvars)
		return;
	else if (rhs == nvars - 1) {
		common_encode_atmostNm1(clset, vars);
		return;
	}
	else if (rhs == 0) {
		common_encode_atmost0(clset, vars);
		return;
	}

	// get smallest power of 2 larger than number of vars
	int exponent = trunc(log(nvars) / log(2));  // assume exponent
	double nvtmp = exp(log(2) * exponent);

	// check if number of vars already is power of 2; correct exponent if required
	exponent = (nvars - nvtmp < 0.000001) ? exponent : exponent + 1;
	int nnvars = trunc(exp(log(2) * exponent) + 0.1);

	// copy set of vars, and extend w/ 0. Note: aux vars are simply 0 ...
	vector<int> vvect(vars); int zvar = 0;
	if ((size_t) nnvars != vars.size()) {
		zvar = ++top_id;
		vvect.resize(nnvars, zvar);
		clset.create_unit_clause(-zvar);
	}

	// 1. generate odd-even sorting network
	vector<int> outv;
	sortn_half_sorter_recur(top_id, clset, vvect, outv, zvar);

	// 2. force constraints on outputs
	clset.create_unit_clause(-outv[rhs]);
}

// cardinality networks
//=============================================================================
inline void cardn_simple_merge_recur(
	int& top_id,
	ClauseSet& clset,
	vector<int>& av,
	vector<int>& bv,
	vector<int>& cv,
	size_t zvar
)
{
	assert(bv.size() == av.size());

	if (av.size() == 1) { // vectors of size 1
		assert(av[0] != 0);
		if (NOPTCLS || (av[0] != zvar && bv[0] != zvar)) {
			create_vvect(top_id, cv, 2);
			clset.create_binary_clause (-av[0],  cv[0]);
			clset.create_binary_clause (-bv[0],  cv[0]);
			clset.create_ternary_clause(-av[0], -bv[0], cv[1]);
		}
		else {
			if (av[0] == zvar) {
				cv.push_back(bv[0]);
				cv.push_back(av[0]);
			}
			else {
				assert(bv[0] == zvar);
				cv.push_back(av[0]);
				cv.push_back(bv[0]);
			}
		}
	}
	else {
		assert(av.size() > 1);
		if (NOPTCLS || ((av[0] != zvar || av[av.size() - 1] != zvar) &&
			        (bv[0] != zvar || bv[av.size() - 1] != zvar))) {
			vector<int> aodd, aeven, bodd, beven, dv, ev;
			mk_odd_vect(aodd, av); mk_even_vect(aeven, av);
			mk_odd_vect(bodd, bv); mk_even_vect(beven, bv);

			cardn_simple_merge_recur(top_id, clset, aodd,  bodd,  dv, zvar);
			assert(dv.size() == av.size() / 2 + 1);
			cardn_simple_merge_recur(top_id, clset, aeven, beven, ev, zvar);
			assert(ev.size() == av.size() / 2 + 1);

			assert(cv.size() == 0);
			cv.push_back(dv[0]);
			create_vvect(top_id, cv, av.size());

			for (size_t i = 0; i < av.size() / 2; ++i) {
				assert(i + 1 < dv.size());
				assert(i < ev.size());
				assert(2 * i + 1 < cv.size());

				clset.create_binary_clause (-dv[i + 1], cv[2 * i + 1]);
				clset.create_binary_clause (-ev[i],     cv[2 * i + 1]);
				clset.create_ternary_clause(-dv[i + 1], -ev[i], cv[2 * i + 2]);
			}
		}
		else {
			if (av[0] == zvar && av[av.size() - 1] == zvar) {
				copy_vvect(top_id, cv, bv);
				copy_vvect(top_id, cv, av);
			}
			else {
				assert(bv[0] == zvar && bv[av.size() - 1] == zvar);
				copy_vvect(top_id, cv, av);
				copy_vvect(top_id, cv, bv);
			}

			while (cv.size() > av.size() + 1)
				cv.pop_back();
		}
	}

	assert(cv.size() == av.size() + 1);
}

//
//=============================================================================
inline vector<int>& cardn_recur(
	int& top_id,
	ClauseSet& clset,
	vector<int>& av,
	vector<int>& cv,
	size_t zvar,
	size_t nkval
)
{
	assert(av.size() > 0);

	if (av.size() == nkval) {
		if (av.size() == 1)
			copy_vvect(top_id, cv, av);
		else
			sortn_half_sorter_recur(top_id, clset, av, cv, zvar);
	}
	else {
		vector<int> dv1, dv2, lav, uav;
		mk_ksize_vect(lav, av, nkval, 0);
		mk_ksize_vect(uav, av, av.size() - nkval, nkval);
		assert(lav.size() == nkval && uav.size() == av.size() - nkval);
		cardn_recur(top_id, clset, lav, dv1, zvar, nkval);
		assert(dv1.size() == nkval);
		cardn_recur(top_id, clset, uav, dv2, zvar, nkval);
		assert(dv2.size() == nkval);
		cardn_simple_merge_recur(top_id, clset, dv1, dv2, cv, zvar);
		assert(cv.size() == nkval + 1);
		cv.pop_back();  // remove last (unused) element
	}

	assert(cv.size() > 0);
	return cv;
}

//
//=============================================================================
inline void cardn_encode_atmostN(
	int& top_id,
	ClauseSet& clset,
	vector<int>& vars,
	int rhs
)
{
	int nvars = vars.size();

	if (rhs >= nvars)
		return;
	else if (rhs == nvars - 1) {
		common_encode_atmostNm1(clset, vars);
		return;
	}
	else if (rhs == 0) {
		common_encode_atmost0(clset, vars);
		return;
	}

	// get smallest power of 2 larger than number of vars
	int exponent = floor(log(rhs) / log(2)) + 1;    // compute exponent
	int nkval = round(exp(log(2) * exponent));
	assert(nkval > rhs);

	int zvar = 0;
	int mval = nvars / nkval;
	int nnvars = nvars;
	vector<int> vvect(vars);
	if (nvars > mval * nkval) {
		nnvars = (mval + 1) * nkval;
		zvar = ++top_id;
		vvect.resize(nnvars, zvar);
		clset.create_unit_clause(-zvar);
	}

	// 1. generate odd-even sorting network
	vector<int> outv;
	cardn_recur(top_id, clset, vvect, outv, zvar, nkval);

	// 2. force constraints on outputs
	assert(outv.size() > (unsigned)rhs);
	clset.create_unit_clause(-outv[rhs]);
}

#endif // SORTCARD_HH_
