# ENIAC chess playing program

This repository contains a chess playing program and associated tools for the
historic ENIAC computer.

## Background

ENIAC was not originally a stored program computer.  Instead, it was a bunch
of function units that could be wired together with patch cables.  People
later figured out how to rig it up as a stored program computer.  To make ENIAC
play chess, we write a search program targetting a VM, and then wire up
ENIAC to implement that VM.

Doing this involves multiple layers of tools and cross-validation.

- ENIAC simulator
- ENIAC patch settings
- VM simulator
- VM assembler
- Chess program
- Chess program model

## Contents

| File         | Description                                     |
| ------------ | ----------------------------------------------- |
| `Makefile`   | `make` to build everything, `make test` to test |
| `chasm.py`   | Assembler for the chess VM                      |
| `chsim.cc`   | Simulator for the chess VM                      |
| `model/`     | High level model for chess engine               |

# Playing with SCID

`model/uci_driver.py` communicates between UCI-compatible Chess software like
[SCID vs Mac](http://scidvspc.sourceforge.net/#toc3) and engines wrapped by the
`uciengine.UCIEngine` class.  To configure SCID, go to Tools > Analysis Engines
and press New.  Then set Command to `/usr/local/bin/python3`, Directory to
`/.../eniac-chess/model`, and parameters to `uci_driver.py`.  (In the future,
different engines will be selectable by command-line arguments.)

To play games directly in SCID, select Play > Computer - UCI Engine.  No UCI
options are supported yet, so best to uncheck most everything.
