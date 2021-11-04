# Programming an ENIAC virtual machine
This is how we wrote a chess program for the ENIAC, the first general purpose electronic digital computer. The ENIAC is an ancient, strange, and very limited machine, so it's surprising to many people that it could have played a decent game of chess. The core of the problem was to wire up the ENIAC so that it emulates a tiny modern CPU, by extending ideas originally developed in the 1940s. This required a new kind of programming language, something like an ENIAC patch assembler. This document describes how we used that tool to create a capable virtual machine on a 1940s computer.

# Contents
  - [What is the problem?](#what-is-the-problem)
    - [ENIAC References](#eniac-references)
  - [Coding the Eniac](#coding-the-eniac)
    - [The accumulator](#the-accumulator)
    - [Hello punch cards](#hello-punch-cards)
    - [Moving data around](#moving-data-around)
    - [Registers, arithmetic, and permutation](#registers-arithmetic-and-permutation)
    - [Conditional branching](#conditional-branching)
  - [Building A Control Cycle](#building-a-control-cycle)
    - [Fetching from the function tables](#fetching-from-the-function-tables)
    - [Instruction decoding](#instruction-decoding)
    - [Bank switching](#bank-switching)
    - [One free accumulator](#one-free-accumulator)
  - [Addressable memory](#addressable-memory)
    - [Addressing accumulators](#addressing-accumulators)
    - [Addressing words](#addressing-words)
  - [Making it all fit](#making-it-all-fit)
    - [Subprograms](#subprograms)
    - [Dummy program allocation](#dummy-program-allocation)

  
# What is the problem?
ENIAC was less like a modern computer and more like a warehouse full of parts designed to be patched together with cables. It was roughly equivalent to a box of old-fashioned discrete logic chips: counters, registers, adders, and so on. The idea of having a computer execute instructions in sequence from an addessable memory was developed by the ENIAC designers and John von Nuemann during the course of building the machine, but that's not what they got when ENIAC become operational in February 1946. 

To execute the [first monte-carlo simulation](https://eniacinaction.com/the-articles/3-los-alamos-bets-on-eniac-nuclear-monte-carlo-simulations-1947-8/) of a nuclear core, ENIAC was converted to ["central control"](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/) in 1948, by using its voluminous numerical function table lookup space to store instruction codes instead. Essentially, they wired the box of parts into the very first CPU. ENIAC stayed wired this way until it was decommissioned in 1956.

But that CPU was not suitable for playing chess. It kept the hardware organization of 10 digit words, there were only 15 words available, and this memory was not indexable. We wanted to show that it was possible to wire up the ENIAC into a much more capable computer. The result is a patch-level setup for the ENIAC that gives the machine two digit words, five registers, and 75 words of linear memory, along with 1600 words of program storage. The full architecture is documented [here](isa.md). This is enough to implement 4-ply alpha-beta search and beat (some) humans at chess. In the sense that all the required hardware was actually built, this could have been implemented in 1946. 

## ENIAC References
This document is a gentle introduction to parts of the ENIAC hardware and programming model, but to do any real programming you'll need greater familiarity with ENIAC's hardware and programming theory. 

ENIAC Chess began with Briain Stuart's pulse-level [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html) which we forked and [further developed](https://github.com/jeredw/eniacsim). He also wrote a great series of introductory ENIAC articles:
 - [Simulating the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - [Programming the ENAIC](https://ieeexplore.ieee.org/document/8467000)
 - [Debugging the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - Or perhaps watch [his talk](https://www.youtube.com/watch?v=u5WYj11cJrY). 
 - eniacsim [commands](https://www.cs.drexel.edu/~bls96/eniac/cmd.pdf) and [patch file](https://www.cs.drexel.edu/~bls96/eniac/ref.pdf) reference.

We also recommend the excellent book [ENIAC In Action](https://eniacinaction.com/) by Crispin Rope and Thomas Haigh, who have also published all kinds of fascinating original ENIAC [documents](https://eniacinaction.com/the-book/supporting-technical-materials/).

# Coding the ENIAC

## The Accumulator
ENIAC is a series of refrigerator-sized units with different functions. The unit we'll use most for programming is the accumulator, a device that holds ten digits plus a sign. It's basically a vaccuum tube version of a [mechanical adding machine accumulator](https://hackaday.com/2018/05/01/inside-mechanical-calculators/). The accumulator is both memory and arithmetic, and its basic function is to add a number recieved on one of its inputs alpha through epsilon (hence a, b, g, d, e). It can also send the stored number in its A (add) output, or its 10's complement on the S (subtract) output. The details are somewhat baroque, but you can think of it abstractly like this:
```
              Outputs
 
              A    S
              │    │
    ┌─────────┴────┴──────────┐
    │      PM DDDDDDDDDD      │     One sign (PM) plus ten digits
    └──┬────┬────┬────┬────┬──┘
       │    │    │    │    │
       a    b    g    d    e
        
              Inputs

```
PM is short for "plus minus" and is essentially a sign bit. The accumulator is triggered by a pulse on a cable jacked into one of 12 "program controls". Each of these has switches that control the operation executed when that "program" is executed. If X is the value in the accumulator, the available operations are
| Operation  | Description |
| - | - |
| X += a,b,g,d,e      | Add |
| X += a,b,g,d,e + 1  | Add and increment |
| X->A              | Output |
| -X->S               | Output complement
| X->A, -X->S          | Output both |
| X=0                 | Clear |
| X->A, X=0           | Output and clear |
| -X->S, X=0          | Output complement and clear |
| X->A, -X->S, X=0     | Output both and clear |

The accumulator is the backbone of the machine, and is simultaneously memory and arithmetic. There are 20 accumulators in the ENIAC, for a total writable memory of 200 digits. This is the only writable memory in the machine. The resources available on each accumulator are limited in several ways: there are only five different inputs, only one uncomplemented and one complemented output, and most of all only 12 program inputs, meaning that without more advanced sequencing techniques each accumulator can be used for at most 12 differet program steps.

To describe the contents of an accumulator (or its value on a data bus) we follow the original sign notation of P or M followed by ten digits, in 10's complement form. Hence P0000000005 is 5 and M9999999995 is -5. To negate a value in 10's complement, take the 9's complement of each digit (subtract from 9) and then add 1. When sending the PM digit, a P is transmitted as a 0 while an M is transmitted as a 9.

The world of ENIAC programming, and the surviving technical documentation, is full of words that meant somewhat different things at the dawn of computing. An ENIAC "program" is a single action on one of the functional units (accumulators, function tables, etc.) that can be triggered by a pulse. A "program line" was a physical wire that triggered a particular program on a particular unit.

What we might consider a "program" today, that is, the sequence of operations to accomplish something, was wired with patch cables (program lines and data trunks) that set the sequence of functional unit program activations, the parameters of each, and the dataflow. We'll use "patch" to refer to the complete set of wires and switch settings, which at the time they called a "setup."  A "patch" is what is in the `.e` file that the simulator loads.

## Hello punch cards
In [`vm-dev/print-naturals.e`](vm-dev/print-naturals.e) is the Hello World of ENIAC programming. It cycles a pulse forever between two units, the printer and an accumulator. It's written in eniacsim patch format, which is defined [here](https://www.cs.drexel.edu/~bls96/eniac/ref.pdf).
```
# initiating pulse to program line 1-1
p i.io 1-1

# 1-1: print accumulator 13
p 1-1 i.pi        # trigger printer by connecting program line 1-1 to printer program input
s pr.3 P          # prints low half of acc 13 
p i.po 1-2        # go to 1-2

# 1-2: increment accumulator 13
# Receive but don't connect anything to the input. Set cc switch to C for an extra +1
p 1-2 a13.5i      # connect program line to program input, use program 5 because 1-4 don't have outputs 
s a13.op5 a       # recieve on input a (no connection, hence zero)
s a13.cc5 C       # add +1
p a13.5o 1-1      # back to 1-1


# press the start button and start the sim
b i
g
```
If you have eniacsim installed, you can run this like so and watch it use up cards
```
% eniacsim vm-dev/print-naturals.e
          00000                                                                 
          00001                                                                 
          00002                                                                 
          00003                                                                 
          00004                                                                 
          00005                                                                                       
```

Scintilating stuff. This patch works as follows: The initiating pulse goes to program line 1-1, which is wired to the printer program input. The printer switches are set to punch only the lower half of accumulator 13, punching the second five digits of an 80 digit punch card. The printer program output goes to program line 1-2, which is connected to program input 5 of accumulator 13. That program is set by switches to increment, and the output pulse is wired back to program line 1-1. 

This sort of thing gets very tedious very quickly with larger ENIAC programs. It would help to be able to label things and have the computer keep track of the underlying resource assignments. This is [`vm-dev/print-naturals-2.easm`](vm-dev/print-naturals.easm)
```
# print integers, let easm take care of things

p i.io {p-print}

p {p-print} i.pi         # trigger printer by connecting program line 1-1 to printer program input
s pr.3 P                 # prints low half of acc 13 
p i.po {p-inc}           # go to increment

p {p-inc} a13.{t-inc}i   # connect program line to program input, use any available transciever
s a13.op{t-inc} a        # recieve on input a (no connection, hence zero)
s a13.cc{t-inc} C        # add +1
p a13.{t-inc}o {p-print} # go back to print

# go
b i
g
```

Easm variables are always of the form `{[type]-[name]}`, and on first use they try to allocate a free resource of that type. This program uses named program lines `{p-print}` and `{p-inc}` and a named transciever program on accumulator 13 called `{t-inc}`. A transciever program is an accumulator program that has an output jack, so it can trigger something else when it's done.

This file can be assembled into a runnable patch by `python easm/easm.py vm-dev/print-naturals-2.easm print-naturals-2.e`.

## Moving data around
Suppose we want to start counting at a different number. There are many ways to do this, including the way you use when you're debugging and you just want to set the machine state:
```
set a13 56  # start at 56
```
If you were actually running the machine you could feed it a punched card, set function table switches, or use the constant transmitter, which is what we do here.

```
p i.io {p-init}

# send 56 from constant transmitter
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
This is the first use of what they called a data trunk and we'd call a data bus, allocated as `{d-main}`. This is actually a collection of 11 individual wires, each of which transmits one digit (plus the PM digit, the sign) in base one. That is, a six is represented by six pulses. This is how telephone equipment worked at the time, so it was familiar to the designers who based the ENIAC heavily on pre-existing mechanical calculators and electro-mechanical phone switches.

The output of the constant transmitter is connected to this main bus and thence to the `{i-main}` input on the accumulator, of which five are available, and the operation is set to add from that input. Both units are triggered on the same initial cycle, and the accumulator enters the {p-print} loop as before once initialized. The full program is [here](vm-dev/transfer.easm).

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

# add src to dst
$send {p-xfer} {a-src} {t-xfer} A {p-next}
$recx {p-xfer} {a-dst} {r-xfer} {i-main}

```
Much shorter: one line to send from `{a-src}` and one line to receive and add at `{a-dst}`. Note that it's still necessary to connect the data bus to outputs and input. The macros in chessvm are designed this way to separate datapath wiring from program step sequencing. Also, only one of these accumulators needs to trigger the next program step. This is why the send uses a transciever `{t-xfer}` while the recx needs only a recieiver `{r-xfer}`. Chessvm uses macros which end in x to denote that an output pulse is not transmitted, hence `recx` vs `rec`, and `sendx` also exists.

## Registers, arithmetic, and permutation
The original [instruction sets](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/) for the ENIAC were all based on moving 10 digit numbers around, because the ENIAC was primarily used for scientific computation. But there are only 20 accumulators, so after allocating a few to machine functions like the program counter and instruction register, this meant there was room for a dozen or so variables. Chessvm uses two digit words instead, making the ENIAC into a 100 word machine. The main [register file](isa.md) is one accumulator broken down into five two-digit registers A-E, plus the PM digit used as an overflow flag N.
```
┌────────────────────┐
│  N AA BB CC DD EE  │
└────────────────────┘
```

This arrangement is carefully chosen so that the A register and overflows to the N bit, which is actually the accumulator PM digit. This makes it easy to implement INC A. To do this, we put P0100000000 on the main bus using the constant transmitter and receive (add) on the register file. 
```
# Implementation of INC A. Triggered by {p-op-inc}.

# define $rec
include macros.easm  

# Wire main bus into RF input
p {d-main} {a-rf}.{i-main}

# send P0100000000 from constant transmitter
p {p-op-inc} c.26i 
s c.s26 Jlr          # send left and right 5 digit halves of J switches
s c.j9 1             # all other digits are 0
p c.o {d-main}       # put output on main data bus

# recieve into register file, which is really an add, then go to {p-next}
$rec {p-op-inc} {a-rf} {t-inc} {i-main} {p-next}
```
Notice the use of the `include` directive to define the macros. The [chessvm macros](chessvm/macros.easm) define an ENIAC programming language on top of the resource allocation provided by easm, including all of the macros in this tutorial. For brevity, we'll omit the `include` statement in subsequent examples.

INC is one of the only operations that can work in place, and in general operating on two digit words reqiures constant packing and unpacking. The ENIAC hardware included adapters that shifted, deleted, or selected digits from a data cable (Goldstine XI-3) and eniacsim supports these as well. However, contemporary documents (such as Goldstines's [1947 plan for a control cycle](https://eniacinaction.com/docs/CentralControlforENIAC1947.pdf)) show that ENIAC staff also built custom cables to implement particular patches. Our update to eniacsim supports arbitrary permutation of the digit lines (1-10) and the sign line (11). We can use this to implement SWAP A,B.
```
# SWAP A,B
# Trigger the operation with {p-op-swapab}. Assumes {a-rf} is the register file and {a-tmp} starts empty.

# Use a permutation adapter between data bus {d-main} and {a-tmp}.{i-swapab} input to effect the swap
p {d-main} ad.permute.{ad-swapab}
s ad.permute.{ad-swapab} 11,8,7,10,9,6,5,4,3,2,1    # switch A and B digits, keep all else unchanged
p ad.permute.{ad-swapab} {a-tmp}.{i-swapab}

# Wire main bus unpermuted into RF input
p {d-main} {a-rf}.{i-main}

# Step 1: RF -swapAB-> TMP, clear 
$sendc {p-op-swapab} {a-rf}  {t-swapab} A {p-op-swapab-2}   # sendc = send and clear
$recx  {p-op-swapab} {a-tmp} {r-swapab} {i-swapab} 

# Step 2: TMP -> RF, clear 
$sendc {p-op-swapab-2} {a-tmp} {t-swapab-2} A {p-next}   # sendc = send and clear
$recx  {p-op-swapab-2} {a-rf} {r-swapab-2} {i-main}
```
Aside from permutation adapters, this example introduces a few new ideas. Note use of the `sendc` macro which clears the accumulator after sending. Because accumulators cannot copy, only add, ENIAC programming involves a lot of moving data from one accumulator to another, via a permutation adapter, whilst clearing the source. To make life a little more bearable chessvm defines a `permute` macro:
```
defmacro permute in permutation out
  p $in ad.permute.{ad-%name}
  s ad.permute.{ad-%name} $permutation
  p ad.permute.{ad-%name} $out
endmacro

# swapab wiring can then be implemented like so
$permute {d-main} 11,8,7,10,9,6,5,4,3,2,1 {a-tmp}.{i-swapab}
```
Note the use of `%` to create a named temporary variable that is visible only inside the macro.

Finally, this example introduces the register transfer notation X -> Y which is used extensively in chessvm comments, and as the microcode notation in the [instruction set reference](isa.md). Here's how it works:

| Notation | Meaning |
| - | - |
| X -> Y | send from X, rec on Y |
| X -input-> Y | send X, rec Y on given input |
| X -S-> Y | send X on S output (complemented) |
| X -S-input-> Y | send X complemented to given input |

In most cases "clear X after sending" is implied.


## Conditional branching
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
All of this is nicely packaged up into a `$discriminate` macro. There's also `discriminatec` to additionally clear the accumulator, which we use to write a loop with a number of iterations set by another accumulator. This is [`looptest.easm`](vm-dev/looptest.easm)
```
# Illustrate conditional branching using discrimination, to count to 10
include ../chessvm/macros.easm

set a1 10       # loop limit 

# Tell easm to bind symbols to physical accumulators
# We don't need {a-test} here because it can go anywhere
{a-limit} = a1  
{a-count} = a13 # counter on a13 so we can print

# LIMIT and COUNT write to main bus, TEST reads from it.
p {a-limit}.A {d-main}
p {a-count}.S {d-main}
p {d-main} {a-test}.{i-main}

p i.io {p-print}

# print low half of COUNT
p {p-print} i.pi
s pr.3 P
p i.po {p-inc}

# increment via recinc from a disconnected input
$recinc {p-inc} {a-count} {t-inc} {i-no-connection} {p-test-1}

# first step of test: LIMIT -> TEST
$send {p-test-1} {a-limit} {t-test-1} A {p-test-2}
$recx {p-test-1} {a-test} {r-test-1} {i-main}

# subtract count: COUNT -S-> TEST
$send {p-test-2} {a-count} {t-test-1} S {p-test-3}
$recx {p-test-2} {a-test} {r-test-2} {i-main}

# test is now negative if we should stop. Discriminate with positive output looping
$discriminatec {p-test-3} {a-test} {a-test}.A {a-test}.S {p-print} {p-exit}

# {p-exit} is not connected, so the program halts when COUNT > LIMIT

# allocate the dummies for $discriminatec
insert-deferred

# go
b i
g
```
There are two new easm features in this program. First we bind `{a-limit}` to `a1` in order to make the `set` statement work, and we bind `{a-count}` to `a13` so our count variable can be conveniently printed. Second, the real `discriminatec` macro uses allocated dummies, meaning that it looks for free transcivers rather than trying to put all dummies on accumulator {a-dummy} as we wrote above. The `insert-deferred` statement tells easm that all other accumulator programs have been allocated, so whatever is left can be used. We'll discuss dummy allocation much more, below.

It would be nice to use an accumulator just for discrimination as we do here, but we badly need the space. It's possible to store data in the accumulator when it's not currently being used for discrimination, with one important caveat: that accumulator must never send from the A output when the value is negative, or send from the S output when the value is positive. Otherwise, one or the other of the branch program lines would be triggered.

# Building a control cycle
To turn ENIAC into a modern computer we need to use these methods to implement a fetch-decode-execute cycle. This was done in 1948 when ENIAC was converted to  ["central control"](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/). Chessvm was inspired by asking if we could create a more modern, microprocessor-like machine out of ENIAC. The first instruction set, implemented in April 1948, had 79 instructions and used a newly-built decoder unit that was designed to route a pulse to one of 100 outputs, based on a two digit opcode. We wanted to implement our machine on stock ENIAC hardware, which we defined as the units available when ENIAC was first [declared operational](https://www.techrxiv.org/articles/preprint/Reconstructing_the_Unveiling_Demonstration_of_the_ENIAC/14538117) in February 1946, and discussed in more detail in Adele Goldstine's Eniac Technical Manual.

As it turns out, Goldstine had documented a design for a 51 opcode instruction set (then called "a 51 order code") in [1947 notes](https://eniacinaction.com/docs/CentralControlforENIAC1947.pdf), recently exhumed and transcribed by Mark Priestley and Thomas Haigh. This document provided the basic ideas behind chessvm's central architecture. Many of the hardest problems in chessvm were solved 70 years ago.

The core machine uses five accumulators:

| Name | Purpose | Layout | Notes |
| - | - | - | - |
| PC | Program counter      | SS RRRR PPPP | PPPP=program counter, RRRR=return adddres, SS used in decode |
| IR | Instruction register | I5 I4 I3 I2 I1 | I1 is the next opcode |
| EX | Execution register   | I1 XX XX XX XX | Holds next opcode during decode, zero when execution starts |
| RF | Register File        | AA BB CC DD EE | Main registers |
| LS | Aux register file    | FF GG HH II JJ | LS=load/store, holds last accessed accumulator contents |

At a high level, the control cycle operates as follows:

| Step | Action |
| - | - | 
| 1. | If IR is negative (PM=M) fetch function table row PPPP into the IR and add 1 to PPPP |
| 2. | Copy I1 into EX |
| 3. | Shift IR to the right by two digits, and set the upper two digits (now empty) to 99 |
| 4. | Decode I1, meaning trigger one of 51 program lines based on the contents of EX |
| 5. | (instruction executes here) |
| 6. | Add 1 to IR. If there are no more instructions, IR will be P9999999999 and will overflow to M0 |
| 7. | Goto 1 |

This is roughly, but not really, a description of the actual machine cycles involved in fetching and decoding instructions. For the real thing, see the [ISA reference](isa.md).

Making this work requires several steps: fetching from the function tables, decoding an instruction, and managing the program counter.

## Fetching from the function tables
The function tables are the ENIAC's ROM. They were originally built in anticipation of storing lookup tables such as sine and cosine, and are even indexed from -2 to 101 to support quadaratic interpolation with boundary conditions. But they became the key to running ENIAC as a modern CPU. All of the original "order codes" use two digit opcodes, and so does chessvm. With three tables, each with 104 rows of 12 digits, that's 3,744 digits or at most 1,872 instructions. A machine that was never designed to be programmed with opcodes was suddenly discovered to have expansive ROM space. More than any other feature of the ENIAC, this is what makes chess possible.

You can think of each function table as a map from a two digit argument to a 12 digit row.

We can modify our simple incrementing accumulator program to read and print succesive lines from the function table. 
```
# Fetch and print successive rows from function table 1
include ../chessvm/macros.easm

p i.io {p-fetch}

# put our "instruction register" somewhere easily printable
{a-ir} = a13

# Connections to main bus
p {a-count}.A {d-main}
p {d-main} {a-ir}.{i-main}
p {d-main} f1.arg

# Each of two f1 outputs is six digits. Combine the bottom 10 of 12 digits into one bus.
$permute f1.A 0,4,3,2,1,0,0,0,0,0,0 {d-main}
p f1.B {d-main}

# 1. Tell the FT we are going to look up a value
p {p-fetch} f1.{t-fetch}i
s f1.cl{t-fetch} C    		# send pulse on C when ready for argument
p f1.C {p-arg}
s f1.op{t-fetch} A0   		# don't offset argument 

# 2. When the FT is ready for its argument, send from {a-count}
$send {p-arg} {a-count} {t-arg} A {p-wait}

# 3. While we are waiting for result, clear {a-ir} and increment {a-count}
$clear {p-wait} {a-ir} {t-clear} {p-readrow}
$recincx {p-wait} {a-count} {r-inc} {i-no-connection} 

# 3-4. We need to wait two cycles, so repeat the clear twice total. This delays {p-readrow}.
s {a-ir}.rp{t-clear} 2

# 5. Read FT output
$rec {p-readrow} {a-ir} {t-readrow} {i-main} {p-print}

# 6. print all ten digits of a13 and loop
p {p-print} i.pi
s pr.2 P
s pr.3 P
p i.po {p-fetch}

# Set switches for a few rows of test data to read
[omitted]
```
The function table is a little weird in terms of timing. It must be triggered on the first cycle with a program pulse, given its argument on the second cycle, and then the result is available on the fifth cycle. We use the `f1.C` output to send the argument, and harmlessly clear the IR twice to delay for two cycles after sending the argument, but there are a variety of ways to accomplish this (typically using dummies). 

This example also shows the weird data format of the function table: each row is two six digit halves called A and B, each of which has its own output. Here, we combine A and B into one ten digit accumulator by dropping the leftmost two digits using a permuter. That's fine for this case, but in the real control cycle we store instructions I6...I2 in IR, and put the top two digits I1 -- the first instruction on the row to be exected -- into EX. There's logic in the control cycle to handle consuming an opcode from EX or from IR depending on whether or not we just fetched. This pattern was borrowed from the 1947 design.

This layout also means that the program counter cannot point to any instruction that's not at the beginning of a row. All jump locations have to be row-aligned. Also, two and three word instructions (those with immediate data or addresses) cannot cross a row. Unused words in each row could be filled with NOP instructions, but if they are filled with 99 instead, which we call SLED, then the control cycle immediately fetches a new row without trying to decode the empty words.


## Instruction decoding
By "decode" we mean trigger one of 51 different program lines based on an opcode in an accumulator. By 1948 there was a custom hardware unit that integrated the instruction register (including shifts to consume opcodes) and the decoder. But the stock ENIAC had nothing like this, which makes the 1947 design using the master programmer unit particularly ingenious.

The master programmer is anything but. Originally designed for nested loops with constant bounds, it was imagined that this unit would drive most of the sequencing for  ENIAC. This was plausible when it was thought that the primary use would calculating trajectory tables -- the "I" in ENIAC stands for "integrator," after all. Also, this was 1943 and no one yet knew anything about how best to sequence the operation of a digital computer. You can think of the master programmer as ten stepper units, each of which can be abstracted like this:
```
          In    Reset   Step  
           │      │      │
     ┌─────┴──────┴──────┴─────┐
     │     Count register      │
     │     Decade switches     │
     └──┬───┬───┬───┬───┬───┬──┘
        │   │   │   │   │   │
        1   2   3   4   5   6
```
The original idea was that you set the number of iterations N on decade switches (ten position digit swtiches). Then each pulse to the input comes out of the first stepper output while an internal counter increments. After N pulses, the stepper advances, the counter resets, and the next N input pulses will be routed to output 2. The reset input sets the stepper to position 1 again, while the step input manually advances the stepper. This is almost, but not quite, a demultiplexer that switches according to number of pulses to the step input. All we have to do is disable the counter so that it never steps automatically. As it turns out, this was anticipated, and the documentation says you just pull vaccuum tube 63 from the master programmer. Our updated eniacsim supports this directive:
```
# "To disassociate a decade from its stepper pull out gate tube 63 in the stepper plug-in unit.
# See block diagram PX-8-304." - ENIAC Operating Manual, PX-8-301
s p.gate63 unplug
```
With this configuration, it's easy to decode one-of-36 by routing the tens digit to stepper A, and the ones digit to steppers B-G, then connecting the six outputs of stepper A to the inputs of the six steppers B-G.
```
# Simple 36 opcode decoder. Valid opcodes are 00-05, 10-15, ... 50..55. Trigger with {p-decode}

# start by resetting all MP steppers
p {p-decode} p.Acdi
p {p-decode} p.Bcdi
p {p-decode} p.Ccdi
p {p-decode} p.Dcdi
p {p-decode} p.Ecdi
p {p-decode} p.Fcdi
p {p-decode} p.Gcdi

# Wait for clear then send opcode from high two digits of EX
$dummy {p-decode} {p-decode-2}
$send {p-decode-2} {a-ex} {t-decode-2} A {p-decode-3}
p {a-ex}.A {d-main}

# Wire tens digit to A step inputs and ones digit to B-G
p {d-main} ad.dp.{ad-opcode-10}.10   # opcode 10's digit (0x-5x)
p ad.dp.{ad-opcode-10}.10 p.Adi
p {d-main} ad.dp.{ad-opcode-9}.9     # opcode 1's digit (0x-5x)
p ad.dp.{ad-opcode-9}.9 p.Bdi
p ad.dp.{ad-opcode-9}.9 p.Cdi
p ad.dp.{ad-opcode-9}.9 p.Ddi
p ad.dp.{ad-opcode-9}.9 p.Edi
p ad.dp.{ad-opcode-9}.9 p.Fdi
p ad.dp.{ad-opcode-9}.9 p.Gdi

# Route the outputs of A to the inputs of B-G
p p.A1o p.Bi
p p.A2o p.Ci
p p.A3o p.Di
p p.A4o p.Ei
p p.A5o p.Fi
p p.A6o p.Gi

# Finally, send a decode pulse to A
p {p-decode-3} p.Ai

# Opcode program lines are now p.[BCDEFG][123456]o
p p.B1o {p-opcode-00}
p p.B2o {p-opcode-01}
...
p p.G5o {p-opcode-54}
p p.G6o {p-opcode-55}
```
This 36 opcode decoder can be extended to 51 by decoding using 33 outputs as above, then using the last three outputs of stepper G to route a pulse between steppers H,I, and J. That's 33 + 18 = 51 outputs. This requires a little more complexity in the control loop to decide whether to route the tens or the ones digit to stepper G, requiring a conditional branch to discriminate between opcodes <= 55 and >= 55. This entire scheme was in the 1947 design and we adopted it for chessvm, though our version is different in the details.

## Bank switching
The above example showed how to fetch from one function table, but we want to use all three. That's why the program counter PPPP and return address RRRR are four digits each. The low two digits are just the row in the current function table, while the high two digits are known as the "functional table selection group" or FTSG, a 1947 name we kept.

| FTSG | Function Table |
| - | - |
| 09 | 1 |
| 90 | 2 |
| 99 | 3 |

Near addresses are two digits and reference the current function table only. All conditional jumps are near addresses, which saves code space. Far jumps and subroutine call and return use four digit far addresses.

To actually do this ROM bank switching, chessvm routes the fetch initiation pulse (`{p-fetch}` above) to only the currently selected table. This is done by wiring the PM digits of the S outout of three accumulators to program inputs on three different function tables, something like

```
defmacro trigger-ft n 
  $sendx {p-fetch} {a-discft$n} {r-fetch} S
  p {a-discft$n}.S ad.dp.{ad-discft$n}.11
  p ad.dp.{ad-discft$n}.11 f$n.{t-fetch}i
endmacro

$trigger-ft 1
$trigger-ft 2
$trigger-ft 3
```
If only one of these accumulators has a positive sign (P in the PM digit) then only one function table will be triggered. This is similar to how discrimination works, and we can't otherwise use the sign or the S output if we store other data in these accumulators (which we do; this represents 15 words of our VM memory). The FTSG is designed so these program counter digits can be sent to the sign digits of the three accumulators once to select only one bank, then again to clear it.
```
# Set/unset current bank using FTSG of PC, that is, digits 4 and 3. Trigger with {p-selft}
# Starting from all accs PM=P, call once to select bank. Calling twice reverts to all P.

$permute {a-pc}.A 4,0,0,0,0,0,0,0,0,0,0 {d-ftsg1}
$permute {a-pc}.A 3,0,0,0,0,0,0,0,0,0,0 {d-ftsg2}

# Send FTSG digits from PC twice
$sendx {p-selft} {a-pc} {t-selft} A
s {a-pc}.rp{t-selft} 2

# Deselect FT1 if FTSG1 set
p {d-ftsg1} {a-discft1}.{i-ftsg1}
$recx {p-selft} {a-discft1} {t-selft} {i-ftsg1} 

# Deselect FT2 if FTSG2 set
p {d-ftsg2} {a-discft2}.{i-ftsg2}
$recx {p-selft} {a-discft2} {t-selft} {i-ftsg2}

# Deselect FT3 if exactly one of FTSG1, FTSG2 set
p {d-ftsg1} {a-discft3}.{i-ftsg1}
$rec {p-selft} {a-discft3} {t-selft} {i-ftsg1} {p-selft-2}
p {d-ftsg2} {a-discft3}.{i-ftsg2}
$recx {p-selft-2} {a-discft3} {r-selft} {i-ftsg2}
```
We borrowed the 09/90/99 encoding from the 1947 design, but this method of multiplexing function tables is a little cleaner and faster than the original, which triggered multiple FTs on different cycles and then selectively activated receive programs.


## One free accumulator
There are a variety of different accumulator resources needed to implement all of chessvm's [instructions](isa.md). Move and swap operations require inputs which permute the data bus in specific patterns. Each conditional branch at the microcode level (including the control cycle) uses the PM digit outputs of one accumulator. Memory access requires the S outputs of multiple accumulators. 

The EX accumulator is used during the control cycle, but is clear when each instruction starts executing. This leads to a pattern of using EX to store the contents of an accumulator that is needed to perform some function, and restoring from EX before the instruction finishes. For example, `SWAP` needs the permuters on the inputs of MOVSWAP, so its contents are saved and restored through EX.
```
1. MOVSWAP -> EX
2. RF -movswap[BCDE]-> MOVSWAP
3. MOVSWAP -> RF
4. EX -> MOVSWAP
```
For complex instructions like memory access, EX will temporarily hold the contents of several different accumulators over the course of execution.


# Addressable memory
ENIAC had no addressable memory. It had no instruction set either, but even after the crazy hacks to turn it into a stored program computer there were still no instructions that could access a data-dependent location in memory. The instruction sets of the time devoted a considerable number of their limited opcodes to load and store instructions, each hard wired for a specific accumulator. There was simply no way to implement something like a pointer or an array -- you know, like a chessboard.

This had to change. 

## Addressing accumulators
We'll start with whole accumulators since that's easier, and our VM has 15 accumulators addressable through the `loadacc A` and `storeacc A` instructions. The challenge is to decode the value stored in A and use it to trigger one of 15 load program lines or one of 15 store program lines, each on a different accumulator. The master programmer could do this but only if we move hardware over from instruction decoding, which means we'd lose at least 30 (!) of our 51 opcodes. Instead we invented a technique that unlocked the whole project, an extension of the use of PM digit pulses to do conditional branches.

Address decoding is based on two ideas: a 10 entry lookup table which is stored in the first rows of FT3, and using the S outputs of accumulators as program triggers. To decode a single digit, we can:

  1. Send the low digit of A to FT3
  2. Store the result in accumulator `{a-decode}`
  3. Send the contents of `{a-decode}` on the `S` output
  4. Wire the ten digits of the `{a-decode}.S` output to ten different programs

The lookup table has entries which are all 9s except for one digit, like this:
```
row 0: 9999999990
row 1: 9999999909
row 2: 9999999099
row 3: 9999990999
row 4: 9999909999
row 5: 9999099999
row 6: 9990999999
row 7: 9909999999
row 8: 9099999999
row 9: 0999999999
```
When we send this value on the `{a-decode}.S` output, the nine's complement means all digit lines will be zero, except for the selected one. These digit lines can then trigger ten different programs on ten different accumulators. Extending this scheme to 15 accumulators requires only a conditional to distinguish 0-9 from 10-14. The same low-digit lookup happens, but the result is stored to and sent from two different accumulators wired to two different sets of programs. In chessvm these are called `{a-memcyc09}` and `{a-memcyc1014}`.

In principle, load and store could use two different programs on each addressable accumulator, one which sends and one which receives. But because storing a value requires clearing first, and connecting the `S` digit lines to program lines requires a dummy program, this would use up five scarce programs on each accumulator. Instead we combine load and store into a single three step sequence, the memory cycle.

```
# Accumulator memory cycle: sends, clears, and recieves
defmacro memcycle x
  $dummy {p-memcyc$x} {p-memcyc$x-2}
  $sendc {p-memcyc$x-2} {a-mem$x} {t-memcyc-2} A {p-memcyc$x-3}
  $recx  {p-memcyc$x-3} {a-mem$x} {x-memcyc-3} {i-main}
endmacro
```
Combining load and store into a single cycle has another important benefit: the `loadacc` and `storeacc` instructions are almost identical and can share most of their sequence. The only difference is that `loadacc` executes MEM->LS, LS->MEM during the memory cycle to restore the memory value, while `storeacc` executes only LS->MEM.

## Addressing words
When an accumulator value is loaded into the LS register the individual words are accessible as registers F-J. The machine is already quite capable without word-level memory access, but a test implementation of tic-tac-toe showed that continually packing and unpacking accumulators would probably make chess too large to fit in the available code space. Instead, chessvm supports 75 words of memory addressed as 0-74. This was originally conceived as load and store subroutines, but hardwired instructions are much faster and use no code space.

A `mov [B],A` instruction is executed in two parts. First accumulator B div 5 loaded, then B mod 5 controls the selection of one of the FGHIJ registers to be copied to A. The trickiest part of all of this is address generation, which works like this:

 1. Add B to itself and shift the result right giving B*2 div 10 or B div 5
 2. Load the accumulator at this index into LS
 3. Lookup the low digit of B in the FT3 decoding table, defined above
 4. Store the result in `{a-movXA}` use the `S` output digits to trigger one of five `MOV [FGHIJ],A` opcodes

Much of the `loadacc` sequence is re-used, which makes this relatively compact in terms of ENIAC resources. The full sequence is documented [here](isa.md#mov-ba-aka-loadword). Essentially we paid for most of loadword already, including all of the pre-existing memory cycle programs on each accumulator.

Storing words is somewhat harder. `MOV A,[B]` is implemented through `loadacc`, storing A into LS, and then `storeacc`.
 1. Add B to itself and shift the result right giving B div 5
 2. Load the accumulator at this index into LS
 3. Lookup the low digit of B in the FT3 decoding table, defined above
 4. Store the result in `{a-movAX}` use the `S` output digits to trigger one of five custom `MOV A,[FGHIJ]` sequences.
 5. Add B to itself and shift the result right giving B div 5
 6. Store LS into the accumulator at this index

This a much more expensive instruction to implement, especially because the five `MOV A,X` sequences are not already implemented for other instructions. It is the slowest opcode, taking 38 cycles to complete. But it's marvelously faster and smaller than implementing this capability as a subroutine, and besides, we only have one level of call stack.

# Making it all fit
Memory is by far the scarcest resource for programs running on the VM. But for the VM implementation itself, the scarce resource is ENIAC hardware. Programming the VM is akin to writing microcode, and the number of program units in the system is a hard limit on the number of microcode steps. It is possible to share program subsequences, but multiple callers must be isolated, requiring further resources in the form of pulse amplifiers and dummy programs . There are also only a limited number of inputs and outputs on each accumulator, which means that hardware functions involving special wiring -- permuters, conditionals, indexed lookups -- must be distributed across many accumulators. This section describes the techniques we developed to use less hardware and trade between available resources.

When you run easm, it gives you a map of the resources used. The current version of chessvm assembles like this:
```
% python easm/easm.py chessvm/chessvm.easm chessvm.e
pas 87/88 ts 159/160 its 6/6 fts 31/33 cts 23/23 mts 14/14 mpas 10/10
a1  ***** ************   a2  ****. ************
a3  ***** ************   a4  ****. ************
a5  ****. ************   a6  **... **..*******.
a7  ***.. ***.********   a8  ****. ************
a9  **... *...********   a10 *.... *...********
a11 ***** ************   a12 ***.. ************
a13 ***** ************   a14 ***** ************
a15 ****. ************   a16 **... **..********
a17 ***** ************   a18 ****. ************
a19 ***.. **..********   a20 ***.. ************
```
The five inputs and 12 programs of each accumulator are shown as a1-a19, where an asterisk means in use. The top row shows a variety of other resources.

| code | meaning |
| - | - |
| pas | pulse amplifiers |
| ts | accumulator transciever programs |
| its | initial clear programs used as dummies |
| fts | function table programs |
| cts | constant transmiter programs used as dummies |
| mts | multiplier programs used as dummies |
| mpas | multiplier programs used as pulse amplifiers |

We had to press many items of hardware into unusual service to create more dummy program steps. Why? They allowed us the ability to create and share complex sequences.

## Subprograms
Subprograms are an important concept and widely used in chessvm to share repeated subsequences between instructions. There are a number of short subprograms for  common operations like clearing the A register, and a number of longer subprograms for complex repeated operations like address decoding. Consider the implementation of the `SWAP A,[BCDE]` instructions again:
```
1. MOVSWAP -> EX
2. RF -movswap[BCDE]-> MOVSWAP
3. MOVSWAP -> RF
4. EX -> MOVSWAP
```
This could be written as four completely separate program sequences, but all operations are shared between these four opcodes except for a different permuted input on MOVSWAP. We can save quite a few programs (both transcievers and receivers) by sharing this sequence. Each of the the `p-opswapAX` program lines can trigger both the shared sequence and one specific receive program from the appropriately permuted input on MOVSWAP. We could draw this for two opcodes like so:
```
      p-opswapAB                          p-opswapAC
          │                                   │
          │                                   │
          ├─────────────────┬─────────────────┤
          │                 │                 │
          │          ┌──────┴──────┐          │
          │          │ MOVSWAP->EX │          │
          │          └──────┬──────┘          │
          │                 │                 │
  ┌───────┴────────┐ ┌──────┴──────┐  ┌───────┴────────┐
  │-swapAB->MOVSWAP│ │    RF->     │  │-swapAC->MOVSWAP│
  └────────────────┘ └──────┬──────┘  └────────────────┘
                            │
                     ┌──────┴──────┐
                     │ MOVSWAP->RF │
                     └──────┬──────┘
                            │
                     ┌──────┴──────┐
                     │ EX->MOVSWAP │
                     └─────────────┘
```
In this diagram, time flows from top to bottom. To ensure that the receive on MOVSWAP is executed when RF is sending we need a dummy program to delay one cycle. The bigger wrinkle is that program lines are bidirectional. Whenever a pulse appears on `p-opswapAB` it is transmitted to `p-opswapAC` as well. We need a way to isolate the users of a subprogram. This problem was understood by the original ENIAC programmers and is discussed at Goldstine XI-10. The answer is a device called a pulse amplifier, which is basically a [vaccuum tube diode](https://en.wikipedia.org/wiki/Diode#Vacuum_tube_diodes). These were built into units with 11 channels, originally to allow connections between data busses, but were very useful in isolating programs in this way. Historical documents indicate that eight pulse amplifier units were eventually built, so the simulator supports 88 pulse amplifier channels.

Chessvm uses pulse amplifiers to share many sequences and thereby save a large number of accumulator programs. For example, almost every instruction begins by saving some other accumulator to EX. We can't use up one EX program for each instruction, so instead we share a single program called `{p-loadex}` that loads EX from `{d-main}`, calling it through a pulse amplifier wherever needed. 

The complete implementation of SWAP A,X with shared programs looks like this.
```
# SWAP A,X with shared programs. Trigger via {p-opswapA[BCDE]}
include macros.easm

# Shared core, triggered from {p-opswapAX}
# 1. MOVSWAP->EX
$sendc {p-opswapAX} {a-movswap} {t-opswapAX} A {t-opswapAX-2}
$pulseamp {p-opswapAX} {p-loadex}         # EX shared program to receive

# 2. RF->
$sendc {p-opswapAX-2} {a-rf} {t-opswapAX-2} A {t-opswapAX-3}

# 3. MOVSWAP->RF
$sendc {p-opswapAX-3} {a-movswap} {t-opswapAX-3} A {t-opswapAX-4}
$recx {p-opswapAX-3} {a->rf} {r-opswapAX-3} {i-main}

# 4. EX->MOVSWAP
$pulseamp {p-opswapAX-4} {p-storeex}       # EX shared program to sendc
$rec {p-opswapAX-4} {a->movswap} {t-opswapAX-4} {i-main} {p-next}

# Instruction-specific operations, triggered from {op-swapA[BCDE]}
# Use a dummy for timing, and a pulseamp to isolate the shared sequence
defmaco do-swapAX x
  $pulseamp {p-opswapA$x} {p-opswapAX}
  $dummy {p-opswapA$x} {p-opswapA$x-2}
  $recx {p-opswapA$x-2} {a-movswap} {x-opswapA$x} {i-swapA$x} # this input is where the actual swap happens
endmacro

$do-swapAX B
$do-swapAX C
$do-swapAX D
$do-swapAX E
```
This snippet also shows the use of an `x` program, which tells easm that it can use either a receiver or a transciever program when allocating `{x-opswapA$x}` for each of four opcodes. We'd like to use recievers since no output pulse is needed (and this saves transcievers) but there are only four receivers per accumulator and at least one of them is already allocated on most accumulators for the memory cycle.

## Dummies, pulse amplifiers, and exotic uses for units
To some extent dummies and pulse amplifiers are interchangable. For example, SWAP A,X could trigger the core shared program with a dummy instead of a pulseamp at the cost of a one cycle delay. This delay may not be a problem in other circumstances, for example when triggering a sub-program to start on cycle 2 with a dummy that begins on cycle 1. Dummies with multi-cycle delays are particularly useful for sequencing arbitrary arrangements of subprograms. 

As much as transcievers, dummies and pulseamps are the scarce resource, because they allow sequencing and re-use of program steps. They're such important resources that we've pressed a number of ENIAC units into service to get many more. First, the function tables have a variable repeat switch which can be used to produce a 5-13 cycle delay, as mentioned in Goldstine VII-24. These and other function table programs (e.g. fetch) are counted as `fts` in the easm output map. We use the six "selective clear" programs on the initiating unit as one-cycle dummies (`its`). These progams were intended to clear non-significant figures in accumulators, but we never set the selective clear switch on any accumulator. 

Then things get weirder. We also repurposed 22 programs on the card reader and constant transmitter unit, turning programs 2-24 into one cycle dummies (`cts`). This works as long as we restrict ourselves to reading only the first 10 columns of each card. If we ever read a card with digits in columns 11-80, these "dummies" will put data on the main bus when the associated ct program is triggered!

Most adventurously, we abuse the multiplier to get an additional 14 dummies with a 6-14 cycle delay ('mts`) and 10 pulse amplifier equivalents (`mpas`). To make this work we needed the ability to simulate disconnecting the multiplier unit from the adjacent accumulators, which in reality involved nothing more than unplugging a few front panel cables. We simulate this via the `s m.pp unplug` setting, which prevents the multiplier from sending over the (already modelled!) partial product connections. This is the most speculative repurposing of ENIAC hardware, but every other accumulator operated without anything connected to these ports, and the pulse level simulation gives us confidence that it would have worked fine.


## Dummy allocation
Dummy programs can go on any accumulator, while programs that do work on a particular accumulator cannot. Initially we just put all dummies on a series of accumulators `{a-dummy}`,`{a-dummy2}`, and so on. It quickly became burdensome to manage allocation across multiple accumulators, and besides, those accumulators were also filling up with useful programs. And then we thought: this is what computers are for!

Enter easm's allocated dummies. When you need one, you can say this:
```
allocate-dummy name
```
This finds a free transciever, searching from a20 towards a1, and allocates two symbols: `{a-name}` is the accumulator and `{t-name}` is the transciver. You can then implement the dummy by patching a program line in to `{a-name}.{t-name}i` and out of `{a-name}.{t-name}o` while setting `{a-name}.op{t-name}` to 0, i.e. NOP.

Sometimes it's important to keep a dummy off of particular accumulators, for example the accumulator used for discrimination or any accumulators used in a subprogram that the dummy is timing. Otherwise, we could end up triggering two programs on the same accumulator at the same time. `allocate-dummy` has an exclude option to handle this case:
```
allocate-dummy name -a1,a8,a14
```

But dummies can still fight with other programs. Really we'd like all dummies to be allocated after all program steps. This is the purpose of the easm `defer` directive. When placed before a line, that line is not assembled until the `insert-deferred` directed is encounterd. This allows all dummy allocation to come after all program allocation, even if the dummy allocation is interspersed in the source file. Chessvm's `dummy` macro is implemented to seamlessly create and then defer allocation of a dummy program until all other programs are placed.
```
defmacro dummy inpr outpr
  defer allocate-dummy %name
  defer p {$inpr} {a-%name}.{t-%name}i
  defer s {a-%name}.op{t-%name} 0
  defer p {a-%name}.{t-%name}o {$outpr}
```
Automated dummy allocation was a key feature that allowed us to make the most efficient use of available ENIAC hardware.
