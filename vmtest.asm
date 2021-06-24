; VM test program
; Run through sequence of opcode tests of increasing complexity
; Print test number and result after each 
; Success is [test num]00

; directives are indented and start with a period
  .isa v4  ; select isa version before any instructions
  .org 100 ; select function table and row number
           ;   hundreds digit is function table [123]
           ;   tens/units digit is row within table


; -- 00 - 09 -- 
; The basics needed to run tests, including arithmetic
; PRINT, INC, DEC, CLR, MOV #X,A, SWAP A,[BCDE], ADD, SUB

; A=B=0 here
; 00: test PRINT
  print AB


; 01: test inc, which also gets us to next test number
  inc A
  print AB


; 02: test swap A,B, dec
  inc A       ; A=2, B=0
  swap A,B    ; A=0, B=2
  inc A       ; A=1, B=2
  dec A       ; A=0, B=2
  dec A       ; A=-99, B=2
  inc A       ; A=0, B=2
  swap A,B    ; A=2, B=0
  print AB


; 3: test swap A,C
  inc A
  swap A,C
  inc A
  swap A,C
  print AB


; 4: test swap A,D
  inc A
  swap A,D
  inc A
  swap A,D
  print AB


; 5: test swap A,E
  inc A
  swap A,E
  inc A
  swap A,E
  print AB


; 6: test clr A
  inc A
  swap A,B

  inc A
  clr A

  swap A,B
  print AB


; 7: test mov #X, A
.align     ; don't test opcode line boundary handling here
  inc A
  swap A,B

  mov 3,A
  dec A
  dec A
  dec A

  swap A,B
  print AB


; 8: test add D,A, sub D,A
; Add 32+32 and subtract 64
  inc A
  swap A,B

  clr A     ; set C=D=0
  swap A,C
  clr A
  swap A,D

  mov 64,A
  swap A,C
  mov 32,A
  swap A,D  ; now A=0, C=64, D=32

  add D,A   ; now A=32
  add D,A   ; now A=64

  swap A,C  ; swap C,D => C=32, D=64
  swap A,D
  swap A,C

  sub D,A   ; should be 64-64=0

  swap A,B
  print AB


; -- 10-19 --
; Jumps, conditionals, bank switching, subroutines
; JMP, JN, JZ, JMP FAR, JSR, RET
; All of these tests start with .align so we get consistent operand splitting
; We also switch to bank 2 here

; 10: JMP
.align
  mov 10,A
  jmp jmptest

jmptest
  print AB


; 11: JN. Also tests that DEC A can produce a negative result
.align
  inc A
  swap A,B
  dec A
  jn jntest
  dec A      ; cause failure if jn not taken

jntest
  inc A
  swap A,B
  print AB


; 12: jmp far, with and without bank switch
.align
  inc A
  swap A,B

  jmp far jmpfar1
  inc A       ; report error if jump not taken
  swap A,B
  print AB
  halt

jmpfar1
  jmp far jmpfar2
  inc A
  swap A,B
  print AB
  halt

; this is used for far JSR/RET test -- weird to put it in the middle of this test, but
inca
 inc A        ; error 01 if ret does not jump
 ret

; continue in new bank
.org 200      ; tests chasm encoding of bank:line as 90:00 = 8999
jmpfar2
  jmp far jmpfar3
  inc A
  swap A,B
  print AB
  halt

jmpfar3
  swap A,B
  print AB


; 13: use JN in a loop. Ensure executed 10 times.
; A=loop counter (counts down), B = testnum, D=count iterations (counts up)
  inc A
  swap A,B

  clr A
  swap A,D   ; clear
  mov 9,A
t13loop
  swap A,D
  inc A
  swap A,D
  dec A  
  jn t13done
  jmp t13loop
t13done
  mov 10,A
  sub D,A    ; result=10-number of iterations counted

  swap A,B
  print AB


; 14: JSR/RET 
  inc A
  swap A,B

  jsr t14sub  ; test near 

  dec A       ; error 99 if jsr does not jump
  jmp t14next

t14sub
 inc A        ; error 01 if ret does not jump
 ret

t14next
 jsr inca     ; now test far
 dec A        ; error 99 if jsr does not jump
 
 swap A,B
 print AB


; -- DONE --
  mov 99,A
  print AB
  halt


