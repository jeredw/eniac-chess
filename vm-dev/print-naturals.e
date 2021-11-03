# print integers

# initiating pulse to 1-1
p i.io 1-1

# 1-1: print accumulator 13
p 1-1 i.pi    # print!
s pr.3 P      # prints low half of acc 13 
p i.po 1-2    # go to 1-2


# 1-2: increment accumulator 13
# Receive but don't connect anything to the input. Set cc switch to C for an extra +1
p 1-2 a13.5i  # use program 5 because 1-4 don't have outputs 
s a13.op5 a   # recieve on input a
s a13.cc5 C   # add +1 at the end

# back to 1-1. If commented out, steps once on each initiating pulse
p a13.5o 1-1

# press the start button
b i
