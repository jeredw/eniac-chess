s cy.op 1a

# When can a ft perform successive reads?
# => Must wait til cycle after data from first read.
p i.io 1-1

# a1 has the ft argument
p a1.A f1.arg

# cycle 1: start first read
p 1-1 f1.1i    # stimulate ft
s f1.rp1 1
s f1.op1 A0
p 1-1 a20.12i  # delay for argument
s a20.op12 0
s a20.rp12 1
p a20.12o 1-2

# cycle 2: send argument
p 1-2 a1.5i
s a1.op5 A
p a1.5o 1-3

# cycle 3: increment arg for next read
p 1-3 a1.6i
s a1.op6 α  # unconnected
s a1.cc6 C
p a1.6o 1-4
p 1-3 a20.11i
s a20.op11 0
s a20.rp11 2
p a20.11o 1-5

# cycle 5: ft returns data in this time
p f1.A a2.α
p 1-5 a2.5i 
s a2.op5 α

# how soon can we trigger a new program?
# If we trigger in 1-5, ft sends first line again 4 cycles from now, i.e. we
# retrigger the first program!
#p 1-5 2-1
p 1-5 a20.5i
s a20.op5 0
s a20.rp5 1
p a20.5o 2-1

# cycle 1: another ft read
p 2-1 f1.2i   # stimulate ft
s f1.rp2 1
s f1.op2 A0
p 2-1 a20.10i  # delay for argument
s a20.op10 0
s a20.rp10 1
p a20.10o 2-2

# cycle 2: send argument
p 2-2 a1.7i
s a1.op7 A
p 2-2 a20.9i  # delay for data
s a20.op9 0
s a20.rp9 3
p a20.9o 2-5

# cycle 5: ft returns data again in this time
p f1.A a3.α
p 2-5 a3.5i 
s a3.op5 α


s f1.RA0L6 1
s f1.RA0L5 1
s f1.RA0L4 1
s f1.RA0L3 1
s f1.RA0L2 1
s f1.RA0L1 1

s f1.RA1L6 2
s f1.RA1L5 2
s f1.RA1L4 2
s f1.RA1L3 2
s f1.RA1L2 2
s f1.RA1L1 2

b i