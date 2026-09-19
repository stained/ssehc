# ssehc

*A chess set that refuses to be chess.*

Chess is defined by the fact that the pieces move. The board is the one thing
that never does — it is the fixed frame that makes the whole game legible, the
reason a position can be named, recorded, and argued about five hundred years
later.

This is chess with the frame moving instead.

---

## The thesis

Four rulesets were built and tested. Three of them collapse.

Every collapse has the same cause: **the pieces were left inert.** Take the
pieces out of the game and the board is a set of 64 interchangeable markers on a
bipartite grid, and every rule you can state about such a set is either
conflict-free, oscillatory, or choiceless.

The version that works is the one where the pieces are given a new job. They stop
being the things you move and become the *movement rules of the thing you move*.
Only then does the board become a game — and only then does the subversion bite,
because the chess player's entire education is still, suddenly, pointed at the
wrong object.

> The pieces cannot be decoration. If the pieces mean nothing, the board means
> nothing either.

---

## The ruleset as settled

1. White moves white squares; Black moves black squares.
2. A square moves the way the piece standing on it moves.
3. Moving swaps the pieces: one square swaps two pieces, and a longer move
   swaps the pieces in between, one square at a time.
4. Moving a square converts the destination to the colour of the square being
   moved — and since a long move is a sequence of one-square steps, the whole
   path is painted.
5. Make the board entirely one colour.

Rule 3 is the load-bearing one. Every cell of an 8×8 board is occupied, so
without it no slider could ever take a step. Swap-chaining is what lets a rook
push its way down a rank, and it is what makes rule 4 explosive: a rook or queen
square can repaint **seven cells in one move**.

Measured (`paint.py`): **the goal is reachable, and games really do end by
painting the whole board.** In 60 greedy games, **29 finished with the board a
single colour** — White 16, Black 13, 31 unfinished. The largest sweep in any
game was 7 cells. The counts swing violently and continuously: a typical game
passes through 42/22, then 24/40, then 32/32 within 125 plies.

Ownership is purely by the square. The pieces' own colours mean nothing, so a
player may move **any** piece standing on one of their squares. In one real game
Black's second move is `B R a1->h1` — Black moving *White's own rook*, because a1
is a dark square and therefore Black's.

Four things fall out that were not designed:

- **The empty middle is the prize.** Only 32 of the 64 squares carry a template.
  The other 32 are immobile — but perfectly paintable. Half the board can be
  taken and cannot be defended.
- **Immobilisation is constant and temporary.** Across 60 games there were
  **141 forced passes**. A player can end up with no movable square at all,
  because every template has migrated onto enemy squares — but the opponent's
  next swap-chain usually hands one back. So the correct rule is that a stuck
  player *passes*; nobody was ever immobilised to death.
- **Caution deadlocks the game.** An offensive bot finishes 29 of 60. A bot that
  refuses to hand over a counter-sweep finished **1 of 12**, and its games
  oscillated around 32/32 for the full 400 plies. The tension is *risk*: every
  attack exposes you to a seven-cell reprisal, and two defensive players can hold
  each other at parity indefinitely.
- **The templates reassemble.** The final board of a 400-ply deadlock is very
  nearly the opening chess position. Sweeping back and forth puts the templates
  home again, so the game keeps a strong memory of its setup.

---

## The collapse ladder

*The variants tried on the way here, and why each one died.*

### 1. Shared custody, capture the king

**Rule.** 64 squares, fixed colour, each carrying a chess piece that rides it.
White commands the 32 light squares, Black the 32 dark ones. On your turn slide
one of your own squares one cell in any direction, swapping with the square
there; then optionally make one capture with a piece of your own colour.
Capturing the king wins.

**Collapse.** A king stands on the *opponent's* colour. White's king is on e1
(dark, Black's); Black's on e8 (light, White's). So neither player can ever move
their own king, and each can walk the enemy king one cell per turn straight into
their own army. Chess's king-safety logic does not merely weaken — it inverts:
your king is not yours.

`march.py` plays it out. Black wins at **ply 6**, by dragging the white king onto
the long diagonal of the c8 bishop, which was open the whole time.

### 2. The race

**Rule.** Get all your squares to the other side of the board first. The pieces
are inert.

**Collapse, two ways, both proved.**

*There is nothing to fight over.* Let `w_top` be White's squares on ranks 5–8 and
`b_bot` Black's on ranks 1–4. The board is full and every move is a swap, so
`w_top + b_top = 32` and `b_top + b_bot = 32`, giving `w_top ≡ b_bot` for every
reachable position. "All my squares across" and "all your squares across" are the
same board state. Exhaustively checked over all 12,870 four-by-four boards, and
over 200,000 random eight-by-eight boards: never a disagreement.

*Nobody can be made to advance.* In the opening position there are **98** legal
moves that change nothing at all — diagonal neighbours share a colour, squares may
now move in any direction, so sliding a white square onto another white square is
a legal no-op. No-ops never run out. Optimal play is mutual refusal: an infinite
draw. Pushing hard, the counter climbs and then plateaus short of 32.

### 3. Conversion

**Rule.** Moving a square onto an enemy square converts it; own the board.

**Collapse, both readings.** If a flipped square can be flipped back, the count
oscillates 32 ↔ 33 forever — the boundary just ripples. If flips are permanent,
no choice matters at all: it is a counting race and the first player wins on a
fixed ply. (Hand-reasoned, not simulated.)

### 4. Erosion — the version that bites

**Rule.** A square moves exactly as the piece standing on it moves. A capture
takes the **square**, not the piece. Win when your opponent has no squares left.

This one plays. `erosion.py`, 200 games each:

| policy | White | Black | unfinished | median length |
|---|---|---|---|---|
| random | 101 | 92 | 7 | 387 plies |
| greedy | 118 | 82 | 0 | 67 plies |

The opening position offers each player **76 legal moves, all 76 of them
immediate square-captures**. Pawns are frozen — there are no holes yet, and every
forward diagonal is a friendly square — so the game opens with knight squares
jumping straight into the enemy's squares.

And the board dissolves. One game, square counts by ply:

```
  0 : 32/32      24 : 20/20      48 :  8/ 8
  6 : 29/29      30 : 17/17      54 :  5/ 5
 12 : 26/26      36 : 14/14      60 :  3/ 2
 18 : 23/23      42 : 11/11      63 :  3/ 0
```

---

## What erosion inverts

| chess | ssehc |
|---|---|
| you capture pieces | you capture squares |
| the board is eternal | the pieces are eternal |
| material is men | material is terrain |
| a defended piece cannot be taken | no square can be defended |
| pawns lock the position as the game goes on | the board opens up as it dies |
| the pieces carry the power | the pieces *are* the power, spent by the ground |
| the game can be written down | nothing can be written down |

Two of these deserve their own paragraph.

**There is no defence.** In chess, protection is most of the game: a piece is
safe because something guards it. Here a captured square is simply gone, and no
piece can guard it. Every attack therefore succeeds, so the game is a pure race
of initiative — which is exactly what the 59/41 first-player split is measuring.

**Nothing can be written down.** Chess is not just a game, it is a literature:
algebraic notation is why a game played in 1851 can still be argued about. This
game cannot be recorded. "The d1 square moves to d3" has no notation, and after a
capture there is no square at the destination to name. A spectator watching the
pieces sees a board slowly emptying and cannot reconstruct a single move. The
subversion is not that the rules are different — it is that the game leaves no
trace.

---

## The object

A standard set. Unmodified pieces, standard starting position. The only unusual
component is the rule card, and the board should ideally be 64 loose tiles in a
shallow tray, so that squares can physically be slid.

**The rule card**

> **ssehc**
>
> Set up as chess.
>
> On your turn, take one of your own squares and move it the way the piece
> standing on it moves. Nothing else moves.
>
> If you land on an enemy square, that square is gone, and the piece on it goes
> with it.
>
> The first player with squares left owns the board.
>
> The pieces are not the game. The pieces are the rules.

**Staging.** The reveal is gradual and should not be explained. A chess player
reads the card, nods, and plays chess — and the first time a *knight square*
jumps, carrying its knight, they look up. By then the board has already begun to
dissolve, and the piece they were protecting is a movement rule that is about to
be deleted.

---

## Playing it

`index.html` is the game: one self-contained page, no build step, no
dependencies. Open it in a browser.

You play White against a computer opponent. A dot marks every square you may
move — note that some of them carry the *other* side's pieces. Clicking one rings
its destinations; hovering a destination previews the path and how many cells it
will paint. The panel toggles the computer off, swaps the pieces between their
traditional chess colours and uniform bronze "templates", and undoes.

## The simulations

```
python3 paint.py       # the settled ruleset: 60 games, 29 painted the board out
python3 march.py       # collapse 1: Black wins at ply 6
python3 race.py        # collapse 2: the two goals are the same state
python3 erosion.py     # an earlier waypoint: the board as the material
python3 inversion.py   # an earlier waypoint: movement templates + king capture
```
