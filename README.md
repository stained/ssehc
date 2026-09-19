# ssehc

Chess with the board moving instead of the pieces.

You command a colour of **square**, not a colour of piece — and any piece standing
on one of your squares is yours to move. Paint the whole board your colour to win.

```
open index.html
```

`index.html` is the game: one self-contained page, no build step, no dependencies,
no server.

## The rules

1. White moves white squares; Black moves black squares.
2. A square moves the way the piece standing on it moves. A square with no piece
   cannot move at all.
3. Moving swaps the pieces — a long move swaps them one square at a time, so a
   slider pushes its way through an occupied board.
4. Every square the path enters is painted the mover's colour. A rook or queen
   square can repaint seven cells in one move.
5. Paint the whole board your colour to win.

## What falls out of that

- **Only 32 pieces stand on 64 squares.** Half the board is immobile but perfectly
  paintable: it can be taken and cannot be defended.
- **The pieces are colourless.** Ownership lives in the square, so each side
  commands eight of its own movement templates and eight of the opponent's. You
  will regularly find yourself moving the other side's pieces — and losing your
  own.
- **The templates migrate.** Because they swap along every path, you can end up
  with no movable square at all. That is usually temporary, but it is a real
  rhythm of the game.
- **Caution deadlocks.** Every attack paints up to seven cells and opens a line
  worth seven cells back. Two defensive players hold each other at parity
  indefinitely; the game belongs to whoever overreaches at the right moment.

## Design notes

`SUBVERSION.md` holds the whole record: the settled ruleset, the measured results,
and the ladder of four earlier variants that collapsed — with the reason in each
case, because the collapse is the interesting part.

## The simulations

```
python3 paint.py       # the settled ruleset: 60 games, 29 painted the board out
python3 march.py       # collapse 1: Black wins at ply 6
python3 race.py        # collapse 2: the two goals are the same state
python3 erosion.py     # an earlier waypoint: the board as the material
python3 inversion.py   # an earlier waypoint: movement templates + king capture
```

The JavaScript engine in `index.html` matches `paint.py` exactly — 96 opening
moves a side, verified against 300 randomised games with invariants asserted
every ply.
