/*
 * iseq.hh
 *
 *  Created on: Dec 15, 2025
 *      Author: Jesse Looney
 *      E-mail: jesselooney+dev@pm.me
 */

#ifndef ISEQ_HH_
#define ISEQ_HH_

#include <algorithm>
#include <cmath>
#include <vector>
#include <deque>
#include "clset.hh"
#include "ptypes.hh"
#include "utils.hh"

using namespace std;

struct SeqState {
    vector<int> lhs;
    // We maintain the invariant that `rhs.size() < lhs.size()`.
    vector<int> rhs;
    // A map from pairs of integers to SAT literals (encoded as integers).
    // We maintain the invariant that, for `1 <= i <= rhs.size()` and
    // `i <= j <= lhs.size()`, `s_vars` contains the key `(i, j)`, and the
    // corresponding element is a literal whose negation requires that the sum
    // of the first `j` literals of `lhs` is at most `i - 1`.
    Pair2IntMap s_vars;
};

// Create an at-most-0 constraint in an instantiated sequential counters state.
// This must always be the first constraint added.
//=============================================================================
void _iseq_add_atmost0(SeqState *state, ClauseSet& dest, int& top)
{
    assert(state->rhs.size() == 0);
    assert(state->lhs.size() > 0);

    int n = state->lhs.size();

    // s_1^1 <-- x_0. We could just reuse the literal for x_0, but it is better
    // to have our own copy: iseq_get() hands out s-variables as standalone
    // constraint literals, and callers should be able to treat s_1^1 as
    // distinct from the input literal x_0.
    int s11 = mk_yvar(top, state->s_vars, make_pair(1, 1));
    int x0 = state->lhs[0];
    dest.create_binary_clause(-x0, s11);

    for (int j = 1; j < n; j++) {
        int s1j1 = mk_yvar(top, state->s_vars, make_pair(1, j + 1));
        int s1j  = mk_yvar(top, state->s_vars, make_pair(1, j));
        int xj   = state->lhs[j];
        // s_1^(j+1) <-- s_1^j v x_j
        dest.create_binary_clause(-s1j, s1j1);
        dest.create_binary_clause(-xj, s1j1);
    }

    int s1n = mk_yvar(top, state->s_vars, make_pair(1, n));
    state->rhs.push_back(s1n);
}

// Create an at-most-k constraint in an instantiated sequential counters state.
// This must always be the (k+1)-th constraint added.
//=============================================================================
void _iseq_add_atmostk(SeqState *state, ClauseSet& dest, int& top, unsigned k)
{
    assert(state->rhs.size() == k);
    assert(state->lhs.size() > k);

    int n = state->lhs.size();

    int sk1k1 = mk_yvar(top, state->s_vars, make_pair(k + 1, k + 1));
    int skk   = mk_yvar(top, state->s_vars, make_pair(k, k));
    int xk    = state->lhs[k];
    // s_(k+1)^(k+1) <-- s_k^k ^ x_k
    dest.create_ternary_clause(-skk, -xk, sk1k1);

    for (int j = k + 1; j < n; j++) {
        int sk1j1 = mk_yvar(top, state->s_vars, make_pair(k + 1, j + 1));
        int sk1j  = mk_yvar(top, state->s_vars, make_pair(k + 1, j));
        int skj   = mk_yvar(top, state->s_vars, make_pair(k, j));
        int xj    = state->lhs[j];
        // s_(k+1)^(j+1) <-- s_(k+1)^j v (s_k^j ^ x_j)
        dest.create_binary_clause(-sk1j, sk1j1);
        dest.create_ternary_clause(-skj, -xj, sk1j1);
    }

    int sk1n = mk_yvar(top, state->s_vars, make_pair(k + 1, n));
    state->rhs.push_back(sk1n);
}

//
//=============================================================================
SeqState *iseq_new(ClauseSet& dest, vector<int>& lhs, unsigned rhs, int& top)
{
    SeqState *state = new SeqState();
    state->lhs = lhs;

    unsigned kmin = std::min(rhs + 1, (unsigned)state->lhs.size());
    state->rhs.reserve(kmin);

    for (unsigned i = 0; i < kmin; i++) {
        if (i == 0) {
            _iseq_add_atmost0(state, dest, top);
        } else {
            _iseq_add_atmostk(state, dest, top, i);
        }
    }

    return state;
}

//
//=============================================================================
void iseq_increase(SeqState *state, ClauseSet& dest, unsigned rhs, int& top)
{
    unsigned kmin = std::min(rhs + 1, (unsigned)state->lhs.size());
    state->rhs.reserve(kmin);

    for (unsigned i = (unsigned)state->rhs.size(); i < kmin; i++) {
        if (i == 0) {
            _iseq_add_atmost0(state, dest, top);
        } else {
            _iseq_add_atmostk(state, dest, top, i);
        }
    }
}

//
//=============================================================================
int iseq_get(SeqState *state, int prefix_len, unsigned bound) {
    assert(bound < state->rhs.size());

    assert((int)bound < prefix_len);
    assert(prefix_len <= (int)state->lhs.size());

    // The above assertions ensure that this key exists in the map.
    return state->s_vars.at(make_pair(bound + 1, prefix_len));
}

//
//=============================================================================
static void iseq_destroy(SeqState *state)
{
	delete state;
}

#endif // ISEQ_HH_
