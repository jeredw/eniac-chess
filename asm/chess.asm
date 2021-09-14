; chess.asm
; 
  .isa v4
  .org 100

; - MEMORY LAYOUT -

; The board is stored as 64 digits in 32 words
; Digit coding:
EMPTY   .equ 0
OTHER   .equ 1
WPAWN   .equ 2
WKNIGHT .equ 3
WBISHOP .equ 4
WQUEEN  .equ 5
BPAWN   .equ 6
BKNIGHT .equ 7
BBISHOP .equ 8
BQUEEN  .equ 9

; OTHER means white/black rook/king. We store the squares of these pieces in another six words
; We'll always have only one queen and two rooks per side (no reason to promote to rook)
; This allows us to represent any number of promoted queens
wking  .equ 32
bking  .equ 33
wrook1 .equ 34
wrook2 .equ 35
; brook1 .equ 36      not needed, if square is occupied and not king or wrook, it's brook
; brook2 .equ 37

; Which player goes next? 0 = white, 1 = black
player .equ 38

; - Piece and Player constants -
; While the board is stored in a two-level encoding, get_square returns piece, player as below
; Note BRQK need to be in sequential order for movegen
PAWN    .equ  1
KNIGHT  .equ  2
BISHOP  .equ  3
QUEEN   .equ  4
ROOK    .equ  5
KING    .equ  6

WHITE   .equ  0
BLACK   .equ  1

; Which direction do pawns go, per player?
pawndir .table 10,-10


; - LOAD BOARD -
; Read initial memory state. Each card is AADD = address, data
; address 99 to end
loadlp
  read
  swapall
  inc A
  jn start
  dec A
  swap A,B
  mov A,[B]
  jmp loadlp

start
  

; - Movegen -
; Just pawns for now

  mov player,A<->B  ; E = [player]
  mov [B],A
  swap A,E

  mov 11,A          ; A = square = 11, begin board scan here

try_sq              ; A=square, E=player
  swap A,C
  clr A             ; C = movestate = 0
  swap A,C

  jsr get_square    ; what's here?
  jz next_square    ; empty?
  swap A,B
  
  ; A=pside, B=ptype, C=movestate, D=square, E=player  

  swap A,D          ; D<->E
  swap A,E         
  swap A,D
  sub D,A
  swap A,E          ; D<->E
  swap A,D
  swap A,E

  ; A=pside-player, B=ptype, C=movestate, D=square, E=player

  jz next_piece_move ; is this our piece?

next_square         ; D=square, E=player
  swap A,D          
  inc A             ; advance one square right
  jil next_line
  jmp try_sq

next_line
  add 2,A           ; advance to left of next rank, e.g. 19->21
  jil done_squares  ; finished scanning squares for moves?
  jmp try_sq

next_piece_move           
  ; A=0, B=ptype, C=movestate, D=square, E=player
  mov C,A           ; movestate == 99?
  inc A
  jz next_square    ; yes, no more moves from this piece

  mov B,A           ; B=ptype
  dec A
  jz next_pawn_move ; is this a pawn? yes, move it
  jmp next_square   ; no, keep scanning

; For pawns, the move state is as follows
;  0 - push 1
;  1 - push 2
;  3 - capture left
;  4 - capture right
next_pawn_move      ; C=movestate, D=square, E=player
  mov C,A           ; move_step += 1
  inc A
  swap A,C

  lodig A           ; A=move_step before increment
  jz push1          ; move_step=0 -> try advancing 1 square

  dec A
  jz push2          ; move_step=1 -> try advancing 2 squares

pawn_capture:       ; move_step 3,4 = captures
  ; NYI
  mov 99,A          ; no more moves for this pice
  swap A,C
  jmp next_piece_move

; try advancing 1 square
push1
  mov E,A
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square, one forward
  jmp output_move

; try advancing 2 squares
push2                 
  mov E,A           ; E=player
  jz push2_white

; push2_black
  mov D,A           ; A=square
  addn 70,A         ; square >= 70? 
  flipn
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=square
  addn 20,A         ; compute destination square, two forward
  jmp output_move

push2_white
  mov D,A           ; A=square
  addn 30,A         ; square < 30? 
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=square
  add 20,A          ; compute destination square, two forward

; We have generated a move! Use it (atm just print it)
output_move
  ; A=to, B=ptype, C=movestate, D=from, E=player
  swap A,B
  swap A,D          ; now A=from, B=to, D=ptype

  print

  swap A,D          
  swap A,B          ; now B=ptype, D=from

  jmp next_piece_move

done_squares
  halt

  .include get_square.asm
