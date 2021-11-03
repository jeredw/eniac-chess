# Programming the ENIAC with EASM
This project began with Briain Stuart's pulse-level [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html). Although a faithful and full-featured simulation of the ENIAC, the input format is nothing more than a list of patch wires and switch settings. Easm is an assembler that provides named resources, macros, includes, conditionals and more and makes ENIAC programming far easier than it has ever been. This document describes how easm works, and how it was used to build chessvm.

# What is the ENIAC?
The rest of this document assumes familiarity with ENIAC's hardware and basic programming theory. That's not a trivial thing! For an introduction, see Stuart's series of articles:
 - [Simulating the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - [Programming the ENAIC](https://ieeexplore.ieee.org/document/8467000)
 - [Debugging the ENIAC](https://ieeexplore.ieee.org/document/8540483)

Or perhaps watch [his talk](https://www.youtube.com/watch?v=u5WYj11cJrY). 

We also recommend the excellent book [ENIAC In Action](https://eniacinaction.com/) by Crispin Rope and Thomas Haigh, who have also published all kinds of fascinating original ENIAC documents.

# 