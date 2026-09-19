#!/usr/bin/env python3
"""ssehc - the paint variant.  Final ruleset.

  1. White moves white squares; Black moves black squares.
  2. A square's movement is the movement of the piece standing on it.
     A square with no piece on it cannot move.
  3. Moving swaps the pieces: one square swaps two pieces, and moving
     further swaps the pieces in between, one square at a time.  The
     swap-chain is what lets a slider travel on a board where every cell
     is already occupied.
  4. Moving a square converts the destination square to the colour of the
     square being moved.  A long move is a sequence of one-square steps,
     so every square along the path is a destination, and the whole path
     is painted.
  5. The goal is to make the board entirely one colour.

Ownership is purely by the SQUARE's colour.  The pieces' own colours mean
nothing: a player may move any piece standing on one of their squares,
friend's or enemy's.  Each side therefore commands eight of its own
templates and eight of the opponent's at the start.

A player with no legal move passes.  Passing is usually temporary -- the
opponent's swaps hand templates back and forth -- but a player who stays
immobile gets painted out.
"""
import random

WHITE, BLACK = 0, 1
OPP = (BLACK, WHITE)

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
GLYPH = {0: '.', PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', ROOK: 'R',
         QUEEN: 'Q', KING: 'K'}

DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
ORTHO = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
KND = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
BACK = (ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK)


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
        piece[idx(0, c)] = BACK[c]
        piece[idx(1, c)] = PAWN
        piece[idx(6, c)] = PAWN
        piece[idx(7, c)] = BACK[c]
    return owner, piece


def gen(owner, piece, me):
    """Every legal move as (origin cell, path tuple).  The last cell of the
    path is the destination; every cell of the path gets painted."""
    out = []
    for a in range(64):
        if owner[a] != me or piece[a] == 0:
            continue
        t = piece[a]
        r, c = rc(a)
        if t == KNIGHT:
            for dr, dc in KND:
                rr, cc = r + dr, c + dc
                if on(rr, cc):
                    out.append((a, (idx(rr, cc),)))
        elif t == KING:
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if on(rr, cc):
                    out.append((a, (idx(rr, cc),)))
        elif t == PAWN:
            dr = 1 if me == WHITE else -1
            for dc in (0, -1, 1):
                rr, cc = r + dr, c + dc
                if on(rr, cc):
                    out.append((a, (idx(rr, cc),)))
        else:
            dirs = ORTHO if t == ROOK else DIAG if t == BISHOP else DIRS
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                path = []
                while on(rr, cc):
                    path.append(idx(rr, cc))
                    out.append((a, tuple(path)))
                    rr += dr
                    cc += dc
    return out


def apply(owner, piece, a, path, me):
    """Swap the pieces one square at a time and paint every cell entered."""
    cur = a
    painted = 0
    for cell in path:
        piece[cur], piece[cell] = piece[cell], piece[cur]
        if owner[cell] != me:
            owner[cell] = me
            painted += 1
        cur = cell
    return painted


def gain(owner, me, path):
    """How many cells a path would actually convert -- no state copy needed."""
    n = 0
    for cell in path:
        if owner[cell] != me:
            n += 1
    return n


def counts(owner):
    w = sum(1 for o in owner if o == WHITE)
    return w, 64 - w


def painted_out(owner):
    if all(o == WHITE for o in owner):
        return WHITE
    if all(o == BLACK for o in owner):
        return BLACK
    return None


def greedy(owner, piece, me, moves, rng):
    best, bestkey = None, None
    for a, path in moves:
        key = (gain(owner, me, path), rng.random())
        if bestkey is None or key > bestkey:
            bestkey, best = key, (a, path)
    return best


def lookahead(owner, piece, me, moves, rng):
    """Paint a lot, but do not hand the opponent a bigger sweep than you took.
    The opponent's reply is estimated from their long lines only, which keeps
    this cheap enough to run over many games."""
    opp = OPP[me]
    threats = [(a, p) for a, p in gen(owner, piece, opp) if len(p) >= 3]
    best, bestkey = None, None
    for a, path in moves:
        n = gain(owner, me, path)
        o2 = owner[:]
        p2 = piece[:]
        apply(o2, p2, a, path, me)
        reply = 0
        for a3, p3 in threats:
            g = gain(o2, opp, p3)
            if g > reply:
                reply = g
        key = (n - 0.9 * reply, rng.random())
        if bestkey is None or key > bestkey:
            bestkey, best = key, (a, path)
    return best


def play(policy, cap=400, seed=0):
    rng = random.Random(seed)
    owner, piece = initial()
    hist = [counts(owner)]
    log = []
    me = WHITE
    passes = 0
    stuck_events = 0
    biggest = 0
    for ply in range(1, cap + 1):
        moves = gen(owner, piece, me)
        if not moves:
            stuck_events += 1
            passes += 1
            if passes >= 2:
                return None, ply, "both stuck", hist, log, stuck_events, biggest
            me = OPP[me]
            hist.append(counts(owner))
            continue
        passes = 0
        a, path = policy(owner, piece, me, moves, rng)
        before = piece[a]
        n = apply(owner, piece, a, path, me)
        if n > biggest:
            biggest = n
        log.append((ply, me, GLYPH[before], name(a), name(path[-1]), n))
        hist.append(counts(owner))
        w = painted_out(owner)
        if w is not None:
            return w, ply, "board painted", hist, log, stuck_events, biggest
        me = OPP[me]
    return None, cap, "unfinished", hist, log, stuck_events, biggest


def board(owner, piece):
    rows = []
    for r in range(7, -1, -1):
        cells = []
        for c in range(8):
            k = idx(r, c)
            ch = GLYPH[piece[k]]
            cells.append(ch if owner[k] == WHITE else ch.lower())
        rows.append(f"{r + 1}  " + " ".join(cells))
    rows.append("   a b c d e f g h")
    return "\n".join(rows)


def main():
    owner, piece = initial()
    print("=" * 72)
    print("OPENING CAPACITY")
    print("=" * 72)
    for me, label in ((WHITE, "White"), (BLACK, "Black")):
        moves = gen(owner, piece, me)
        movable = sum(1 for c in range(64) if owner[c] == me and piece[c])
        by_piece = {}
        for a, path in moves:
            by_piece.setdefault(GLYPH[piece[a]], []).append(len(path))
        print(f"   {label}: {len(moves)} moves from {movable} of its 32 "
              f"squares")
        for g in "QRBNP":
            if g in by_piece:
                lens = by_piece[g]
                print(f"      {g}: {len(lens):3d} moves, longest paints "
                      f"{max(lens)} cells")
    print("   Only 32 of the 64 squares carry a template.  The other 32 are")
    print("   immobile -- but paintable.  Half the board cannot defend itself.")

    print()
    print("=" * 72)
    print("SIMULATION")
    print("=" * 72)
    for label, pol, games in (("greedy", greedy, 60), ("lookahead", lookahead, 12)):
        wins = {WHITE: 0, BLACK: 0, None: 0}
        plies, peaks, reasons, stuck, sweeps = [], [], {}, 0, 0
        for g in range(games):
            w, p, why, hist, _, se, bg = play(pol, cap=400, seed=g)
            wins[w] += 1
            plies.append(p)
            peaks.append(max(max(h) for h in hist))
            reasons[why] = reasons.get(why, 0) + 1
            stuck += se
            sweeps = max(sweeps, bg)
        plies.sort()
        print(f"   {label:9s} {games:3d} games | White {wins[WHITE]:2d} "
              f"Black {wins[BLACK]:2d} drawn {wins[None]:2d} | median "
              f"{plies[len(plies)//2]:3d} plies | best count {max(peaks)}/64 "
              f"| biggest sweep {sweeps}")
        print(f"             endings {reasons} | forced passes {stuck}")

    print()
    print("=" * 72)
    print("ONE GAME (lookahead), COLOUR COUNTS")
    print("=" * 72)
    w, p, why, hist, log, se, bg = play(lookahead, cap=400, seed=4)
    print(f"   winner: {'White' if w == WHITE else 'Black' if w == BLACK else 'drawn'}"
          f"  ({why}) after {p} plies")
    step = max(1, len(hist) // 16)
    for i in range(0, len(hist), step):
        print(f"   {i:4d} : {hist[i][0]:2d}/{hist[i][1]:2d}")
    print("   White's range:", min(h[0] for h in hist), "..",
          max(h[0] for h in hist), "cells")

    print()
    print("   first 10 moves:")
    for ply, me, g, a, b, n in log[:10]:
        print(f"   {ply:2d}. {'W' if me == WHITE else 'B'} {g} square {a} -> "
              f"{b}  (paints {n})")

    print()
    print("=" * 72)
    print("FINAL POSITION")
    print("=" * 72)
    print(board(owner, piece))
    print("   (uppercase = White cell, lowercase = Black cell; the letter is")
    print("    the movement template currently standing there)")


if __name__ == "__main__":
    main()
