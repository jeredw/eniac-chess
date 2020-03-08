# Read and print successive lines of ft1, both A and B outputs this time
# a1  - PC
# a20 - A output from ft
# a19 - B output from ft
# c26 - 1
# d1 - increment PC
# d2 - send to FT
# d3 - from FT.A
# d4 - from FT.B

# program start
p i.io 1-1

# STEP 1-1: a20=0, a19=0, trigger ft 
# 
p 1-1 a20.5i  # delay four cycles for RT results
s a20.op5 0   # nop
s a20.cc5 C   # then clear 
s a20.rp5 4   # repeat 4
p a20.5o 1-3  # then go to 1-3

p 1-1 a19.5i  # clear a19
s a19.op5 0   # nop
s a19.cc5 C   # then clear 

p 1-1 f1.1i   # trigger ft
s f1.rp1 1    # 1 repeat
s f1.op1 A0   # don't offset argument 
s f1.cl1 C    # pulse on C when done
p f1.C 1-2    # proceed to 1-2 when ready for argument


# STEP 1-2: send a1 to the ft
#
p 1-2 a1.5i   # a1 -> d2
s a1.op5 A
s a1.rp5 1
p a1.A 2

p 2 f1.arg    # d2 -> ft


# STEP 1-3: store retrieved value to acc20, acc19
#
p f1.A 3      # ft.A -> d3
p 1-3 a20.6i  # d3 -> a20
p 3 a20.α     
s a20.op6 α
p a20.6o 1-4  # completed fetch

p f1.B 4      # ft.B -> d4
p 1-3 a19.6i  # d4 -> a19
p 4 a19.α     
s a19.op6 α

# STEP 1-4: shift four digits into 
# 

# STEP 2-x: print a20, increment a1
#
p 1-4 c.26i   # constant 1 -> d1
s c.s26 Jlr
s c.j1 1
p c.o 1

p 1-4 a1.1i   # a1 += d1
p 1 a1.a
s a1.op1 a

p 1-4 i.pi    # print a20,a19
s pr.13 P
s pr.14 P
s pr.15 P
s pr.16 P
p i.po 1-1   # back to start


# opcodes

# 10-00 NOP


# ------------ DATA --------------

# function table init
s f1.mpm1 p   # don't negate

# function table values
s f1.RA0L6 0
s f1.RA0L5 1
s f1.RA0L4 0
s f1.RA0L3 2
s f1.RA0L2 0
s f1.RA0L1 3

s f1.RB0L6 0
s f1.RB0L5 4
s f1.RB0L4 0
s f1.RB0L3 5
s f1.RB0L2 0
s f1.RB0L1 6


s f1.RA1L6 1
s f1.RA1L5 1
s f1.RA1L4 1
s f1.RA1L3 2
s f1.RA1L2 1
s f1.RA1L1 3

s f1.RB1L6 1
s f1.RB1L5 4
s f1.RB1L4 1
s f1.RB1L3 5
s f1.RB1L2 1
s f1.RB1L1 6


s f1.RA2L6 2
s f1.RA2L5 1
s f1.RA2L4 2
s f1.RA2L3 2
s f1.RA2L2 2
s f1.RA2L1 3

s f1.RB2L6 2
s f1.RB2L5 4
s f1.RB2L4 2
s f1.RB2L3 5
s f1.RB2L2 2
s f1.RB2L1 6


s f1.RA3L6 3
s f1.RA3L5 1
s f1.RA3L4 3
s f1.RA3L3 2
s f1.RA3L2 3
s f1.RA3L1 3

s f1.RB3L6 3
s f1.RB3L5 4
s f1.RB3L4 3
s f1.RB3L3 5
s f1.RB3L2 3
s f1.RB3L1 6


s f1.RA4L6 4
s f1.RA4L5 1
s f1.RA4L4 4
s f1.RA4L3 2
s f1.RA4L2 4
s f1.RA4L1 3

s f1.RB4L6 4
s f1.RB4L5 4
s f1.RB4L4 4
s f1.RB4L3 5
s f1.RB4L2 4
s f1.RB4L1 6

