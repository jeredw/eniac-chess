# Programming an ENIAC VM with EASM
ENIAC Chess began with Briain Stuart's pulse-level [simulator](https://www.cs.drexel.edu/~bls96/eniac/eniac.html) which we forked and [further developed](https://github.com/jeredw/eniacsim). Although a faithful and full-featured simulation of the ENIAC, the input format is nothing more than a list of patch wires and switch settings. Easm is an assembler that provides named resources, macros, includes, conditionals and more and makes ENIAC programming far easier than it has ever been. This document describes how easm works, and how it was used to build chessvm.

# What is the ENIAC?
This document is a very gentle introduction to parts of the ENIAC hardware and programming model, but to do any real programming you'll need some familiarity with ENIAC's hardware and basic programming theory. For an introduction, see Stuart's series of articles:
 - [Simulating the ENIAC](https://ieeexplore.ieee.org/document/8540483)
 - [Programming the ENAIC](https://ieeexplore.ieee.org/document/8467000)
 - [Debugging the ENIAC](https://ieeexplore.ieee.org/document/8540483)

Or perhaps watch [his talk](https://www.youtube.com/watch?v=u5WYj11cJrY). 

We also recommend the excellent book [ENIAC In Action](https://eniacinaction.com/) by Crispin Rope and Thomas Haigh, who have also published all kinds of fascinating original ENIAC documents.

# The Accumulator
ENIAC is a series of refrigerator-sized units with different functions. The unit we'll use most for programming is the accumulator, a device that holds ten digits plus a sign. It's basically a vaccuum tube version of a [mechanical adding machine accumulator](https://hackaday.com/2018/05/01/inside-mechanical-calculators/). The accumulator is both memory and arithmetic, and its basic function is to add a number recieved on one of its inputs alpha through epsilon (hence a, b, g, d, e). It can also send the stored number in its A (add) output, or its 10's complement on the S (subtract) output.
```
               Outputs
 
               A    S
               |    |
    +--------------------------+
    |      PM DDDDDDDDDD       |     One sign (PM) plus ten digits
    +--------------------------+
       |    |    |    |    |
       a    b    g    d    e
        
              Inputs

```
PM is short for "plus minus" and you can think of it as a sign bit. The accumulator is triggered by a pulse into one of 12 "program controls". Each of these has switches that control the operation executed when that "program" is executed. If X is the value in the accumulator, the available operations are
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

The accumulator is the backbone of the machine, and is simultaneously memory, addition, and subtraction. There are 20 accumulators in the ENIAC, for a total writable memory of 200 digits. This is more or less the only writable memory in the machine (excluding a few internal registers in other units). Note that the resources available on each accumulator are limited in several ways: there are only five different inputs, only one uncomplemented and one complemented output, and most of all only 12 program inputs, meaning that without more advanced sequencing techniques each accumulator can be involved in at most 12 program steps.

To describe the contents of an accumulator (or its value on a data bus) we follow the original sign notation of P or M followed by ten digits, in 10's complement form. Hence P0000000005 is 5 and M9999999995 is -5. To negate a value in 10's complement, take the 9's complement of each digit (subtract from 9) and then add 1. When sending the PM digit, a P is transmitted as a 0 while an M is transmitted as a 9.

# Programs and patches
The world of ENIAC programming, and the surviving technical documentation, is full of words that meant somewhat different things at the dawn of computing. An ENIAC "program" is a single action on one of the functional units (accumulators, function tables, etc.) that can be triggered by a pulse. A "program line" was a physical wire that triggered a particular program on a particular unit.

What we might consider a "program" today, that is, the sequence of operations to accomplish something, was wired with patch cables (program lines and data trunks) that set the sequence of functional unit program activations, the parameters of each, and the dataflow. We'll use "patch" to refer to the complete set of wires and switch settings, which at the time they called a "setup."  A "patch" is what is in the `.e` file that the simulator loads.

# Hello EASM
In [`vm-dev/print-naturals.e`](vm-dev/print-naturals.e) is the Hello World of ENIAC programming. It cycles a pulse forever between two units, the printer and an accumulator. We use accumulator 13 because 13-20 are hard wired to connect to the 80 columns of the punch card printer, ten digits from each of eight accumulators. 
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
% ./eniacsim vm-dev/print-naturals.e
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

# Moving data around
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

# add Alice into Bob
$send {p-xfer} {a-src} {t-xfer} A {p-next}
$recx {p-xfer} {a-dst} {r-xfer} {i-main}

```
Much shorter: one line to send from `{a-src}` and one line to receive and add at `{a-dst}`. Note that it's still necessary to connect the data bus to outputs and input. The macros in chessvm are designed this way to separate datapath wiring from program step sequencing. Also, only one of these accumulators needs to trigger the next program step. This is why the send uses a transciever `{t-xfer}` while the recx needs only a recieiver `{r-xfer}`. Chessvm uses macros which end in x to denote that an output pulse is not transmitted, hence `recx` vs `rec`, and `sendx` also exists.

# Registers, Arithmetic, and Permutation
The original [instruction sets](https://eniacinaction.com/the-articles/2-engineering-the-miracle-of-the-eniac-implementing-the-modern-code-paradigm/) for the ENIAC were all based on moving 10 digit numbers around, because the ENIAC was primarily used for scientific computation. But there are only 20 accumulators, so after allocating a few to machine functions like the program counter and instruction register, this meant there were very few memory locations left. Chessvm uses two digit words instead, making the ENIAC into a 100 word machine. The main [register file](isa.md) is one accumulator broken down into five two-digit registers A-E, plus the PM digit used as an overflow flag N.
```
+------------------+
| N AA BB CC DD EE |
+------------------+
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

Finally, this example introduces the register transfer notation X -> Y which is used extensively in chessvm comments and design docs. Here's how it works:

| Notation  | Meaning |
| - | - |
| X -> Y | send from X, rec on Y |
| X -input-> Y | send X, rec Y on given input |
| X -S-> Y | send X on S output (complemented) |
| X -S-input-> Y | send X complemented to given input |

In most cases "clear X after sending" is implied.


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



