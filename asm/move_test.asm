; MOVETEST.ASM
;
; test harness for move.asm (move), to be called by asm_test.py
; tests board state updates
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  jsr move
  jmp far print_board

  .include move.asm
  .include get_square.asm

  .org 200
  .include score.asm
  .include print_board.asm
