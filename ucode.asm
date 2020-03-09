; Microcode for fundamental VM operations.
  .isa v3

; Swap [B] and A.
; B contains an address in 0..74
; Preserves B-E.
MSWAP .org 300
  ; Swap the RF accumulator with the load/store accumulator.
  swapacc 15              ;    RF:ABCDE/LS:xxxxx/M:43210
                          ; -> RF:xxxxx/LS:ABCDE/M:43210
  
  ; Read [B] into the RF and clobber [B].
  indexjmp1               ;    RF:xxxxx/LS:ABCDE/M:43210
                          ; -> RF:43210/LS:ABCDE/M:xxxxx
  .align
  swapacc 0
  jmp     MSWAP_insert
  .align
  swapacc 1
  jmp     MSWAP_insert
  .align
  swapacc 2
  jmp     MSWAP_insert
  .align
  swapacc 3
  jmp     MSWAP_insert
  .align
  swapacc 4
  jmp     MSWAP_insert
  .align
  swapacc 5
  jmp     MSWAP_insert
  .align
  swapacc 6
  jmp     MSWAP_insert
  .align
  swapacc 7
  jmp     MSWAP_insert
  .align
  swapacc 8
  jmp     MSWAP_insert
  .align
  swapacc 9
  jmp     MSWAP_insert
  .align
  swapacc 10
  jmp     MSWAP_insert
  .align
  swapacc 11
  jmp     MSWAP_insert
  .align
  swapacc 12
  jmp     MSWAP_insert
  .align
  swapacc 13
  jmp     MSWAP_insert
  .align
  swapacc 14
  jmp     MSWAP_insert

MSWAP_insert .align
  ; Set desired word of RF to Z, and then restore it and memory.
  indexjmp2               ;    RF:43210/LS:ABCDE/M:xxxxx
                          ; -> RF:4Z210/LS:3BCDE/M:xxxxx
  .align
  swap A, Z
  jmp  MSWAP_restore
  .align
  swap A, B
  swap A, Z
  swap A, B
  jmp  MSWAP_restore
  .align
  swap A, C
  swap A, Z
  swap A, C
  jmp  MSWAP_restore
  .align
  swap A, D
  swap A, Z
  swap A, D
  jmp  MSWAP_restore
  .align
  swap A, E
  swap A, Z
  swap A, E
  jmp  MSWAP_restore

MSWAP_restore .align
  ; Unclobber memory by swapping back RF.
  indexjmp1            ;    RF:4Z210/LS:3BCDE/M:xxxxx
                       ; -> RF:xxxxx/LS:3BCDE/M:4Z210
  .align
  swapacc 0
  jmp     MSWAP_finish
  .align
  swapacc 1
  jmp     MSWAP_finish
  .align
  swapacc 2
  jmp     MSWAP_finish
  .align
  swapacc 3
  jmp     MSWAP_finish
  .align
  swapacc 4
  jmp     MSWAP_finish
  .align
  swapacc 5
  jmp     MSWAP_finish
  .align
  swapacc 6
  jmp     MSWAP_finish
  .align
  swapacc 7
  jmp     MSWAP_finish
  .align
  swapacc 8
  jmp     MSWAP_finish
  .align
  swapacc 9
  jmp     MSWAP_finish
  .align
  swapacc 10
  jmp     MSWAP_finish
  .align
  swapacc 11
  jmp     MSWAP_finish
  .align
  swapacc 12
  jmp     MSWAP_finish
  .align
  swapacc 13
  jmp     MSWAP_finish
  .align
  swapacc 14
  jmp     MSWAP_finish

MSWAP_finish .align
  ; Restore the original RF, updating A from Z.
  swapacc 15           ;    RF:xxxxx/LS:3BCDE/M:4Z210
                       ; -> RF:3BCDE/LS:xxxxx/M:4Z210
  ret
