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
; data tables can be declared in ft3 using .table
; the first word after .table is the base row address for the table (8-99)
; following words are data values for that and subsequent rows of the table
  .table 8,  1, 2, 3
  .table 12, 4, 5, 6

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
  ftl A
  mov B, A
  mov C, A
  mov D, A
  mov E, A
  mov F, A
  mov G, A
  mov H, A
  mov I, A
  mov J, A
  mov A, B    ; pseudo op
  mov A, C    ; pseudo op
  mov A, D    ; pseudo op
  mov A, E    ; pseudo op
  clr A
  mov 10, A
  mov king, A
  mov 10, D
  mov king, D
  mov [king], A
  mov [10], A
  mov [B], A
  mov [king], A
  mov [10], A
  mov A, [B]
  inc A
  inc B
  dec A
  add D, A
  add 42, A
  sub D, A
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
  read
  print
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
  mov 99, A

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
