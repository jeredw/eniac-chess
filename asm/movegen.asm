; - Movegen -
  mov 11,A          ; A = square = 11, begin board scan here

try_sq              ; A=square
  jsr get_square    ; what's here?
  jz next_square    ; empty?
  ; does the piece belong to the current player?
  swap A,C          ; C=pp on square
  mov pp,A<->B      ; E=saved [pp]
  mov [B],A<->E
  mov E,A           ; A=current pp
  swapdig A
  lodig A           ; A=player to move
  jz try_sq_w       ; white to move?
;try_sq_b           ; black to move
  mov C,A
  swapdig A
  lodig A           ; A=piece color
  jz next_square    ; if piece is white, skip
  jmp try_sq_ours
try_sq_w            ; white to move
  mov C,A
  swapdig A
  lodig A           ; A=piece color
  jz try_sq_ours    ; if piece is white, ours
  jmp next_square
try_sq_ours
  swap C,A
  swap A,E          ; E=pp here
  mov from,A<->B
  mov D,A
  mov A,[B]         ; [from]=current square
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
  ; A=?, B=?, C=movestate, D=from square, E=pp
  mov C,A           ; movestate == 99?
  inc A
  jz next_square    ; yes, no more moves from this piece

  mov E,A
  lodig A           ; A=piece type
  dec A
  jz next_pawn_move ; is this a pawn? yes, move it
  dec A
  jz next_knight_move; is this a knight? yes, move it
  jmp next_bqrk_move ; sliding piece

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
  jz pawn_capture_l ; try capturing -1 file
  dec A
  jz pawn_capture_r ; try capturing +1 file
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

pawn_capture_l      ; capture -1 file
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square
  dec A             ; -1 file
  jmp check_pawn_capture

pawn_capture_r      ; move_step 0,1 = captures
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute destination square
  inc A             ; +1 file

; like check_square but specific to pawn captures
; (pawns can only move diagonally when capturing, so can't move to an empty
; square in that case)
check_pawn_capture
  jil next_pawn_move; if off the board, no go
  swap A,D          ; D=save target square
  mov target,A<->B  ;
  swap D,A          ;
  mov A,[B]         ; [target]=target square
  jsr get_square    ; get piece currently on target square
  jz move_bad
  jmp move_if_capture

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
; C=movestate, D=from square, E=pp
next_knight_move
  mov C,A           ; movestate is ndir table offset
  addn 80,A
  jn next_square    ; if offset >= 80, done
  mov C,A
  add 10,A          ; next offset is +10
  swap A,C          ; A=movestate before increment
  add ndir,A        ; A+=table base address
  ftl A             ; lookup move delta
  add D,A           ; compute the target square
  jil next_knight_move ; off the board means no go

; output move if target square is empty or capture
; On entry
;   A=target square, will be saved in [target]
; On exit
;   D will get reset from [from]
;   [blocked] will be set if target is nonempty
check_square
  swap A,D          ; D=save target square
  mov target,A<->B  ;
  swap D,A          ;
  mov A,[B]         ; [target]=target square
  jsr get_square    ; get piece currently on target square
  jz move_ok        ; if target is empty, can move there
  ; record that there is something in the square so that sliding pieces
  ; stop sliding at this position
  swap A,D
  mov blocked,A<->B
  mov A,[B]         ; set blocked=nonzero value
  swap D,A

; output move if empty square or an opponent's piece
; - A has the contents of the new square
move_if_capture
  swapdig A
  lodig A           ; A=piece color on target
  swap A,D          ; D=piece color on target
  mov E,A
  swapdig A
  lodig A           ; A=player piece color
  sub D,A           ; compare player color and piece color
  jz move_bad       ; can't capture own piece

move_ok
  mov from,A<->B
  mov [B],A<->D     ; D=from square
  mov target,A<->B
  mov [B],A         ; A=target square
  jmp output_move

move_bad
  mov from,A<->B
  mov [B],A<->D     ; D=from square
  jmp next_piece_move

; Sliding pieces (bishop / queen / rook / king)
; C=movestate is d where d=dir index
; [target] is the current square along dir
next_bqrk_move
  mov C,A
  jz init_sliding   ; d=0 means initialize
  mov blocked,A<->B ;
  mov [B],A         ; test if last move was blocked
  jz not_blocked    ; if not, continue sliding
  jmp next_dir_b    ; else reset blocked flag+change dir
not_blocked
  mov E,A
  lodig A           ; isolate piece
  addn KING,A       ; test if piece==KING
  jz block_king
do_bqrk_move
  mov target,A<->B  ;
  mov [B],A<->D     ; D=cur square
  mov C,A           ; A=movestate (d)
  add bqrkdir-1,A   ; index bqrkdir[d-1]
  ftl A             ; lookup move delta for dir
  jz next_square    ; 0 means past last dir, done
  add D,A           ; A=D(square) + A(delta)
  jil next_dir      ; if off board, next direction
  jmp check_square  ; output move if valid

; always flag king moves as blocked so they only move one step
block_king
  inc A
  mov A,[B]         ; set [B]=[blocked] to a nonzero value
  jmp do_bqrk_move

; set starting dir index based on piece type
; (this could use ftl, but conserving table space)
init_sliding
  mov blocked,A<->B
  clr A
  mov A,[B]         ; clear blocked flag
  mov target,A<->B
  mov D,A           ; D is from square on entry
  mov A,[B]         ; [target] = from square
  mov E,A           ; E=player|piece
  lodig A           ; isolate piece
  addn BISHOP,A     ; test if piece==BISHOP
  jz init_dir_5     ; bishop starts from diagonal moves
  swap C,A
  inc A             ; start from d=1 (orthogonal moves)
  swap A,C
  jmp next_bqrk_move
init_dir_5
  swap C,A
  add 5,A           ; start from d=5 (diagonal moves)
  swap A,C
  jmp next_bqrk_move

next_dir_b
  clr A
  mov A,[B]         ; clear blocked flag
; select next dir index based on piece type
next_dir
  mov from,A<->B
  mov [B],A<->D     ; restore D=[from]
  mov target,A<->B
  mov D,A
  mov A,[B]         ; [target]=D
  mov E,A           ; E=player|piece
  swap C,A
  inc A             ; next direction
  swap A,C
  lodig A           ; isolate piece
  addn ROOK,A       ; test if piece==ROOK
  jz next_dir_rook  ; special case for rook
  jmp next_bqrk_move
next_dir_rook
  mov C,A
  addn 5,A          ; test if dir is diagonal
  jz next_square    ; if so, done with rook moves
  jmp next_bqrk_move
