; - Movegen -
  mov 11,A          ; A=square=11, begin board scan here

try_square          ; A=square
  jsr get_square    ; what's here?
  jz next_square    ; empty?
  ; there is a piece here so A=10*player + piece.  we need to check if it
  ; belongs to the current player, tracked in [from_piece]=10*cur_player + ?
  ; do so by computing (10*cur_player + 9) - (10*player + piece) and checking
  ; that the high digit is 0
  ; TODO consider storing piece_player instead to reduce swapdigs?
  swap D,A          ; A=square, D=player_piece on square
  swap A,C          ; C=square
  mov from_piece,A<->B
  mov [B],A         ; A=current player_piece
  swapdig A         ;
  lodig A           ; isolate current player
  swapdig A         ; get 10*current player + 0
  add 9,A           ; prevent sub from borrowing
  sub D,A           ; A -= player_piece on square
  swapdig A
  lodig A           ; isolate player difference
  jz .ours          ; if 0, piece is ours
  swap C,A
  swap A,D          ; D=square
  jmp next_square   ; not our piece
.ours
  swap D,A
  mov A,[B]         ; [from_piece]=player_piece on square
  swap A,E          ; E=from_piece
  mov from,A<->B
  swap C,A
  mov A,[B]         ; [from]=square
  swap A,D          ; D=square
  clr A
  swap A,C          ; C=movestate=0
  jmp next_piece_move

next_square         ; D=square
  swap A,D          
  inc A             ; advance one square right
  jil .next_line
  jmp try_square

.next_line
  add 2,A           ; advance to left of next rank, e.g. 19->21
  jil done_squares  ; finished scanning squares for moves?
  jmp try_square

next_piece_move           
  ; A=?, B=?, C=movestate, D=from square, E=from player_piece
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
next_pawn_move      ; C=movestate, D=from square, E=from player_piece
  mov C,A           ; movestate += 1
  inc A
  swap A,C

  ; A=movestate before increment
  jz .capture_left  ; try capturing -1 file
  dec A
  jz .capture_right ; try capturing +1 file
  dec A
  jz .push1         ; try advancing 1 square

; try advancing 2 squares
; this is only ever reached if push1 is allowed, so the square directly ahead
; of the pawn is empty, and we only need to check that the pawn is in the
; starting rank and the square +2 away is empty
;.push2
  mov 99,A          ; no more pawn moves after push2
  swap A,C
  mov E,A           ; E=player_piece
  swapdig A
  lodig A           ; A=player
  jz .push2_white

;.push2_black
  mov D,A           ; A=from square
  addn 70,A         ; from square >= 70? 
  flipn
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=from square
  addn 20,A         ; compute target square, two forward
  jmp .check_move

.push2_white
  mov D,A           ; A=from square
  addn 30,A         ; from square < 30? 
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=from square
  add 20,A          ; compute target square, two forward
  jmp .check_move

.capture_left       ; capture -1 file
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute target square
  dec A             ; -1 file
  jmp .check_capture

.capture_right      ; move_step 0,1 = captures
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute target square
  inc A             ; +1 file
  ; fallthrough

; like check_square but specific to pawn captures
; (pawns can only move diagonally when capturing, so can't move to an empty
; square in that case)
.check_capture
  jil next_pawn_move; if off the board, no go
  swap A,D          ; D=save target square
  mov target,A<->B  ;
  swap D,A          ;
  mov A,[B]         ; [target]=target square
  jsr get_square    ; get piece currently on target square
  jz move_bad
  jmp move_if_capture

; try advancing 1 square
.push1
  mov E,A
  swapdig A
  lodig A           ; player index
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute target square, one forward
  ; fallthrough

.check_move
  jil next_pawn_move; if off the board, no go
  swap A,D          ; D=save target square
  mov target,A<->B  ;
  swap D,A          ;
  mov A,[B]         ; [target]=target square
  jsr get_square    ; get piece currently on target square
  jz move_ok
  mov 99,A          ; skip push2 if push1 fails
  swap A,C
  jmp move_bad


; knights
; C=movestate, D=from square, E=player_piece
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
  ; fallthrough

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
  jz .init          ; d=0 means initialize
  mov blocked,A<->B ;
  mov [B],A         ; test if last move was blocked
  jz .not_blocked   ; if not, continue sliding
  jmp .next_dir_b   ; else reset blocked flag+change dir
.not_blocked
  mov E,A
  lodig A           ; isolate piece
  addn KING,A       ; test if piece==KING
  jz .block_king
.move
  mov target,A<->B  ;
  mov [B],A<->D     ; D=cur square
  mov C,A           ; A=movestate (d)
  add bqrkdir-1,A   ; index bqrkdir[d-1]
  ftl A             ; lookup move delta for dir
  jz next_square    ; 0 means past last dir, done
  add D,A           ; A=D(square) + A(delta)
  jil .next_dir     ; if off board, next direction
  jmp check_square  ; output move if valid

; always flag king moves as blocked so they only move one step
.block_king
  inc A
  mov A,[B]         ; set [B]=[blocked] to a nonzero value
  jmp .move

; set starting dir index based on piece type
; (this could use ftl, but conserving table space)
.init
  mov blocked,A<->B
  clr A
  mov A,[B]         ; clear blocked flag
  mov target,A<->B
  mov D,A           ; D is from square on entry
  mov A,[B]         ; [target] = from square
  mov E,A           ; E=player|piece
  lodig A           ; isolate piece
  addn BISHOP,A     ; test if piece==BISHOP
  jz .start_at_5    ; bishop starts from diagonal moves
  swap C,A
  inc A             ; start from d=1 (orthogonal moves)
  swap A,C
  jmp next_bqrk_move
.start_at_5
  swap C,A
  add 5,A           ; start from d=5 (diagonal moves)
  swap A,C
  jmp next_bqrk_move

.next_dir_b
  clr A
  mov A,[B]         ; clear blocked flag
; select next dir index based on piece type
.next_dir
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
  jz .rook          ; special case for rook
  jmp next_bqrk_move
.rook
  mov C,A
  addn 5,A          ; test if dir is diagonal
  jz next_square    ; if so, done with rook moves
  jmp next_bqrk_move
