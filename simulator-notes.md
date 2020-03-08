Notes on simulator oddities


Commands
--------

b p = pulse button

dt, pt, u do nothing (?)


Adapters
--------
Each adapter type is numbered and represents a unique communication channel.

ad.[type].[id].[parameter]

the id's are unique within the setup (you re-use them to do a wired-or, see below)

So ad.s.1.2 is an adapter with id 1 that shifts it input 2 to the right. 
Simplest use is a patch directly between units, like this:

p a1.A ad.s.1.2
p ad.s.1.2 a2.a 

If you want to use the same output (e.g. A) through different adapters on
different programs, then connect adapters to a data trunk

p a1.A 1            # output a1 to d1
p 1 a2.a            # copy directly to a2
p 1 ad.s.d.1.-3     # adapter clears first 3 digits 
p ad.s.d.1.-3 a3.a  # a3 loaded from adapter

The ad.sd.[id].[x] adapter type ("special digit") takes 2 consecutive digits
starting at x+1 and places them in digits 1,2 (so a right shift by x)

You can combine the digits from two adapters by connecting them both to a bus:

# 1122334455 -> 5500000011
p 1 ad.s.1.6 
p ad.s.1.6 2
p 1 ad.s.2.-6 
p ad.s.2.-6 2
p 2 a1.a 

It's also possible to do this without an second data bus, by setting to adapters to the
same ID. Note that the order of these lines matters to the simulator 
(not sure why; this may exploit a hack, probably writing to a bus is cleaner)
p 1 ad.s.6.-8
p ad.s.6.-8 a1.a  
p 1 ad.s.6.8
s a1.op1 a


Printer switch settings
-----------------------

from sq3-comments.e
## These are in pairs, and 5th is not a full pair (only one of the two digit sets will print)
## Watch out, accumulator 17 works for operations but doesn't print (ever, I think) anything besides 0s.
s pr.3 P  <- print low half of accumulator 13

pr.n where n in [1..16], I think high and low halves of acc 13-20
8 acc X 10 digits = one 80 column punch card

READOUTS
--------

Top
---
000000000000010
?,?,?,?,?,?,?,?,?,?,?,?,?,init,pulse           


Accumulator
-----------

P 0000000000 0000000000 3 000010000000

sign, data, digit pulses, repeat, active program


Function table
--------------

10000000000 0 1 0 0 0

active program, 0 cycle 0 0 0 


Constants
---------

000000000000000000000000010000

active program 26