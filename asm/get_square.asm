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
  jn .low       ; square mod 2 == 1?

  swap A,B      ; mod2 = 0 means left of two pieces in word, thus pieces high digit
  mov [B],A
  swapdig A
  lodig A
  jmp .decode

.low
  swap A,B      ; piece in low digit
  mov [B],A
  lodig A

.decode
  jz .empty     ; nothing here?
  dec A
  jz .other     ; piece == OTHER == 1? meaning it's king or rook

  add 95,A     
  jn .black     ; A >= 5? meaning piece >= 6

; white, A = piece + 94 (after dec, add 95)
  add 5,A       ; 5 = PAWN - WPAWN - 94 + 100  (1 - 2 - 94 + 100)  
  ret

; black, A = piece + 95 (after dec, add 96)
.black
  add 11,A      ; add BLACK in high digit + PAWN
  ret

; piece == OTHER
; Find which piece is on square D
.other
  mov 6,A       ; wking div 5 
  loadacc A
  mov H,A       ; wking
  sub D,A
  jz .wking
  mov I,A       ; bking
  sub D,A
  jz .bking
  mov J,A       ; wrook1
  sub D,A
  jz .wrook
  mov wrook2,A
  swap A,B
  mov [B],A     ; wrook2
  sub D,A
  jz .wrook

; there is a piece here and it's not a king or white rook, must be black rook
  mov 10,A      ; A=BLACK

.wrook          ; A=0=WHITE if we jump here
  add ROOK,A
  ret

.bking          ; A=0 here
  add 10,A      ; A+=BLACK
  
.wking          ; A=0=WHITE if we jump here
  add KING,A
  ret

.empty          ; A=0 here
  ret
