; ENIAC chess search program
; 3-ply minimax search with alpha/beta pruning and simple material scoring,
; and no special opening or endgame logic.  ENIAC always plays white.
  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far game       ; the game outer loop is in ft3

  .include movegen.asm
  .include get_square.asm
done_squares
output_move
  halt
checkcheckret
  .include score.asm

  .org 200
  .include move.asm
  .include checkcheck.asm

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
  mov 99,A<->E      ; beta=99
  clr A
  swap A,D          ; alpha=0
  mov SZERO,A<->C   ; best_score=50 (zero)
  clr A
  swap A,B          ; bestto=0
  clr A             ; bestfrom=0
  swapall
  mov TOPS,A
  storeacc A        ; store TOPS
  ; [movestate]=0 makes movegen initialize TOPM
  mov movestate,A<->B
  clr A
  mov A,[B]         ; movestate=0

search
  mov depth,A<->B
  mov [B],A         ; check stack depth
  jz search_done    ; if stack is empty, done
  ; top of stack contains the current search state

  ; movestate==0 signals the start of a search at new depth
  mov movestate,A<->B
  mov [B],A         ; A=[movestate]
  jz new_depth      ; if movestate=0, new depth
  ; else iterating over possible moves at current depth

  ; TODO jsr undo_move
  ; TODO update the best move at current depth
  jmp next_move

  ; cannot search deeper, cut off at current depth
search_cutoff
  jmp search

next_move
  ; TODO before iterating to next move, apply alpha/beta pruning
  ; can stop searching moves at this depth if alpha >= beta
  jmp check_move

new_depth
  ; begin search at new depth, unless search should terminate here
  ; TODO check for a winner. if the game is won, short-circuit
  ; check for stack cutoff
  mov depth,A<->B
  mov [B],A         ; read stack depth
  addn MAXD,A
  jz search_cutoff

check_move
  ; TODO call movegen
  ; TODO if no more moves, pop and jmp back to search
  ; else current stack frame will reflect movegen iteration
  ; apply move and push a new recursive frame
  ; jsr push
  ; TODO init bestscore according to whether this is a min/max frame
  ; TODO tell movegen to start over for this new frame
  jmp search

search_done
  ; TODO copy bestfrom/bestto into move fields and jsr move
  ; TODO print out the board state before looping
  jmp game

  .include stack.asm
