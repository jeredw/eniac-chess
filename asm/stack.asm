; Pop the search stack
pop
  mov 35,A<->B
  mov [B],A<->E   ; E=save [35]
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
  addn 14,A       ; 
  jz .out         ; if A==14, done copying
  add 14+3,A
  jmp .loop
.out
  ; fix [35], [45] and [55] which got clobbered
  mov 35,A<->B
  swap E,A
  mov A,[B]       ; restore [35]
  mov 45,A<->B
  swap C,A
  mov A,[B]       ; restore [45]
  mov 55,A<->B
  swap D,A
  mov A,[B]       ; restore [55]
  ret

; Push the search stack
push
  mov 45,A
  mov [B],A<->C   ; C=save [45]
  mov 55,A
  mov [B],A<->D   ; D=save [55]
  mov 65,A
  mov [B],A<->E   ; E=save [65]
  mov 12,A
.loop
  loadacc A       ; load acc A
  inc A
  inc A
  storeacc A      ; copy to A+2
  addn 9,A        ;
  jz .out         ; if A==9, done copying
  add 9-3,A
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
