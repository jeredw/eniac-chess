# ChessVM Instruction Set and Microarchitecture Reference
This is a virtual machine implemented on top of the ENIAC for the purpose of playing chess, but it's actually a pretty general tiny CPU.

## VM Architecture

There are 200 digits of writable memory in the machine, so a two digit word size conviently addresses all possible words in its 0..99 range, which is also a useful range for arithmetic. We are limited to at most 51 opcodes by the decoding scheme built out of the master programmer, and code space is at a premium so we don't want to add an address word to every instruction. These considerations drive the architecture to a simple accumulator machine, where every operation goes throug a single register A. We add nine more general purpose registers to implement complex routines compactly, but we can only load them into A or swap with A.

The VM implementation takes up five accumulators to store the register file and machine state. This leaves 15 accumulators / 75 words for our RAM. Memory can be accessed through loads and stores of accumulators or words. There is only one addressing mode: address in A. Additionally, there are 94 words of function table memory set aside as a single program-defined lookup table.

|                     |     |
| ------------------- | --- |
| `PC`                | Program counter, ft(1-3) and row (0-99) |
| `RR`                | Return address, ft(1-3) and row (0-99) |
| `A`,`B`,`C`,`D`,`E` | RF, 5 words  |
| `F`,`G`,`H`,`I`,`J` | LS, 5 words  |
| `N`                 | RF sign (0/1 i.e. +/-) |
| `M`                 | LS sign (0/1 i.e. +/-) |
| `acc[0-14]`         | Memory, 75 words (0-74) |
| `ft3[]`             | Constant data, 94 words (6-99) |
| `ft1-3[]`           | Instructions, 1660 words |

Arithmetic treats `A` as a 2-digit 10's complement number -100 ≤ A < 100 with sign bit `N`.  `N` is visible to control flow instructions, but is cleared by
most register moves and cannot be loaded or stored to memory.  So practically, most arithmetic is unsigned.

The load/store register `LS` is overwritten by all memory accesses. Registers `FGHIJ` are stored in `LS`, and can only be read into `A` whereas `BCDE` can also be swapped with `A`. The `swapall` instruction switches `RF` and `LS` to permit operating on the contents of `LS` more directly, so `M` saves `N` in this special case. Cards are also read into LS, meaning we can only read the first ten digits of each card.

Function table rows are 12 digits wide, and `PC` and `RR` address only the first instruction of a row.  This means that branch targets must be aligned to row boundaries, so programs are subject to packing inefficiencies. Additionally, some rows of ft3 are reserved for VM implementation, and the first two digits of ft3 rows are reserved for constant data instead of instructions accessed through the `FTL` (function table lookup) operation.


## Instruction Set

| op  | mnemonic     | cycles[¹](#cycles) | effect | flags |
| --- | ------------ | ------- | ----------------- | ----- |
| 00  | clrall       | 4       | ABCDE←0           | N←0   |
| 01  | swap A,B     | 4       | A↔︎B               | N←0   |
| 02  | swap A,C     | 4       | A↔︎C               | N←0   |
| 03  | swap A,D     | 4       | A↔︎D               | N←0   |
| 04  | swap A,E     | 4       | A↔︎E               | N←0   |
| 05  | _(reserved)_ | -       | -                 | -     |
| 10  | loadacc A    | 11      | FGHIJ←acc\[A\]    | M←acc[†](#macc) |
| 11  | storeacc A   | 13      | acc\[A\]←FGHIJ    | M←acc[†](#macc) |
| 12  | swapall      | 5       | ABCDE︎︎︎︎↔︎FGHIJ       | N↔︎M   |
| 13  | -            | -       | -                 | -     |
| 14  | ftl A        | 7       | A←ft3\[A\]        | N←ft3 |
| 15  | -            | -       | -                 | -     |
| 20  | mov B,A      | 9       | A←B               | N←0   |
| 21  | mov C,A      | 9       | A←C               | N←0   |
| 22  | mov D,A      | 9       | A←D       ︎        | N←0   |
| 23  | mov E,A      | 9       | A←E               | N←0   |
| 24  | _(reserved)_ | -       | -                 | -     |
| 25  | _(reserved)_ | -       | -                 | -     |
| 30  | mov G,A      | 9       | A←G               | N←0   |
| 31  | mov H,A      | 9       | A←H               | N←0   |
| 32  | mov I,A      | 9       | A←I       ︎        | N←0   |
| 33  | mov J,A      | 9       | A←J               | N←0   |
| 34  | mov F,A      | 9       | A←F               | N←0   |
| 35  | _(reserved)_ | -       | -                 | -     |
| 40 xx | mov xx,A   | 4       | A←xx              | N←0   |
| 41  | mov [B],A    | 28      | FGHIJ←acc[B/5]<br>A←FGHIJ[B%5] | N←0<br>M←acc |
| 42  | mov A,[B]    | 37      | FGHIJ←acc[B/5]<br>FGHIJ[B%5]←︎A[‡](#msign)<br>acc[B/5]←FGHIJ | M←acc  |
| 43  | lodig A      | 5       | A₁A₀←0A₀          | -   |
| 44  | swapdig A    | 5       | A₁A₀←A₀A₁         | -   |
| 45  | _(reserved)_ | -       | -                 | -   |
| 50  | _(reserved)_ | -       | -                 | -   |
| 51  | _(reserved)_ | -       | -                 | -   |
| 52  | inc A        | 1       | A←A+1             | N←A[¶](#arith) |
| 53  | dec A        | 1       | A←A-1             | N←A[¶](#arith) |
| 54  | flipn        | 2       | -                 | N←1-N |
| 55  | _(reserved)_ | -       | -                 | -   |
| 70  | add D,A      | 5       | A←A+D             | N←A[¶](#arith) |
| 71 xx | add xx,A   | 2       | A←A+xx            | N←A[¶](#arith) |
| 72  | sub D,A      | 5       | A←A-D             | N←A[¶](#arith) |
| 73 xx | jmp xx     | 2       | PC←xx  (cur ft)   | -   |
| 74 xx xx | jmp far xxxx | 6  | PC←xxxx (any ft)  | -   |
| 75  | -            | -       | -                 | -   |
| 80 xx | jn xx      | 6       | if A<0: PC←xx     | -   |
| 81 xx | jz xx      | 10      | if A=0 or A=-100: PC←xx | -   |
| 82 xx | jil xx     | 10      | if A₁A₀ illegal[§](#jil): PC←xx | -   |
| 83  | -            | -       | -                 | -   |
| 84 xx xx | jsr xxxx| 6       | RR←PC, PC←xxxx    | -   |
| 85  | ret          | 6       | PC←RR             | -   |
| 90  | clr A        | 2       | A←0               | N←0 |
| 91  | read         | ?       | input F₁F₀G₁G₀H₁[‼](#read)︎  | -   |
| 92  | print        | ?       | output A₁A₀B₁B₀   | -   |
| 93  | -            | -       | -                 | -   |
| 94  | brk          | -       | break debugger    | -   |
| 95  | halt         | -       | stop machine      | -   |

### Instruction notes
"Reserved" means the master programmer is wired such that this opcode can never be used, while a dash means that opcode is available for future use.

<a name="cycles">¹</a> Timings are 5kHz ENIAC add cycles, excluding instruction
fetch cycles.  Fetch costs are +6 cycles within a ft row; +12 cycles for a new
row in ft1/2; and +13 cycles for a new row in ft3.  See [Control
Cycle](#control-cycle) for more details.

<a name="macc">†</a> `loadacc` and `storeacc` set `M` from acc (prior to
updating acc), so `M` always reflects acc and changes are not saved.

<a name="msign">‡</a> `mov A,[B]` stores the digits of `A` but does not store
`N`.

<a name="arith">¶</a> `inc`, `dec`, `add`, and `sub` affect `A` and `N`
according to 10's complement arithmetic, wrapping `N` from + to - or - to + at
boundaries; e.g. for `inc A`, +98→+99, +99→-100, -100→-99, and -1→+0.

<a name="jil">§</a> `jil` branches if either digit of A is 0 or 9, which would
be an illegal square index on a chess board indexed by A₀=1-8 and A₁=1-8.

<a name="read">‼</a> `read` adds into the aux RF accumulator without first
clearing it, so relies on the assembler to emit necessary clearing instructions
as a preamble.

### Assembler pseudo-instructions

For convenience, the assembler recognizes pseudo-instructions for common
unsupported cases of `mov`.

|               |      |     |
| ---           | ---  | --- |
| `mov A,X`     | `swap A,X`<br>`mov X,A` | move A to register X
| `mov X,A<->Y` | `mov X,A`<br>`swap A,Y` | move RF/immediate X to Y (BCDE) via A



## Memory map
| accumulator | name | contents |
| - | - | - |
| 1 | Program counter      | `SS` `RRRR` `PPPP` |
| 2 | Instruction register | `I5` `I4` `I3` `I2` `I1` | 
| 3 | Execution register   | `I1` `XX` `XX` `XX` `XX` | 
| 4 | Load/store registers | `FF` `GG` `HH` `II` `JJ` |
| 5 | memory 0 | `00` `01` `02` `03` `04` |
| 6 | memory 1 | `05` `06` `07` `08` `09` |
| 7 | memory 2 | `10` `11` `12` `13` `14` |
| 8 | memory 3 | `15` `16` `17` `18` `19` |
| 9 | memory 4 | `21` `22` `23` `24` `25` |
| 10 | memory 5 | `25` `26` `27` `28` `29` |
| 11 | memory 6 | `30` `31` `32` `33` `34` |
| 12 | memory 7 | `35` `36` `37` `38` `39` |
| 13 | Register File | `AA` `BB` `CC` `DD` `EE` | 
| 14 | memory 8 | `40` `41` `42` `42` `44`  |
| 15 | memory 9 | `45` `46` `47` `48` `49`  |
| 16 | memory 10 | `50` `51` `52` `53` `54` |
| 17 | memory 11| `55` `56` `57` `58` `59` |
| 18 | memory 12 | `60` `61` `62` `63` `64` |
| 19 | memory 13| `65` `66` `67` `68` `69` |
| 20 | memory 14 | `70` `71` `72` `73` `74` |
## VM Microarchitecture

### Accumulator layout 

Typical contents, plus wiring for inputs and outputs

#### PC (A1)

Current program counter PPPP and return address RRRR, plus a temp SS which is
usually I1, the next instruction to execute.

<pre>
layout: SS RRRR PPPP

A - main (to mp steppers, op<=55)
S - main (to mp steppers, op>55; SS field digits swapped)
a - main
b - shiftl8-ir: XX XX XX XX I1 -> I1 00 00 00 00, used in control cycle
g - clearA: XX RRRR PPPP -> 00 RRRR PPPP, wired to EX.S for control cycle
d - loadPC2: SS RRRR PPPP -> 00 0000 00PP, used for JMP/JN/JZ/JIL
e - fetch-i1: from FT for instruction fetch
</pre>


#### IR (A2)

Up to five next instructions. `M0` if empty, otherwise `P I6 I5 I4 I3 I2`.  99
fills in from the left as instructions are consumed so we can easily detect
an empty IR by adding 1, giving P999... + 1 = M0.

<pre>
A - d-irA (sign used in control cycle)
    main (digits but not sign)
S - d-irS, used in control cycle
AS - fetch discriminate
a - main
b - from FT
g - fill99: replace top 2 digits with 99
</pre>


#### EX (A3)

Clear at the start of every op, general purpose temp.

Also used to disc opcode >55.

<pre>
A - d-exA (sign used in control cycle)
    main (digits but not sign)
S - exS, used in control cycle
AS - op discriminate
a - main
b - rotate-ir: I5 I4 I3 I2 I1 -> I1 I5 I4 I3 I2, used in control cycle
g - clearA: S aa bb cc dd ee -> 0 00 bb cc dd ee, used in control cycle
d - clearPC2: XX XX XX XX 21 -> XX XX XX XX 00, used for JN/JZ/JIL
e - fetch-i1: from FT for instruction fetch
</pre>


#### RF (A13)

Main register file

<pre>
layout: PM AA BB CC DD EE

A - main
S - main, deleting PM and digit 1, used for SUB D,A
a - main
b - selectA: X aa XX XX XX XX -> 0 aa 00 00 00 00, used for MOV X,A
g - selDA:   X XX XX XX dd XX -> 0 dd 00 00 00 00, used for ADD D,A
d - selEA:   X XX XX XX XX ee -> 0 ee 00 00 00 00, used for MOV #XX,A
e - ftldata: S XX XX aa XX XX -> S aa 00 00 00 00, used for FTL
</pre>


#### LS (A4)

Secondary register file / load/store accumulator 

<pre>
layout: FF GG HH II JJ

A - main
a - main
b - signonly: delete all digits, used to preserve sign of DISCFTx in STOREACC
</pre>


#### MEM0 / DISCMEMCYC (A5)
Discriminate memory cycle 0-9 vs. 10-14

<pre>
AS - Discriminate memcyc
A - main
a - main
b - splitA: Prepare A for disc A<10, X XX XX XX XX A2A1 -> A2 00 00 00 00 0A1
g - dropsign: used to clear sign of LS in STOREACC
</pre>


#### MEM1 / MEMCYC1014 (A6)

<pre>
A - main
S - trigger memcyc 10-14
a - main
b - ftselacc: read from FT output
</pre>


#### MEM2 / LOADWORD (A7)

<pre>
A - main
S - Trigger MOV [FGHIJ],A on S outputs
a - main
b - windexB (word index): X XX B2B1 XX XX XX -> 0 00 00 00 00 0B1
b - accidxB: (acc index): X XX B2B1 XX XX XX -> 0 B2B1 00 00 00 00
g - ftselacc: read from FT output
</pre>


#### MEM3 / RFTMP (A8)

<pre>
A - main
a - main

b - i-clearA: X XX XX XX XX XX -> X 00 XX XX XX XX
</pre>


#### MEM4 / STOREWORD (A9)

<pre>
A - main
S - Trigger MOV A,[FGHIJ] on S outputs
a - main
b - ftselacc: read from FT output
</pre>


#### MEM5 (A10)

<pre>
A - main
a - main
</pre>


#### MEM6 / NEWPC (A11)

<pre>
A - main
a - main
b - extract-pc: XX XXXX PPPP -> 00 0000 PPPP
g - keep-r:     XX RRRR XXXX -> 00 RRRR 0000
d - shiftr4-pc: XX RRRR PPPP -> 00 0000 RRRR
e - shiftl4-pc: XX XXXX PPPP -> XX PPPP 0000
</pre>


#### MEM7 (A12)

<pre>
a - main
b - shiftA: used to shift RF A into digits 1+2 for ft arg
c - clearA: used to clear RF A for ftl
</pre>


#### MEM8 (A14)

<pre>
A - main
a - main

# inputs to suport mov A,[FGHIJ]
b - swapAB: S aa bb XX XX XX -> S bb aa XX XX XX
g - swapAC: S aa XX cc XX XX -> S cc XX aa XX XX
d - swapAD: S aa XX XX dd XX -> S dd XX XX aa XX
e - swapAE: S aa XX XX XX ee -> S ee XX XX XX aa
</pre>


#### MEM9 / DISCJX (A15)

<pre>
AS - disc JX
A - main
S - trigger conditional jump/taken
a - main
b - shiftA: used to shift RF A into digits 1+2 for ft arg
g - ftjzsign: get sign for jz discrimination
d - ftjilsign: get sign fo jil discrimination
</pre>


#### MEM10 / MEMCYC09 (A16)

<pre>
A - main
S - trigger memcyc 0-9
a - main 
b - ftselacc: assemble 10 digits from FT output
</pre>


#### MEM11 / MOVSWAP (A17)

<pre>
A - main
a - main

# inputs for all MOV X,A and SWAP A,X operations
b - movAB: S aa bb XX XX XX -> S bb aa XX XX XX
g - movAC: S aa XX cc XX XX -> S cc XX aa XX XX
d - movAD: S aa XX XX dd XX -> S dd XX XX aa XX
e - movAE: S aa XX XX XX ee -> S ee XX XX XX aa
</pre>


#### MEM12 / DISCFT1 (A18)

<pre>
A - main
S - discft1
a - main
b - resetPC: sign digit to ftsg1, used to load initial PC
g - ftsg1: x xx xx xx xD xx -> PM
d - ftsg2: x xx xx xx Dx xx -> PM
</pre>


#### MEM13 / DISCFT2 (A19)

<pre>
A - main
S - discft2
a - main
b - ftsg1: x xx xx xx xD xx -> PM
g - ftsg2: x xx xx xx Dx xx -> PM
</pre>


#### MEM14 / DISCFT3 (A20)

<pre>
A - main
S - discft3
a - main
b - ftsg1: x xx xx xx xD xx -> PM
g - ftsg2: x xx xx xx Dx xx -> PM
</pre>


### Control cycle

The control loop usually resumes from cycle 1.  It takes 6 cycles to dispatch
instructions from the IR, and 12 cycles to dispatch instructions when we must
load IR from an ft, ignoring the actual instruction time.  There is no `nop`
instruction, but in theory one would take 0 cycles, so a program consisting
entirely of `nop` would take 6 &times; 5 + 12 &times; 1 cycles per 6 `nop`s, or
7 cpi.  With 5kHz add cycles this gives a theoretical maximum rate of 714
instructions/second.

```
1. [p-fetch] IR -> EX, IR-shiftl8->PC,
             discriminate IR (P->p-nofetch-eat-op, M->p-fetchline)
  (IR>=0, p-nofetch-eat-op: triggers both p-nofetch and p-eat-op via pulse amps)
  2. [p-nofetch] EX += 43                     [p-nofetch-eat-op] nop
  3. [p-disc-op] disc EX,                     [p-eat-op] M00000 -fill99-> IR,
                 clear EX,                               EX -fill99-> IR,
                 clear mp                                IR += 1
    (EX>=0, op<=55)                           
    4. [p-oplt55] PC -clearA-> EX,
                  PC-A->master programmer
    5. [p-oplt55] EX -> PC,
                  clear EX,
                  trigger master programmer
    6. (decode)
    7. operation begins in this add time
  else
    (EX<0, op>55)
    4. [p-opgt55] PC-S->EX,
                  PC-S->master programmer
    5. [p-opgt55] EX-S-clearA->PC,
                  clear EX,
                  trigger master programmer
    6. (decode)
    7. operation begins in this add time
else
  2. [p-fetchline]  MEM17-S->dummy, MEM18-S->dummy, MEM19-S->dummy
  3. [p-fetchtrig]  stim FT
  4. [p-fetcharg]   PC->FT
  5. [p-preinc-fetch]  EX += P01..., PC += P01...
  6. wait
  7. [p-fetchread]   FT -> IR,EX,PC, IR += 1
                     goto p-nofetch*, **

* note this does not trigger p-eat-op so the top of IR is preserved.
** see note about special case for ft3, below
```

#### Special case for ft3

ft1 and ft2 hold 6 instructions per row, so `p-fetchline` normally fills PC.SS
with the first instruction of the line (`I1`) and IR with the following 5
instructions (`I6 I5 I4 I3 I2`).  Since the `I1` slot of ft3 holds constant
data for `ftl`, `p-fetchline` uses an alternate sequence for ft3 which only
places instructions in IR (`I6 I5 I4 I3 I2`), and then resumes from `p-fetch`
instead of `p-nofetch` to shift in `I2` as the next instruction.  This takes 13
rather than 12 cycles.

In principle the alternate sequence for ft3 could pre-shift IR and operate in
12 cycles, but ft3 output is on a separate bus from ft1/2 so that it can be
used for concurrent dummy programs, and EX doesn't have enough free inputs to
read from the ft3 bus.

#### Changing function tables

The current ft for instruction fetch is selected by the signs of `MEM18/19/20`,
where P means to fetch from the corresponding ft. Signs are decoded from PC ftsg
only for instructions which may change it,

<pre>
MEM18.S = P+ftsg2 -> ft 1 (09)  # disable for 90 or 99
MEM19.S = P+ftsg1 -> ft 2 (90)  # disable for 09 or 99
MEM20.S = P+ftsg1+ftsg2 -> ft 3 (99)  # disable for 09 or 90

[p-decode-ftsg]
  1. PC-ftsg2->MEM18, PC-ftsg1->MEM19, PC-ftsg1->MEM20
  2. PC-ftsg2->MEM20
</pre>

`p-decode-ftsg` relies on having signs at P initially, and will toggle signs for
disabled fts so that applying it twice is a nop. Hence the sequence for changing
is:

<pre>
  A. -> p-decode-ftsg  # (using old ftsg) reset all signs to P
  B. set new ftsg
  C. -> p-decode-ftsg  # select the new ftsg
</pre>


### Opcode Microprograms

#### LOADACC A

Accumulator index in A, store result in LS.  Use function table as a 1-of-10
decoder on A1 (ones digit).  Use A2 (tens digit) to place ft result in
`MEMCYC09` or `MEMCYC1014`.  Then S outputs of `MEMCYC09`/`MEMCYC1014` trigger a
single accumulator to transmit its value.

```
1. DISCMEMCYC -> EX, clear, clear LS
2. RF -splitA-> DISCMEMCYC, X XX XX XX XX A2A1 -> A2 00 00 00 00 0A1, trigger ft3
3. discriminate DISCMEMCYC, send arg, clear
4. EX -> DISCMEMCYC             (ft shadow)

DISCMEMCYC pos, A < 10
  5. MEMCYC09 -> EX, clear        (ft shadow)
  6. FT3 -> MEMCYC09
  7. send MEMCYC09.S, clear, trigger accumulator memory cycle
  8. EX -> MEMCYC09

DISCMEMCYC neg, A >= 10
  5. MEMCYC1014 -> EX, clear        (ft shadow)
  6. FT3 -> MEMCYC1014
  7. send MEMCYC1014.S, clear, trigger accumulator memory cycle
  8. EX -> MEMCYC1014

9. main -> LS
10. LS -> main
```


#### STOREACC A

Based on LOADACC. Basic idea is we ignore the memcycle sendc, then send LS for
the rec phase. This replaces accumulator value with LS, instead of vice-versa.
Voilla!  Complication is we can't change the sign of destination, as M18-M20
signs are used for FT decode ("bank switch"). To prevent changes, we store the
sign only during the sendc phase. This also requires clearing LS sign in
advance.

```
1. DISCMEMCYC -> EX, clear
2. LS -dropsign-> DISCMEMCYC  # clears LS.PM
3. DISCMEMCYC -> LS
goto step 2 of LOADACC 
.
. wait 8 cycles
.
11. main -signonly-> LS       # leaves LS contents intact, but saves memacc PM
```


#### MOV [B],A (aka LOADWORD)


```
# Decode word index (0-4) and begin timers
# i-windexB = X A2A1 XX XX XX XX -> 0 00 00 00 00 0A1

1. LOADWORD -> EX, clear LS
2. RF -windexB-> LOADWORD, trigger ft3
3. LOADWORD -> ft3.arg          # usual 10 entry lookup table

4. wait                         # ft shadow
5. wait

6. ft3 -> LOADWORD
7. send LOADWORD.S              # begin word timers, mod 5 wired
8. EX -> LOADWORD

# Now do a LOADACC, decoding the acc idx from B by doubling it in the high digits
# i-accidxB = X XX B2B1 XX XX XX XX -> 0 B2B1 00 00 00 00

9. DISCMEMCYC -> EX               
10. RF -i-accidxB-> DISCMEMCYC
11. RF -i-accidxB-> DISCMEMCYC
12. send M0->DISCMEMCYC, trigger ft3

# Jump into LOADWORD step 3. But this time DISCMEMCYC.1 is zero, while DISCMEMCYC.10
# contains the (complement of) acc idx, which goes to d-main via S output

13. discriminate DISCMEMCYC, DISCMEMCYC -S-> ft3.arg
14. EX -> DISCMEMCYC
15. MEMCYC09/1014 -> EX
16. ft3 -> MEMCYC09/1014
17. MEMCYC09/1014 -> S          # trigger acc memcycle
18. EX -> MEMCYC09/1014

19. memacc -> LS
20. LS -> memacc

# The timer set in cycle 7 triggers the appropriate MOV program here,
# Which returns to fetch when it's done.
21. MOV [FGHIJ],A begins
...
```


#### MOV [BCDE],A and MOV [FGHIJ],A
(Shared with SWAP)

```
1. $clearA-1
2. $clearA-2
3. MOVSWAP -> EX
4. (RF or LS) -movswap[BCDE]-> MOVSWAP
5. MOVSWAP -selectA-> RF
6. EX -> MOVSWAP
```


#### SWAP A,[BCDE]
(Shared with MOV)

```
1. MOVSWAP -> EX
2. RF -movswap[BCDE]-> MOVSWAP
3. MOVSWAP -> RF
4. EX -> MOVSWAP
```


#### MOV #XX,A

```
1. $clearA-1
2. $clearA-2
3. $consume-op-1  -rf-selEA-> RF
4. $consume-op-2
```


#### CLR A

```
1. RF -clearA-> EX, clear   
2. EX -> RF, clear
```


#### INC A

```
CT sends P 01 00 00 00 00 -> RF
```


#### DEC A

```
1. M99000 -> RF
```


#### ADD D,A   (A += D)

```
1. RFTMP -> EX            # can't use EX directly because RF may be -
2. RF -addDA-> RFTMP
3. RFTMP -> RF
4. EX -> RFTMP
```


#### SUB D,A   (A -= D, treating D as +)

```
1. RF.S -> EX             # adapter on S deletes PM and digit 1 (so no 1'p)
2. EX -selDA-> RF, clear  # A += 99-D
3. P01000 -> RF           # A += 100-D
4. M00000 -> RF           # Fix sign (don't have M01 constant)
```


#### JMP XXXX 

```
1. NEWPC -> EX
2. IR -extract-pc -> NEWPC
3. PC -keep-r     -> NEWPC $discft-1
4. (send PC)               $discft-2
5. NEWPC -> PC             $discft-1
6. (send NEWPC)            $discft-2
goto fetchline
 . EX -> NEWPC  # parallel with p-fetchline
```


#### JMP XX

```
nearjump:                    # maybe an opcode, used as subprogram for conditionals
1. PC -clearPC2-> EX         # zero current PC
2. EX -> PC, clear
3. IR -S-loadim2-irS-> PC    # load next PC
   goto fetchline
```


#### JN XX

```
1. DISCJX->EX, clear
2. RF->DISCJX
3. disc DISCJX, clear
  (A>=0)
  4. EX->DISCJX, clear
  5. IR -S-> EX, clear      # consume operand; assumes IR<0 so disc not triggered
  6. EX -S-fill99exS-> IR, clear 
  (A<0)
  4. EX->DISCJX, clear
     goto nearjump
```


#### JZ XX   (NB treats M00 as P00)

```
1. DISCJX -> EX, clear
2. RF -shiftA-> DISCJX, trigger ft2
3. DISCJX -> ft2.arg
4. wait
5. wait
6. ft2.AxxS -> DISCJX
7. goto JN-3
```


#### JIL XX

```
1. DISCJX -> EX, clear
2. RF -shiftA-> DISCJX, trigger ft2
3. DISCJX -> ft2.arg
4. wait
5. wait
6. ft2.BxxS -> DISCJX
7. goto JN-3
```


#### JSR XXXX

```
1. NEWPC -> EX
2. IR -extract-pc -> NEWPC
3. PC -shiftl4-pc -> NEWPC  $discft-1
4. (send PC)                $discft-2
5. NEWPC -> PC              $discft-1
6. (send NEWPC)             $discft-2
goto fetchline
 . EX -> NEWPC  # parallel with p-fetchline
```


#### RET

```
1. NEWPC -> EX
2. nop  # because sharing sequence
3. PC -shiftr4-pc -> NEWPC  $discft-1
4. (send PC)                $discft-2
5. NEWPC -> PC              $discft-1
6. (send NEWPC)             $discft-2
goto fetchline
 . EX -> NEWPC  # parallel with p-fetchline
```
