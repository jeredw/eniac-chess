; SEARCH.ASM
; Minimax search loop with alpha/beta pruning
; Finds the best move to play next and then jumps to search_done

; assume it is ENIAC's turn to move, and that the starting position is
; legal (both sides have a king, and the opponent's king can't be
; immediately captured)

; load_board.asm sets up the initial search stack frame
; the initial best move 0000 means to resign.  any legal move should
; score better, but if there is none (i.e. checkmate) eniac will resign
search
  ; call movegen for top of stack
  jmp far next_move

; movegen jumps here when there is a move to try
output_move
  ; before iterating to next move, apply alpha/beta pruning
  ; can stop searching moves at this depth if alpha >= beta
  mov depth,A<->B
  mov [B],A         ; A=depth
  add alpha0,A      ; index alpha for depth
  swap A,B
  mov [B],A<->D     ; D=alpha
  swap B,A          ; get alpha address
  add beta0-alpha0,A ; beta is +4 from it
  swap A,B
  mov [B],A         ; A=beta
  sub D,A           ; compare alpha and beta
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
  jz .no_capture    ; if no piece captured, consider pruning
  addn KING,A       ; is it a king?
  jz search_pop     ; if would capture king, fixup stack
  jmp .apply_move

  ; optimization: at leaf nodes, only evaluate capture moves
  ; we must still record that there _was_ a move possible, otherwise
  ; moves with no answering captures look like checkmate
.no_capture
  swap A,E          ; set E=0 to flag not to undo move
  mov depth,A<->B
  mov [B],A
  addn MAXD,A
  jz leaf           ; assume parent mscore
  ; not a leaf, so fallthrough to evaluate move

  ; apply the move (updating mscore)
.apply_move
  jmp far move
move_ret
  mov 1,A
  swap A,E          ; flag that we must undo move later

  mov depth,A<->B
  mov [B],A         ; A=stack depth
  addn MAXD,A       ; is depth at maximum?
  jz leaf           ; if yes, this is a leaf node

  ; the score for this node is the min or max of its children
  ; push a child search node, with alpha/beta copied from this node
  jmp push
push_ret
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
  ; undoes move only if E is nonzero
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
  mov beta0+MAXD,A<->B ; first update beta
  mov [B],A
  sub D,A           ; beta - score
  jn .minbest       ; if beta < score, no update
  mov D,A
  mov A,[B]         ; set new beta
.minbest
  mov bestscore,A<->B
  mov [B],A         ; A=bestscore
  sub D,A           ; A=bestscore - mscore
  flipn
  jn .newbest       ; if mscore < bestscore, new best move
  jmp .movedone
.max
  mov alpha0+MAXD,A<->B; first update alpha
  mov [B],A         ; alpha
  sub D,A           ; alpha - score
  flipn
  jn .maxbest       ; if score < alpha, no update
  mov D,A
  mov A,[B]         ; set new alpha
.maxbest
  mov bestscore,A<->B
  mov [B],A         ; A=bestscore
  sub D,A           ; A=bestscore - mscore
  flipn
  jn .movedone      ; if mscore <= bestscore, not a best move
.newbest            ; else >
  swap D,A
  mov A,[B]         ; [bestscore] = current score
.movedone
  swap E,A
  jz search         ; if E=0, move was skipped, so don't undo_move
  jmp far undo_move ; continues at undo_move_ret

; movegen jumps here when there are no more moves possible
no_more_moves
  ; check if we have found the best move
  ;brk
  mov depth,A<->B
  mov [B],A
  dec A
  jz search_done    ; if depth==1, done
  swap A,E          ; save depth-1 in E to update alpha/beta

  ; done iterating over child moves
  ; now we know the parent move was legal (otherwise we would have jumped
  ; to search_pop) and bestscore is the final score of this subtree
  ; update parent's bestscore if this move is better than its current best
  mov bestscore,A<->B
  mov [B],A<->C     ; C=best score for this node
  ; determine if the parent stack frame is for min or max
  jsr other_player  ; get 1-player in A's low digit
  jz .pmax          ; if white, score pmax
;.pmin              ; else, score pmin
  ; parent is min, update its best move if bestscore < pbestscore
  ; (if this is a new low, first update beta)
  mov E,A           ; A=depth-1
  add beta0,A       ; index parent beta
  swap A,B
  swap C,A
  swap A,D          ; D=best score
  mov [B],A         ; A=beta
  sub D,A           ; A=beta - bestscore
  jn .minbest       ; if beta < bestscore, no update
  mov D,A
  mov A,[B]         ; set new beta
.minbest
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jz search_pop     ; if bestscore == pbestscore, continue
  jn .newbest       ; if bestscore < pbestscore, new best move
  jmp search_pop
.pmax
  ; parent is max, update its best move if bestscore >= pbestscore
  ; (if this is a new high, first update alpha)
  mov E,A           ; A=depth-1
  add alpha0,A      ; index parent alpha
  swap A,B
  swap C,A
  swap A,D          ; D=best score
  mov [B],A         ; A=alpha
  sub D,A           ; A=alpha - bestscore
  flipn
  jn .maxbest       ; if bestscore < alpha, no update
  mov D,A
  mov A,[B]         ; set new alpha
.maxbest
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jn search_pop     ; if bestscore < pbestscore, not a best move
.newbest
  swap D,A
  mov A,[B]         ; [pbestscore] = current score

  swap E,A          ; A=depth-1
  dec A             ; at depth 2?
  jz set_best_move  ; if so, update best move
  ; fallthrough to search_pop

search_pop
  ; no more moves at current depth.  parent stack frame has already
  ; been updated with best score, so just pop
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

; records the current move at depth 1 as the best move
set_best_move
  mov pfrom,A<->B
  mov [B],A<->D     ; D=[pfrom]
  mov bestfrom,A<->B
  swap D,A
  mov A,[B]         ; [bestfrom]=D
  mov ptarget,A<->B
  mov [B],A<->D     ; D=[ptarget]
  mov bestto,A<->B
  swap D,A
  mov A,[B]         ; [bestto]=D
  jmp search_pop
