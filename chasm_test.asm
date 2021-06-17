; this is a comment
; directives are indented and start with a period
  .isa v4  ; select isa version before any instructions
  .org 100 ; select function table and row number
           ;   hundreds digit is function table [123]
           ;   tens/units digit is row within table
  .org 00  ; set row within current function table
  .align   ; pad to start of row if not already aligned
  .dw -10, 20, 30  ; output these raw values here
                   ; values may be between -50 and 99

; label definitions start in column zero
; a label defined with .align is the row number after alignment
label .align
; ditto labels without a directive - these also force alignment
implicitly_aligned
; a label defined with .equ is a constant
king .equ 10
; .equ can reference previously defined labels
flub .equ king
; .equ can't reference labels defined later in source text
; err .equ target  ; illegal
; constants can be used in .dw lists
  .dw king, 42
; only single word constants are supported
;constant2 .equ 999
; can't redefine labels
;constant .equ 11  ; illegal
; instructions can have labels too
labeled_instr nop

test_each_instruction
  ; instructions must be indented
  nop
  swap A, B
  swap A, C
  swap A, D
  swap A, E
  swap A, F
  swap B, A
  swap C, A
  swap D, A
  swap E, A
  swap F, A
  loadacc A
  storeacc A
  swapall
  scanall
  ftload A
  ftlookup A, 10
  ftlookup A, king
  mov A, B
  mov A, C
  mov A, D
  mov A, E
  mov A, F
  mov A, G
  mov A, H
  mov A, I
  mov A, J
  indexswap
  clr A
  mov A, 10
  mov A, king
  mov D, 10
  mov D, king
  mov A, [king]
  mov A, [10]
  mov A, [B]
  mov [king], A
  mov [10], A
  ;mov [B], A
  inc A
  inc B
  dec A
  add A, D
  neg A
  sub A, D
  jmp target
  jmp far faraway
  jmp +A
  jn target
  jz target
  jil target
  loop target
  jsr faraway
  ret
  ;jnz target
  read AB
  print AB
  nextline
  halt

  ; test that multiword instructions are forced into a single row
  .align
  nop
  nop
  nop
  nop
  nop
  mov A, [10]

  .align
  nop
  nop
  nop
  nop
  nop
  mov A, 99

  .align
  nop
  nop
  nop
  nop
  nop
  jmp 99

  .align
  nop
  nop
  nop
  nop
  jmp far 399

  .align
  nop
  nop
  nop
  jmp far 399

  .align
  nop
  nop
  nop
  nop
  jmp far 399

  .align
  nop
  nop
  nop
  nop
  jsr 399

  .align
  nop
  nop
  nop
  jsr 399

  .align
  nop
  nop
  nop
  nop
  jsr 399

  .align
  nop
  nop
  nop
  nop
  nop
  jn  99

  .align
  nop
  nop
  nop
  nop
  nop
  jz  99

  .align
  nop
  nop
  nop
  nop
  nop
  loop  99

  .align
  nop
force
  jmp force

target .org 99
faraway .org 300
  .org 399
  inc A
  nop
  nop
  nop
  nop
  nop
