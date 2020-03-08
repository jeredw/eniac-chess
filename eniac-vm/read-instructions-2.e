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
# a4 - SAVE
#   Temporarily holds value of register file. Accessed with SAVE, RESTORE 
#   instructions. Z register is mapped to the saved A register.
# a13  - register file 
#    Registers A-E of the virtual machine. Use a13 so we can print it.
#
# Control cycle
# -------------
# This is the setup that turns the ENIAC into a CPU: fetch, decode, execute. 
# The basic idea is from "Central Control for ENIAC", Adele Goldstine, 1947
# Control lines as follows:
#
# 1-1 initialize
#
# 2-1 begin fetch cycle
#      - clear EX
#      - discriminate on IR, M to 3-1, P to 4-1
# 3-1 instruction ready in IR
#      - EX += IR
#      - clear IR
# 3-2 shift IR right, fill in left with 99
#      - IR += EX>>2
#      - IR += P 9900000000 from ct
#      - IR +=1 to cause sign rollover if empty
#      - goto 5-2
# 4-1 load new line of instructions from ft
#      - stimulate FT
#      - clear IR (not needed?)
#      - clear EX
#      - delay 4 then goto 4-3
# 4-2 fetch ft argument request
#      - FT <- bottom two digits of PC
#      (function table decode logic here)
# 4-3 read ft line of instructions
#      FT sends complement of A and B
#      - IR = M I6 I5 I4 I3 I2+1 = B2B1 B4B3 B6B5 A2A1 A4A3+1
#      - EX = M 99 99 99 99 I1 = 99 99 99 99 A6A5
#      - PC += 1
#      - goto 5-1
#
# 5-1 dispatch instruction in low two digits of EX
#      - EX += 53 from ct
#      now EX is 153-I
#      goto 5-3
# 5-2 instruction decode: I >= 53?
#      - reset all MP steppers
#      - discriminate on EX, P to 5-4 and M to 5-6
#
# 5-3 dispatch I > 53
#      - EX += some magic constant from CT
#      - goto 5-4
# 5-4 dispatch I>53 continued
#      - send I2 to mp.G
#      - send I1 to mp.H, mp.J, mp.K
#      - goto 5-5
# 5-5 start execution I>52
#      - in pulse to MP.G
#
# 5-6 dispatch I<=53
#      - send 9-I2 to A
#      - send 9-I1 to mp.B, mp.C, mp.D, mp.E, mp.F, mp.G
#      - goto 5-9
# 5-7 start executio I<53
#      - in pulse to MP.A


# 6-1 to 9-11: instruction program lines. Loop to 2-1 (fetch) when done


# dummy programs used:
# a20.12 - from 2-1 fetch line M
# a20.11 - - from 2-1 fetch line P



# -- 1-1 initialize

# initiate button
p i.io 1-1

# start PC (a1) at 0
p 1-1 a1.5i
s a1.op5 0
a a1.cc5 C
p a1.5o 2-1

# start IR (a2) at 0 to force a fetch on first cycle
p 1-1 a2.5i
s a2.op5 0
a a2.cc5 C


# -- 2-1 begin fetch cycle

# - clear EX (a3)
p 2-1 a3.1i
s a3.op1 0
s a3.cc1 C

# - discriminate on IR (a2), M to 3-1, P to 4-1
p 2-1 a2.5i
s a2.op5 AS # send on both A and S outputs so one of 3-1,4-1 gets a pulse

# use sign digit adapters and dummy programs a20.11, a20.12 to discriminate
p a2.A ad.dp.1.11
p ad.dp.1.11 a20.11i  # IR < 0
p a2.11o 3-1

p a2.S ad.dp.2.11
p ad.dp.2.11 a20.12i  # IR >= 0
p a2.12o 4-1


# -- 3-1 instruction ready in IR

# - EX (a3) += IR (a2), clear IR (a2)
p 3-1 a2.5i   # IR -> d1
s a2.op5 A
s a2.cc5 C    # clear IR
p a2.A 1
p a2.5o 3-2

p 3-1 a3.2i   # d1 -> EX 
s a3.op2 a
p 1 a3.a 


# -- 3-2 shift IR right, fill in left with 99, add 1
# - IR (a2) += EX (a3)>>2. 
# - IR +=1 to cause sign rollover if empty
# - goto 5-2

# EX < 0 here (we discriminated at 2-1) so shift will sign-extend 99 into left of IR
# Adding 1 to IR will overflow 99 99 99 99 99 (no more instructions)

p 3-2 a3.5i   # EX (a3) -> d1
s a3.op5 A
p a3.A 1 
p a3.5o 5-2   # goto 5-2 to dispatch instruction in EX

p 3-1 a2.1i   # IR (a2) += d1>>2 + 1 
p 1 a.s.3.-2  # shift EX right by 2, to delete instruction we will execute
p a.s.3.-2 a2.a 
s a2.op1 a
s a2.CC1 C    # add 1


# -- 4-1 load new line of instructions from ft
# - stimulate FT, goto 4-2 for argument
# - delay 4 then goto 4-3

# - clear IR (a2) (not needed? already zero here from overflow?) 
p 4-1 a2.6i 
s a2.op6 0   # nop
s a2.cc6 C   # then clear 
s a2.rp6 4   # repeat 4. This is our delay.
p a2.6o 4-3  # then go to 4-3

# - clear EX (a3) as well, it will also receive from FT
p 4-1 a2.6i  
s a2.op6 0
s a2.cc6 C

p 4-1 f1.1i   # trigger ft
s f1.rp1 1    # 1 repeat
s f1.op1 A0   # don't offset argument 
s f1.cl1 C    # pulse on C when done
p f1.C 4-2    # proceed to 4-2 when ready for argument


# -- 4-2 fetch ft argument request
#  - FT <- bottom two digits of PC (a1)
#  (function table decode logic here)

p 4-2 a1.6i   # a1 -> d2
s a1.op6 A
p a1.A 2

p 2 ad.sd.4.0 # bottom two digits of d2
p ad.sd.4.0 f1.arg

# 4-3 read ft line of instructions
#      FT sends complement of A and B
#      - IR (a2) = M I6 I5 I4 I3 I2+1 = B2B1 B4B3 B6B5 A2A1 A4A3+1
#      - EX (a3) = M 99 99 99 99 I1 = 99 99 99 99 A6A5
#      - PC (a1) += 1
#      - goto 5-1

p f1.A 3      # ft.A -> d
p 4-3 a2.7i   # d3 -> IR (a2)
p 3 a2.b     
s a2.op7 b
p a2.7o 5-1   # goto 5-1, dispatch

p f1.B 4      # ft.B -> d4
p 4-3 a2.2i   # d4 -> EX (a3)
s a2.op2 b
p 4 a2.b

# PC (a1) += 1
p 4-3 a1.1i
s a1.op1 b    # nothing connected to a1.b, add 0
a a1.cc1 C    # +1


# 5-1 dispatch instruction in low two digits of EX
#      - EX += 53 from ct
#      now EX is 153-I
#      goto 5-3

# decode magic here


# 5-2 instruction decode: I >= 53?
#      - reset all MP steppers
#      - discriminate on EX, P to 5-4 and M to 5-6
#
# 5-3 dispatch I > 53
#      - EX += some magic constant from CT
#      - goto 5-4
# 5-4 dispatch I>53 continued
#      - send I2 to mp.G
#      - send I1 to mp.H, mp.J, mp.K
#      - goto 5-5
# 5-5 start execution I>52
#      - in pulse to MP.G
#
# 5-6 dispatch I<=53
#      - send 9-I2 to A
#      - send 9-I1 to mp.B, mp.C, mp.D, mp.E, mp.F, mp.G
#      - goto 5-9
# 5-7 start executio I<53
#      - in pulse to MP.A









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

