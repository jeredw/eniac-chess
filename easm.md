# Programming the ENIAC with EASM
This project began with Briain Stuart's pulse-level [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html). Although a faithful and full-featured simulation of the ENIAC, the input format is nothing more than a list of patch wires and switch settings. Easm is an assembler that provides named resources, macros, includes, conditionals and more and makes ENIAC programming far easier than it has ever been. This document describes how easm works, and how it was used to build chessvm.

# What is the ENIAC?
The rest of this document assumes familiarity with ENIAC's hardware and basic programming theory. That's not a trivial thing! For an introduction, see Stuart's series of articles:
 - [Simulating the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - [Programming the ENAIC](https://ieeexplore.ieee.org/document/8467000)
 - [Debugging the ENIAC](https://ieeexplore.ieee.org/document/8540483)

Or perhaps watch [his talk](https://www.youtube.com/watch?v=u5WYj11cJrY). 

We also recommend the excellent book [ENIAC In Action](https://eniacinaction.com/) by Crispin Rope and Thomas Haigh, who have also published all kinds of fascinating original ENIAC documents.

# A Word on Words
The world of ENIAC programming, and the surviving technical documentation, is full of words that meant somewhat different things at the dawn of computing. An ENIAC "program" is a single action on one of the functional units (accumulators, function tables, etc.) that can be triggered by a pulse. A "program line" was a physical wire that triggered a particular program on a particular unit.

What we might consider a "program" today, that is, the sequence of operations to accomplish something, was wired with patch cables (program lines and data trunks) that set the sequence of functional unit program activations, the parameters of each, and the dataflow. We'll use "patch" to refer to the complete set of wires and switch settings, which at the time they called a "setup."  A "patch" is what is in the `.e` file that the simulator loads.

# EASM Introduction: Naming Things
In [`vm-dev/print-naturals.e`](vm-dev/print-naturals.e) is the Hello World of ENIAC programming. It cycles a pulse forever between two units, the printer and an accumulator.
```
# initiating pulse to program line 1-1
p i.io 1-1

# 1-1: print accumulator 13
p 1-1 i.pi    # print!
s pr.3 P      # prints low half of acc 13 
p i.po 1-2    # go to 1-2

# 1-2: increment accumulator 13
# Receive but don't connect anything to the input. Set cc switch to C for an extra +1
p 1-2 a13.5i  # use program 5 because 1-4 don't have outputs 
s a13.op5 a   # recieve on input a
s a13.cc5 C   # add +1
p a13.5o 1-1  # back to 1-1


# press the start button and start the sim
b i
g
```
If you have eniacsim installed, you can run this like so and watch it use up cards
```
% ./eniacsim vm-dev/print-naturals.e
          00000                                                                 
          00001                                                                 
          00002                                                                 
          00003                                                                 
          00004                                                                 
          00005                                                                                       
```

Scintilating stuff. This patch works as follows: The initiating pulse goes to program line 1-1, which is wired to the printer program input. The printer switches are set to punch only the lower half of accumulator 13, punching the first five digits of an 80 digit punch card. The printer program output goes to program line 1-2, which is connected to program input 5 of accumulator 13. That program is set by switches to increment, and the output pulse is wired back to program line 1-1. 

This sort of thing gets very tedious very quickly with larger ENIAC programs. It would help to be able to label things and have the computer keep track of the underlying resource assignments. This is [`vm-dev/print-naturals-2.easm`](vm-dev/print-naturals.easm)
```
# print integers, let easm take care of things

p i.io {p-print}

p {p-print} i.pi   	# print!
s pr.3 P      		# prints low half of acc 13 
p i.po {p-inc}    	# go to increment

p {p-inc} a13.{t-inc}i 		# take any available transciever
s a13.op{t-inc} a   		# recieve on input a
s a13.cc{t-inc} C   		# add +1
p a13.{t-inc}o {p-print}    # go back to print

# go
b i
g
```

Easm variables are always of the form `{[type]-[name]}`, and on first use they try to allocate a free resource of that type. This program uses named program lines `{p-print}` and `{p-inc}` and a named transciever program on accumulator 13 called `{t-inc}`. A transciever program is a program that has an output jack, so it can trigger something else when it's done.

This can be assembled into a runnable patch by `python easm/easm.py vm-dev/print-naturals-2.easm print-naturals-2.e`.

