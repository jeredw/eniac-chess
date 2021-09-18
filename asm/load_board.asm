; Read initial memory state. Each card is AADD = address, data
; address 99 to end
loadlp
  read
  swapall
  inc A
  jn start
  dec A
  swap A,B
  mov A,[B]
  jmp loadlp
