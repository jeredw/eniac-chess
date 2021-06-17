# experiment with shift adapter cables

s cy.op 1a

# initiating pulse to 1-1
p i.io 1-1

# 1-1: load constant into a1 from constant transmitter
#
p 1-1 c.26i 
s c.s26 Jlr
#s c.jl M
s c.j1 1
s c.j2 1
s c.j3 2
s c.j4 2
s c.j5 3
s c.j6 3
s c.j7 4
s c.j8 4
s c.j9 5
s c.j10 5
p c.o 1       # output to data bus 1

p 1-1 a1.5i   # need one of 5-12 here because 1-4 don't have outputs 
p 1 a1.a      # read from data bus 1
s a1.op5 a
p a1.5o 1-2   # goto 1-2


# 1-2 test adapters
#
p 1-2 a1.6i   # a1.A -> d1 (data bus 1), a2.S -> d2
s a1.op6 AS
p a1.A 1
p a1.S 2

# shift left 2
p 1-2 a2.1i   
s a2.op1 a
p 1 ad.s.1.2
p ad.s.1.2 a2.a  

# shift right 2
p 1-2 a4.1i   
s a4.op1 a
p 1 ad.s.2.-0     # now test shift "-0", was: # a4 = a1>>2
p ad.s.2.-0 a4.a  

# keep first 4 digits
p 1-2 a6.1i   
s a6.op1 a
p 1 ad.d.3.4      # a6 = first four digits of a1
p ad.d.3.4 a6.a  

# AABBCCDDEE -> DDEE00AABB into a8, via d4
p 1-2 a8.1i   
s a8.op1 a
p 1 ad.s.4.6 
p ad.s.4.6 4
p 1 ad.s.5.-6 
p ad.s.5.-6 4
p 4 a8.a  

# AABBCCDDEE -> EE000000AA into a10
p 1-2 a10.1i   
s a10.op1 a
p 1 ad.s.6.-8
p ad.s.6.-8 a10.a  
# p 1 ad.s.6.8

# AABBCCDDEE -> 0000CCBBAA into a12, via d3
# computed as AA sd.x.8 + BB (sd.x.6 then s.x.2) + CC (sd.x4 then s.x.4)
# from bus 1 to 3 (bus 2 used for a8)
p 1-2 a12.1i   
s a12.op1 a

p 1 ad.sd.7.8
p ad.sd.7.8 3

p 1 ad.sd.8.6
p ad.sd.8.6 ad.s.9.2   
p ad.s.9.2 3

p 1 ad.sd.10.4
p ad.sd.10.4 ad.s.11.4    
p ad.s.11.4 3

p 3 a12.a

# a14: drop first two digits and sign
p 1-2 a14.1i   
s a14.op1 a
p 2 ad.d.12.-2      # drop first two digits -a1, also drop the PM digit (sign)
p ad.d.12.-2 a14.a  

# a16: Move 1,2 of -a1 into 10,8 (left shift by 8, drop sign)
p 1-2 a16.1i   
s a16.op1 a
p 2 ad.s.13.8
p ad.s.13.8 a16.a  

# a18: keep only sign (M)
p 1-2 a18.1i   
s a18.op1 a
p 2 ad.d.14.0      # keep 0 digits
p ad.d.14.0 a18.a  




