; test bench for movegen.asm
; reads initial memory state then outputs possible moves
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  .include movegen.asm
  .include get_square.asm

output_move
  ; A=to, B=ptype, C=movestate, D=from, E=player
  swap A,B
  swap A,D          ; now A=from, B=to, D=ptype

  print

  swap A,D          
  swap A,B          ; now B=ptype, D=from

  jmp next_piece_move

done_squares
  halt
