; Simulates Conway's game of life
  .isa v4
  .org 100

; The current and next state of an 8x8 grid are stored in words 0-63.
; One digit of each word has the current state (0=dead or 1=alive), and the
; other digit has the next state for the cell in word 8*y+x - which digit
; is selected by the current generation# in E.  Initially, E=0 and the ones
; digit has the current state.

; Read initial state from cards
init
  read            ; read F=position G=value
  swapall         ;
  jil gen         ; illegal position (e.g. 99) signals done
  jsr index       ; get B=address, A=value
  mov A,[B]       ; set initial value for cell 
  jmp init

; Simulate one generation
gen
  ; Print the current state
  clr A
  swap A,C        ; C=counter from 11 to 88
pr_next_row
  swap C,A
  swapdig A       ; rc -> cr
  lodig A         ; isolate 0r
  inc A           ; inc row
  swapdig A       ; A=r0
  inc A           ; A=r1
  jil pr_done     ; if row==9, printing done
  dec A           ; A=r0
  swap A,C        ;
pr_next_col
  swap C,A
  inc A           ; next col
  mov A,C         ;
  jil pr_next_row ; if col==9, go to next row

  jsr index       ; B=address for position
  jsr get_cell    ; A=cell value
  jz pr_next_col  ; if empty, don't print
  swap A,B        ; B=cell value
  mov C,A         ; A=position
  print
  jmp pr_next_col
pr_done    
  clr A
  swap A,B        ; B=0
  mov 99,A        ; A=99
  print           ; print 9900 to signal end of grid 

  ; Compute the next generation
  clr A
  swap A,C        ; C=counter from 11 to 88
next_row
  swap C,A
  swapdig A       ; rc -> cr
  lodig A         ; isolate 0r
  inc A           ; inc row
  swapdig A       ; A=r0
  inc A           ; A=r1
  jil gen_done    ; if row==9, generation done
  dec A           ; A=r0
  swap A,C        ;
next_col
  swap C,A
  inc A           ; next col
  mov A,C         ;
  jil next_row    ; if col==9, go to next row

  ; Update cell at position C

  ; Count live neighbors
  ; It would be much more efficient for code space to iterate over a table
  ; of deltas, but doing so would take more table space and would probably
  ; require register spills.
  clr A
  swap A,D        ; D=0 counts active neighbors
;count_nw
  mov C,A         ;
  dec A           ; A=(r, c-1)
  swapdig A       ; A=(c-1, r)
  dec A           ; A=(c-1, r-1)
  swapdig A       ; A=(r-1, c-1)
  jil count_n     ; skip if out-of-bounds
  jsr index       ; B=address for (r-1,c-1)
  jsr get_cell    ; A=value
  jz count_n      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_n
  mov C,A         ;
  swapdig A       ; A=(c, r)
  dec A           ; A=(c, r-1)
  swapdig A       ; A=(r-1, c)
  jil count_ne    ; skip if out-of-bounds
  jsr index       ; B=address for (r-1,c)
  jsr get_cell    ; A=value
  jz count_ne     ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_ne
  mov C,A         ;
  inc A           ; A=(r, c+1)
  swapdig A       ; A=(c+1, r)
  dec A           ; A=(c+1, r-1)
  swapdig A       ; A=(r-1, c+1)
  jil count_w     ; skip if out-of-bounds
  jsr index       ; B=address for (r-1,c+1)
  jsr get_cell    ; A=value
  jz count_w      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_w
  mov C,A         ;
  dec A           ; A=(r, c-1)
  jil count_e     ; skip if out-of-bounds
  jsr index       ; B=address for (r, c-1)
  jsr get_cell    ; A=value
  jz count_e      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_e
  mov C,A         ;
  inc A           ; A=(r, c+1)
  jil count_sw    ; skip if out-of-bounds
  jsr index       ; B=address for (r, c+1)
  jsr get_cell    ; A=value
  jz count_sw     ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_sw
  mov C,A         ;
  dec A           ; A=(r, c-1)
  swapdig A       ; A=(c-1, r)
  inc A           ; A=(c-1, r+1)
  swapdig A       ; A=(r+1, c-1)
  jil count_s     ; skip if out-of-bounds
  jsr index       ; B=address for (r+1, c-1)
  jsr get_cell    ; A=value
  jz count_s      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_s
  mov C,A         ;
  swapdig A       ; A=(c, r)
  inc A           ; A=(c, r+1)
  swapdig A       ; A=(r+1, c)
  jil count_se    ; skip if out-of-bounds
  jsr index       ; B=address for (r+1, c)
  jsr get_cell    ; A=value
  jz count_se     ;
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_se
  mov C,A         ;
  inc A           ; A=(r, c+1)
  swapdig A       ; A=(c+1, r)
  inc A           ; A=(c+1, r+1)
  swapdig A       ; A=(r+1, c+1)
  jil rules       ; skip if out-of-bounds
  jsr index       ; B=address for (r+1, c+1)
  jsr get_cell    ; A=value
  jz rules        ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

  ; Apply rules for life
rules
  mov C,A
  jsr index       ; B=address for cur cel
  jsr get_cell    ; A=cur value
  jz cur_dead
;cur_alive        ; cell is currently alive
  swap D,A
  dec A
  dec A
  jz live         ; 2 live neighbors -> live
  dec A
  jz live         ; 3 live neighbors -> live
  jmp dead        ; else -> dead
cur_dead          ; cell is currently dead
  swap D,A
  dec A
  dec A
  dec A
  jz live         ; 3 live neighbors -> live
  jmp dead        ; else -> dead

live
  mov 10,A
  jsr set_cell    ; cell becomes alive
  jmp next_col
dead
  clr A
  jsr set_cell    ; cell becomes dead
  jmp next_col

  ; Toggle generation flag
gen_done
toggle .table 1,0
  swap E,A        ; generation (0 or 1) in A
  add toggle,A
  ftl A           ; lookup next generation in A
  swap A,E        ; set next generation
  jmp gen


; Returns B=address for cell with index A
; offset table maps positions 11..88 to address
; NOTE relying on .table allocating this contiguously
; TODO support arithmetic on "offset" instead using a padding row
offset  .table 0, 0, 0, 0, 0, 0, 0, 0, 0,0
offset1 .table 0, 0, 1, 2, 3, 4, 5, 6, 7,0
offset2 .table 0, 8, 9,10,11,12,13,14,15,0
offset3 .table 0,16,17,18,19,20,21,22,23,0
offset4 .table 0,24,25,26,27,28,29,30,31,0
offset5 .table 0,32,33,34,35,36,37,38,39,0
offset6 .table 0,40,41,42,43,44,45,46,47,0
offset7 .table 0,48,49,50,51,52,53,54,55,0
offset8 .table 0,56,57,58,59,60,61,62,63
index
  add offset,A
  ftl A
  swap A,B
  ret

; Returns A=current value of cell at address B
get_cell
  mov [B],A       ; read cell value
  swap E,A        ; A=generation
  jz get_cell_low ; if generation==0, low digit has cur state
  swap A,E        ; reset E=generation
  swapdig A       ; high digit has cur state 
  jmp get_cell_out
get_cell_low
  swap A,E        ; reset E=generation
get_cell_out
  lodig A         ; get cur state
  ret

; Sets the next value of cell at address B to A
; (A=10 means the cell should turn on)
set_cell
  swap A,D        ; D=next value (in high digit)

  ;jsr get_cell    ; A=current value (in low digit)
    mov [B],A       ; read cell value
    swap E,A        ; A=generation
    jz sgt_cell_low ; if generation==0, low digit has cur state
    swap A,E        ; reset E=generation
    swapdig A       ; high digit has cur state 
    jmp sgt_cell_out
sgt_cell_low
    swap A,E        ; reset E=generation
sgt_cell_out
    lodig A         ; get cur state

  add D,A         ; add in next value
  swap E,A        ; A=generation
  jz set_cell_hi  ; if generation==0, high digit has next state
  swap A,E        ; reset E=generation
  swapdig A       ; low digit has next state
  jmp set_cell_out
set_cell_hi
  swap E,A        ; reset E=generation
set_cell_out
  mov A,[B]       ; set current+next state
  ret