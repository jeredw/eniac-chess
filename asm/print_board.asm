; - Print Board -
; Halts at end, not a subroutine because it calls get_square
print_board
  mov 11,A
.next_square
  swap A,D
  jsr get_square
  swap A,B        ; B=what is here
  mov D,A         ; A=square
  print
  inc A           ; move one square right
  jil .next_line
  jmp .next_square
.next_line
  add 2,A         ; move to start of next line, e.g. 19 -> 21
  jil .done
  jmp .next_square
.done
  halt
