#!/usr/bin/env python3
"""ssehc - the erosion variant.

The rule that makes this one bite: a SQUARE moves exactly as the PIECE
standing on it moves.  And a capture takes the SQUARE, not the piece.

  * 64 cells; all 64 hold a square at the start.
  * every square carries a standard chess piece, fixed at setup, and the
    piece never leaves its square.
  * White owns the 32 squares on light cells, Black the 32 on dark cells.
  * a move: take one of your squares and move it the way its piece moves.
  * landing on an enemy square DESTROYS that square (and its piece);
    landing in a hole just relocates.
  * you win when the opponent has no squares left.

Three things this inverts:

  1. There is no such thing as a defended square.  A capture is always
     profitable, because nothing can save the square that is taken.  Chess
     is a game of protection; this is a game with no protection at all.
  2. The pieces never die individually.  They are the movement rules of
     the terrain, fixed at setup, and a rule only disappears when the
     square carrying it is destroyed.
  3. Holes do not block sliders, so the board OPENS UP as it dies --
     the exact reverse of chess, where pawns lock the position.
"""
import random

WHITE, BLACK = 0, 1
OPP = (BLACK, WHITE)

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
CHAR = {PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', ROOK: 'R', QUEEN: 'Q', KING: 'K'}

DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
ORTHO = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
KND = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
BACK = (ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK)


def mk(t, col):
    return t | (col << 3)


def ptype(p):
    return p & 7


def pcol(p):
    return p >> 3


def rc(c):
    return divmod(c, 8)


def idx(r, c):
    return r * 8 + c


def on(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def is_light(c):
    r, cc = rc(c)
    return (r + cc) & 1 == 1          # a1 is dark


def name(c):
    r, cc = rc(c)
    return "abcdefgh"[cc] + str(r + 1)


def initial():
    owner = [WHITE if is_light(c) else BLACK for c in range(64)]
    piece = [0] * 64
    for c in range(8):
        piece[idx(0, c)] = mk(BACK[c], WHITE)
        piece[idx(1, c)] = mk(PAWN, WHITE)
        piece[idx(6, c)] = mk(PAWN, BLACK)
        piece[idx(7, c)] = mk(BACK[c], BLACK)
    return owner, piece


def gen(owner, piece, me):
    out = []
    for c in range(64):
        if owner[c] != me:
            continue
        t = ptype(piece[c])
        r, cc = rc(c)
        if t == PAWN:
            dr = 1 if me == WHITE else -1
            rr, ccc = r + dr, cc
            if on(rr, ccc):
                d = idx(rr, ccc)
                if owner[d] is None:              # straight into a hole
                    out.append((c, d))
            for dc in (-1, 1):                     # captures stay diagonal
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    d = idx(rr, ccc)
                    if owner[d] == OPP[me]:
                        out.append((c, d))
        elif t == KNIGHT:
            for dr, dc in KND:
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    d = idx(rr, ccc)
                    if owner[d] != me:
                        out.append((c, d))
        elif t == KING:
            for dr, dc in DIRS:
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    d = idx(rr, ccc)
                    if owner[d] != me:
                        out.append((c, d))
        else:
            dirs = ORTHO if t == ROOK else DIAG if t == BISHOP else DIRS
            for dr, dc in dirs:
                rr, ccc = r + dr, cc + dc
                while on(rr, ccc):
                    d = idx(rr, ccc)
                    o = owner[d]
                    if o == me:
                        break
                    out.append((c, d))
                    if o is not None:              # took a square; stop
                        break
                    rr += dr
                    ccc += dc
    return out


def apply(owner, piece, mv):
    a, b = mv
    captured = owner[b] is not None
    owner[b], piece[b] = owner[a], piece[a]
    owner[a], piece[a] = None, 0
    if ptype(piece[b]) == PAWN:                    # a rule can change
        r, _ = rc(b)
        if (owner[b] == WHITE and r == 7) or (owner[b] == BLACK and r == 0):
            piece[b] = mk(QUEEN, owner[b])
    return captured


def counts(owner):
    return (sum(1 for o in owner if o == WHITE),
            sum(1 for o in owner if o == BLACK))


def random_policy(owner, piece, me, moves, rng):
    return rng.choice(moves)


def greedy_policy(owner, piece, me, moves, rng):
    caps = [m for m in moves if owner[m[1]] == OPP[me]]
    return rng.choice(caps) if caps else rng.choice(moves)


def play(policy, cap=600, seed=0):
    rng = random.Random(seed)
    owner, piece = initial()
    hist = [counts(owner)]
    me = WHITE
    for ply in range(1, cap + 1):
        moves = gen(owner, piece, me)
        if not moves:
            return OPP[me], ply, hist, "no moves left"
        apply(owner, piece, policy(owner, piece, me, moves, rng))
        w, b = counts(owner)
        hist.append((w, b))
        if b == 0:
            return WHITE, ply, hist, "board taken"
        if w == 0:
            return BLACK, ply, hist, "board taken"
        me = OPP[me]
    return None, cap, hist, "unfinished"


def main():
    owner, piece = initial()
    for me, label in ((WHITE, "White"), (BLACK, "Black")):
        moves = gen(owner, piece, me)
        caps = [m for m in moves if owner[m[1]] == OPP[me]]
        print(f"   {label}: {len(moves):3d} opening moves, {len(caps)} of them "
              f"immediate square-captures")
    print("   (pawns are frozen: there are no holes yet, and every forward")
    print("    diagonal is a friendly square.  So the game opens with knights")
    print("    jumping straight into the enemy's squares.)")

    print()
    print("=" * 72)
    print("SIMULATION")
    print("=" * 72)
    for label, pol in (("random", random_policy), ("greedy", greedy_policy)):
        wins = {WHITE: 0, BLACK: 0, None: 0}
        plies = []
        reasons = {}
        peak = 0
        for g in range(200):
            w, p, hist, why = play(pol, cap=600, seed=g)
            wins[w] += 1
            plies.append(p)
            reasons[why] = reasons.get(why, 0) + 1
            peak = max(peak, min(hist[0][0], hist[0][1]) - min(hist[-1][0],
                                                               hist[-1][1]))
        plies.sort()
        print(f"   {label:7s} 200 games | White {wins[WHITE]:3d}  "
              f"Black {wins[BLACK]:3d}  unfinished {wins[None]:3d} | "
              f"median {plies[len(plies) // 2]} plies, max {plies[-1]}")
        print(f"            endings: {reasons}")

    print()
    print("=" * 72)
    print("ONE GAME, SQUARE COUNTS")
    print("=" * 72)
    w, p, hist, why = play(greedy_policy, cap=600, seed=7)
    print(f"   winner: {'White' if w == WHITE else 'Black' if w == BLACK else 'nobody'}"
          f"  ({why}) after {p} plies")
    step = max(1, len(hist) // 20)
    print("   ply : W/B")
    for i in range(0, len(hist), step):
        print(f"   {i:4d} : {hist[i][0]:2d}/{hist[i][1]:2d}")
    print(f"   {len(hist)-1:4d} : {hist[-1][0]:2d}/{hist[-1][1]:2d}")


if __name__ == "__main__":
    main()
