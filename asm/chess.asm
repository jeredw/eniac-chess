; ENIAC chess search program
; 4-ply minimax search with alpha/beta pruning and simple material scoring,
; and no special opening or endgame logic.  ENIAC always plays white.
  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far game       ; the game outer loop is in ft3
done_squares         ; where movegen jumps when done
  jmp far no_more_moves
  .include movegen.asm
  .include get_square.asm

  .org 200
  .include move.asm
  .include score.asm
  ;.include checkcheck.asm

  .org 306
game
  ; set memory state from cards
  ; assume this includes the human player's move
  .include load_board.asm
start
  ; eniac to move
  ; set up the initial search stack frame
  mov depth,A<->B
  mov 1,A
  mov A,[B]         ; depth=1 i.e. one entry on stack
  ; XXX if needed we could delegate this to load_board.asm
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
  clrall
  swapall
  mov TOP0,A        ;
  storeacc A

search
  jmp far next_move

; movegen jumps here when there are no more moves possible
no_more_moves
  ; if depth==1 then we have the best move at top of stack
  mov depth,A<->B
  mov [B],A
  dec A
  jz search_done    ; if depth==1, done

  mov bestscore,A<->B
  mov [B],A<->D     ; D=best score for this node
  ; determine if the parent stack frame is for min or max
  ; if parent is max, it will take max of its children, and so we should update
  ; it only if our best score is better than its best, etc.
  mov fromp,A<->B
  mov [B],A         ; get current player (from player|piece)
  swapdig A
  lodig A           ; A=player
  add oplayer,A
  ftl A             ; A=1-player
  jz .pmax          ; if white, score pmax
;.pmin               ; else, score pmin
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jn .newbest       ; if bestscore < pbestscore, new best move
  jmp .pop
.pmax
  mov pbestscore,A<->B
  mov [B],A         ; A=pbestscore
  sub D,A           ; A=pbestscore - bestscore
  flipn
  jn .pop           ; if bestscore < pbestscore, not a best move
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

.pop
  ; no more moves at current depth.  parent stack frame has already
  ; been updated with best move and score, so just pop
  jsr pop
  jsr undo_move
  ; reset [fromp] for movegen
  mov from,A<->B
  mov [B],A<->D     ; D=[from] square
  jsr get_square
  swap A,D
  mov fromp,A<->B
  swap D,A
  mov A,[B]         ; [fromp]
  jmp search

; movegen jumps here when there is a move to try
output_move
  ; apply the move (updating mscore)
  jsr move
  mov depth,A<->B
  mov [B],A         ; A=stack depth
  addn MAXD,A       ; is depth at maximum?
  jz leaf           ; if yes, this is a leaf node
  ; TODO if a king is missing, the previous move wasn't legal
  ; deal with this in some intelligent way

  ; the score for this node is the min or max of its children
  ; push a child search node
  jsr push
  ; init bestscore according to whether this is a min/max frame
  jsr flip_player
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
  ; TODO should probably have a special case for no king/checkmate
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
  jn .movedone      ; if mscore < bestscore, not a best move
.newbest            ; else >=
  swap D,A
  mov A,[B]         ; [bestscore] = current score
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
.movedone
  jsr undo_move
  jmp search

checkcheckret
  jmp search

search_done
  ; print the best move found during the search
  mov bestfrom,A<->B  ; 
  mov [B],A<->D       ; D=[bestfrom]
  mov bestto,A<->B
  mov [B],A<->B       ; B=[bestto]
  swap D,A            ; A=[bestfrom]
  print               ;
  halt
  jmp game

  .include stack.asm

; flip the current player for movegen
; returns new player in A
flip_player
  mov fromp,A<->B
  mov [B],A         ; A=[fromp]
  swapdig A         ;
  lodig A           ; A=player field from current fromp
  add oplayer,A     ; 
  ftl A             ; A=1-current player
  swapdig A         ; (swap into player field)
  mov A,[B]         ; store new fromp
  ret
