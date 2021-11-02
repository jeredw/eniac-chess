; DEBUG.ASM
; Some helper routines for debugging, not usually included from chess.asm.

print_best_move
  mov depth,A<->B  ; 
  mov [B],A<->D       ; D=[depth]
  mov bestscore,A<->B
  mov [B],A<->B       ; B=[bestscore]
  swap D,A            ; A=[depth]
  print               ;
  mov bestfrom,A<->B  ; 
  mov [B],A<->D       ; D=[bestfrom]
  mov bestto,A<->B
  mov [B],A<->B       ; B=[bestto]
  swap D,A            ; A=[bestfrom]
  print               ;
  ret
