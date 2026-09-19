#!/usr/bin/env python3
"""ssehc - the pure race variant (chess pieces irrelevant).

Board : 8x8 cells.
Squares: 64 - 32 White, 32 Black, initially a proper checkerboard
         (White on the light cells, a1 dark).
Move  : slide one of your own squares one cell in any of the 8 directions,
        swapping ownership with the square already there.
Goal  : all White squares on ranks 5-8
        (equivalently: all Black squares on ranks 1-4 -- proved below).

The chess pieces are present but inert: they ride the squares and change
nothing.
"""
from itertools import combinations
import random

N = 8
CELLS = 64


def rc(cell):
    return divmod(cell, 8)


def idx(r, c):
    return r * 8 + c


def is_light(cell):
    r, c = rc(cell)
    return (r + c) & 1 == 1          # a1 is dark


NEIGH = [[] for _ in range(CELLS)]
for _cell in range(CELLS):
    _r, _c = rc(_cell)
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr or _dc:
                _rr, _cc = _r + _dr, _c + _dc
                if 0 <= _rr < N and 0 <= _cc < N:
                    NEIGH[_cell].append(idx(_rr, _cc))


def initial():
    return ['W' if is_light(c) else 'B' for c in range(CELLS)]


def w_top(ow):
    """How many White squares sit on ranks 5-8."""
    return sum(1 for c in range(CELLS) if ow[c] == 'W' and rc(c)[0] >= 4)


def b_bot(ow):
    """How many Black squares sit on ranks 1-4."""
    return sum(1 for c in range(CELLS) if ow[c] == 'B' and rc(c)[0] < 4)


def legal(ow, me):
    """Adjacent pairs where at least one square belongs to `me`."""
    out = []
    for a in range(CELLS):
        for b in NEIGH[a]:
            if a < b and (ow[a] == me or ow[b] == me):
                out.append((a, b))
    return out


def delta(ow, mv):
    """Change in w_top if `mv` is played."""
    a, b = mv
    before = w_top(ow)
    ow[a], ow[b] = ow[b], ow[a]
    after = w_top(ow)
    ow[a], ow[b] = ow[b], ow[a]
    return after - before


def null_pairs(ow):
    """Adjacent pairs with the same owner: swapping them changes nothing at all."""
    return [(a, b) for a in range(CELLS) for b in NEIGH[a]
            if a < b and ow[a] == ow[b]]


# --------------------------------------------------------------------------
# 1. The two win conditions are literally the same board state.
# --------------------------------------------------------------------------

def prove_identity_exhaustive():
    """Exhaustive over every 4x4 board: w_top == b_bot always."""
    m = 4
    total = bad = same_goal = 0
    for ws in combinations(range(m * m), m * m // 2):
        wset = set(ws)
        wt = sum(1 for i in ws if i // m >= 2)                      # top half
        bb = sum(1 for i in range(m * m) if i not in wset and i // m < 2)
        total += 1
        if wt != bb:
            bad += 1
        if (wt == m * m // 2) == (bb == m * m // 2):
            same_goal += 1
    return total, bad, same_goal


def prove_identity_random(trials=200_000, seed=0):
    rng = random.Random(seed)
    bad = 0
    for _ in range(trials):
        ow = ['W'] * 32 + ['B'] * 32
        rng.shuffle(ow)
        if w_top(ow) != b_bot(ow):
            bad += 1
    return trials, bad


# --------------------------------------------------------------------------
# 2. The race itself.
# --------------------------------------------------------------------------

def pick(ow, me, want, rng):
    """Choose a move whose delta is as close to `want` as possible."""
    best, bestkey = None, None
    for mv in legal(ow, me):
        key = (abs(delta(ow, mv) - want), rng.random())
        if bestkey is None or key < bestkey:
            bestkey, best = key, mv
    return best


def play(pol_w, pol_b, cap=200, seed=0):
    """pol_* = desired delta (+1 advance, 0 stall).

    Returns (winner, plies, trajectory of w_top).
    """
    rng = random.Random(seed)
    ow = initial()
    traj = [w_top(ow)]
    for ply in range(1, cap + 1):
        me = 'W' if ply % 2 else 'B'
        mv = pick(ow, me, pol_w if me == 'W' else pol_b, rng)
        ow[mv[0]], ow[mv[1]] = ow[mv[1]], ow[mv[0]]
        traj.append(w_top(ow))
        if w_top(ow) == 32:
            return me, ply, traj
    return None, cap, traj


def main():
    ow = initial()

    print("=" * 72)
    print("1. THE TWO GOALS ARE THE SAME BOARD STATE")
    print("=" * 72)
    total, bad, same_goal = prove_identity_exhaustive()
    print(f"   exhaustive 4x4 boards checked      : {total}")
    print(f"   boards where w_top != b_bot        : {bad}")
    print(f"   boards where the two goals agree    : {same_goal} / {total}")
    trials, rbad = prove_identity_random()
    print(f"   random 8x8 boards where w_top != b_bot : {rbad} / {trials}")
    print("   -> 'all my squares across' and 'all your squares across'")
    print("      describe one and the same position. There is no conflict.")

    print()
    print("=" * 72)
    print("2. NULL MOVES EXIST ON MOVE ONE")
    print("=" * 72)
    npairs = null_pairs(ow)
    print(f"   adjacent same-owner pairs in the opening position: {len(npairs)}")
    print("   (diagonal neighbours share a colour, and squares may now move")
    print("    in any direction, so every one of these is a legal no-op)")
    a, b = npairs[0]
    print(f"   e.g. slide {chr(97 + rc(a)[1])}{rc(a)[0]+1} -> "
          f"{chr(97 + rc(b)[1])}{rc(b)[0]+1}: both squares are White's, the")
    print("   board is unchanged. Two such moves per turn forever = infinite draw.")

    print()
    print("=" * 72)
    print("3. THE CROSSING MOVES, AND THE PARITY RACE")
    print("=" * 72)
    for me in ('W', 'B'):
        inc = sum(1 for mv in legal(ow, me) if delta(ow, mv) > 0)
        dec = sum(1 for mv in legal(ow, me) if delta(ow, mv) < 0)
        flat = sum(1 for mv in legal(ow, me) if delta(ow, mv) == 0)
        print(f"   {me}: {len(legal(ow, me)):3d} legal moves "
              f"({inc} advance, {dec} retreat, {flat} neutral)")
    print(f"   White needs {32 - w_top(ow)} more crossings to win.")

    print()
    print("   Can anyone actually finish?  200-ply runs, three policies:")
    for pw, pb, label in ((+1, +1, "both push"),
                          (+1, 0, "W pushes, B stalls"),
                          (0, 0, "both stall")):
        w, plies, traj = play(pw, pb)
        peak = max(traj)
        for seed in range(5):
            peak = max(peak, max(play(pw, pb, seed=seed)[2]))
        print(f"     {label:22s} -> winner {w}, {plies} plies, "
              f"peak count {peak}/32")
    print("   The counter climbs for a while and then plateaus short of 32.")
    print("   So the goal is reachable, but nobody is ever made to pursue it.")

    print()
    print("=" * 72)
    print("VERDICT")
    print("=" * 72)
    print("   The race has no conflict in it:")
    print("     a) the two goals are one and the same board state, so there is")
    print("        nothing to fight over -- progress for one is progress for")
    print("        both, and 200,000 random boards never disagreed;")
    print("     b) 98 legal no-op moves exist in the opening position and")
    print("        no-ops never run out, so neither player can ever be forced")
    print("        to advance.  Optimal play is mutual refusal: an endless draw.")
    print("   The pieces were the only thing that made the board matter.")


if __name__ == "__main__":
    main()
