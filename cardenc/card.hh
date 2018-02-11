/*
 * card.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef CARD_HH_
#define CARD_HH_

#include "bitwise.hh"
#include "clset.hh"
#include "ladder.hh"
#include "mto.hh"
#include "pairwise.hh"
#include "seqcounter.hh"
#include "sortcard.hh"

// supported types of cardinality encoding
//=============================================================================
enum EncType {
	enc_exp   = 0,  // pairwise, only for bound == 1
	enc_seqc  = 1,
	enc_sortn = 2,
	enc_cardn = 3,
	enc_bitw  = 4,
	enc_ladd  = 5,
	enc_tot   = 6,
	enc_mtot  = 7,
	enc_kmtot = 8
};

//
//=============================================================================
static inline void _encode_atmost(
	ClauseSet& dest,
	vector<int>& lhs,
	int rhs,
	int& top,
	int enc
)
{
	if (enc == enc_cardn)
		cardn_encode_atmostN(top, dest, lhs, rhs);
	else if (enc == enc_sortn)
		sortn_encode_atmostN(top, dest, lhs, rhs);
	else if (enc == enc_kmtot)
		kmto_encode_atmostN(top, dest, lhs, rhs);
	else if (enc == enc_mtot)
		mto_encode_atmostN(top, dest, lhs, rhs);
	else if (enc == enc_tot)
		to_encode_atmostN(top, dest, lhs, rhs);
	else if (enc == enc_seqc)
		seqcounter_encode_atmostN(top, dest, lhs, rhs);
	else if (rhs == 1) {
		if (enc == enc_bitw)
			bitwise_encode_atmost1(top, dest, lhs);
		else if (enc == enc_exp)
			pairwise_encode_atmost1(dest, lhs);
		else if (enc == enc_ladd)
			ladder_encode_atmost1(top, dest, lhs);
	}
}

//
//=============================================================================
static inline void _encode_atleast(
	ClauseSet& dest,
	vector<int>& lhs,
	int rhs,
	int& top,
	int enc
)
{
	if (rhs == 1)
		common_encode_atleast1(dest, lhs);
	else {
		for (size_t i = 0; i < lhs.size(); ++i)
			lhs[i] = -lhs[i];

		rhs = lhs.size() - rhs;
		_encode_atmost(dest, lhs, rhs, top, enc);
	}
}

#endif // CARD_HH_
