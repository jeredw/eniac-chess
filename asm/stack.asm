; STACK.ASM 
; Push and pop the search stack
; 
; Instead of indirecting through a stack pointer, the top of the move stack
; is kept at a fixed address to save code space. This requires copying on
; push and pop.

; Pop the move stack, i.e. copy accumulators down
pop
  mov TOP+1,A
  loadacc A
  dec A
  storeacc A      ; copy a10->a9
  add 2,A
  loadacc A
  dec A
  storeacc A      ; copy a11->a10
  add 2,A
  loadacc A
  dec A
  storeacc A      ; copy a12->a11

  ; dec stack depth
dec_depth         ; called from make_eniac_move as a game over sentinel
  mov depth,A<->B
  mov [B],A
  dec A
  mov A,[B]
  ret

; Push the move stack, i.e. copy accumulators up
push
  mov TOP+2,A
  loadacc A
  inc A
  storeacc A      ; copy a11->a12
  dec A
  dec A
  loadacc A
  inc A
  storeacc A      ; copy a10->a11
  dec A
  dec A
  loadacc A
  inc A
  storeacc A      ; copy a9->a10

  ; must also copy alpha/beta from parent to child
  mov depth,A<->B
  mov [B],A         ; A=depth
  add alpha0,A      ; index alpha for depth
  jsr copy_up
  add beta0-alpha0-1,A ; index beta for depth
  jsr copy_up

  ; inc stack depth
  mov depth,A<->B
  mov [B],A
  inc A
  mov A,[B]
  jmp push_ret

; copy word at A to A+1
copy_up
  swap A,B
  mov [B],A<->D     ; D=mem[A]
  swap B,A
  inc A             ; inc address
  swap A,B
  swap D,A
  mov A,[B]         ; mem[A+1] = D
  swap B,A
  ret
