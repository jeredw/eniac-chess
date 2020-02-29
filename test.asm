; this is a comment
; directives are indented and start with a period
  .isa v3  ; select isa version before any instructions
  .org 100 ; select function table and row number
           ;   hundreds digit is function table [123]
           ;   tens/units digit is row within table
  .org 00  ; set row within current function table
  .align   ; pad to start of row if not already aligned
                                                           ; expected output
                                                           ; 100: 000000302090
  .dw -10, 20, 30  ; output these raw values here
                   ; values may be between -50 and 99

; label definitions start in column zero
; a label defined with .align is the row number after alignment
label .align
; a label defined with .equ is a constant
constant .equ 10
; .equ can reference previously defined labels
flub .equ constant
; .equ can't reference labels defined later in source text
; err .equ target  ; illegal
                                                           ; 101: 000000004210
; constants can be used in .dw lists
  .dw constant, 42
; only single word constants are supported
;constant2 .equ 999
; can't redefine labels
;constant .equ 11  ; illegal
; can't label instructions
;label nop  ; illegal because too error prone

  ; instructions must be indented
  ; test each instruction
  .align
                                                           ; 102: 050403020100
  nop
  swapacc 0
  swapacc 1
  swapacc 2
  swapacc 3
  swapacc 4
                                                           ; 103: 151413121110
  swapacc 5
  swapacc 6
  swapacc 7
  swapacc 8
  swapacc 9
  swapacc 10
                                                           ; 104: 252423222120
  swapacc 11
  swapacc 12
  swapacc 13
  swapacc 14
  swapacc 15
  ftl        ; ABCDE = ft3[A], for initial board load
                                                           ; 105: 103201323130
  indexjmp1  ; T = 2*J2 + J1>4; jmp +T
  indexjmp2  ; T = J1%5; jmp +T
  mov A, [label]
; mov A, [XX] ; mov J,XX; jsr LOAD
; mov from different function table is illegal
;  mov A, [300]
  mov A, [10]
                                                           ; 106: 103542353433
  mov A, [B]  ; mov J,B; jsr LOAD
  mov [B], A  ; mov J,B; jsr STORE
  mov A, 42
  mov A, constant
                                                           ; 107: 004443424140
  mov A, B
  mov A, C
  mov A, D
  mov A, E
  mov Z, A
  nop
                                                           ; 108: 007052515045
  swap B, A
  swap C, A
  swap D, A
  swap E, A
  swap Z, A
  nop
                                                           ; 109: 007052515045
  swap A, B
  swap A, C
  swap A, D
  swap A, E
  swap A, Z
  nop
                                                           ; 110: 000099737271
  inc A
  inc B
  jmp target  ; within current function table
  nop
  nop
                                                           ; 111: 998075030074
  ; must use "far" for far targets
  jmp far faraway ; to any function table
  jmp +A
  jn target      ; all conditionals within current function table only
                                                           ; 112: 000099829981
  jz target
  loop target    ; dec C; if C!=0 jmp XX
  nop
  nop
                                                           ; 113: 008584030083
  jsr faraway
  ret
  add A, D
  nop
                                                           ; 114: 959493929190
  sub A, D    ; aka compare
  neg A
  clr A
  read AB
  print AB
  halt

  ; test that multiword instructions are forced into a single row
  .align                                                   ; 115: 000000000000
  nop
  nop
  nop
  nop
  nop
  mov A, [99]                                              ; 116: 000000009932

  .align                                                   ; 117: 000000000000
  nop
  nop
  nop
  nop
  nop
  mov A, 99                                                ; 118: 000000009935

  .align                                                   ; 119: 000000000000
  nop
  nop
  nop
  nop
  nop
  jmp 99                                                   ; 120: 000000009973

  .align                                                   ; 121: 000000000000
  nop
  nop
  nop
  nop
  jmp far 399                                              ; 122: 000000039974

  .align                                                   ; 123: 039974000000
  nop
  nop
  nop
  jmp far 399

  .align                                                   ; 124: 000000000000
  nop
  nop
  nop
  nop
  jmp far 399                                              ; 125: 000000039974

  .align                                                   ; 126: 000000000000
  nop
  nop
  nop
  nop
  jsr 399                                                  ; 127: 000000039983

  .align                                                   ; 128: 039983000000
  nop
  nop
  nop
  jsr 399

  .align                                                   ; 129: 000000000000
  nop
  nop
  nop
  nop
  jsr 399                                                  ; 130: 000000039983

  .align                                                   ; 131: 000000000000
  nop
  nop
  nop
  nop
  nop
  jn  99                                                   ; 132: 000000009980

  .align                                                   ; 133: 000000000000
  nop
  nop
  nop
  nop
  nop
  jz  99                                                   ; 134: 000000009981

  .align                                                   ; 135: 000000000000
  nop
  nop
  nop
  nop
  nop
  loop  99                                                 ; 136: 000000009982

target .org 99
faraway .org 300
  .org 399
  nop
  nop
  nop
  nop
  nop
  nop
;  nop
