; make_eniac_move.asm
; Update board with ENIAC's move, to keep the GUI in sync
; technically not needed, but easiest way to demo. Include after move print op.

; Make ENIAC's move on board. Requires setting fromp, from, target in top of stack
; Input: A=bestfrom, B=bestto

  jz resign       ; if no move, resign
  swap A,D
  swap A,B
  swap A,E
  jsr get_square
  swap A,C        ; C=player|piece on bestfrom
  mov TOP,A
  loadacc A
  swapall         ; A=xx, C=from, D=target, F=TOP, H=player|piece, I=bestfrom, J=bestto
  mov I,A
  swap A,C        ; from=bestfrom
  mov J,A 
  swap A,D        ; target=bestto  
  swapall
  storeacc A
  mov fromp,A<->B
  swap C,A
  mov A,[B]       ; fromp=player|piece

  ; set stack depth=0 to signal move to jump to game
  jsr dec_depth
  jmp far move

resign
  ; we could halt here, but for engine play it's nicer to just jump
  ; back to the game loop to accept a new game position
  jmp far game
