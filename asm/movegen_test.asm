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
  mov 7,A
  loadacc A
  mov I,A           ; C = movestate = [38]
  swap A,C
  mov G,A           ; D = from = [36]
  swap D,A
  mov H,A           ; E = fromp = player|piece = [37]
  swap A,E
  mov J,A           ; A = target = [39]
  jmp next_piece_move

no_check
  jsr undo_move

  mov 7,A
  loadacc A
  mov I,A           ; C = movestate = [38]
  swap A,C
  mov H,A           ; E = fromp = player|piece = [37]
  swap A,E
  mov J,A           ; B = target = [39]
  swap A,B
  mov G,A           ; A = from = [36]

  print

  swap A,D          
  swap A,B          ; now A=to, C=movestate, D=from, E=fromp
  
  jmp next_piece_move

done_squares
  halt

  .org 200
  .include move.asm
  .include checkcheck.asm

  .org 310
  .include get_square.asm


