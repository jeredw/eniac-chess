# Putting the Chess in ENIAC Chess
This document describes how we wrote a tiny chess program on top of [chessvm](easm.md), our virtual machine for the ENIAC. The main limitation is memory: we have only 75 words. Speed is also a concern, as the VM executes only about 500 instructions per second. The real constraint here is historical: the time to compute a move has to be less than the time between ENIAC hardware failures, which was apprently 24-48 hours on a good week.

## Software bringup prework
We developed the chess program concurrently with the VM and tools such as assemblers and simulators. While we had theories about how it might come together, it wasn't clear what instructions we'd need, or what would actually fit into the 1946 ENIAC hardware. So we began with some simpler test programs.

### vmtest
A self-test program `vmtest` was critical to sanity check everything from early on in VM development. We refined `vmtest` as we added instructions, tool features, and more complex test programs found more complex microarchitecture and simulator bugs. For the actual ENIAC, software self-tests were an essential part of day-to-day operations because of frequent hardware faults.

### tic
The first real program we tried was `tic`, a depth first minimax search to play [tic-tac-toe](https://en.wikipedia.org/wiki/Tic-tac-toe). Basic arithmetic, control flow, and one level of subroutine stack were ok. Our spartan register move ISA made for an annoying profusion of `swap`s, but we really didn't have room for more, so we papered over it with syntactic sugar and macro instructions in the assembler like `mov 42,A<->B`.

The biggest issue was that we only had `loadacc` and `storeacc` working, and weren't sure word load/store would fit. It was just possible to write `tic` without them, but the code was bloated. One entire function table was consumed by detecting if someone had won the game. Chess would probably not fit without word load/store. As the final instructions came online, we rewrote `tic` to vet them and realized some nice simplifications.

`tic` was also frighteningly slow -- we'd wait 5 minutes per move _in simulation_, only to discover a bug where the computer lost! This prompted more exhaustive vmtests, and lots of simulator and some VM optimizations.

### c4
Next we tried `c4`, a [connect four](https://en.wikipedia.org/wiki/Connect_Four) search program. Structurally `c4` is similar to `tic`, but tested program size, memory, and runtime limits, since we couldn't completely search the game. It also explored more complex array scans of the sort we'd see in chess.

`c4` showed that our minimal load/store and single word table lookups with `ftl` were slow but adequate for array scans like looking for diagonal runs of 4 pieces. `ftl` proved so useful that we revised it from a busted minimal placeholder `ftl A,D` to `ftl A` -- not quite the `ftl A,#imm` we hoped for but decent.

ROM space for `c4` was more crunched than for `tic` but still cozy. A deeper subroutine stack would be nice and we spitballed some ideas, but there was no room, and carefully planned spaghetti code fit ok. RAM was another issue. We quickly ran out of registers and spill space, and had to double up some variables. We realized belatedly that rather than use 42 words for a 6x7 board, we should explore using 42 packed digits in 21 words.

`c4`s runtime was alarming, at first taking almost an hour of real time per move (around a day of simulated time). alpha/beta pruning and searching moves in a better order, inner columns first, helped dramatically, so spending more on better algorithms made a ton of sense as usual. But demoing chess would still be like watching paint dry. Optimizations to `eniacsim` got its pulse level hardware simulations to around 40x realtime, but we needed 1000x. So we decided to have `eniacsim` checkpoint state with `chsim`, and after cross validating the simulators we relied on much faster VM-level simulation most of the time.

### life
A small `life` program simulating [Conway's game of life](https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life) made a good quick testbed for digit packing, which proved vital. Surprisingly, we also found in `life` that copy loops using `loadacc`/`storeacc` netted out faster than simulating indexed arithmetic. In most `life` programs, you can double buffer and flip between two arrays for the current and next generation, but it was better to always operate in place. This informed the stack layout for chess.

## Chess program design

### Square numbering
Chessvm has hardware support for chess in the form of the `jil A` instruction, branch if A contains an illegal square index. We number squares as rank|file from 11 to 88. Moving right adds 1, moving up adds 10. We can continue adding or subracting and use `jil` to determine when we've run off the board. 

### Board representation
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

### Stack frames
We search using a standard depth-first [alpha-beta search](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning) algorithm with a 4 ply stack. Each stack frame is 9 entires.

| address | name | description |
| - | - | - |
| 36 | targetp | player/piece captured, or zero if square is empty |
| 37 | from | from square index |
| 38 | target | to square index |
| 39 | movestate | state to generate next move |
| 40 | bestfrom | best move from square |
| 41 | bestto | best move to square |
| 42 | bestscore | best move score |
| 43 | alpha | lower pruning threshold |
| 44 | beta | upper pruning threshold |

The VM does not support indexed addressing modes. So instead of indirecting through a stack pointer, the top of stack is kept at a fixed address to save code space. This requires copying on push and pop. To make that copying more efficient using loadacc/storeacc, stack entries are stored with a stride of 10 words at offsets 36, 46, 56, and 66.


### Memory map
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
