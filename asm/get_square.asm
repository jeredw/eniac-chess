; - get_square -
; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - 0 if empty, else player|piece type
;   D - square
; Overwrites:
;   B, LS (aka FGHIJ)

get_square
  mov A,D       ; save sq to D in case piece=OTHER
  add offset-11,A
  ftl A
  jn gs_hi      ; square mod 2 == 1?

  swap A,B      ; mod2 = 0 means left of two pieces in word, thus pieces high digit
  mov [B],A
  swapdig A
  lodig A
  jmp decode

gs_hi
  swap A,B      ; piece in low digit
  mov [B],A
  lodig A

decode
  jz gs_empty   ; nothing here?
  dec A
  jz gs_other   ; piece == OTHER == 1? meaning it's king or rook

  add 95,A     
  jn gs_black   ; A >= 5? meaning piece >= 6

; white, A = piece + 94 (after dec, add 95)
  add 5,A       ; 5 = PAWN - WPAWN - 94 + 100  (1 - 2 - 94 + 100)  
  ret

; black, A = piece + 95 (after dec, add 96)
gs_black
  add 11,A      ; add BLACK in high digit + PAWN
  ret

; piece == OTHER
; Find which piece is on square D
gs_other
  mov 6,A       ; wking div 5 
  loadacc A
  mov H,A       ; wking
  sub D,A
  jz gs_wking
  mov I,A       ; bking
  sub D,A
  jz gs_bking
  mov J,A       ; wrook1
  sub D,A
  jz gs_wrook
  mov wrook2,A
  swap A,B
  mov [B],A     ; wrook2
  sub D,A
  jz gs_wrook

; there is a piece here and it's not a king or white rook, must be black rook
  mov 10,A      ; A=BLACK

gs_wrook        ; A=0=WHITE if we jump here
  add ROOK,A
  ret

gs_bking        ; A=0 here
  add 10,A      ; A+=BLACK
  
gs_wking        ; A=0=WHITE if we jump here
  add KING,A
  ret

gs_empty
  clr A
  ret


; Returns zero if square is empty and nonzero otherwise
; Duplicates part of get_square to save some registers and avoid decoding
; when it is not needed (for checking move eligibility)
; Inputs: 
;   A - square
; Outputs:
;   A - zero if empty, nonzero otherwise
; Overwrites:
;   B, LS
test_empty
  add offset-11,A
  ftl A
  jn te_hi      ; square mod 2 == 1?

  swap A,B      ; mod2 = 0 means left of two pieces in word, thus pieces high digit
  mov [B],A
  swapdig A
  lodig A
  ret

te_hi
  swap A,B      ; piece in low digit
  mov [B],A
  lodig A
  ret
