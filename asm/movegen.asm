; - Movegen -
; Just pawns for now

; Which direction do pawns go, per player?
pawndir .table 10,-10

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
;  0 - capture left
;  1 - capture right
;  2 - push 1
;  3 - push 2
next_pawn_move      ; C=movestate, D=square, E=player
  mov C,A           ; move_step += 1
  inc A
  swap A,C

  lodig A           ; A=move_step before increment
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
  mov E,A           ; E=player
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

; try advancing 1 square
push1
  mov E,A
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square, one forward
  jsr test_empty    ; test if square is already occupied
  jz push1_ok       ; zero means no piece in square
  jmp next_square   ; if blocked, can't push1 or push2

push1_ok
  mov PAWN,A<->B    ; restore B=ptype=PAWN
  mov E,A           ; XXX recompute target square (out of regs)
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square, one forward
  jmp output_move
