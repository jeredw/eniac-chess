; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - piece index or -1 for empty square
  .isa v4
  .org 100
  
; We have to scan 0-31 in memory, which we do through loadacc
; Register use:
;  B - piece index (word address)
;  C - loop counter (acc address, 5..0)
;  D - square to find
getsquare
  swap A,D

; Start with partial acc containing 30,31
  mov 6,A
  loadacc A
  swap A,C

  mov 31,A
  jmp checkstart

; main loop: load next acc and search
getsqloop

  ; check addr x4 
  mov B,A         ; dec B to update piece index
  dec A
  swap A,B
  mov J,A         ; load x4 word
  sub D,A         ; compare to square index
  jz found     

  ; check addr x3
  mov B,A
  dec A
  swap A,B
  mov I,A  		    ; load x3 word
  sub D,A
  jz found     

  ; check addr x2
  mov B,A
  dec A
  swap A,B
  mov H,A  		    ; load x2 word
  sub D,A
  jz found     

  ; check addr x1
  mov B,A
  dec A
checkstart
  swap A,B
  mov G,A  		    ; load x1 word
  sub D,A
  jz found     

  ; check addr x0
  mov B,A
  dec A
  swap A,B
  mov F,A  		    ; load x0 word
  sub D,A
  jz found     

; dec C and load next accumulator value, or exit
  swap A,C 		    ; load loop counter/acc idx
  dec A
  jn notfound	    ; A already -1 here, convenient
  loadacc A
  swap A,C 		    ; save loop counter
  jmp getsqloop  

found
  mov B,A  	      ; put piece index in A
  ret

notfound
  ret 		        ; A=-1 for empty


; SHORT version, doesn't unroll the acummulator access loop
getsquare2
  swap A,D
  mov 31,A
  swap A,B
loop2
  mov [B],A
  sub D,A
  jz found
  mov B,A
  dec A
  jn notfound
  swap A,B
  jmp loop2

  

