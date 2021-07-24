; chess.asm
; 
  .isa v4
  .org 100

; The board is stored as a piece list to keep it as small as possible
; Each word contains the board square of a particular piece, or 0 if missing
; 00        white king
; 01        white queen
; 02 - 09   white pawns
; 10 - 11   white knights
; 12 - 13   white bishops
; 14 - 15   white rooks
; 16        black king
; 17        black queen
; 18 - 25   black pawns
; 26 - 27   black knights
; 28 - 29   black bishops
; 30 - 31   black rooks

; To handle promotion, we also count the number of queens for each side
; Promoted pawns will be in former pawn spots
wqueens .equ 32
bqueens .equ 33

; - LOAD BOARD -
; Read initial board state. Each card is SSPP = square, piece
; illegal square (such as 00) to end
loadlp
  read
  swapall
  jil start
  mov A,[B]
  jmp loadlp

start
  print
  halt

; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - piece index or -1 for empty square
getsquare2
  swap A,D
  mov 31,A
  swap A,B
getsqlp
  mov [B],A
  sub D,A
  jz found
  mov B,A
  dec A
  jn notfound
  swap A,B
  jmp getsqlp

found
  swap A,B
  ret

notfound
  ret
