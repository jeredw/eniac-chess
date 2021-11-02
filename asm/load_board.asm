; LOAD_BOARD.ASM

; Read initial memory state, one word per card.
; Each card is AADD = address, data
; Card with address=99 to end
; Near jump to "start" on exit
init_memory
  read
  swapall
  inc A
  jn start
  dec A
  swap A,B
  mov A,[B]
  jmp init_memory
