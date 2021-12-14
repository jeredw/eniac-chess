; MOVE.ASM

; - move -
; Modifies the board in place to move piece [fromp] from square [from] to square
; [target], first removing piece [targetp] if any.
move
  ; does this move capture a piece?
  mov targetp,A<->B
  mov [B],A         ; A=[targetp]
  jz clear_from     ; no, target square already clear

  ; update material score when capturing a piece
  mov A,C           ; C=save [targetp]
  lodig A
  dec A             ; map PAWN=1 to 0
  swapdig A         ; 10*(piece type-1)
  add pval,A        ; index piece values
  ftl A             ; lookup value
  swap A,D          ; D=value
  jsr add_score
  swap C,A          ; restore A=[targetp]

  lodig A
  addn ROOK,A       ; test if piece >= ROOK
  flipn
  jn clear_from     ; if not, no need to update_pos
  ; if we're capturing a king or rook, need to clear its auxiliary position.
  ; other captures just need to update the board array which happens for free.
  clr A
  swap A,C          ; C=new position=0
  mov target,A<->B  ;
  mov [B],A<->D     ; D=old position=[target]
  clr A
  swap A,E          ; E=0 (return to clear_from)
  jmp update_pos    ; call update_pos

  ; clear from square in board array
clear_from
  mov from,A<->B
  mov [B],A         ; A=[from]
  add offset-11,A
  ftl A             ; lookup square offset
  jn .clear_low     ; square mod 2 == 1?

  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (clearing high digit)
  mov A,[B]         ; update board
  jmp .set_target

.clear_low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (clearing low digit)
  swapdig A
  mov A,[B]         ; update board

  ; set target square to fromp
.set_target
  mov fromp,A<->B
  mov [B],A         ; A=player_piece=[fromp]
  mov A,C           ; C= [fromp]
  lodig A           ; get piece type
  dec A             ; compare to PAWN=1
  jz .check_promo   ; if pawn, check for promotion
.do_set_square
  mov from,A<->B
  mov [B],A<->D     ; D=old pos=[from]
  jsr set_square

  ; return to depth>0 ? move_ret : game
  mov depth,A<->B
  mov [B],A
  jz .game_ret     
  jmp far move_ret
.game_ret
  jmp far game

  ; check if this move is a pawn promotion
.check_promo
  mov target,A<->B  ;
  mov [B],A         ; A=target square
  swapdig A
  lodig A           ; isolate rank
  dec A             ; compare to rank 1
  jz .promo         ; if rank 1, promote
  addn 7,A          ; compare to rank 8
  jz .promo         ; if rank 8, promote
  jmp .do_set_square ; normal pawn move

  ; promote pawn to queen
  ; movestate is 1-3 and never 99 here
.promo
  mov movestate,A<->B
  mov [B],A         ; A=[movestate]
  add PROMO,A       ; flag promotion for undo_move later
  mov A,[B]         ; save movestate

  mov C,A           ; A=from player_piece
  add QUEEN-PAWN,A  ; upgrade piece to queen
  swap A,C

  mov -PBONUS,A      ; add_score is + for black
  swap A,D 
  jsr add_score

  jmp .do_set_square


; - undo_move -
; Undoes the previous move. Modifies board in place to move the piece at [target]
; to square [from], and replaces the captured piece [targetp] (if any) on square
; [target].
;
; Does not read [fromp], which is inferred via [target] square instead
undo_move
  ; clear [target], placing its former encoded piece in the low digit of D
  mov target,A<->B
  mov [B],A         ; A=[target]
  add offset-11,A
  ftl A             ; lookup square offset
  jn .low           ; square mod 2 == 1?

; clear high digit of target square word
;.hi
  swap A,B          ;
  mov [B],A         ; get board at offset
  mov A,D           ; D=save square
  swapdig A
  lodig A           ; isolate high digit (fromp)
  swap A,D          ; D=fromp, A=saved square
  lodig A           ; isolate low digit (clearing high=fromp) 
  mov A,[B]         ; clear target square
  jmp .reset_from

; clear low digit of target square word
.low
  swap A,B          ;
  mov [B],A         ; get board at offset
  mov A,D           ; D=save square
  lodig A           ; isolate low digit (fromp)
  swap A,D          ; D=fromp, A=saved square
  swapdig A
  lodig A           ; isolate high digit (clearing low=fromp)
  swapdig A
  mov A,[B]         ; clear target square
  ; fallthrough

  ; put D=encoded fromp back at [from]
.reset_from
  mov movestate,A<->B ;
  mov [B],A         ; A=movestate
  addn PROMO,A
  jn .unpromo       ; if pawn promotion, undo it
.do_reset_from
  mov from,A<->B    ;
  mov [B],A         ; get from square index
  add offset-11,A   ;
  ftl A             ; lookup square offset
  jn .reset_low

; write high digit of from square word
;.reset_hi
  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (clearing high digit)
  swapdig A
  add D,A           ; add fromp into (high) digit
  swapdig A
  mov A,[B]         ; update board
  jmp .check_other

  ; update player_piece to be a pawn instead of queen
  ; and adjust mscore accordingly
.unpromo
  mov A,[B]         ; clear PROMO flag from movestate
  swap D,A
  addn QUEEN-PAWN,A ; turn queen back into pawn
  swap A,E          ; E=piece 
  
  mov fromp,A<->B
  mov [B],A
  swap A,C          ; C = player|piece for add_score

  mov PBONUS,A
  swap A,D
  jsr add_score

  swap A,E          ; .do_reset_from expects D = piece
  swap A,D
  jmp .do_reset_from

; write low digit of from square word
.reset_low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A         ;
  lodig A           ; isolate high digit (clearing low digit)
  swapdig A
  add D,A           ; add fromp into low digit
  mov A,[B]         ; update board
  ; fallthrough

  ; now the board array has 0 at [target] and encoded fromp back at [from].
  ; but if fromp is a king or rook (aka OTHER), also need to reset the
  ; corresponding auxiliary position
.check_other
  swap D,A
  addn OTHER,A      ; test if from piece is OTHER
  jz reset_other    ; if OTHER, set aux position

  ; put captured [targetp] back on the target square
reset_target
  mov targetp,A<->B ;
  mov [B],A         ; A=[targetp]
  jz reset_out      ; if no capture, done

  ; update material score when undoing a capture
  mov A,C           ; C=save [targetp]
  lodig A
  dec A             ; map PAWN=1 to 0
  swapdig A         ; 10*(piece type-1)
  add pval,A        ; index piece values
  ftl A             ; lookup value
  swap A,D          ; D=value
  clr A
  sub D,A           ; D=-D, we are undoing
  swap A,D          
  jsr add_score

  ; move C=targetp back to target square
  clr A
  swap A,D          ; D=old pos=0
  jsr set_square
reset_out
  jmp far undo_move_ret

  ; set auxiliary position [target] back to [from]. for example if [wrook1]
  ; moved from A7 to A8, set [wrook1] back to A7.
reset_other
  mov from,A<->B    ;
  mov [B],A<->C     ; C=new position=from square
  mov target,A<->B  ;
  mov [B],A<->D     ; D=old position=target square
  mov 2,A<->E       ; E=return to reset_target
  jmp update_pos    ; call update_pos (return to reset_target)


; update_pos updates an auxiliary king or rook position by scanning [wking],
; [bking], [wrook*] for an old position, and setting the matching location to
; a new position.
;
; it is a "nested" subroutine shared by move and undo_move to save code space.
; because the VM has only one level of subroutine stack, E is used to select
; where to return.
;
; C: new position
; D: old position
; E: return address 
update_pos
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
  jmp .out          ; must be implicit brook
.wking
  mov wking,A<->B
  jmp .update
.bking
  mov bking,A<->B
  jmp .update
.wrook1
  mov wrook1,A<->B
  jmp .update
.wrook2
  mov wrook2,A<->B
.update
  swap C,A
  mov A,[B]         ; [pos]=new position
  ; fallthrough
.out
  swap E,A
  jz clear_from     ; E=0 return to clear_from
  dec A
  jz set_other      ; E=1 return to set_target_other
  jmp reset_target  ; E=2+ return to reset_target


; set_square encodes player_piece into the board array at [target]. if the piece
; is a rook or king, it also updates the corresponding auxiliary position to
; [target].
;
; note set_square is tail called by both move and undo_move.
;
; C: player_piece
; D: old position (0 if none, when undoing a capture)
set_square
  mov C,A           ; A=player_piece 
  ; special case for kings/rooks stored outside board array
  lodig A
  addn ROOK,A       ; test if piece >= ROOK
  jn set_aux        ; if so, update other piece pos
  ; encode pawn/knight/bishop/queen for board array
  mov C,A
  swapdig A
  lodig A           ; isolate piece color (0=white, 1=black)
  add pbase,A       ; lookup base piece for color-1
  ftl A
  swap A,D
  mov C,A
  lodig A           ; isolate piece kind
  add D,A           ; encode piece (e.g. for BPAWN, A=5+1)
  ; update board array
  ; A=piece kind
set_target
  swap A,D          ; D=encoded piece kind
  mov target,A<->B  ;
  mov [B],A         ; A=target square
  add offset-11,A
  ftl A             ; lookup square offset
  jn .low           ; square mod 2 == 1?

  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (replacing high digit)
  swapdig A
  add D,A           ; add in piece kind 
  swapdig A
  mov A,[B]         ; update board
  ret

.low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (replacing low digit)
  swapdig A
  add D,A           ; add in piece kind 
  mov A,[B]         ; update board
  ret

  ; update auxiliary positions for rook or king
set_aux
  mov D,A           ; A=D=old position
  jz .undo_capture  ; an old position of 0 means undoing capture
  ; otherwise, call update_pos to update stored position to target
  mov target,A<->B
  mov [B],A<->C     ; C=new position
  mov 1,A<->E       ; E=1 (return to other)
  ; D=old position still
  jmp update_pos    ; update stored position (return to other)

  ; the rook or king was captured, so its auxiliary position will be 0
  ; find the correct auxiliary entry by piece type and update it
.undo_capture
  mov target,A<->B
  mov [B],A<->D     ; D=target
  mov C,A           ; A=player_piece
  addn KING,A       ; white king?
  jz set_wking
  mov C,A
  addn 10+KING,A    ; black king?
  jz set_bking
  mov C,A
  addn ROOK,A       ; white rook?
  jz set_wrook
  ; black rook positions are not stored
  ; fallthrough

  ; now go update the board array
set_other
  mov OTHER,A       ; A=piece kind (OTHER) 
  jmp set_target    ; update board array

set_wking
  mov wking,A<->B   ;
  jmp set_update
set_bking
  mov bking,A<->B   ;
  jmp set_update
set_wrook
  mov wrook1,A<->B  ;
  mov [B],A
  jz set_update     ; if wrook1 is not on board, reuse it
  ; fallthrough
;.wrook2
  mov wrook2,A<->B  ; else reuse wrook2
set_update
  swap D,A          ; A=target
  mov A,[B]         ; [pos]=target
  jmp set_other


; add_score - updates mscore, adding or subtracting depending on which player
; NB: sign convention for captures, that is, add score for black
; C = player|piece
; D = score to add
add_score
  mov mscore,A<->B
  mov C,A
  swapdig A
  lodig A           ; get player
  jz .white
;.black
  mov [B],A
  add D,A           ; mscore += piece value
  jmp .score
.white
  mov [B],A
  sub D,A           ; mscore -= piece value
.score
  mov A,[B]         ; update mscore
  ret

