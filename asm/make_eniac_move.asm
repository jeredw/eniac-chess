; make_eniac_move.asm
; Update board with ENIAC's move, to keep the GUI in sync
; technically not needed, but easiest way to demo. Include after move print op.

; Make ENIAC's move on board. Requires setting fromp, from, target in top of stack
; We've just printed a move so A = bestfrom, B=bestto

  swap A,D 				; D=bestfrom
  swap A,B
  swap A,E 				; E=bestto
  jsr get_square
  swap A,C 				; C=player|piece on bestfrom
  mov fromp, A<->B
  swap A,C
  mov A,[B]  			; fromp = player|piece
  mov from,A<->B
  swap A,D
  mov A,[B] 			; from = bestfrom
  mov target,A<->B
  swap A,E
  mov A,[B] 			; target = bestto
  jsr move


