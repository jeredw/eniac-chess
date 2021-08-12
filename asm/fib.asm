; compute fibonacci numbers
.isa v4
.org 100
  mov 10, A   ; 10 numbers
  swap A, B
              ; D=Fn-2 (starting at 0)
  mov 1, A    ; C=Fn-1
  swap A, C

loop
  mov C, A    ; A=Fn-1
  add D, A    ; A=Fn = Fn-1 + Fn-2
  print
  ; now A=Fn, C=Fn-1, D=Fn-2
  ; want C=Fn, D=Fn-1
  swap A, C   ; A=Fn-1, C=Fn
  swap A, D   ; A=xx, C=Fn, D=Fn-1
  mov B, A
  dec A       ; dec loop counter
  jz done     ; if 0, all done
  swap B, A   ; update counter and continue
  jmp loop

done
  mov 99, A
  print
  halt