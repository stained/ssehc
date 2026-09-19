#!/usr/bin/env python3
"""ssehc - shared-custody variant with king capture: the march is a forced win.

Rules being tested (the previous ruleset, kept because the result matters):
  * 64 squares of fixed colour, each carrying a chess piece that rides it.
  * White commands the 32 light squares, Black the 32 dark ones.
  * A turn: slide one of your own squares one cell in any of the 8
    directions, swapping with the square already there; then optionally
    make one capture with a piece of your own colour.
  * Capturing the enemy king wins.

Finding: a king stands on the *opponent's* colour.  White's king is on e1
(dark -> Black's), Black's king is on e8 (light -> White's).  So neither
player can ever move their own king, and each can walk the enemy king one
cell per turn straight into their own army.  White is simply faster.
"""
import random

WHITE, BLACK = 0, 1
OPP = (BLACK, WHITE)

EMPTY = 0
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


ADJ = []
for _c in range(64):
    _r, _cc = rc(_c)
    for _dr, _dc in DIRS:
        _rr, _ccc = _r + _dr, _cc + _dc
        if on(_rr, _ccc):
            _d = idx(_rr, _ccc)
            if _c < _d:
                ADJ.append((_c, _d))


class State:
    __slots__ = ("sq_at", "cell_of", "piece", "turn")

    def __init__(self):
        self.sq_at = list(range(64))      # cell -> square id
        self.cell_of = list(range(64))    # square id -> cell
        self.piece = [0] * 64             # square id -> piece (rides the square)
        self.turn = WHITE

    def clone(self):
        s = State.__new__(State)
        s.sq_at = self.sq_at[:]
        s.cell_of = self.cell_of[:]
        s.piece = self.piece[:]
        s.turn = self.turn
        return s


def initial():
    st = State()
    for c in range(8):
        st.piece[idx(0, c)] = mk(BACK[c], WHITE)
        st.piece[idx(1, c)] = mk(PAWN, WHITE)
        st.piece[idx(6, c)] = mk(PAWN, BLACK)
        st.piece[idx(7, c)] = mk(BACK[c], BLACK)
    return st


def owns(sq, player):
    """Ownership is by the SQUARE's colour, not the piece's."""
    return is_light(sq) == (player == WHITE)


def sq_moves(st, me):
    return [(a, b) for a, b in ADJ
            if owns(st.sq_at[a], me) or owns(st.sq_at[b], me)]


def swap(st, a, b):
    sa, sb = st.sq_at[a], st.sq_at[b]
    st.sq_at[a], st.sq_at[b] = sb, sa
    st.cell_of[sa], st.cell_of[sb] = b, a


def occupancy(st):
    m = 0
    for c in range(64):
        if st.piece[st.sq_at[c]]:
            m |= 1 << c
    return m


def attacks(st, player, occm=None):
    if occm is None:
        occm = occupancy(st)
    res = 0
    for c in range(64):
        p = st.piece[st.sq_at[c]]
        if not p or pcol(p) != player:
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
                    if occm & bit:
                        break
                    rr += dr
                    ccc += dc
    return res


def captures(st, player):
    at = attacks(st, player)
    out = []
    for c in range(64):
        p = st.piece[st.sq_at[c]]
        if (at >> c) & 1 and p and pcol(p) != player:
            out.append(c)
    return out


def king_sq(st, colour):
    for s in range(64):
        p = st.piece[s]
        if p and ptype(p) == KING and pcol(p) == colour:
            return s
    return -1


def name(c):
    r, cc = rc(c)
    return "abcdefgh"[cc] + str(r + 1)


def board(st):
    rows = []
    for r in range(7, -1, -1):
        row = []
        for c in range(8):
            p = st.piece[st.sq_at[idx(r, c)]]
            ch = '.' if not p else CHAR[ptype(p)]
            row.append(ch.lower() if p and pcol(p) == BLACK else ch)
        rows.append(f"{r + 1}  " + " ".join(row))
    rows.append("   a b c d e f g h")
    return "\n".join(rows)


def march_move(st, me, rng):
    """Drag the enemy king one step toward my own army; take it if the step
    lands on a square I already cover."""
    eks = king_sq(st, OPP[me])
    home_r = 0 if me == WHITE else 7
    best = bestkey = None
    for a, b in sq_moves(st, me):
        if eks not in (st.sq_at[a], st.sq_at[b]):
            continue
        cur = st.cell_of[eks]
        dst = b if cur == a else a
        st2 = st.clone()
        swap(st2, a, b)
        covered = bool((attacks(st2, me) >> dst) & 1)
        r, _ = rc(dst)
        key = (0 if covered else 1, abs(r - home_r), rng.random())
        if bestkey is None or key < bestkey:
            bestkey, best = key, (a, b, cur, dst, covered)
    return best


def play(seed=1, cap=40, verbose=True):
    rng = random.Random(seed)
    st = initial()
    for ply in range(1, cap + 1):
        me = st.turn
        pick = march_move(st, me, rng)
        if pick is None:
            print("no king-drag available (unexpected)")
            break
        a, b, cur, dst, covered = pick
        swap(st, a, b)
        caps = captures(st, me)
        king_cap = [c for c in caps if ptype(st.piece[st.sq_at[c]]) == KING]
        if verbose:
            tag = "W" if me == WHITE else "B"
            note = "  king dragged onto a covered square" if covered else ""
            print(f"  {ply:2d}. {tag} slides the enemy king's square "
                  f"{name(cur)} -> {name(dst)}{note}")
        if king_cap:
            victim = st.piece[st.sq_at[king_cap[0]]]
            st.piece[st.sq_at[king_cap[0]]] = EMPTY
            if verbose:
                print(f"      {('White' if me == WHITE else 'Black')} captures the "
                      f"{'black' if pcol(victim) == BLACK else 'white'} king at "
                      f"{name(king_cap[0])}  ->  GAME OVER, "
                      f"{'White' if me == WHITE else 'Black'} wins at ply {ply}")
            return me, ply, st
        st.turn = OPP[me]
    return None, cap, st


def main():
    st = initial()
    wk = st.cell_of[king_sq(st, WHITE)]
    bk = st.cell_of[king_sq(st, BLACK)]
    print("=" * 72)
    print("WHO CONTROLS THE KINGS?")
    print("=" * 72)
    print(f"   White king on {name(wk)}  -> ", end="")
    print("owned by " + ("White" if owns(st.sq_at[wk], WHITE) else "Black"))
    print(f"   Black king on {name(bk)}  -> ", end="")
    print("owned by " + ("White" if owns(st.sq_at[bk], WHITE) else "Black"))
    print("   Each king stands on the OPPONENT's colour. So neither player can")
    print("   ever move their own king, and each can walk the enemy king.")
    print()
    print("=" * 72)
    print("WHITE MARCHES THE BLACK KING DOWN THE BOARD")
    print("=" * 72)
    winner, ply, final = play(seed=1)
    print()
    print("=" * 72)
    print("FINAL POSITION")
    print("=" * 72)
    print(board(final))
    print(f"\n   Result: {'White' if winner == WHITE else 'Black'} wins at ply {ply}.")


if __name__ == "__main__":
    main()
