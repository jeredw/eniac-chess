# Putting the Chess in ENIAC Chess
This document describes how we wrote a tiny chess program on top of [chessvm](easm.md), our virtual machine for the ENIAC. The main limitation is memory: we have only 75 words. Speed is also a concern, as the VM executes only about 500 instructions per second. The real constraint here is historical: the time to compute a move has to be less than the time between ENIAC hardware failures, 24-48 hours on a good week.

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

## Fitting chess
The chess program is algorithmically pretty simple, but cramming it into the available space was still interesting. So we'll omit a code walk here and focus instead on interesting memory layout and program organization decisions. Here is a quick summary of the program's memory map, which will be explained more in the following sections.

```
00   B  B  B  B  B
05   B  B  B  B  B
10   B  B  B  B  B
15   B  B  B  B  B
20   B  B  B  B  B
25   B  B  B  B  B
30   B  B  O  O  O
35   G  S0 S0 S0 S0
40   S0 S0 S0 S0 S0
45   O  S1 S1 S1 S1
50   S1 S1 S1 S1 S1
55   G  S2 S2 S2 S2
60   S2 S2 S2 S2 S2
65   G  S3 S3 S3 S3
70   S3 S3 S3 S3 S3

B=board square, O=other piece square, Sx=stack frame x, G=global
```

### Square numbering
From our earliest prototyping with 2-digit words, we decided to number squares as rank|file from 11 to 88 with an extra guard band of "illegal" sentinel squares numbered 0x, x0, 9x, and x9. Chessvm has hardware support for this numbering in the form of `jil`, which branches if A contains an illegal square index. This way moving right adds 1, moving up adds 10, and we can continue adding or subracting and use `jil` to determine when we've run off the board. Conveniently, this also works to bound knight moves at the edges of the board.

### Board representation
A square can be empty or have one of 6 types of pieces for one of 2 players, 13 states. If we used one entire word per square it'd leave only 11 words for all other computation, and we'd never fit a search stack. So initially we discounted array representations.

The shortest board representation is a piece list, the location of all 32 starting pieces, but that has two serious drawbacks. First, it is very slow to find the contents of a particular board square, which is a frequent operation. Second, extra memory is required to keep track of pawn promotions. We thought we were stuck with piece lists so explored adding special accelerated piece scanning microprograms to the VM, but there just wasn't room.

Instead we use a hybrid solution based on 64 digits stored in 32 words. One digit isn't enough to represent all combinations of players and pieces, so we code kings and rooks as OTHER falling back to a small piece list.

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
When a square is coded `OTHER`, we look in these four locations. If none of them reference the square, then the piece must be a black rook. 

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

Updating this board representation is somewhat more elaborate than querying it; the routines to do and undo moves consume most of a function table even after cramming. Fitting them required tricks like tail calling shared nested subs, and simulating an additional level of subroutine stack using a small jump table. But this is still ok, on balance, since most squares are empty and there are many more square lookups than moves tried.

### Square lookup
A key inner loop operation in `get_square` needs to translate a logical square number from 11-88 to a word and digit address. This could have been microprogrammed if there'd been room in the VM, but it was convenient and fast enough to use a table lookup with `ftl`. A 64 entry sparse table maps from 11-88 back to word addresses 0-31, using the sign to pick the high or low digit.

Hogging so much table space for address translation does make some other things awkward. We need pretty much all the table space, so have to use table entries corresponding to guard band squares (which don't need to be translated) to store other tables. For example the table of deltas for knight jumps (8, 12, 19, 21, 79, 81, 88, 92) is squeezed into locations 16, 26, 36, 46, ... instead of a more natural contiguous order.

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

While the VM supports addressable memory it does not support indexed addressing modes, meaning that we would have to load the stack stack pointer from memory and add the field offset on every access. Instead, the top of stack is kept at a fixed address to save code space. Stack push and pop then require copying the remaining stack entries up or down.

If stack entries were packed densely into a range of linear addresses, we'd need to copy one word at a time, messily unpacking and repacking hardware accumulators. Instead, we store stack entries aligned to accumulators, with a stride of 10 words at offsets 36, 46, 56, and 66. This means that the copy has to be careful to preserve locations 35, 45, 55, and 65 in registers during the copy, but can otherwise use `loadacc` and `storeacc` to do more natural and efficient accumulator-width copies.

### Legal move detection
The core of the chess program iterates over available moves for the current board position. It is simple enough to enumerate the basic moves for each piece, and try one at a time. However, chess has several more complicated rules -- draws by repetition, en passant captures, castling. Like lots of small chess programs we chose to handwave those away, and rely on the player to override some state should they want somesuch fancy thing. Castling is the most unfortunate casualty and it would be a nice addition to allow ENIAC to castle.

However, responding correctly to check and respecting king pins is quite important for nonjanky normal chess. We first explored adding additional move enumeration logic to detect check and avoid playing into it, but this takes quite a lot of code, about half as much move generation proper. So instead we took the approach of some other tiny chess programs and integrated legal move detection into search, unwinding the stack to skip illegal moves when we find a king capture. This works because four ply search means we always end on the opponent's move.

### Scoring
Right now the program just uses simple material scoring with the usual piece values 1=PAWN, 3=BISHOP/KNIGHT, 5=ROOK, 9=QUEEN. The score is updated incrementally as moves are done and undone since scanning the entire board would be too slow.

Because the VM isn't very good at signed arithmetic, a balanced position has score 50. This gives a low dynamic range for scores, just +/-50 points -- normally modern chess programs use larger values and think in "centipawns", but we lack facilities for extended precision arithmetic and stack space to store larger scores. This is somewhat mitigated because the program operates one move at a time, so we reset the position score to 50 at the start of each search since only differential value matters.

## Future work
As of this writing the chess program itself is pretty early in development. It sorta works but there is lots of room for improvement and extension. The program is probably not bug free as it stands, so more validation and eventually tournament play would be interesting.

Simple position scoring heuristics would be a nice enhancement and should take little code space. Some other simple chess programs with more table space use small lookup tables for this, but we'd likely have to fall back on code. For example, we could add points for pieces in the center, or score the number of ranks with a pawn or connected pawn.

While the machinery for pawn promotion is available, we don't actually do it right now. This would probably make endgames much more interesting.
