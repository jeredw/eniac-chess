#s cy.op 1a

# Read succesive instructions lines and "execute" individual instructions
#
# Accumulator layout
# ------------------
# a1 - PC
#    Program counter. A three level stack of 3 digit addresses, current PC on right. 
# a2 - IR
#    Instruction register. Holds up to 5 instructions queued to execute after
#    loading from a function table line. Rightmost instruction is next.
#    Instructions are stored in 9's complement form, to make it easy to detect
#    when the register is empty (adding 1 to 9999999999 flips the sign)
# a3 - EX 
#   "Execution" register. Holds instruction to be executed and sends to decode.
#   Cleared before instruction execute starts, can be used as temp for instruction
# a4 - LS
#   Load/save. Registers FGHIJ. Location of accumulator read/writes.
# a13  - register file 
#    Registers ABCDE of the virtual machine. Use a13 so we can print it.
#
# Control cycle
# -------------
# This is the setup that turns the ENIAC into a CPU: fetch, decode, execute. 
# The basic idea is from "Central Control for ENIAC", Adele Goldstine, 1947
# Control lines as follows:
#
#
# 1-1 begin fetch cycle
#      - clear EX
# 1-2 do we need to fetch?
#      - discriminate on IR: M to 1-3, P to 1-4
#      - EX = IR
# 1-3 no fetch needed, consume instruction
#      - IR(a2) = EX(a3)>>2 + 1
#      - goto 2-1
# 1-4 no more instructons in IR, load new line from ft
#      - stimulate FT
#      - clear IR (should already be, but we may go to 1-4 after loading PC in jump instructions )
#      - clear EX
#      - delay 4 then goto 1-6
# 1-5 ft argument request
#      - FT <- bottom two digits of PC
# 1-6 read ft line of instructions
#      FT sends complement of A and B
#      - IR = M I6 I5 I4 I3 I2+1 = B2B1 B4B3 B6B5 A2A1 A4A3+1
#      - EX = M 99 99 99 99 I1 = 99 99 99 99 A6A5 +1?
#      - PC += 1
#      - goto 2-1
#
# 2-1 dispatch instruction in low two digits of EX
#      - EX += 53 from ct
#      now EX is 153-I
#      goto 2-3
# 2-2 instruction decode: I >= 53?
#      - reset all MP steppers
#      - discriminate on EX, P to 5-4 and M to 5-6
#
# 2-3 dispatch I > 53
#      - EX += some magic constant from CT
#      - goto 2-4
# 2-4 dispatch I>53 continued
#      - send I2 to mp.G
#      - send I1 to mp.H, mp.J, mp.K
#      - goto 2-5
# 2-5 start execution I>52
#      - in pulse to MP.G
#
# 2-6 dispatch I<=53
#      - send 9-I2 to A
#      - send 9-I1 to mp.B, mp.C, mp.D, mp.E, mp.F, mp.G
#      - goto 2-9
# 2-7 start executio I<53
#      - in pulse to MP.A


# 3-1 to 9-9: instruction program lines. Loop to 1-1 (fetch) when done


# dummy programs used:
# a20.12 - from 1-1 fetch line M
# a20.11 - from 1-1 fetch line P

# data trunks used
# d8  - IR.A
# d9  - IR.S
# d10 - d8 permuted: I5 I4 I3 I2 I1 -> I1 I5 I4 I3 I2 

# -- 1-1 begin fetch cycle

# initiate button
p i.io 1-1

# - clear EX(a3)
p 1-1 a3.5i
s a3.op5 0
s a3.cc5 C
p a3.5o 1-2


# -- 1-2 discriminate on IR (a2): M to 1-3, P to 1-4
# During this cycle we both discriminate and read out the contents of IR into EX
# We permute IR into EX to put next instruction in first digits to setup discrimination on decode

# - IR.A -> d8, IR.S-> d9
p 1-2 a2.6i
s a2.op6 AS # send on both A and S outputs so one of 1-3,1-8 gets a pulse
s a2.cc6 C  # clear IR after transmission
p a2.A 8
p a2.S 9

# IR.M -> 1-3 (no fetch) via dummy program a20.11 on 9-1
p 8 ad.dp.1.11
p ad.dp.1.11 9-1
p 9-1 a20.11i  # IR < 0
p a20.11o 1-3

# IR.P -> 1-8 (fetch line) via dummy program a20.12 on 9-2
p 9 ad.dp.2.11
p ad.dp.2.11 9-2
p 9-2 a20.12i  # IR >= 0
p a20.12o 1-8

# EX(a3) = IR(a2) permuted, I5 I4 I3 I2 I1 -> I1 I5 I4 I3 I2, assembled on d10
# This puts the next instruction in the left of EX, ready to discriminate
p 1-2 a3.1i   
s a3.op1 b

# extract IR2,1 and shift to far left. 
p 8 ad.s.19.8
p ad.s.19.8 10

# Shift the rest right, then drop the first two digits so the sign extend doesn't give 99
p 8 ad.s.20.-2
p ad.s.20.-2 ad.d.21.-2 
p ad.d.21.-2 10

p 10 a3.b


# -- 1-3 no fetch needed, begin instruction decode
# EX is now 100-I1 99-I5 99-I4 99-I2 99-I1
# Begin decode by adding 53 to EX, from constant transmitter

# P53 -> d1
p 1-3 c.26i 
s c.s26 Klr
s c.k10 5
s c.k9  3 
p c.o 1 

# EX(a3) += d1
p 1-3 a3.6i
s a3.op6 a
p 1 a3.a
p a3.6o 1-4     # goto 1-4, discriminate opcode

# -- 1-4 discriminate I1>=53, to switch between two decode pathways
# Also store shifted instructions back to IR(a2), this deletes just-dispatched opcode

p 1-4 a3.7i
s a3.op7 AS
p a3.A 1
p a3.7o 2-1  # for now just print EX

# Store EX(a3) back to I2(a2), with opcode replaced by 99, 
# and add 1 to rightmost instruction (overflow if no more inst)
p 1-4 a2.1i   
s a2.op1 a
p 1 ad.s.17.2  # set EX10,9 to 99 by shifting left 2 then right 2
p ad.s.17.2 ad.s.18.-2 
p ad.s.18.-2 a2.a
s a2.cc1 C      # add 1 to next instruction, this is key to detecting no more opcodes


# -- 1-8 no more instructons in IR, load new line from ft
# - stimulate FT, goto 1-5 for argument
# - delay 4 then goto 1-6

# - clear IR (a2) (not needed? already zero here from overflow?) and delay 4
p 1-8 a2.7i 
s a2.op7 0   # nop
s a2.cc7 C   # then clear 
s a2.rp7 4   # repeat 4 to wait for FT result
p a2.7o 1-10  # then go to 1-10

# - clear EX (a3) as well, it will also receive from FT
p 1-8 a3.8i  
s a3.op8 0
s a3.cc8 C

p 1-8 f1.1i   # trigger ft
s f1.rp1 1    # 1 repeat (neccessary?)
s f1.op1 S0   # send complement, don't offset argument
s f1.cl1 C    # pulse on C when done
p f1.C 1-9    # proceed to 1-9 when ready for argument


# -- 1-9 ft argument request
# - FT <- bottom two digits of PC (a1)

p 1-9 a1.6i   # PC -> d2
s a1.op6 A
p a1.A 2      # use d2 not d1 because we're going through adapter
p 2 ad.sd.4.0 # bottom two digits of d2
p ad.sd.4.0 f1.arg

# -- 1-10 read ft line of instructions
#  - FT sends complement of A and B
#  - IR (a2) = M I6 I5 I4 I3 I2+1 = B2B1 B4B3 B6B5 A2A1 A4A3+1
#  - EX (a3) = M 99 99 99 99 I1 = 99 99 99 99 A6A5+1
#  - PC (a1) += 1
#  - goto 2-1 decode

p f1.A 3      # ft.A -> d3
p f1.B 4      # ft.B -> d4

# build up the re-ordered IR on d5, then d5 -> IR(a2)
# use deleters to prevent sign extension of 9s when isolating opcodes
# Simulator makes this a lot harder than it needs to be... in reality, 
# all this is a single adapter with the pins soldered in permuted order.

p 3 ad.d.5.-6   # A4A3
p ad.d.5.-6 ad.s.6.-2
p ad.s.6.-2 5

p 3 ad.d.7.-8   # A2A1
p ad.d.7.-8 ad.s.8.2 
p ad.s.8.2 5

p 4 ad.d.8.-4   # B6B5 digits don't move but must delete other digits
p ad.d.8.-4 ad.s.9.-4
p ad.s.9.-4 ad.s.10.4
p ad.s.10.4 5

p 4 ad.d.11.-6   # B4B3
p ad.d.11.-6 ad.s.12.-2
p ad.s.12.-2 ad.s.13.6
p ad.s.13.6 5

p 4 ad.s.14.8  # B2B1, don't need to delete left digits b/c we want M sign
p ad.s.14.8 5

# B2B1 B4B3 B6B5 A2A1 A4A3+1 -> IR(a2)
p 1-10 a2.8i   
s a2.op8 b
s a2.cc8 C    # +1
p 5 a2.b     
p a2.8o 2-1   # goto 2-1, decode

# 99 99 99 99 A6A5+1 -> EX(a3)
p 1-10 a3.2i   
s a3.op2 g
s a3.cc2 C    # +1
p 3 ad.s.15.-4     # A>>4 to select first instruction, and pad with 9s
p ad.s.15.-4 a3.g

# PC (a1) += 1
p 1-10 a1.1i
s a1.op1 e    # nothing connected
s a1.cc1 C    # +1


# 2-1 decode instruction in low two digits of EX

# decode magic here
p 2-1 a13.5i  # clear a13
s a13.op5 0
s a13.cc5 C
p a13.5o 2-2

p 2-2 a3.9i   # EX(a3) -> d1
s a3.op9 A
p a3.A 1
p a3.9o 2-3

p 2-2 a13.1i  # d1 -> RF(a13)
s a13.op1 a
p 1 a13.a

# 2-3 print "decoded" instruction, it's in a13
p 2-3 i.pi 
s pr.2 P
s pr.3 P





# ------------ DATA --------------

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

