; chess.asm
; 
  .isa v4
  .org 100

  .include memory_layout.asm
  .include load_board.asm

start
  .include movegen.asm
  .include get_square.asm

; We have generated a move! Use it (atm just print it)
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

; - Print Board -
; Halts at end, not a subroutine because it calls get_square
printboard
  mov 11,A
pb_nextsq
  jsr get_square
  print
  mov D,A         ; restore square
  inc A           ; move one square right
  jil pb_nextline
  jmp pb_nextsq
pb_nextline
  add 2,A         ; move to start of next line, e.g. 19 -> 21
  jil pb_done
  jmp pb_nextsq
pb_done
  halt
