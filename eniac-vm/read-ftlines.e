# Read and print successive lines of function table 1
# a1  - PC
# a13 - retrived value
# c26 - 1
# d.1 - increment PC
# d.2 - send to FT
# d.3 - retrieve from FT

# program start
p i.io 1-1

# STEP 1-1: a13=0, trigger ft 
# 

p 1-1 a13.5i  # delay four cycles for RT results
s a13.op5 0   # nop
s a13.cc5 C   # then clear 
s a13.rp5 4   # repeat 4
p a13.5o 1-3  # then go to 1-3

p 1-1 f1.1i   # trigger ft
s f1.rp1 1    # 1 repeat
s f1.op1 A0   # don't offset argument 
s f1.cl1 C    # pulse on C when done
p f1.C 1-2    # proceed to 1-2 when ft ready for argument


# STEP 1-2: lookup a1
#
p 1-2 a1.5i   # a1 -> d.2
s a1.op5 A
s a1.rp5 1
p a1.A 2

p 2 f1.arg    # d.2 -> ft


# STEP 1-3: store retrieved value to acc13
#
p f1.A 3      # output ft value to d.3

p 1-3 a13.6i  # d3 -> a13, stores value
p 3 a13.α     
s a13.op6 α
s a13.rp6 1
p a13.6o 1-4  # print when done


# STEP 1-4: print a13, increment a1
#
p 1-4 c.26i   # constant 1 -> d.1
s c.s26 Jlr
s c.j1 1
p c.o 1

p 1-4 a1.1i   # a1 += d.1
p 1 a1.a
s a1.op1 a

p 1-4 i.pi    # print!
s pr.2 P
s pr.3 P
p i.po 1-1   # back to start



# ------------ DATA --------------

# function table init
s f1.mpm1 p   # don't negate

# function table values
s f1.RA0S p
s f1.RA0L6 1
s f1.RA0L5 2
s f1.RA0L4 3
s f1.RA0L3 4
s f1.RA0L2 5
s f1.RA0L1 6

s f1.RA1L6 6
s f1.RA1L5 6
s f1.RA1L4 6
s f1.RA1L3 6
s f1.RA1L2 6
s f1.RA1L1 6

s f1.RA2L6 5
s f1.RA2L5 5
s f1.RA2L4 5
s f1.RA2L3 5
s f1.RA2L2 5
s f1.RA2L1 5

s f1.RA3L6 4
s f1.RA3L5 4
s f1.RA3L4 4
s f1.RA3L3 4
s f1.RA3L2 4
s f1.RA3L1 4

s f1.RA4L6 3
s f1.RA4L5 3
s f1.RA4L4 3
s f1.RA4L3 3
s f1.RA4L2 3
s f1.RA4L1 3

s f1.RA5L6 2
s f1.RA5L5 2
s f1.RA5L4 2
s f1.RA5L3 2
s f1.RA5L2 2
s f1.RA5L1 2

s f1.RA6L6 1
s f1.RA6L5 1
s f1.RA6L4 1
s f1.RA6L3 1
s f1.RA6L2 1
s f1.RA6L1 1
