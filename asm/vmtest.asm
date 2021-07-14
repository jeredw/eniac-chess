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
  print


; 01: test inc, which also gets us to next test number
  inc A
  print


; 02: test swap A,B, dec
  inc A       ; A=2, B=0
  swap A,B    ; A=0, B=2
  inc A       ; A=1, B=2
  dec A       ; A=0, B=2
  dec A       ; A=-99, B=2
  inc A       ; A=0, B=2
  swap A,B    ; A=2, B=0
  print


; 3: test swap A,C
  inc A
  swap A,C
  inc A
  swap A,C
  print


; 4: test swap A,D
  inc A
  swap A,D
  inc A
  swap A,D
  print


; 5: test swap A,E
  inc A
  swap A,E
  inc A
  swap A,E
  print


; 6: test clr A
  inc A
  swap A,B

  inc A
  clr A

  swap A,B
  print


; 7: test mov #X, A
.align     ; don't test opcode line boundary handling here
  inc A
  swap A,B

  mov 3,A
  dec A
  dec A
  dec A

  swap A,B
  print


; 8: test add D,A, sub D,A, add XX,A
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
  add 32,A  ; now A=64

  swap A,C  ; swap C,D => C=32, D=64
  swap A,D
  swap A,C

  sub D,A   ; should be 64-64=0

  swap A,B
  print


; 9: test add with negative RF
  inc A
  swap A,B

  mov 1,A   ; set D=1
  swap A,D
  clr A
  dec A     ; set A=M99
  ; if RF sign were sent to EX, this would crash!
  add D,A   ; add P01 to A

  swap A,B
  print


; -- 10-19 --
; Jumps, conditionals, bank switching, subroutines
; JMP, JN, JZ, JIL, JMP FAR, JSR, RET
; All of these tests start with .align so we get consistent operand splitting
; We also switch to bank 2 here

; 10: JMP
.align
  mov 10,A
  swap A,B
  jmp jmptest
  dec A      ; error 99 if jmp not taken

jmptest
  swap A,B
  print


; 11: JN. Also tests that DEC A can produce a negative result
.align
  inc A
  swap A,B
  dec A
  jn jntest
  dec A      ; error 99 if jn not taken

jntest
  inc A
  swap A,B
  print


; 12: jmp far, with and without bank switch
.align
  inc A
  swap A,B

  jmp far jmpfar1
  inc A       ; error 01 if jump not taken
  swap A,B
  print
  halt

jmpfar1
  jmp far jmpfar2
  mov 2,A     ; error 02 if jump not taken
  swap A,B
  print
  halt


; Simple subroutine for JSR/RET test
inca
 inc A
 ret


; continue in new bank
.org 200      ; tests chasm encoding of bank:line as 90:00 = 8999
jmpfar2
  jmp far jmpfar3
  inc A
  swap A,B
  print
  halt

jmpfar3
  swap A,B
  print


; 13: execution from ft3
; On ft3, first two digits (I1) are used for lookup tables, not instructions
; As usual this tests both chasm and the vm implementation
  inc A
  swap A,B
  jmp far jmpft3
  print
  halt


; Useful subroutines for memory tests

clearRF
  clr A       
  mov A,B     ; tests chasm psuedo-instructions
  mov A,C
  mov A,D
  mov A,E
  ret

fillLS        ; set LS = A A+1 A+2 A+3 A+4. Destroys RF
  mov A,B     ; B=X
  inc A
  inc A
  mov A,C     ; C=X+2
  inc A
  mov A,D     ; D=X+3
  inc A
  mov A,E     ; E=X+4
  mov B,A     
  inc A
  swap A,B    ; A=X, B=X+1
  swapall     ; LS <-> RF
  ret

.org 310
jmpft3:
  inc A     ; will fail test if chasm puts first op in I1 not I2
  dec A
  swap A,B
  print


; 14: use JN in a loop. Ensure executed 10 times.
; A=loop counter (counts down), B = testnum, D=count iterations (counts up)
  inc A
  swap A,B

  clr A
  swap A,D   ; clear
  mov 9,A

t14loop
  swap A,D
  inc A
  swap A,D
  dec A  
  jn t14done
  jmp t14loop
t14done
  mov 10,A
  sub D,A    ; result=10-number of iterations counted

  swap A,B
  print


; 15: JSR/RET 
  inc A
  swap A,B
  jsr t15sub  ; test near 
  dec A       ; error 99 if jsr does not jump
  jmp t15next

t15sub
 inc A        ; error 01 if ret does not jump
 ret

t15next
 jsr inca     ; now test far
 dec A        ; error 99 if jsr does not jump
 
 swap A,B
 print


; 16: JZ
.align
  inc A
  swap A, B

  ;mov 42,A
  clr A
  jz t16out
  dec A       ; fail if jz not taken

t16out
  swap A,B
  print


; 17: JIL
.align
  inc A
  swap A, B

  mov 11,A    ; 11=legal, fall through
  jil t17out
  mov 88,A    ; 88=legal, fall through
  jil t17out
  mov 64,A    ; 64=legal, fall through
  jil t17out
  mov 89,A    ; 89=illegal, goto t17ok
  jil t17ok
  jmp t17out

t17ok
  clr A

t17out
  swap A,B
  print


; -- 20-29 --
; RF and memory access, I/O
; MOV, LOADACC, STOREACC, READ, FTL

; 20: test swapall when RF has - sign
  clr A
  dec A       ; set A to M99
  ; if RF sign were sent to EX, this would crash
  swapall     ; swap into LS
  swapall     ; swap back into RF
  inc A       ; should increment A from M99 to P00
  swap A,B
  mov 20,A
  print

; 21: test storeacc/loadacc, swapall
t21acc .equ 4 ; which accum
  mov 42,A
  jsr fillLS
  mov t21acc,A
  storeacc A  ; store mem4 [42 43 44 45 46]
  jsr clearRF
  swapall     ; clear LS
  jsr clearRF
  mov t21acc,A
  loadacc A   ; load mem4 again
  mov 42,A    ; D=42
  mov A,D
  mov F,A
  sub D,A     ; A-=42 (== 0)
  jz t21aok
  jmp t21out
t21aok
  mov 43,A    ; D=43
  mov A,D
  mov G,A
  sub D,A     ; A-=43 (== 0)
  jz t21bok
  jmp t21out
t21bok
  mov 44,A    ; D=44
  mov A,D
  mov H,A
  sub D,A     ; A-=44 (== 0)
  jz t21cok
  jmp t21out
t21cok
  mov 45,A    ; D=45
  mov A,D
  mov I,A
  sub D,A     ; A-=45 (== 0)
  jz t21dok
  jmp t21out
t21dok
  mov 46,A    ; D=46
  mov A,D
  mov J,A
  sub D,A     ; A-=46 (== 0)
  jmp t21out

t21out
  swap A,B
  mov 21,A
  print


; 22: test LOADWORD
  mov 42,A
  jsr fillLS
  clr A
  storeacc A
  inc A
  swap A,B
  mov [B],A   ; load address 01 == 43
  swap A,D
  mov 43,A
  sub D,A
  jz t22ok01
  jmp t22out

t22ok01
  mov 66,A
  jsr fillLS
  mov 9,A
  storeacc A  ; 66 67 68 69 70
  mov 49,A
  swap A,B
  mov [B],A   ; load address 49 == 70
  swap A,D
  mov 70,A
  sub D,A
  jz t22ok49
  jmp t22out

t22ok49
  mov 99,A
  jsr fillLS
  mov 14,A
  storeacc A  ; 99 00 01 02 03
  mov 72,A
  swap A,B
  mov [B],A   ; load address 72 == 01
  dec A

t22out
  swap A,B
  mov 22,A
  print


; 23: test READ
t23
  read     ; read 01020 into LS (clear other digits)
  swapall  ; A=01, B=02
  dec A    ; A=00
  jz t23aok
  jmp t23out
t23aok
  swap A,B ; A=02
  dec A
  dec A    ; A=00
t23out
  mov A,B
  mov 23,A
  print


; 24: exercise all accs for loadacc/storeacc
; goal is to detect timing and dummy placement issues which will fail by
; assertion, so no need to verify any data
t24
  mov 14,A
t24loop
  loadacc A
  storeacc A
  dec A
  jn t24out
  jmp t24loop
t24out
  clr A
  swap A,B
  mov 24,A
  print

; 25: ftl
; spiritually, this is I/O, and so belongs in the 20s somewhere
testtab .table 1, 2, 3
t25
  clr A
  swap A,D
  mov testtab,A
  ftl A,D  ; D=1
  mov 1,A
  sub D,A
  jz t25_2
  jmp t25out
t25_2
  clr A
  swap A,D
  mov testtab,A
  add 1,A
  ftl A,D  ; D=2
  mov 2,A
  sub D,A
  jz t25_3
  jmp t25out
t25_3
  clr A
  swap A,D
  mov testtab,A
  add 2,A
  ftl A,D  ; D=3
  mov 3,A
  sub D,A
t25out
  swap A,B
  mov 25,A
  print
  

; -- DONE --
  mov 99,A
  print
  halt


