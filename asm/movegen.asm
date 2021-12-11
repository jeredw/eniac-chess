; MOVE_GEN.ASM
; Main move generator

; Communicates through top of stack: 
;  [from]      - from square
;  [fromp]     - current player player | piece on from
;  [target]    - to square
;  [targetp]   - 0 if empty, or opposing player | piece on to
;  [movestate] - opaque iteration state
;
; To call: jump to next_move
; Initializes move generation if [from]=0
; Returns next move in updated top of stack, via far jump to output_move
; When no more moves, far jump to no_more_moves
; 
; Approach:
;  - check for pawn moves
;  - check for BRQK moves in 4 or 8 directions
;  - check for knight moves
;
; Returns psuedo-legal moves, that is, does not check for check

; - next_move - 
; Main entrypoint
next_move           
  mov TOP0,A
  loadacc A         ; (F=fromp, G=targetp, H=from, I=target, J=movestate)
  mov H,A           ;
  jz init_move      ; [from]==0 means start of iteration
  swap A,D          ; D=from
  mov J,A<->C       ; C=movestate
  mov F,A<->E       ; E=fromp

; Generate next move for current piece 
; Here: C=movestate, D=from square, E=from player_piece
next_move_inner
  mov E,A
  lodig A           ; A=piece type
  dec A
  jz next_pawn_move ; is this a pawn? yes, move it
  dec A
  jz next_knight_move; is this a knight? yes, move it
  jmp next_bqrk_move ; sliding piece

init_move
  mov 11,A
  ; fallthrough to try_square

; Try a new square. See if one our pieces is there.
; Here: A=square, [fromp]=player*10
try_square          ; A=square
  swap A,D
  jsr get_square    ; what's here?
  jz next_square    ; empty?

  ; check if the piece here is ours
  swap A,E          ; E=player|piece on target square
  swap D,A          ;
  swap A,C          ; C=square
  mov fromp,A<->B
  mov [B],A         ; A=current player|piece
  swapdig A
  lodig A           ; A=current player
  swap A,D          ; D=current player
  mov E,A
  swapdig A
  lodig A           ; A=player on square
  sub D,A           ; test if curent player==player on square
  jz .ours          ; if yes, piece is ours
  swap C,A
  swap A,D          ; D=square
  jmp next_square   ; not our piece

; Found one of our pieces, set globla fromp and from and start generating moves
.ours
  mov E,A
  mov A,[B]         ; [fromp]=player|piece on square
  mov from,A<->B
  swap C,A
  mov A,[B]         ; [from]=square
  swap A,D          ; D=square
  clr A
  swap A,C          ; C=movestate=0
  jmp next_move_inner

next_square         ; D=square
  swap A,D          
  inc A             ; advance one square right
  jil .next_line    ; roll over to next rank?
  jmp try_square

.next_line
  add 2,A           ; advance to left of next rank, e.g. 19->21
  jil done_squares  ; finished scanning all squares for moves?
  jmp try_square

; For pawns, movestate is coded as follows
;  0 - capture left
;  1 - capture right
;  2 - push 1
;  3 - push 2
;  4+ - next piece (done)
; Here: C=movestate, D=from, E=fromp
next_pawn_move      
  mov C,A           ; movestate += 1
  inc A
  swap A,C

  ; A=movestate before increment
  jz .capture_left  ; try capturing -1 file
  dec A
  jz .capture_right ; try capturing +1 file
  dec A
  jz .push1         ; try advancing 1 square
  dec A
  jz .push2         ; try advancing 2 squares
  jmp next_square   ; next piece

; try advancing 2 squares
; this is only ever reached if push1 is allowed, so the square directly ahead
; of the pawn is empty, and we only need to check that the pawn is in the
; starting rank and the square +2 away is empty
.push2
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
  addn 20,A         ; compute target square, two down
  jmp .check_move

.push2_white
  mov D,A           ; A=from square
  addn 30,A         ; from square < 30? 
  jn next_square    ; nope, can't push 2
  mov D,A           ; A=from square
  add 20,A          ; compute target square, two up
  jmp .check_move

.capture_left       ; capture -1 file
  mov E,A
  swapdig A
  lodig A           ; A=player
  add pawndir,A
  ftl A             ; +10 for white, -10 for black
  add D,A           ; compute target square
  dec A             ; -1 file
  jmp .check_capture

.capture_right      ; capture +1 file
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
  swap D,A
  jsr get_square    ; get piece currently on target square
  jz move_bad       ; if empty, no capture possible
  swap A,D
  mov targetp,A<->B
  swap D,A
  mov A,[B]         ; [targetp]=player|piece on target
  jmp move_if_capture ; capture if occupied by opposite player

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
  swap D,A          ;
  jsr get_square    ; get piece currently on target square
  swap A,D
  mov targetp,A<->B
  swap D,A
  mov A,[B]         ; [targetp]=player_piece on target
  jz move_ok
  mov 4,A           ; skip push2 if push1 fails
  swap A,C
  jmp move_bad      ; restore D=[from square]


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
;   [targetp] will be set if target is nonempty
;   Jump to output_move for valid moves
check_square
  swap A,D          ; D=save target square
  mov target,A<->B  ;
  swap D,A          ;
  mov A,[B]         ; [target]=target square
  swap D,A          ;
  jsr get_square    ; get piece currently on target square
  swap A,D
  mov targetp,A<->B
  swap D,A
  mov A,[B]         ; [targetp]=player_piece on target
  jz move_ok        ; if target is empty, can move there

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
  ; We have a move to output and need to save movegen state.
  ; [from], [target] and [targetp] are already up to date, just need to save
  ; [movestate].
  mov movestate,A<->B
  swap A,C
  mov A,[B]         ; save [movestate]
  jmp far output_move

move_bad
  mov from,A<->B
  mov [B],A<->D     ; D=from square
  ; note we do not update [movestate] here
  jmp next_move_inner

; Sliding pieces (bishop / queen / rook / king)
; C=movestate is n|d where d=dir index, n=steps (for king)
; [target] is the current square along dir
next_bqrk_move
  mov C,A
  jz .init          ; d=0 means initialize
  mov targetp,A<->B ;
  mov [B],A         ; test if last move was blocked/capture
  jz .not_blocked   ; if not, continue sliding
  jmp .next_dir_b   ; else reset targetp+change dir
.not_blocked
  mov E,A
  lodig A           ; isolate piece
  addn KING,A       ; test if piece==KING
  jz .king
.move
  mov target,A<->B  ;
  mov [B],A<->D     ; D=cur square
  mov C,A           ; A=movestate (d)
  lodig A           ; isolate d (king uses high digit as n)
  add bqrkdir-1,A   ; index bqrkdir[d-1]
  ftl A             ; lookup move delta for dir
  jz next_square    ; 0 means past last dir, done
  add D,A           ; A=D(square) + A(delta)
  jil .next_dir     ; if off board, next direction
  jmp check_square  ; output move if valid

; king can only move one step in each direction
.king
  mov C,A           ;
  add 10,A          ; inc current step
  swap A,C          ; A=movestate before update
  swapdig A         ;
  lodig A           ; get step number
  jz .move          ; if first step, move
  jmp .next_dir     ; else select new dir

; set starting dir index based on piece type
; (this could use ftl, but conserving table space)
.init
  mov targetp,A<->B
  clr A
  mov A,[B]         ; clear [targetp]
  mov target,A<->B
  mov D,A           ; D is from square on entry
  mov A,[B]         ; [target] = from square
  mov E,A           ; E=player|piece
  lodig A           ; isolate piece
  addn BISHOP,A     ; test if piece==BISHOP
  jz .start_at_5    ; bishop starts from diagonal moves
  mov 1,A           ; start from d=1 (orthogonal moves)
  swap A,C
  jmp next_bqrk_move
.start_at_5
  mov 5,A           ; start from d=5 (diagonal moves)
  swap A,C
  jmp next_bqrk_move

.next_dir_b
  clr A
  mov A,[B]         ; clear [targetp]
; select next dir index based on piece type
.next_dir
  mov from,A<->B
  mov [B],A<->D     ; restore D=[from]
  mov target,A<->B
  mov D,A
  mov A,[B]         ; [target]=D
  mov E,A           ; E=player|piece
  swap C,A
  lodig A           ; clear step number (for king)
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

done_squares         
  jmp far no_more_moves
