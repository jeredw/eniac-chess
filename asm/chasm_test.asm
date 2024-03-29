; this is a comment
; directives are indented and start with a period
  .isa v4  ; select isa version before any instructions
  .org 100 ; select function table and row number
           ;   hundreds digit is function table [123]
           ;   tens/units digit is row within table
  .org 00  ; set row within current function table
  .align   ; pad to start of row if not already aligned
  .dw 10, 20, 30   ; output these raw values here

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
labeled_instr clrall
; data tables can be declared in ft3 using .table
; the first word after .table is the base row address for the table (8-99)
; following words are data values for that and subsequent rows of the table
noms    .table 1, 2, 3
nomnoms .table 4, 5, 6, -42, M03
  .include chasm_test2.asm

test_each_instruction
  ; instructions must be indented
  clrall
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
  mov J, A<->B ; psuedo op
  mov A, B    ; pseudo op
  mov A, C    ; pseudo op
  mov A, D    ; pseudo op
  mov A, E    ; pseudo op
  mov 10, A
  mov king, A
  mov king+2, A ; can do basic arithmetic
  mov king-2, A ;
  mov 10, A<->B ; psuedo op
  mov [B], A
  mov [B], A<->C ; psuedo op
  mov A, [B]
  inc A
  dec A
  flipn
  add D, A
  add 42, A
  addn 42, A
  sub D, A
  jmp target
  jmp far faraway
  jn target
  jz target
  jil target
  jsr faraway
  ret
  clr A
  read
  print
  brk
  halt

  ; test that multiword instructions are forced into a single row
  .align
  clrall
  clrall
  clrall
  clrall
  clrall
  mov 99, A

  .align
  clrall
  clrall
  clrall
  clrall
  clrall
  jmp 99

  .align
  clrall
  clrall
  clrall
  clrall
  jmp far 399

  .align
  clrall
  clrall
  clrall
  jmp far 399

  .align
  clrall
  clrall
  clrall
  clrall
  jmp far 399

  .align
  clrall
  clrall
  clrall
  clrall
  jsr 399

  .align
  clrall
  clrall
  clrall
  jsr 399

  .align
  clrall
  clrall
  clrall
  clrall
  jsr 399

  .align
  clrall
  clrall
  clrall
  clrall
  clrall
  jn  99

  .align
  clrall
  clrall
  clrall
  clrall
  clrall
  jz  99

  .align
  clrall
  clrall
  clrall
  clrall
  clrall
  jil 99

  .align
  clrall
force
.foo
  jmp .foo
foo
.foo
  jmp .foo

target .org 99
faraway .org 300
  .org 399
  inc A
  clrall
  clrall
  clrall
  clrall
