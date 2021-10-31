; Pop the search stack (invalidates fromp)
pop
  mov 45,A<->B
  mov [B],A<->C   ; C=save [45]
  mov 55,A<->B
  mov [B],A<->D   ; D=save [55]
  mov 9,A
.loop
  loadacc A       ; load acc A
  dec A
  dec A
  storeacc A      ; copy to A-2
  inc A
  addn 15,A       ; 
  jz .out         ; if A==15, done copying
  add 15,A
  jmp .loop
.out
  ; fix [45] and [55] which got clobbered
  mov 45,A<->B
  swap C,A
  mov A,[B]       ; restore [45]
  mov 55,A<->B
  swap D,A
  mov A,[B]       ; restore [55]
  ret

; Push the search stack (invalidates fromp)
push
  mov 45,A
  mov [B],A<->C   ; C=save [45]
  mov 55,A
  mov [B],A<->D   ; D=save [55]
  mov 65,A
  mov [B],A<->E   ; E=save [65]
  mov 7,A
.loop
  loadacc A       ; load acc A
  inc A
  inc A
  storeacc A      ; copy to A+2
  dec A
  addn 13,A       ; 
  jz .out         ; if A==13, done copying
  add 13,A
  jmp .loop
.out
  ; fix [45], [55], and [65] which got clobbered
  mov 45,A<->B
  swap C,A
  mov A,[B]       ; restore [45]
  mov 55,A<->B
  swap D,A
  mov A,[B]       ; restore [55]
  mov 65,A<->B
  swap E,A
  mov A,[B]       ; restore [65]
  ret
