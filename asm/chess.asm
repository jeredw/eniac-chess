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





; - get_square -
; Find the piece on a square
; Inputs: 
;   A - square
; Outputs:
;   A - piece type
;   B - player (NB: undefined if nothing on this square)
;   D - square
; Overwrites:
;   LS (aka FGHIJ)

; Offset table maps positions 11..88 to address
; Value = square div 2, sign = square mod 2, indicates low or high digit
; NOTE relying on .table allocating this contiguously
; TODO support arithmetic on "offset" instead using a padding row, will free up 11 words

offset  .table 0,  0,   0,   0,  0,    0,   0,   0,   0,  0
offset1 .table 0,  0,  M0,   1,  M1,   2,  M2,   3,  M3,  0
offset2 .table 0,  4,  M4,   5,  M5,   6,  M6,   7,  M7,  0
offset3 .table 0,  8,  M8,   9,  M9,  10, M10,  11, M11,  0
offset4 .table 0, 12, M12,  13, M13,  14, M14,  15, M15,  0
offset5 .table 0, 16, M16,  17, M17,  18, M18,  19, M19,  0
offset6 .table 0, 20, M20,  21, M21,  22, M22,  23, M23,  0
offset7 .table 0, 24, M24,  25, M25,  26, M26,  27, M27,  0
offset8 .table 0, 28, M28,  29, M29,  30, M30,  31, M31

get_square
  mov A,D       ; save sq to D in case piece=OTHER
  add offset,A
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
  swap A,B
  clr A         ; mov WHITE,A
  swap A,B
  ret

; black, A = piece + 95 (after dec, add 96)
gs_black        
  inc A         ; add PAWN,A
  swap A,B
  mov BLACK,A
  swap A,B
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
  mov BLACK,A

gs_wrook        ; A=0=WHITE if we jump here
  swap A,B
  mov ROOK,A
  ret

gs_bking        ; A=0 here
  inc A         ; mov BLACK,A
  
gs_wking        ; A=0=WHITE if we jump here
  swap A,B
  mov KING,A
  ret

gs_empty
  swap A,B      ; clr B only needed for pretty printing 
  clr A
  ret


; - Print Board -
; Halts at end, not a subroutine because it calls get_square
printboard
  mov 11,A
pb_nextsq
  jsr get_square
  print
  mov D,A         ; restore square
  inc A           ; move one square right
  jil pb_nextline
  jmp pb_nextsq
pb_nextline
  add 2,A         ; move to start of next line, e.g. 19 -> 21
  jil pb_done
  jmp pb_nextsq
pb_done
  halt





