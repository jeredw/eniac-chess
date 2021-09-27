; - get_square -
; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - 0 if empty, else player|piece type
;   D - square
; Overwrites:
;   B, LS (aka FGHIJ)

; Offset table maps positions 11..88 to address
; Value = square div 2, sign = square mod 2, indicates low or high digit
; NOTE relying on .table allocating this contiguously
offset  .table     0,  M0,   1,  M1,   2,  M2,   3,  M3,  0
offset2 .table 0,  4,  M4,   5,  M5,   6,  M6,   7,  M7,  0
offset3 .table 0,  8,  M8,   9,  M9,  10, M10,  11, M11,  0
offset4 .table 0, 12, M12,  13, M13,  14, M14,  15, M15,  0
offset5 .table 0, 16, M16,  17, M17,  18, M18,  19, M19,  0
offset6 .table 0, 20, M20,  21, M21,  22, M22,  23, M23,  0
offset7 .table 0, 24, M24,  25, M25,  26, M26,  27, M27,  0
offset8 .table 0, 28, M28,  29, M29,  30, M30,  31, M31

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
  add 10,A      ; A+=BLACK

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
