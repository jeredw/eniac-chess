# Putting the Chess in ENIAC Chess
This document describes how we wrote a tiny chess program on top of [chessvm](easm.md), our virtual machine for the ENIAC. The main limitation is memory: we have only 75 words. Speed is also a concern, as the ENIAC executes only about 500 instructions per second. The real constraint here is historical: the time to compute a move has to be less than the time between vaccuum tube failures, which was apprently 24-48 hours.

# Square numbering
Chessvm has hardware support for chess in the form of the `jil A` instruction, branch if A contains an illegal square index. We number squares as rank|file from 11 to 88. Moving right adds 1, moving up adds 10. We can continue adding or subracting and use `jil` to determine when we've run off the board. 

# Board representation
If we use one word per square, that leaves us only 11 words for all computation, which will never hold multiple search stack levels. The shortest board representation is a piece list, the location of all 32 starting pieces, but that has two serious drawbacks. First, it is very slow to find the contents of a particular board square, which is a frequent operation. Second, extra memory is required to keep track of pawn promotions.

# Memory map
```
00   B  B  B  B  B
05   B  B  B  B  B
10   B  B  B  B  B
15   B  B  B  B  B
20   B  B  B  B  B
25   B  B  B  B  B
30   B  B  O  O  O
35   O  S0 S0 S0 S0
40   S0 S0 S0 S0 S0
45   G  S1 S1 S1 S1
50   S1 S1 S1 S1 S1
55   G  S2 S2 S2 S2
60   S2 S2 S2 S2 S2
65   G  S3 S3 S3 S3
70   S3 S3 S3 S3 S3

B=board square, O=other piece square, Sx=stack frame x, G=global
```
