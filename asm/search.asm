; SEARCH.ASM
; Minimax search loop with alpha/beta pruning
; Finds the best move to play next and then jumps to search_done

; assume it is ENIAC's turn to move, and that ENIAC is playing white
; also assume the starting position is legal (both sides have a king,
; and black's king can't be immediately captured)

; set up the initial search stack frame
; the initial best move 0000 means to resign.  any legal move should
; score better, but if there is none (i.e. checkmate) eniac will resign
  mov depth,A<->B
  mov 1,A
  mov A,[B]         ; depth=1 i.e. one entry on stack
  ; NOTE if needed we could delegate this to load_board.asm
  clrall            ; ABCDE=0
  mov 99,A<->E      ; E=beta=99
                    ; D=alpha=0
                    ; C=best_score=0
                    ; B=bestto=0
  clr A             ; A=bestfrom=0
  swapall
  mov TOP1,A
  storeacc A        ; store TOP1
  ; init TOP0 to 0, setting all move-related state to zero
  ; NOTE this also sets [35]=[fromp] to 0, white to move
  clrall
  swapall
  mov TOP0,A
  storeacc A

search
  ; call movegen for top of stack
  jmp far next_move

; movegen jumps here when there is a move to try
output_move
  ; DEBUG <depth><bestscore> <from><target>
  ; jsr print_move

  ; before iterating to next move, apply alpha/beta pruning
  ; can stop searching moves at this depth if alpha >= beta
  mov alpha,A<->B   ;
  mov [B],A<->D     ; D=alpha
  mov beta,A<->B    ;
  mov [B],A         ; A=beta
  sub D,A
  jn no_more_moves  ; if beta<alpha, stop iteration
  jz no_more_moves  ; if beta==alpha, stop iteration

  ; check for illegal moves
  ; if we are about to capture a king, don't. instead, stop iteration at
  ; this level and skip over the parent move.
  ; note the illegal parent move can't have been set as the best move at
  ; its depth because we are stopping before no_more_moves
  mov targetp,A<->B
  mov [B],A
  lodig A           ; get captured piece
  addn KING,A       ; is it a king?
  jz search_pop     ; if capturing king, fixup stack

  ; apply the move (updating mscore)
  mov 10,A
  jmp far move
move_ret

  mov depth,A<->B
  mov [B],A         ; A=stack depth
  addn MAXD,A       ; is depth at maximum?
  jz leaf           ; if yes, this is a leaf node

  ; the score for this node is the min or max of its children
  ; push a child search node
  jsr push
  ; init child bestscore according to whether it is a min/max frame
  jsr other_player  ; get other player
  swapdig A         ; (swap into player field)
  mov A,[B]         ; store new fromp (B=fromp)
  jz .max           ; if player is white then maximize score
;.min
  mov bestscore,A<->B
  mov 99,A
  mov A,[B]         ; init best score=99
  jmp .reset_movegen
.max
  mov bestscore,A<->B
  clr A
  mov A,[B]         ; init best score=0
  ; fallthrough
.reset_movegen
  ; tell movegen to start over for this new recursive stack frame
  mov from,A<->B
  clr A
  mov A,[B]         ; set from=0 so movegen starts over
  jmp search

  ; update best score for leaf nodes using material score
leaf
  mov mscore,A<->B
  mov [B],A<->D     ; D=mscore
  ; determine if the current stack frame is for min or max
  mov fromp,A<->B
  mov [B],A         ; get current player (from player|piece)
  swapdig A
  lodig A           ; A=player
  jz .max           ; if white, score max
;.min               ; else, score min
  mov bestscore,A<->B
  mov [B],A         ; A=bestscore
  sub D,A           ; A=bestscore - mscore
  flipn
  jn .newbest       ; if mscore < bestscore, new best move
  jmp .movedone
.max
  mov bestscore,A<->B
  mov [B],A         ; A=bestscore
  sub D,A           ; A=bestscore - mscore
  flipn
  jn .movedone      ; if mscore <= bestscore, not a best move
.newbest            ; else >
  swap D,A
  mov A,[B]         ; [bestscore] = current score
  jsr set_best_move
.movedone
  jmp far undo_move ; continues at undo_move_ret

; movegen jumps here when there are no more moves possible
no_more_moves
  ; if depth==1 then we have the best move at top of stack
  mov depth,A<->B
  mov [B],A
  dec A
  jz search_done    ; if depth==1, done

  ; done iterating over child moves
  ; now we know the parent move was legal (otherwise check_legal would
  ; have stopped iteration) and bestscore is the final score of this subtree
  ; update parent's bestscore if this move is better than its current best
  mov bestscore,A<->B
  mov [B],A<->D     ; D=best score for this node
  ; determine if the parent stack frame is for min or max
  jsr other_player  ; get 1-player in A's low digit
  jz .pmax          ; if white, score pmax
;.pmin              ; else, score pmin
  ; parent is min, update its best move if bestscore < pbestscore
  ; (if this is a new low, first update beta)
  mov pbeta,A<->B
  mov [B],A         ; A=pbeta
  sub D,A           ; A=pbeta - bestscore
  jn .minbest       ; if beta < bestscore, no update
  mov D,A
  mov A,[B]         ; set new pbeta
.minbest
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jn .newbest       ; if bestscore < pbestscore, new best move
  jmp search_pop
.pmax
  ; parent is max, update its best move if bestscore >= pbestscore
  ; (if this is a new high, first update alpha)
  mov palpha,A<->B
  mov [B],A         ; A=palpha
  sub D,A           ; A=palpha - bestscore
  flipn
  jn .maxbest       ; if bestscore < palpha, no update
  mov D,A
  mov A,[B]         ; set new palpha
.maxbest
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jn search_pop     ; if bestscore < pbestscore, not a best move
.newbest
  swap D,A
  mov A,[B]         ; [pbestscore] = current score
  mov pfrom,A<->B
  mov [B],A<->D     ; D=[pfrom]
  mov pbestfrom,A<->B
  swap D,A
  mov A,[B]         ; [pbestfrom]=D
  mov ptarget,A<->B
  mov [B],A<->D     ; D=[ptarget]
  mov pbestto,A<->B
  swap D,A
  mov A,[B]         ; [pbestto]=D

search_pop
  ; no more moves at current depth.  parent stack frame has already
  ; been updated with best move and score, so just pop
  jsr pop

  ; fromp is not stored in stack frame, must be restored from board state after pop
  ; but note we're about to undo the last move we made at this depth, so fromp is
  ; actually stored in the target square
  mov target,A<->B
  mov [B],A<->D     ; D=target
  jsr get_square
  swap A,D
  mov fromp,A<->B
  swap D,A
  mov A,[B]         ; fromp=player|piece

  ; DEBUG 99xx <depth><bestscore> <bestfrom><bestto>
  ;jsr print_best_move

  jmp far undo_move
undo_move_ret
  jmp search

; stack routines
  .include stack.asm

; returns the opposite player
other_player
  mov fromp,A<->B
  mov [B],A         ; A=[fromp]
  swapdig A         ;
  lodig A           ; A=player field from current fromp
  add oplayer,A     ; 
  ftl A             ; A=1-current player
  ret

; sets the best move at top of stack to the current move
set_best_move
  mov from,A<->B
  mov [B],A<->D     ; D=[from]
  mov bestfrom,A<->B
  swap D,A
  mov A,[B]         ; [bestfrom]=D
  mov target,A<->B
  mov [B],A<->D     ; D=[target]
  mov bestto,A<->B
  swap D,A
  mov A,[B]         ; [bestto]=D
  ret
