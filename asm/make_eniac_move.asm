; make_eniac_move.asm
; Update board with ENIAC's move, to keep the GUI in sync
; technically not needed, but easiest way to demo. Include after move print op.

; Make ENIAC's move on board. Requires setting fromp, from, target in top of stack
; Input: A=bestfrom, B=bestto

  jz resign
  swap A,D
  swap A,B
  swap A,E
  jsr get_square
  swap A,C        ; C=player|piece on bestfrom
  mov TOP0,A
  loadacc A
  swapall         ; A=fromp, C=from, D=target, F=TOP0, H=player|piece, I=bestfrom, J=bestto
  mov I,A
  swap A,C        ; from=bestfrom
  mov J,A 
  swap A,D        ; target=bestto  
  mov H,A         ; from=player|piece
  swapall
  storeacc A

  ; set stack depth=0 to signal move to jump to game
  jsr dec_depth
  jmp far move

resign
  halt
