; Read initial memory state. Each card is AADD = address, data
; address 99 to end
init_memory
  read
  swapall
  inc A
  jn start
  dec A
  swap A,B
  mov A,[B]
  jmp init_memory
