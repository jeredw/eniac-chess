### 'p' commands are plugs, essentially wiring between ins and outs.   ###
### 's' commands are switches, essentially the settings for 'programs' ###



#################################################################
### This section wires up some accumulators to data trunks ######
#################################################################
### The A used is the additive output of an accumulator,   ######
### in other words, the sum of the accumulator is output here ###
### When the program is switched to output.                ######
#################################################################
### alpha and beta are inputs, when the program is told to ######
### take an input, these plugs allow for numbers to be sent #####
#################################################################
### Things can be plugged directly to eachother and not to a ####
### trunk if they're only needed in one other place. I believe ##
### this works always and for example, the last two in this  ####
### could be simplified to 'p a13.A a20.beta' 				#####
#################################################################
# Wire Constant Emitter [OUTPUT] to Data Trunk 1
p c.o 1
# Wire Accumulator 13 [ALPHA - INPUT] to Data Trunk 1
p 1 a13.α
# Wire Accumulator 20 [ALPHA - INPUT] to Data Trunk 1
p 1 a20.α
# Wire Accumulator 13 [CAPITAL A - OUTPUT] to Data Trunk 2
p a13.A 2
# Wire Accumulator 20 [BETA - INPUT] to Data Trunk 2
p 2 a20.β
#################################################################
###       This section is all about program signals.       ######
#################################################################
### Program signals start programs when recieved, and output a ##
### single signal on their output trunk. a20.6o for example,  ###
### means the signal sent when program 6 on 20 finishes, and ####
### a13.5i is the port to send a signal to start program 5 on ###
### accumulator 20.											  ###
#################################################################
### Keep in mind, when you pulse a program to start, and it #####
### expects a number from another accumulator, that other #######
### accumulator needs to be triggered by the same pulse so that #
### it outputs while the other expects to recieve			#####
### essentially, you need output programs and input programs ####
### for each interaction/exchange.							#####
#################################################################
### You have at least 9 trunks to use, I didn't see any real ####
### maximum.												 ####
#################################################################
# Output from the program starter to program trunk 1-1. 
# This is what happens when you type 'b i' (button initiator or something) when running an example
p i.io 1-1
# This wires the constant emitter to be triggered by 1-1
p 1-1 p.Ci
# This wires the constant emmitter output to 1-4
p p.C1o 1-4
# This connects (starts) program 6 on accumulator 13 when 1-4 is pulsed
p 1-4 a13.6i
# This connects (starts) program 6 on accumulator 20 when 1-4 is pulsed
p 1-4 a20.6i
# This pulses 1-2 when 5 finishes on accumulator 20
p a20.5o 1-2
# This connects (starts) program 7 on accumulator 20 when 1-2 is pulsed
p 1-2 a20.7i

p a20.6o 1-3

p 1-3 a13.5i

p 1-3 a20.5i

p 1-3 c.26i

p a20.7o i.pi

p i.po 1-1


#################################################################
### This section covers switches. These are easy. Look at  ######
### the manual posted on learn shows you the switches on each ###
### panel. Essentially just the settings for each dial and  #####
### how you "write" programs.								 ####
#################################################################
# set program 5 on accumulator 13 to expect [INPUT] on alpha
s a13.op5 α
# set program 6 on accumulator 13 to [OUTPUT] on A
s a13.op6 A
# set repeat count on program 5, accumulator 13 to 1 time
s a13.rp5 1
# set repeat count on program 6, accumulator 13 to 2 times
s a13.rp6 2
# set program 5 on accumulator 20 to expect [INPUT] on alpha
s a20.op5 α
# set program 6 on accumulator 20 to expect [INPUT] on beta
s a20.op6 β
# set program 7 on accumulator 20 to [OUTPUT] on A
s a20.op7 A
# set repeat count on program 5, accumulator 20 to 1 time
s a20.rp5 1
# set repeat count on program 6, accumulator 20 to 2 times
s a20.rp6 2
# set repeat count on program 7, accumulator 20 to 1 time
s a20.rp7 1
# set program 26 on constant transmitter to J (you can also use K in a similar way). LR means both digit sets (dont worry about it)
s c.s26 Jlr
# set constant j digit 1's value to 1
s c.j1 1


## set master programmer values, this setup is a little past what I can explain but essentially says DO THIS 9999 TIMES
s p.d17s1 9
s p.d16s1 9
s p.d15s1 9
s p.d14s1 9
s p.d14s2 1
s p.cC 4


## These are in pairs, and 5th is not a full pair (only one of the two digit sets will print)
## Watch out, accumulator 17 works for operations but doesn't print (ever, I think) anything besides 0s.
## Print All of Accumulator 13 digits 
s pr.2 P
s pr.3 P
## Print All of accumulator 20 digits
s pr.15 P
s pr.16 P
