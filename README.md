# ENIAC chess playing program

This repository contains a chess playing program and associated tools for the historic ENIAC computer.

## Background

ENIAC was not originally a stored program computer.  Instead, it was a bunch of function units that could be wired together with patch cables.  People [later](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/) figured out how to rig it up to execute opcodes stored in the 3,600 digits of the machine's "function tables." These were originally intented to be lookup tables for things like cosines but ended up being used as the machine's ROM.

To make ENIAC play chess, first we set up the machine to implement a custom CPU with 51 opcodes, essentially a "virtual machine." [The VM](https://github.com/jeredw/eniac-chess/blob/master/isa.md) appears to the programmer to have 10 registers and 75 words of linear addressable memory, where each word is two decimal digits, and would execute about 500 virtual instructions per second on the real machine. On the bright side, we have space for somehwat less than 1,800 instructions in ROM, and plenty of chess programs have been [smaller](https://www.chessprogramming.org/MicroChess) than this. Then we write a tiny chess program targetting this VM, based on alpha-beta search with some extensions. 

Interaction with the final program is via virtual punched cards. The human enters their move via a card containing from and to squares, and the machine prints its move on a similar card. Because ENIAC is so slow, reasonable play takes hours per move, so we envision the machine used to play [correspondence chess](https://en.wikipedia.org/wiki/Correspondence_chess).

Doing this involves multiple layers of tools and cross-validation. 

## Contents

| File                     | Description                                     |
| ------------------------ | ----------------------------------------------- |
| `Makefile`               | `make` to build everything, `make test` to test |
| `isa.md`                 | A description of VM opcodes and accumulator layout |
| `easm.py`                | An ENIAC "patch assembler" which converts `.easm` we code into `.e` the simulator runs |
| `chessvm.easm`           | VM source code, written in the custom patch assembly language |
| `chessvm.e`              | Assembled VM (output of `easm` on `chessvm.easm`). Effectively a [netlist](https://en.wikipedia.org/wiki/Netlist) for the VM which the simulator can run. |
| `chess.asm`              | Chess program written in VM assembly |
| `chasm.py`               | Assembler targeting chess VM. Turns `.asm` into object code representing function table switch settings -- the ENIAC's "ROM" |
| `chsim.cc`               | Simulator for the chess VM, for efficient development and cross-validation of the `.easm` implementation |
| `model/`                 | High level models for the chess engine, written in Python to test tiny chess algorithms |

We then run `chessvm.e` on an [ENIAC simulator](https://www.github.com/jeredw/eniacsim).
