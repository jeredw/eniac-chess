; STACK.ASM 
; Push and pop the search stack
; 
; 36 words of memory form a 4-level software stack for alpha/beta search.
; Instead of indirecting through a stack pointer, the top of stack is kept at
; a fixed address to save code space. This requires copying on push and pop.
;
; To make that copying more efficient using loadacc/storeacc, stack entries are
; stored with a stride of 10 words at offsets 36, 46, 56, and 66. Thus we can
; copy quickly using loadacc/storeacc. Locations 35,35,55,65 are used for 
; various game state and must be preserved.
;
; a7  |xx 36 37 38 39
; a8   40 41 42 43 44|
; a9  |xx 46 47 48 49
; a10  50 51 52 53 54|
; a11 |xx 56 57 58 59
; a12  60 61 62 63 64|
; a13 |xx 66 67 68 69
; a14  70 71 72 73 74|

; Pop a move off the search stack, i.e. copy accumulators down
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
  addn 12,A       ;
  jz .out         ; if A==12, done copying
  add 12+3,A
  flipn
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
  ; dec stack depth
  mov depth,A<->B
  mov [B],A
  dec A
  mov A,[B]
  ret

; Push the search stack, i.e. copy accumulators up
push
  mov 45,A<->B
  mov [B],A<->C   ; C=save [45]
  mov 55,A<->B
  mov [B],A<->D   ; D=save [55]
  mov 65,A<->B
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
  flipn
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
  ; inc stack depth
  mov depth,A<->B
  mov [B],A
  inc A
  mov A,[B]
  ret
