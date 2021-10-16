; test bench for move.asm (undo_move)
; tests board state updates
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  jsr undo_move
  jmp print_board

  .include move.asm
  .include print_board.asm
  .include get_square.asm
