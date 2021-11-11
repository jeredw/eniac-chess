; CHESS_TEST.ASM
; Test harness version of chess.asm, to be called by asm_test.py
; Makes a single move and then halts

  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far test

  .include movegen.asm    ; 71 lines
  .include get_square.asm ; 15 lines

  .org 200
  .include move.asm       ; 65 lines
  ;.include debug.asm

  .org 306
test
  .include load_board.asm
start
  .include search.asm
search_done
  ; print the best move found during the search
  mov bestfrom,A<->B  ; 
  mov [B],A<->D       ; D=[bestfrom]
  mov bestto,A<->B
  mov [B],A<->B       ; B=[bestto]
  swap D,A            ; A=[bestfrom]
  print               ;
  halt
