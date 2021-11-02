; CHESS.ASM
; ENIAC chess - the best game for the first computer
; By Jonathan Stray and Jered Wierzbicki
; 
; This is the main game file which includes and places all routines and does the search.
; It is a 4-ply minimax search with alpha/beta pruning and simple material scoring,
; and no special opening or endgame logic. ENIAC always plays white.
;
; This file, like all asm files in this project, is written in the custom VM language
; It is assembled by chasm.py into simulator switch settings chess.e, concatenated by
; with VM wiring patch setup chessvm.e, and then executed by eniacsim. 

  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far game       ; the game outer loop is in ft3

  .include movegen.asm    ; 71 lines
  .include get_square.asm ; 15 lines

  .org 200
  .include move.asm       ; 65 lines
  .include score.asm      ; 11 lines
  ;.include checkcheck.asm ; 41 lines

;debug_print
;  mov depth,A<->B  ; 
;  mov [B],A<->D       ; D=[depth]
;  mov bestscore,A<->B
;  mov [B],A<->B       ; B=[bestscore]
;  swap D,A            ; A=[depth]
;  print               ;
;  mov bestfrom,A<->B  ; 
;  mov [B],A<->D       ; D=[bestfrom]
;  mov bestto,A<->B
;  mov [B],A<->B       ; B=[bestto]
;  swap D,A            ; A=[bestfrom]
;  print               ;
;  ret


; Main program - we jump here on reset
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
  ; note this also sets [35]=[fromp] to 0, white to move
  clrall
  swapall
  mov TOP0,A
  storeacc A

search
  ; call movegen for top of stack
  jmp far next_move

; movegen jumps here when there is a move to try
output_move
  ; init best move to the current move if there is none
  ; this is needed in case there are no child moves
  mov bestfrom,A<->B
  mov [B],A
  jz .set_best
  jmp .prune
.set_best
  jsr set_best_move

.prune
  ; before iterating to next move, apply alpha/beta pruning
  ; can stop searching moves at this depth if alpha >= beta
  mov alpha,A<->B   ;
  mov [B],A<->D     ; D=alpha
  mov beta,A<->B    ;
  mov [B],A         ; A=beta
  sub D,A
  jn no_more_moves  ; if beta<=alpha, stop iteration
  jz no_more_moves  ; if beta==alpha, stop iteration

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
  jn .movedone      ; if mscore <= bestscore, not a best move
.newbest            ; else >
  swap D,A
  mov A,[B]         ; [bestscore] = current score
  jsr set_best_move
.movedone
  jsr undo_move
  jmp search

; movegen jumps here when there are no more moves possible
no_more_moves
  ; if depth==1 then we have the best move at top of stack
  mov depth,A<->B
  mov [B],A
  dec A
  jz search_done    ; if depth==1, done

  ; done iterating over child moves, so bestscore is the final score
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
  jmp .pop
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

  ; DEBUG <depth><bestscore> <bestfrom><bestto>
  ;jsr debug_print

  jsr undo_move
  ; reset [fromp] from board state for movegen
  mov from,A<->B
  mov [B],A<->D     ; D=[from] square
  jsr get_square
  swap A,D
  mov fromp,A<->B
  swap D,A
  mov A,[B]         ; [fromp]
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
