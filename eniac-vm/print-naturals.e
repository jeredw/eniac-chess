# print integers

# initiating pulse to 1-1
p i.io 1-1

# 1-1: print
p 1-1 i.pi   # print!
s pr.3 P    # prints low half of accumulator 13 because why?
p i.po 1-2   # go to 1-2/increment

# 1-2: increment

# send 1 from constant transmitter
p 1-2 c.26i 
s c.s26 Jlr
s c.j1 1
p c.o 1

# add 1 from constant transmitter to acc 
p 1-2 a13.5i  # use 5 because 1-4 don't have outputs 
p 1 a13.a
s a13.op5 a

# back to 1-1/looptop
#p a13.5o 1-1
