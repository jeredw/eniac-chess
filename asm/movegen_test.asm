; test bench for movegen.asm
; reads initial memory state then outputs possible moves
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  .include movegen.asm

output_move
  ; save generated move to memory - should be in movegen.asm
  ; A=to, B=?, C=movestate, D=from, E=player|piece
  swap A,B
  mov target,A
  swap A,B
  mov A,[B]         ; target = A
  mov movestate,A<->B
  swap A,C
  mov A,[B]         ; movestate = C

  ; make the move, then check for check
  jsr move
  jmp far checkcheck

checkcheckret
  jz no_check

  jsr undo_move

  ; all this should be in movegen.asm
  ; F=35,G=36,H=37,I=38,J=39
  mov 7,A
  loadacc A
  mov J,A           ; C = movestate = [39]
  swap A,C
  mov H,A           ; D = from = [37]
  swap A,D
  mov F,A           ; E = fromp = player|piece = [35]
  swap A,E
  mov I,A           ; A = target = [38]
  jmp next_piece_move

no_check
  jsr undo_move

  ; F=35,G=36,H=37,I=38,J=39
  mov 7,A
  loadacc A
  mov J,A           ; C = movestate = [39]
  swap A,C
  mov F,A           ; E = fromp = player|piece = [35]
  swap A,E
  mov I,A           ; B = target = [38]
  swap A,B
  mov H,A           ; A = from = [37]

  print

  swap A,D          
  swap A,B          ; now A=to, C=movestate, D=from, E=fromp
  
  jmp next_piece_move

done_squares
  halt

  .org 200
  .include move.asm
  .include checkcheck.asm

  .org 306
  .include get_square.asm
  .include score.asm
