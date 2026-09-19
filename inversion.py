#!/usr/bin/env python3
"""ssehc - the inversion variant.

Rules being tested:

  * 64 cells, every cell always holds a square.  64 squares, each with a
    fixed owner (White / Black) and a fixed chess piece.
  * White commands the white squares, Black the black ones.
  * a move: take one of your squares and move it the way its piece moves.
  * the square you land on INVERTS to your colour.  The two squares swap
    cells; the one that travels back flips.

So every move gains you exactly one square, and a square move inverts the
colour of the square it is moving to -- which means each player is exactly
one move away from flipping the square their own king stands on.

Two hard consequences fall out; both are reported below.

  A. The board is always full, so SQUARES BLOCK EACH OTHER.  A rook,
     bishop or queen can therefore only ever reach the first square in
     each direction -- and attacks are blocked the same way.  Every
     long-range piece collapses to a one-step piece.  The knight is the
     only leaper left, so the knight is the strongest piece on the board.

  B. One inversion per move means the square count just oscillates
     32 -> 33 -> 32.  "Own the board" is unreachable.  The rule fixes the
     king problem; it does not fix the goal problem.
"""
import random

WHITE, BLACK = 0, 1
OPP = (BLACK, WHITE)

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
CHAR = {PAWN: 'P', KNIGHT: 'N', BISHOP: 'B', ROOK: 'R', QUEEN: 'Q', KING: 'K'}
VALUE = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9, KING: 100}

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
    return (r + cc) & 1 == 1


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


def gen(owner, piece, me, mode="block"):
    """mode: 'block' -> sliders stop at the first square (physical board)
             'jump'  -> sliders ignore blockers, invert the destination only
             'path'  -> sliders ignore blockers and invert everything crossed
    """
    out = []
    for c in range(64):
        if owner[c] != me:
            continue
        t = ptype(piece[c])
        r, cc = rc(c)
        if t == PAWN:
            dr = 1 if me == WHITE else -1
            for dc in (-1, 1):                    # diagonal only: board is full
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    d = idx(rr, ccc)
                    if owner[d] != me:
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
                    if owner[d] == me:
                        if mode == "block":
                            break
                        rr += dr
                        ccc += dc
                        continue
                    out.append((c, d))
                    if mode == "block":
                        break
                    rr += dr
                    ccc += dc
    return out


def apply(owner, piece, mv):
    a, b = mv
    oa, ob = owner[a], owner[b]
    owner[a], owner[b] = OPP[ob], oa       # the travelling square flips
    piece[a], piece[b] = piece[b], piece[a]


def attacks(owner, piece, player):
    occ = 0
    for c in range(64):
        if owner[c] is not None:
            occ |= 1 << c
    res = 0
    for c in range(64):
        if owner[c] is None:
            continue
        p = piece[c]
        if pcol(p) != player:
            continue
        t = ptype(p)
        r, cc = rc(c)
        if t == PAWN:
            dr = 1 if player == WHITE else -1
            for dc in (-1, 1):
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    res |= 1 << idx(rr, ccc)
        elif t == KNIGHT:
            for dr, dc in KND:
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    res |= 1 << idx(rr, ccc)
        elif t == KING:
            for dr, dc in DIRS:
                rr, ccc = r + dr, cc + dc
                if on(rr, ccc):
                    res |= 1 << idx(rr, ccc)
        else:
            dirs = ORTHO if t == ROOK else DIAG if t == BISHOP else DIRS
            for dr, dc in dirs:
                rr, ccc = r + dr, cc + dc
                while on(rr, ccc):
                    bit = 1 << idx(rr, ccc)
                    res |= bit
                    if occ & bit:
                        break
                    rr += dr
                    ccc += dc
    return res


def captures(owner, piece, player):
    at = attacks(owner, piece, player)
    return [c for c in range(64)
            if (at >> c) & 1 and pcol(piece[c]) != player]


def king_cell(owner, piece, colour):
    for c in range(64):
        if ptype(piece[c]) == KING and pcol(piece[c]) == colour:
            return c
    return -1


def bot(owner, piece, me, moves, rng):
    """1. take the king  2. seize my own king's square  3. drag his king
       4. otherwise convert whatever is closest to my home rank."""
    my_k = king_cell(owner, piece, me)
    his_k = king_cell(owner, piece, OPP[me])
    home = 0 if me == WHITE else 7
    best, bestkey = None, None
    for mv in moves:
        a, b = mv
        o2, p2 = owner[:], piece[:]
        apply(o2, p2, mv)
        win = his_k >= 0 and ptype(p2[his_k]) == KING and pcol(p2[his_k]) != me
        caps = captures(o2, p2, me)
        takes_king = any(ptype(p2[c]) == KING for c in caps)
        if takes_king:
            return mv
        key = 0
        if owner[my_k] != me and b == my_k:
            key += 1000                       # reclaimed my own king
        if owner[his_k] != me and b == his_k:
            key += 500                        # seized custody of his king
        if owner[his_k] == me:                # I have his king; drag it home
            r, _ = rc(his_k)
            key += 200 + (7 - abs(r - home))
        if caps:
            key += 50 + max(VALUE[ptype(p2[c])] for c in caps)
        r, _ = rc(b)
        key += (7 - abs(r - home))
        key += rng.random()
        if bestkey is None or key > bestkey:
            bestkey, best = key, mv
    return best


def play(mode="block", cap=300, seed=0, trace=False):
    rng = random.Random(seed)
    owner, piece = initial()
    me = WHITE
    log = []
    for ply in range(1, cap + 1):
        moves = gen(owner, piece, me, mode)
        if not moves:
            return OPP[me], ply, "no moves", log
        mv = bot(owner, piece, me, moves, rng)
        a, b = mv
        apply(owner, piece, mv)
        his_k = king_cell(owner, piece, OPP[me])
        caps = captures(owner, piece, me)
        killed = [c for c in caps if ptype(piece[c]) == KING]
        log.append((ply, me, name(a), name(b)))
        if killed:
            return me, ply, "king taken", log
        me = OPP[me]
    return None, cap, "unfinished", log


def main():
    owner, piece = initial()
    print("=" * 72)
    print("IS EACH PLAYER ONE MOVE FROM THEIR OWN KING'S SQUARE?")
    print("=" * 72)
    for me, label in ((WHITE, "White"), (BLACK, "Black")):
        k = king_cell(owner, piece, me)
        who = "own" if owner[k] == me else ("ENEMY" if owner[k] == OPP[me] else "?")
        seizes = [(a, b) for a, b in gen(owner, piece, me) if b == k]
        print(f"   {label}'s king on {name(k)}: square is {who}'s")
        print(f"      moves that invert it in one go: "
              f"{', '.join(name(a) + '->' + name(b) for a, b in seizes) or 'none'}")
    print("   -> yes.  d1->e1 flips the king's square to White; d8->e8 flips")
    print("      Black's.  Neither player is stuck in enemy custody.")

    print()
    print("=" * 72)
    print("WHAT HAPPENS TO THE LONG-RANGE PIECES?")
    print("=" * 72)
    for mode in ("block", "jump", "path"):
        m = gen(owner, piece, WHITE, mode)
        print(f"   mode={mode:6s}  White has {len(m):3d} legal square moves")
    print("   In 'block' (the physical reading: tiles cannot pass through each")
    print("   other) a rook/bishop/queen reaches only the adjacent square, and")
    print("   so does its attack.  The knight is the only leaper left, which")
    print("   makes it the strongest piece on the board.")

    print()
    print("=" * 72)
    print("SIMULATION - can anyone actually win?")
    print("=" * 72)
    for mode in ("block", "jump", "path"):
        wins = {WHITE: 0, BLACK: 0, None: 0}
        plies, reasons = [], {}
        for g in range(100):
            w, p, why, _ = play(mode=mode, cap=300, seed=g)
            wins[w] += 1
            plies.append(p)
            reasons[why] = reasons.get(why, 0) + 1
        plies.sort()
        print(f"   {mode:6s} White {wins[WHITE]:3d}  Black {wins[BLACK]:3d}  "
              f"unfinished {wins[None]:3d} | median {plies[len(plies)//2]:3d} "
              f"plies | {reasons}")

    print()
    print("=" * 72)
    print("SAMPLE GAME (block mode)")
    print("=" * 72)
    w, p, why, log = play(mode="block", seed=3)
    for ply, me, a, b in log[:14]:
        print(f"   {ply:2d}. {'W' if me == WHITE else 'B'} square {a} -> {b}")
    print(f"   ... {len(log)} plies total")
    print(f"   winner: {'White' if w == WHITE else 'Black' if w == BLACK else 'nobody'}"
          f"  ({why})")


if __name__ == "__main__":
    main()
