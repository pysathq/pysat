/*
 * itot.hh
 *
 *  Created on: May 29, 2015
 *      Author: Antonio Morgado, Alexey S. Ignatiev
 *      E-mail: {ajmorgado,aignatiev}@ciencias.ulisboa.pt
 */

#ifndef ITOT_HH_
#define ITOT_HH_

#include <algorithm>
#include <cmath>
#include <vector>
#include <deque>
#include "clset.hh"

using namespace std;

typedef struct TotTree {
	vector<int> vars;
	unsigned nof_input;
	TotTree *left;
	TotTree *right;
} TotTree;

//
//=============================================================================
void itot_new_ua(
	int& top,
	ClauseSet& dest,
	vector<int>& ov,
	unsigned rhs,
	vector<int>& av,
	vector<int>& bv
)
{
	// i = 0
	unsigned kmin = std::min(rhs, (unsigned)bv.size());
	for (unsigned j = 0; j < kmin; ++j)
		dest.create_binary_clause(-bv[j], ov[j]);

	// j = 0
	kmin = std::min(rhs, (unsigned)av.size());
	for (unsigned i = 0; i < kmin; ++i)
		dest.create_binary_clause(-av[i], ov[i]);

	// i, j > 0
	for (unsigned i = 1; i <= kmin; ++i) {
		unsigned minj = std::min(rhs - i, (unsigned)bv.size());
		for (unsigned j = 1; j <= minj; ++j)
			dest.create_ternary_clause(-av[i - 1], -bv[j - 1], ov[i + j - 1]);
	}
}

//
//=============================================================================
TotTree *itot_new(ClauseSet& dest, vector<int>& lhs, unsigned rhs, int& top)
{
	unsigned n = lhs.size();
	deque<TotTree *> nqueue;

	for (unsigned i = 0; i < n; ++i) {
		TotTree *tree = new TotTree();

		tree->vars.resize(1);
		tree->vars[0]   = lhs[i];
		tree->nof_input = 1;
		tree->left      = 0;
		tree->right     = 0;

		nqueue.push_back(tree);
	}

	while (nqueue.size() > 1) {
		TotTree *l = nqueue.front();
		nqueue.pop_front();
		TotTree *r = nqueue.front();
		nqueue.pop_front();

		TotTree *node = new TotTree();
		node->nof_input = l->nof_input + r->nof_input;
		node->left      = l;
		node->right     = r;

		unsigned kmin = std::min(rhs + 1, node->nof_input);

		node->vars.resize(kmin);
		for (unsigned i = 0; i < kmin; ++i)
			node->vars[i] = ++top;

		itot_new_ua(top, dest, node->vars, kmin, l->vars, r->vars);
		nqueue.push_back(node);
	}

	return nqueue.front();
}

//
//=============================================================================
void itot_increase_ua(
	int& top,
	ClauseSet& dest,
	vector<int>& ov,
	vector<int>& av,
	vector<int>& bv,
	unsigned rhs
)
{
	unsigned last = ov.size();

	for (unsigned i = last; i < rhs; ++i)
		ov.push_back(++top);

	// add the constraints
	// i = 0
	unsigned maxj = std::min(rhs, (unsigned)bv.size());
	for (unsigned j = last; j < maxj; ++j)
		dest.create_binary_clause(-bv[j], ov[j]);

	// j = 0
	unsigned maxi = std::min(rhs, (unsigned)av.size());
	for (unsigned i = last; i < maxi; ++i)
		dest.create_binary_clause(-av[i], ov[i]);

	// i, j > 0
	for (unsigned i = 1; i <= maxi; ++i) {
		unsigned maxj = std::min(rhs - i, (unsigned)bv.size());
		unsigned minj = std::max((int)last - (int)i + 1, 1);
		for (unsigned j = minj; j <= maxj; ++j)
			dest.create_ternary_clause(-av[i - 1], -bv[j - 1], ov[i + j - 1]);
	}
}

//
//=============================================================================
void itot_increase(TotTree *tree, ClauseSet& dest, unsigned rhs, int& top)
{
	unsigned kmin = std::min(rhs + 1, tree->nof_input);

	if (kmin <= tree->vars.size())
		return;

	itot_increase   (tree->left,  dest, rhs, top);
	itot_increase   (tree->right, dest, rhs, top);
	itot_increase_ua(top, dest, tree->vars, tree->left->vars, tree->right->vars, kmin);
}

//
//=============================================================================
TotTree *itot_merge(
	TotTree *ta,
	TotTree *tb,
	ClauseSet& dest,
	unsigned rhs,
	int& top
)
{
	itot_increase(ta, dest, rhs, top);
	itot_increase(tb, dest, rhs, top);

	unsigned n    = ta->nof_input + tb->nof_input;
	unsigned kmin = std::min(rhs + 1, n);

	TotTree *tree = new TotTree();
	tree->nof_input = n;
	tree->left      = ta;
	tree->right     = tb;

	tree->vars.resize(kmin);
	for (unsigned i = 0; i < kmin; ++i)
		tree->vars[i] = ++top;

	itot_new_ua(top, dest, tree->vars, kmin, ta->vars, tb->vars);
	return tree;
}

//
//=============================================================================
TotTree *itot_extend(
	vector<int>& newin,
	TotTree *ta,
	ClauseSet& dest,
	unsigned rhs,
	int& top
)
{
	TotTree *tb = itot_new(dest, newin, rhs, top);
	return itot_merge(ta, tb, dest, rhs, top);
}

// recursive destruction of the tree
//=============================================================================
static void itot_destroy(TotTree *tree)
{
	if (tree->left )
		itot_destroy(tree->left );
	if (tree->right)
		itot_destroy(tree->right);

	tree->vars.clear();
	delete tree;
}

#endif // ITOT_HH_
