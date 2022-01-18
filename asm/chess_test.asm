; CHESS_TEST.ASM
; Test harness version of chess.asm, to be called by asm_test.py
; Makes a single move and then halts

  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far test

  .include movegen.asm
  .include get_square.asm

  .org 200
  .include move.asm
  ;.include debug.asm

  .org 306
test
  .include load_board.asm
start
  .include search.asm
search_done
  ; print the best move found during the search
  mov BEST,A
  loadacc A           ; I=bestfrom, J=bestto
  mov J,A
  swap A,B
  mov I,A
  print
  halt

game