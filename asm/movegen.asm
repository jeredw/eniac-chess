; - Movegen -

  mov pp,A<->B      ; E = [pp]
  mov [B],A
  swap A,E

  mov 11,A          ; A = square = 11, begin board scan here

try_sq              ; A=square, E=pp
  jsr get_square    ; what's here?
  jz next_square    ; empty?
  ; does the piece belong to the current player?
  swap A,B          ; B=pp on square
  mov E,A           ; A=current pp
  swapdig A
  lodig A           ; A=player to move
  jz try_sq_w       ; white to move?
;try_sq_b           ; black to move
  mov B,A
  swapdig A
  lodig A           ; A=piece color
  jz next_square    ; if piece is white, skip
  jmp try_sq_ours
try_sq_w            ; white to move
  mov B,A
  swapdig A
  lodig A           ; A=piece color
  jz try_sq_ours    ; if piece is white, ours
  jmp next_square
try_sq_ours
  swap B,A
  swap A,E          ; E=pp here
  mov square,A<->B
  mov D,A
  mov A,[B]         ; [square]=current square
  clr A
  swap A,C          ; C=movestate=0
  jmp next_piece_move

next_square         ; D=square, E=pp
  swap A,D          
  inc A             ; advance one square right
  jil next_line
  jmp try_sq

next_line
  add 2,A           ; advance to left of next rank, e.g. 19->21
  jil done_squares  ; finished scanning squares for moves?
  jmp try_sq

next_piece_move           
  ; A=?, B=?, C=movestate, D=square, E=pp
  mov C,A           ; movestate == 99?
  inc A
  jz next_square    ; yes, no more moves from this piece

  mov E,A
  lodig A           ; A=piece type
  dec A
  jz next_pawn_move ; is this a pawn? yes, move it
  dec A
  jz next_knight_move; is this a knight? yes, move it
  jmp next_square   ; no, keep scanning

; For pawns, the move state is as follows
;  0 - capture left
;  1 - capture right
;  2 - push 1
;  3 - push 2
next_pawn_move      ; C=movestate, D=square, E=pp
  mov C,A           ; movestate += 1
  inc A
  swap A,C

  ; A=movestate before increment
  jz pawn_capture_l ; try capturing left
  dec A
  jz pawn_capture_r ; try capturing right
  dec A
  jz push1          ; try advancing 1 square

; try advancing 2 squares
; this is only ever reached if push1 is allowed, so the square directly ahead
; of the pawn is empty, and we only need to check that the pawn is in the
; starting rank and the square +2 away is empty
;push2
  mov 99,A          ; no more pawn moves after push2
  swap A,C
  mov E,A           ; E=pp
  swapdig A
  lodig A           ; A=player
  jz push2_white

; push2_black
  mov D,A           ; A=square
  addn 70,A         ; square >= 70? 
  flipn
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=square
  addn 20,A         ; compute destination square, two forward
  jsr test_empty    ; test if square is already occupied
  jz push2_black_ok ; zero means no piece in square
  jmp next_square   ; if blocked, can't push1 or push2

push2_black_ok
  mov D,A           ; A=square
  addn 20,A         ; compute destination square, two forward
  jmp output_move

push2_white
  mov D,A           ; A=square
  addn 30,A         ; square < 30? 
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=square
  add 20,A          ; compute destination square, two forward
  jsr test_empty    ; test if square is already occupied
  jz push2_white_ok ; zero means no piece in square
  jmp next_square   ; if blocked, can't push1 or push2

push2_white_ok
  mov D,A           ; A=square
  add 20,A          ; compute destination square, two forward
  jmp output_move

pawn_capture_l      ; move_step 0,1 = captures
  ; TODO
  jmp next_pawn_move

pawn_capture_r      ; move_step 0,1 = captures
  ; TODO
  jmp next_pawn_move

; Which direction do pawns go, per player?
pawndir .table 10,-10

; try advancing 1 square
push1
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square, one forward
  ; NOTE we don't need to bounds check the destination square because a move to
  ; the last rank will always be treated as a promotion to queen, so pawns
  ; should never be on the last rank.
  jsr test_empty    ; test if square is already occupied
  jz push1_ok       ; zero means no piece in square
  jmp next_square   ; if blocked, can't push1 or push2

push1_ok
  mov E,A           ; XXX recompute target square (out of regs)
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square, one forward
  jmp output_move

; knights
; C=movestate, D=square, E=pp
next_knight_move
  mov C,A           ; move_step += 1
  inc A
  swap A,C          ; A=move_step before increment

  ; movestate indexes a table of deltas
nmoves .table 8, 12, 19, 21, 79, 81, 88, 92, 0
  add nmoves,A      ; A+=table base address
  ftl A             ; lookup move delta
  jz next_square    ; 0 means end of table
  add D,A           ; compute the target square

  ; check if the square is a valid target
  jil next_knight_move ; off the board
  ; need to see what is there, which means calling get_square.
  ; clobber D (stored in [square]) to spill target square
  swap A,D          ; D=save target square
  mov tmp,A<->B     ;
  swap D,A          ;
  mov A,[B]         ; [tmp]=target square

; output move if target is empty square or an opponent's piece
output_if_ok
  jsr get_square    ; get piece currently on target square
  jz move_ok        ; if target is empty, can move there
  swapdig A
  lodig A           ; A=piece color on target
  swap A,D          ; D=piece color on target
  mov E,A
  swapdig A
  lodig A           ; A=player piece color
  sub D,A           ; compare player color and piece color
  jz move_bad       ; can't capture own piece

move_ok
  mov square,A<->B
  mov [B],A<->D     ; D=from square
  mov tmp,A<->B
  mov [B],A         ; A=target square
  jmp output_move

move_bad
  mov square,A<->B
  mov [B],A<->D     ; D=from square
  jmp next_piece_move
