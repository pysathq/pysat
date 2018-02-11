/*
 * ptypes.hh (based on the 'card' library from BOLT)
 *
 *  Created on: Sep 25, 2017
 *      Author: aign
 */

#ifndef PTYPES_HH_
#define PTYPES_HH_

#include <unordered_map>

using namespace std;

//
//=============================================================================
typedef pair<int, int> IntPair;

//
//=============================================================================
class IntPairHash {
public:
	int operator() (IntPair pval) const
	{
		return pval.first * pval.second;
	}
};

//
//=============================================================================
class IntPairEqual {
public:
	bool operator() (IntPair p1, IntPair p2) const
	{
		return p1.first == p2.first && p1.second == p2.second;
	}
};

//
//=============================================================================
typedef unordered_map<IntPair, int, IntPairHash, IntPairEqual> Pair2IntMap;

#endif // PTYPES_HH_
