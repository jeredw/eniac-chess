  .isa v4
  .org 390

; Load word at address B into A.  Clobbers F-J.
LOAD .align
  indexacc    ; A = accumulator# with address B
  loadacc A   ; LS = accumulator[A]
  swapall     ; stash RF (in the process, setting G=B)
  indexswap   ; A = ABCDE[G%5]
  swapall     ; restore RF
  mov A, F    ; A = the selected value
  ret

; Store A into address B.  Clobbers E-J.
STORE .align
  swap A, E   ; Save A into E so we can use A for indexacc
  indexacc    ; A = accumulator# with address B
  loadacc A   ; LS = accumulator[A]
  swapall     ; stash RF (in the process, setting G=B, J=E)
  indexswap   ; swap RF[G%5] with RF[0]
  mov A, J    ; RF[0] = the value to store
  indexswap   ; swap stored value back into place
  swapall     ; restore RF and put new memory in LS
              ; A is still the accumulator with address B
  storeacc A  ; accumulator[A] = LS
  swap A, E   ; get stored value back from E
  ret
