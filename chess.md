# Putting the Chess in ENIAC Chess
This document describes how we wrote a tiny chess program on top of [chessvm](easm.md), our virtual machine for the ENIAC. The main limitation is memory: we have only 75 words. Speed is also a concern, as the ENIAC executes only about 500 instructions per second. The real constraint here is historical: the time to compute a move has to be less than the time between vaccuum tube failures, which was apprently 24-48 hours.

## Square numbering
Chessvm has hardware support for chess in the form of the `jil A` instruction, branch if A contains an illegal square index. We number squares as rank|file from 11 to 88. Moving right adds 1, moving up adds 10. We can continue adding or subracting and use `jil` to determine when we've run off the board. 

## Board representation
If we use one word per square, that leaves us only 11 words for all computation, which will never hold multiple search stack levels. The shortest board representation is a piece list, the location of all 32 starting pieces, but that has two serious drawbacks. First, it is very slow to find the contents of a particular board square, which is a frequent operation. Second, extra memory is required to keep track of pawn promotions. 

Instead we use a hybrid solution based on 64 digits stored in 32 words. One digit isn't enough to represent all combinations of players and pieces, so we code kings and rooks as OTHER.

```
; Board digit coding
EMPTY   .equ 0
OTHER   .equ 1
WPAWN   .equ 2
WKNIGHT .equ 3
WBISHOP .equ 4
WQUEEN  .equ 5
BPAWN   .equ 6
BKNIGHT .equ 7
BBISHOP .equ 8
BQUEEN  .equ 9
```

This allows fast checks for whether the square is occupied, and quick retrieval of most player/piece combinations. The position of the kings and rooks are stored in four other locations. 
```
; We'll always have only one king and two rooks per side (no reason to promote to rook)
; This allows us to represent any number of promoted queens
wking  .equ 32
bking  .equ 33
wrook1 .equ 34
wrook2 .equ 45  ; not adjacent to wrook1 so movegen state fits in a7
```
When a square is coded OTHER, we look in these four locations. If none of them reference the square, then the piece must be a black rook. 

In practice the `get_square` routine abstracts all of this away, and just returns player|piece in two digits.
```
WHITE   .equ  0
BLACK   .equ  1

PAWN    .equ  1
KNIGHT  .equ  2
BISHOP  .equ  3
QUEEN   .equ  4
ROOK    .equ  5
KING    .equ  6
```

## Stack frames
We search using a standard depth-first [alpha-beta search](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning) algorithm with a 4 ply stack. Each stack frame is 9 entires.

| address | name | description |
| - | - | - |
| 36 | targetp | player/piece captured, or zero if square is empty |
| 37 | from | from square index |
| 38 | target | to square index |
| 39 | movestate | state to generate next move |
| 40 | bestfrom | best move from square |
| 41 | bestto | best move from square |
| 42 | bestscore | best move score |
| 43 | alpha | lower pruning threshold |
| 44 | beta | upper pruning threshold |

Instead of indirecting through a stack pointer, the top of stack is kept at a fixed address to save code space. This requires copying on push and pop. To make that copying more efficient using loadacc/storeacc, stack entries are stored with a stride of 10 words at offsets 36, 46, 56, and 66.


## Memory map
Four stack frames, three globals, and one board. That's all you need, baby.
```
00   B  B  B  B  B
05   B  B  B  B  B
10   B  B  B  B  B
15   B  B  B  B  B
20   B  B  B  B  B
25   B  B  B  B  B
30   B  B  O  O  O
35   O  S0 S0 S0 S0
40   S0 S0 S0 S0 S0
45   G  S1 S1 S1 S1
50   S1 S1 S1 S1 S1
55   G  S2 S2 S2 S2
60   S2 S2 S2 S2 S2
65   G  S3 S3 S3 S3
70   S3 S3 S3 S3 S3

B=board square, O=other piece square, Sx=stack frame x, G=global
```
