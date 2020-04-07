# Test the ability to fire the same program from two different places

p i.io 1-1

# a1 = 1
p 1-1 a1.5i
s a1.op5 a
s a1.cc5 C
p a1.5o 1-2


p 1-2 a3.5i # dummy
s a3.op5 0
s a3.rp5 3
p a3.5o 1-3

# a1 = 2
p 1-3 a1.6i
s a1.op6 a
s a1.cc6 C
p a1.6o 1-4

# connection between "main" above and "subprogram" below

# - this works
#p 1-2 2-1 # first connection
#p 1-4 2-1 # second connection
p 2-1 a2.5i

# - this crashes
p 1-2 a2.5i
p 1-4 a2.5i


# sub-program a2.5i: a2 = 2*a1
# clear a2
s a2.op5 0
s a2.cc5 C
p a2.5o 2-2

# Send a1 to d1 twice
p 2-2 a1.7i
s a1.op7 A
s a1.rp7 2
p a1.A 1

# receive on a2 twice
p 2-2 a2.6i
s a2.op6 a
s a2.rp6 2
p 1 a2.a