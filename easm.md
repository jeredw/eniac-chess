# Programming the ENIAC with EASM
This project began with Briain Stuart's pulse-level [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html) which we forked and [further developed](https://github.com/jeredw/eniacsim). Although a faithful and full-featured simulation of the ENIAC, the input format is nothing more than a list of patch wires and switch settings. Easm is an assembler that provides named resources, macros, includes, conditionals and more and makes ENIAC programming far easier than it has ever been. This document describes how easm works, and how it was used to build chessvm.

# What is the ENIAC?
The rest of this document assumes some familiarity with ENIAC's hardware and basic programming theory. For an introduction, see Stuart's series of articles:
 - [Simulating the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - [Programming the ENAIC](https://ieeexplore.ieee.org/document/8467000)
 - [Debugging the ENIAC](https://ieeexplore.ieee.org/document/8540483)

Or perhaps watch [his talk](https://www.youtube.com/watch?v=u5WYj11cJrY). 

We also recommend the excellent book [ENIAC In Action](https://eniacinaction.com/) by Crispin Rope and Thomas Haigh, who have also published all kinds of fascinating original ENIAC documents.

# A Word on Words
The world of ENIAC programming, and the surviving technical documentation, is full of words that meant somewhat different things at the dawn of computing. An ENIAC "program" is a single action on one of the functional units (accumulators, function tables, etc.) that can be triggered by a pulse. A "program line" was a physical wire that triggered a particular program on a particular unit.

What we might consider a "program" today, that is, the sequence of operations to accomplish something, was wired with patch cables (program lines and data trunks) that set the sequence of functional unit program activations, the parameters of each, and the dataflow. We'll use "patch" to refer to the complete set of wires and switch settings, which at the time they called a "setup."  A "patch" is what is in the `.e` file that the simulator loads.

# Hello EASM
In [`vm-dev/print-naturals.e`](vm-dev/print-naturals.e) is the Hello World of ENIAC programming. It cycles a pulse forever between two units, the printer and an accumulator.
```
# initiating pulse to program line 1-1
p i.io 1-1

# 1-1: print accumulator 13
p 1-1 i.pi        # print!
s pr.3 P          # prints low half of acc 13 
p i.po 1-2        # go to 1-2

# 1-2: increment accumulator 13
# Receive but don't connect anything to the input. Set cc switch to C for an extra +1
p 1-2 a13.5i      # use program 5 because 1-4 don't have outputs 
s a13.op5 a       # recieve on null input a
s a13.cc5 C       # add +1
p a13.5o 1-1      # back to 1-1


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

p {p-print} i.pi         # print!
s pr.3 P                 # prints low half of acc 13 
p i.po {p-inc}           # go to increment

p {p-inc} a13.{t-inc}i   # take any available transciever
s a13.op{t-inc} a        # recieve on null input a
s a13.cc{t-inc} C        # add +1
p a13.{t-inc}o {p-print} # go back to print

# go
b i
g
```

Easm variables are always of the form `{[type]-[name]}`, and on first use they try to allocate a free resource of that type. This program uses named program lines `{p-print}` and `{p-inc}` and a named transciever program on accumulator 13 called `{t-inc}`. A transciever program is a program that has an output jack, so it can trigger something else when it's done.

This can be assembled into a runnable patch by `python easm/easm.py vm-dev/print-naturals-2.easm print-naturals-2.e`.

# Moving data around
Suppose we want to start counting at a different number. There are many ways to do this, including the way you use when you're debugging and you just want to set the machine state:
```
set a13 56  # start at 56
```
If you were actually running the machine you could feed it a punched card, set function table switches, or use the constant transmitter, which is what we do here.

```
p i.io {p-init}

# send 11 from constant transmitter
p {p-init} c.26i # 26 is the first program that can send a constant (as opposed to card contents)
s c.s26 Jlr      # send left and right 5 digit halves of J switches
s c.j2 5   
s c.j1 6
p c.o {d-main}   # put output on main data bus

# add number on main data bus
p {p-init} a13.{t-init}i
p {d-main} a13.{i-main}
s a13.op{t-init} {i-main}
p a13.{t-init}i {p-print}

```
This is the first use of what they called a data trunk and we'd call a data bus, allocated as `{d-main}`. The output of the constant transmitter is connected to this bus and thence to the `{i-main}` input on the accumulator, of which five are available, and the operation is set to add from that input. Both units are triggered on the same initial cycle, and the accumulator enters the {p-print} loop as before once initialized. The full program is [here](vm-dev/transfer.easm).

This is a lot of code to move a number from one place to another, so chessvm is mostly written using a set of macros. The fundamental operations are send and receive. 
```
defmacro send inpr acc program AorS outpr
  p $inpr $acc.$programi
  s $acc.op$program $AorS
  p $acc.$programo $outpr
endmacro

# receive on given input and do not (X) emit an output program pulse
defmacro recx inpr acc program input 
  p $inpr $acc.$programi
  s $acc.op$program $input
endmacro

# Connect src's A output and one of dst's inputs to main bus
p {a-src} {d-main}
p {d-main} {a-dst}.{i-main}

# add Alice into Bob
$send {p-xfer} {a-src} {t-xfer} A {p-next}
$recx {p-xfer} {a-dst} {r-xfer} {i-main}

```
Much shorter: one line to send from `{a-src}` and one line to receive and add at `{a-dst}`. Note that it's still necessary to connect the data bus to outputs and input. The macros in chessvm are designed this way to separate datapath wiring from program step sequencing. Also, only one of these accumulators needs to trigger the next program step. This is why the send uses a transciever `{t-xfer}` while the recx needs only a recieiver `{r-xfer}`. Chessvm uses macros which end in x to denote that an output pulse is not transmitted, hence `recx` vs `rec`, and `sendx` also exists.




# Conditional Branching
There are several ways to conditionally route a pulse based on data in an accumulator, which is how conditional branching is accomplished in the ENIAC's chained program pulse scheme. This was understood at the time and there are several ways of doing it, including multi-way selection and constant size loops using the master programmer unit. We're going to use the sign of an accumulator to implement a simple branch, a technique documented in Goldstine IV-28.

The idea is that we trigger an accumulator to send on both the uncomplemented A (add) output and the complemented S (subtract) output at the same time, and then use the sign wires of both outputs to trigger one of two programs. 
```
p {p-conditional} {a-disc}.{r-disc}i
s {a-disc}.op{r-disc} AS  # send on both outputs

# select sign digit of each output with an adapter and route to program lines
p {a-disc}.S ad.dp.{ad-disc-S}.11
p ad.dp.{ad-disc-S}.11 {p-positive-dummy}

p {a-disc}.A ad.dp.{ad-disc-A}.11
p ad.dp.{ad-disc-A}.11 {p-negative-dummy}
```

Note digit data lines are being routed to program triggers. This is sort of a type error, and indeed there's a timing problem. We have to resynchronize to the master cycle by triggering a "dummy" program, set to no-op, and then trigger the next actions on the dummy outputs.
```
p {p-positive-dummy} {a-dummy}.{t-pos}i
s {a-dummy}.op{t-pos} 0
p {a-dummy}.{t-pos}o {p-positive-branch}

p {p-negative-dummy} {a-dummy}.{t-neg}i
s {a-dummy}.op{t-neg} 0
p {a-dummy}.{t-neg}o {p-negative-branch}
```



