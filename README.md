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
| `test.asm`   | Assembler test program                          |
| `chsim.cc`   | Simulator for the chess VM                      |
| `chester.py` | High level model for chess program              |
