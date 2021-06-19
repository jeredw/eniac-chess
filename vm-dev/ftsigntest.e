# Can we load PMA from FT?

s cy.op 1a

s f3.RA0S  P
s f3.RA0L6 6
s f3.RA0L5 5
s f3.RA0L4 4
s f3.RA0L3 3
s f3.RA0L2 2
s f3.RA0L1 1

s f3.RB0S  M
s f3.RB0L6 1
s f3.RB0L5 2
s f3.RB0L4 3
s f3.RB0L3 4
s f3.RB0L2 5
s f3.RB0L1 6 

s f3.mpm1 T
s f3.mpm2 T

# try to load this row into a1,a2

p i.io 1-1

p 1-1 f3.1i
s f3.op1 A0

p 1-1 a1.5i
s a1.op5 0
s a1.rp5 4

p a1.5o a1.6i
p a1.5o a2.6i

p f3.A a1.a
s a1.op6 a

p f3.B a2.a
s a2.op6 a

b i