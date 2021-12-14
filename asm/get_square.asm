; GET_SQUARE.ASM
; Lookup piece at board square.

; See memory_layout.asm for board encoding, but briefly:
;   - Board layout is 64 digits in 32 words in addresses 0-31.
;   - Digit 0=empty, digit=OTHER, meaning a king or rook, 
;     digit 2-9=white/black pawn/bishop/queen/knight
;   - Location of kings and white rooks are in [wking], [bking], [wrook1], [wrook2]
;   - If it's OTHER but not in those four locations, it's black rook
;
; This layout is compact while remaining constant time to lookup 

; - get_square -
; Find the piece on a square
; Inputs: 
;   D - square, numbered rank|file from 11 to 88
; Outputs:
;   A - 0 if empty, else player|piece
;   D - square
; Overwrites:
;   B, LS (aka FGHIJ)

get_square
  mov D,A
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



; sets square A digit to piece D
; A = piece (board form) 
; D = square
set_board_array
  swap A,D          ; A=square
  add offset-11,A
  ftl A             ; lookup square offset
  jn .low           ; square mod 2 == 1?

  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (replacing high digit)
  swapdig A
  add D,A           ; add in piece kind 
  swapdig A
  mov A,[B]         ; update board
  ret

.low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (replacing low digit)
  swapdig A
  add D,A           ; add in piece kind 
  mov A,[B]         ; update board
  ret

