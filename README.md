# ENIAC Chess

This repository contains a chess playing program for the historic ENIAC computer, and the tooling used to create it. It implements 4 ply [alpha-beta](https://www.chessprogramming.org/Alpha-Beta) search with a simple materiel evaluation function, and would generate one move in about 5 hours of ENIAC machine time (much faster in simulation, of course). 

The goal is to demonstrate that a reasonably powerful chess playing program was already possible when ENIAC became the first operational general purpose digital computer in early 1946, perhaps a few months after Alan Turing set down (what we believe to be) the [first reference](https://www.google.com/books/edition/Alan_Turing_s_Electronic_Brain/wfMDW-IP8yMC?hl=en&gbpv=1&bsq=chess) to the possibility of a digital computer playing chess. Or perhaps the goal is to demonstrate that, even though chess has been a measure of human intelligence for centuries and then a measure of machine intelligence, it's not actually that difficult if the very first computer could play it at an amateur level.

## Background

ENIAC was not originally a stored program computer.  Instead, it was a bunch of function units that could be wired together with patch cables.  People [later](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/) figured out how to rig it up to execute opcodes stored in the 3,600 digits of the machine's "function tables." These were originally intented to be lookup tables for things like cosines but ended up being used as the machine's ROM.

To make ENIAC play chess, first we set up the machine to implement a custom CPU with 51 opcodes, essentially a "virtual machine." [The VM](https://github.com/jeredw/eniac-chess/blob/master/isa.md) appears to the programmer to have 10 registers and 75 words of linear addressable memory, where each word is two decimal digits, and would execute about 500 virtual instructions per second on the real machine. On the bright side, we have space for somehwat less than 1,800 instructions in ROM, and plenty of chess programs have been [smaller](https://www.chessprogramming.org/MicroChess) than this. Then we wrote a tiny chess program for this VM, based on alpha-beta search with some extensions. 

Interaction with the final program is via virtual punched cards. The human sets up the board via punched cards, each of which writes a one word to a given address. After the search completes, the machine prints its best move as from and to squares on a similar card. Because ENIAC is so slow, reasonable play takes nearly a day per move, so we envision the machine used to play [correspondence chess](https://en.wikipedia.org/wiki/Correspondence_chess).

Creating this program involves multiple layers of tools and cross-validation. 

## How this all works
 - [Programming an ENIAC virtual machine](easm.md) - how we built chessvm on top of ENIAC's ill-suited hardware. 
 - [ChessVM Reference](isa.md) - chessvm instruction set, architecture, and microcode reference
 - [Putting the Chess in ENIAC Chess](chess.md) - How our tiny chess program runs on our tiny VM
 
 
## Main Files

| File                     | Description                                     |
| ------------------------ | ----------------------------------------------- |
| `Makefile`               | `make` to build everything, `make test` to test |
| `easm/easm.py`           | An ENIAC "patch assembler" which converts `.easm` code into `.e` patches the simulator runs |
| `chessvm/chessvm.easm`   | VM source code, written in the custom patch assembly language |
| `chessvm.e`              | Assembled VM (output of `easm` on `chessvm.easm`). Effectively a [netlist](https://en.wikipedia.org/wiki/Netlist) for the VM which the simulator can run. |
| `chsim/chsim.cc`         | Emulator for the chess VM, for efficient development of asm programs and cross-validation of `chessvm.easm` VM implementation |
| `chasm/chasm.py`         | Assembler targeting chess VM. Turns `.asm` into `.e` ENIAC function table switch seetings (ROM)|
| `asm/chess.asm`          | Chess program written in VM assembly |
| `chess.e`                | Assembled chess program, the object code for `chess.asm`
| `asm_test.py`            | Python unit tests for the chess engine move generation, move execution, and search. |
| `fen2deck.py`            | Converts [FEN notation](https://www.chess-poster.com/english/fen/fen_epd_viewer.htm) board setups into `.deck` files for the simulator |
| `vis/`                   | HTML/JS visualizations of the ENIAC state, for the VM registers, chess, life, and connect 4 |
| `model/`                 | High level models for the chess engine, written in Python to test tiny chess algorithms |


## Playing Chess
This project relies on a pulse-level [ENIAC simulator](https://www.github.com/jeredw/eniacsim) derived from Briain Stuart's original [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html). Assuming that's installed, and the starting position is in `board.fen`, 
```
make chess
python fen2deck.py < board.fen > asm/chess.deck
eniacsim chess.e
```

This will read in the deck, and (eventually) output a single card with four digits FFTT, where FF=from square, TT=tosquare. The squares are numbered 11 to 88 in rank,file notation. Currently ENIAC always plays white, though setting memory location [`fromp`](https://github.com/jeredw/eniac-chess/blob/master/asm/memory_layout.asm) to 10 (adding a card punched 3510 to the intial deck) should make it play black.

You can also run the chess program much faster (~1000x vs ~100x realtime) by executing on the VM emulator `chsim`, which skips pulse-level simulation. Note that eniacsim also executes `chsim` in parallel to validate the ENIAC VM implementation `chessvm.easm` against the VM emulator `chsim.cc`.
```
chsim/chsim -f asm/chess.deck chess.e
```

### Running with ENIAC blinkenlights and chess GUI
You can simply use the script `runchess.py` to play a game against ENIAC.  Just run
```
python runchess.py
```

The script will build the chess program and invoke `eniacsim` in a mode that loads `chsim` as a dynamic library to get faster simulation. It also starts an eniacsim debug GUI for inspecting machine state at [http://localhost:8000/vm.html](http://localhost:8000/vm.html) and another for visualizing ENIAC hardware state at [http://localhost:8000/blinkenlights](http://localhost:8000/blinkenlights)

### Playing Connnect 4, TicTacToe, and Life
We implemented these simpler games during VM development. Python wrappers provide nice interfaces so you don't have to punch cards manually (create .deck files) to enter your move. Try any of
```
python runtic.py
python runc4.py
make life; eniacsim chess.e
```

## Testing
Do `make test` to test easm, chasm, chsim, and chess.

To test the VM implementation, do `make vmtest` to assemble `chessvm.easm` into an ENIAC patch, assemble `asm/vmtest.asm` into switch settings, and then concatenate the two into the simulator to run a self test. A successful test will print out TTSS where TT=incrementing test numbers and SS=test status code, where success is 00 and anything else is failure. The ENIAC may also hang or loop, of course. This also tests `chsim` by running the VM emulator in parallel and comparing the results to the simulator state.

To test the chess engine, do `python asm_test.py`. This will assemble `asm/movegen_test.asm`,`asm/move_test.asm` and `asm/chess.asm` to test move generation, move execution, and move search respectively.

