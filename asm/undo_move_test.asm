; test bench for move.asm (undo_move)
; tests board state updates
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  jmp far undo_move
undo_move_ret
  jmp far print_board

  .include get_square.asm
  .include print_board.asm

  .org 200
  .include move.asm

move_ret