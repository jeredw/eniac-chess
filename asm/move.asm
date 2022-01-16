; MOVE.ASM

; - move -
; Modifies the board in place to move piece [fromp] from square [from] to square
; [target], removing piece [targetp] if any.
move
  ; does this move capture a piece?
  mov targetp,A<->B
  mov [B],A         ; A=targetp
  jz .no_capture    ; no, target square already clear

  ; update material score when capturing a piece
  lodig A
  swapdig A         ; 10*(piece type)
  add pval-10,A     ; index piece values, -10 to map PAWN=0
  ftl A             ; lookup value
  swap A,D          ; D=value
  mov fromp,A<->B
  mov [B],A<->E     ; E=fromp
  jsr add_score     ; D=value, E=player=fromp

  ; remove targetp from piecelist, if necessary
  mov TOP,A
  loadacc A         ; G=targetp, H=from, I=target, J=movestate
  mov G,A
  lodig A
  addn ROOK,A       ; piece type >= rook?
  flipn
  jn .no_capture    ; no, this piece is not in the piece list

  clrall            ; C=0
  mov I,A          
  swap A,D          ; D=target
  jsr do_update_piecelist  ; C=new pos=0, D=old pos=target

.no_capture
  mov TOP,A
  loadacc A
  swapall           ; B=targetp, C=from, D=target, E=movestate
  mov fromp,A<->B
  mov [B],A<->E     ; E=fromp

  ; Score entering/exiting center of board
  jsr update_center_score ; C=from, D=target, E=fromp
  
  mov TOP,A         ; restore D=target, A=E=fromp
  loadacc A
  swapall           ; B=targetp, C=from, D=target, E=movestate
  mov fromp,A<->B
  mov [B],A         ;
  mov A,E           ; A=E=fromp

  ; compute promotion delta (0 if no promotion)
  lodig A
  dec A             ; compare to PAWN=1
  jz .check_promo   ; if pawn, check for promotion
  clr A             ; no promotion

.do_move
  ; here A=delta, C=from, D=target
  ; need C=from, D=delta, E=target
  swap A,D
  swap A,E
  jsr move_and_promote
  
  ; return to depth>0 ? move_ret : game
  mov depth,A<->B
  mov [B],A
  jz .game_ret     
  jmp far move_ret
.game_ret
  jmp far game

  ; if this move is a pawn promotion, add to score and set A=delta=QUEEN-PAWN
.check_promo
  mov D,A           ; A=target
  swapdig A
  lodig A           ; isolate rank
  dec A             ; compare to rank 1
  jz .promo         ; if rank 1, promote
  addn 7,A          ; compare to rank 8
  jz .promo         ; if rank 8, promote
  clr A             ; no promotion
  jmp .do_move      ; normal pawn move

  ; promote pawn to queen
  ; set promotion flag (hi digit of movesate), add score, set A=QUEEN-PAWN
  ; movestate is 1-3 and never 99 here
.promo
  mov movestate,A<->B
  mov [B],A         ; A=[movestate]
  add PROMO,A       ; flag promotion for undo_move later
  mov A,[B]         ; save movestate

  mov PBONUS,A      ; add_score is + for white
  swap A,D
  jsr add_score     ; D=score, E=fromp 

  mov target,A<->B  ; restore D=target
  mov [B],A
  swap A,D

  mov QUEEN-PAWN,A  ; upgrade piece to queen
  jmp .do_move


; - undo_move -
; Undoes the previous move. Modifies board in place to move the piece at [target]
; to square [from], and replaces the captured piece [targetp] (if any) on square
; [target].
;
undo_move
  mov TOP,A
  loadacc A
  swapall           ; B=targetp, C=from, D=target, E=movestate
  mov fromp,A<->B
  mov [B],A
  swap A,E          ; A=movestate, B=xx, C=from, D=target, E=fromp

  ; was this a promotion? promo flag is hi digit of movestate
  addn PROMO,A
  jn .unpromo       ; if pawn promotion, undo it
  clr A             ; no promotion delta

  ; move the piece back
.undo_move
  ; here: A=delta, C=from, D=target
  ; need: C=target, D=delta, E=from
  swap A,D
  swap A,C
  swap A,E
  jsr move_and_promote

  ; Score entering/exiting center of board (set E=targetp for reverse score)
  ; here C=target
  mov TOP,A
  loadacc A
  swapall           ; B=targetp, C=from, D=target, E=movestate
  swap A,C
  swap A,D
  swap A,C
  mov fromp,A<->B
  mov [B],A<->E
  jsr update_center_score  ; C=target, D=from, E=fromp

  ; if there was a capture, adjust score and replace piece
  mov targetp,A<->B
  mov [B],A
  jz .out   ; no capture to undo

  ; uncapture. here A=E=targetp
  ; update material score when undoing a capture
  mov A,E           ; save for add_score,set_square
  lodig A
  swapdig A         ; 10*(piece type)
  add pval-10,A     ; index piece values, -10 to map PAWN=0
  ftl A             ; lookup value
  swap A,D          ; D=value
  jsr add_score     ; A=value, E=targetp, subtracts because targetp is other player

  ; put captureed piece back on target square
  mov target,A<->B  
  mov [B],A
  mov A,C
  jsr set_square  ; C=square, E=targetp

.out
  jmp far undo_move_ret

.unpromo
  mov movestate,A<->B
  mov [B],A
  lodig A           ; clear PROMO flag from movestate (assumes PROMO % 10 == 0)
  mov A,[B]         

  mov -PBONUS,A     ; add_score is + for white
  swap A,D 
  jsr add_score     ; D=score, E=fromp 

  ; restore D=target
  mov target,A<->B  
  mov [B],A
  swap A,D

  mov PAWN-QUEEN,A  ; queen back to pawn, will be negative (9x)
  jmp .undo_move


; move_and_promote
; Copies the board array at from to target, adding delta (the promote)
; Clears from square. Updates piece list if needed.
; 
; C = from
; D = delta
; E = target
move_and_promote
  ; read from, store contents + delta to D, set to 0
  mov C,A
  add offset-11,A
  ftl A             ; lookup square offset
  jn .lo_from       ; square mod 2 == 1?

;.hi
  swap A,B         
  mov [B],A         ; get board at offset
  swapdig A         ; get high digit
  lodig A
  add D,A           ; add delta
  lodig A           ; clear oveflow (allow negative D)
  swap A,D          ; save piece in D
  mov [B],A         ; re-read board
  lodig A           ; clear hi piece
  mov A,[B]         ; update board
  jmp .set_target

.lo_from
  swap A,B         
  mov [B],A         ; get board at offset
  lodig A           ; get low digit
  add D,A           ; add delta
  lodig A           ; clear oveflow (allow negative D)
  swap A,D          ; save piece in D
  mov [B],A         ; re-read board
  swapdig A
  lodig A           ; clear lo piece
  swapdig A
  mov A,[B]         ; update board

.set_target 
  mov E,A           ; read target square
  add offset-11,A
  ftl A             ; lookup square offset
  jn .lo_target     ; square mod 2 == 1?

;.hi_target
  swap A,B         
  mov [B],A         ; get board at offset
  lodig A           ; clear hi digit
  swapdig A
  add D,A           ; write new piece
  swapdig A
  mov A,[B]         ; update board
  jmp .check_piecelist

.lo_target
  swap A,B         
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; clear lo digit
  swapdig A
  add D,A           ; write new piece
  mov A,[B]         ; update board

.check_piecelist
  ; update piece list if OTHER
  mov D,A
  dec A
  jz .update_piecelist  ; piece is OTHER
  ret

.update_piecelist
  ; here C=from, E=target
  ; need C=target, D=from
  mov C,A
  swap A,D
  mov E,A
  swap A,C
  jmp do_update_piecelist ; tail call update_piecelist


; set_square encodes player|piece into the board array
; Used only for uncapture
; 
; C: square
; E: player|piece
set_square
  mov E,A           ; A=player_piece 
  lodig A
  addn ROOK,A       ; test if piece is ROOK
  jz .uncapture_rook; if so update piecelist
  ; note kings are never captured so we omit code to undo that

  ; encode pawn/knight/bishop/queen for board array
  mov E,A
  swapdig A
  lodig A           ; isolate piece color (0=white, 1=black)
  add pbase,A       ; lookup base piece for color-1
  ftl A
  swap A,D
  mov E,A
  lodig A           ; isolate piece kind
  add D,A           ; encode piece (e.g. for BPAWN, A=5+1)

  ; update board array target square
  ; A=board piece, C=square
.set_board_array
  swap A,D          ; D=piece
  mov C,A           ; A=square
  add offset-11,A
  ftl A             ; lookup square offset
  jn .lo            ; square mod 2 == 1?

;hi
  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (replacing high digit)
  swapdig A
  add D,A           ; add in piece kind 
  swapdig A
  mov A,[B]         ; update board
  ret

.lo
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (replacing low digit)
  swapdig A
  add D,A           ; add in piece kind 
  mov A,[B]         ; update board
  ret

; a rook was captured, so its auxiliary position will be 0
; find a free auxiliary entry and update it
; C=target, E=player|piece
.uncapture_rook
  mov E,A
  swapdig A
  lodig A           ; white rook?
  jz .wrook
  ; black rook positions are not stored
  mov OTHER,A       ; A=piece kind (OTHER) 
  jmp .set_board_array

.wrook
  mov wrook1,A<->B  ;
  mov [B],A
  jz .do_uncapture   ; if wrook1 is not on board, reuse it
  ; fallthrough
;.wrook2
  mov wrook2,A<->B  ; else reuse wrook2
.do_uncapture
  mov C,A           ; A=target
  mov A,[B]         ; [pos]=target
  mov OTHER,A       ; A=piece kind (OTHER) 
  jmp .set_board_array


; do_update_piecelist
; Assumes (and is not able to check) that this piece is actually a king or rook!
; C: new position
; D: old position
do_update_piecelist:
  mov 6,A           ; wking div 5 
  loadacc A
  mov H,A           ; wking
  sub D,A
  jz .wking
  mov I,A           ; bking
  sub D,A
  jz .bking
  mov J,A           ; wrook1
  sub D,A
  jz .wrook1
  mov wrook2,A
  swap A,B
  mov [B],A         ; wrook2
  sub D,A
  jz .wrook2
  ret
.wking
  mov wking,A<->B
  mov C,A
  mov A,[B]         ; [pos]=new position
  ret
.bking
  mov bking,A<->B
  mov C,A
  mov A,[B]         ; [pos]=new position
  ret
.wrook1
  mov wrook1,A<->B
  mov C,A
  mov A,[B]         ; [pos]=new position
  ret
.wrook2
  mov wrook2,A<->B
  mov C,A
  mov A,[B]         ; [pos]=new position
  ret


; Update center score - adds +1/0/-1 to mscore for entering/leaving board center
; Uses a sign lookup table to identify digits 3,4,5,6
; C=from
; D=target
; Uses: A,B,D
update_center_score
  clr A
  swap A,B      ; init B=0

  ; Add 1 if center(target)
  mov D,A
  add 22,A      ; if +22 is illegal, not center
  jil .check_from
  addn 44,A     ; if -22 is illegal, not center
  jil .check_from
  mov 1,A
  swap A,B      ; score += 1

  ; Subtract 1 if center(from)
.check_from  
  mov C,A
  add 22,A      ; if +22 is illegal, not center
  jil .total
  addn 44,A     ; if -22 is illegal, not center
  jil .total
  swap A,B
  dec A         ; score -= 1
  swap A,B

.total
  swap A,B      ; A = center(from)-center(to)
  swap A,D
  ; fall through to add_score. D=score, E=player|piece


; add_score - updates mscore, adding or subtracting depending on which player
; D = score to add
; E = player|piece, add for player=WHITE
; Uses: A,B
add_score
  mov mscore,A<->B
  mov E,A
  swapdig A
  lodig A           ; get player
  jz .white
;.black
  mov [B],A
  sub D,A           ; mscore += piece value
  mov A,[B]
  ret
.white
  mov [B],A
  add D,A           ; mscore += piece value
  mov A,[B]
  ret




