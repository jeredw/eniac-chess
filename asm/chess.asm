; chess.asm
; 
  .isa v4
  .org 100

; - MEMORY LAYOUT -

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

; Which player goes next? 0 = ENIAC, 16 = opponent
player .equ 34

; which piece are we checking next for moves?
nextpiece .equ 35


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

; - MOVE GENERATION -


; start nextpiece at current player index (0 or 16)
  mov player, A
  swap A,B
  mov [B],A
  swap A,B
  inc A         ; nextpiece = player+1
  swap A,B
  mov A, [B]

; generate moves for the next piece

; Start with the pawns
; C = player
  mov player,A
  swap A,B
  mov [B],A
  swap A,C

; B = piece index
  clr A
  swap A,B

; D = direction (9,10,11)
  mov 10,A
  swap A,D

; loop over pawns, trying three moves for each
pawnloop
  mov [B],A     ; where is this pawn?
  swap A,C
  jz p0pawn     ; which direction are we going?
  swap A,C
  sub D,A       ; p1 -> going down board, subtract D
  jmp checkpawn
p0pawn
  swap A,C
  add D,A       ; p0 -> going up board, add D

; is there anything where we want to go?
checkpawn
  mov A,E       ; save square
  jsr getsquare
  jn empty 
  
; something is blocking this pawn, try left and right
  swap A,D
  dec D

; pawn can move here
trymove
  ; check for check, then output


  mov nextpiece, A
  swap A,B
  mov [B],A
  swap A,E


pieceloop

; C = player
; E = piece index
  
; try moving up the board
  mov 10,A
  swap A,D



; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - piece index or -1 for empty square
getsquare
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
