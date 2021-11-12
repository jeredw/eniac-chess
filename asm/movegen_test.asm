; MOVEGEN_TEST.ASM
;
; Test harness for movegen.asm and checkcheck.asm, to be called by asm_test.py
; reads initial memory state then outputs possible moves
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm
start
  jmp next_move

output_move
  ; make the move, then check for check
  jsr move
  jmp far checkcheck

checkcheckret
  jz no_check
  jsr undo_move

  jmp next_move

no_check
  jsr undo_move

  ; read out target and from squares to print
  mov 7,A
  loadacc A
  mov I,A           ; B = target = [38]
  swap A,B
  mov H,A           ; A = from = [37]

  print
  
  jmp next_move

no_more_moves
  halt

  .include movegen.asm
  .include get_square.asm

  .org 200
  .include move.asm  
 
  .org 306
  .include checkcheck.asm
