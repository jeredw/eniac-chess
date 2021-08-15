; Simulates Conway's game of life
  .isa v4
  .org 100

; The current state of an 8x8 grid is stored digit packed in words 0-31
; (accs 0-6) and the next state in words 35-66 (accs 7-13).
next_grid .equ 35

; Read initial state from cards
init
  read            ; read F=position G=value
  swapall         ;
  jil init_done   ; illegal position (e.g. 99) signals done
  swap B,A        ; 
  swap A,D        ; D=value
  swap A,B        ; A=position
  jsr set_cell
  jmp init

init_done
  jsr copy_grid

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
  jsr get_cell    ; A=value
  jz count_w      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_w
  mov C,A         ;
  dec A           ; A=(r, c-1)
  jil count_e     ; skip if out-of-bounds
  jsr get_cell    ; A=value
  jz count_e      ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

count_e
  mov C,A         ;
  inc A           ; A=(r, c+1)
  jil count_sw    ; skip if out-of-bounds
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
  jsr get_cell    ; A=value
  jz rules        ; 
  swap D,A        ;
  inc A           ; neighbor count++
  swap A,D        ;

  ; Apply rules for life
rules
  mov C,A
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
  mov 1,A<->D
  mov C,A
  jsr set_cell    ; cell becomes alive
  jmp next_col
dead
  clr A
  swap A,D
  mov C,A
  jsr set_cell    ; cell becomes dead
  jmp next_col

  ; Copy new grid over old grid
gen_done
  jsr copy_grid
  jmp gen


; Returns A=current value of cell at position A
; offset table maps positions 11..88 to address
; NOTE relying on .table allocating this contiguously
; TODO support arithmetic on "offset" instead using a padding row
offset  .table 0,  0,00,  0, 0,  0, 0,  0, 0,0
offset1 .table 0,M00,00,M01,01,M02,02,M03,03,0
offset2 .table 0,M04,04,M05,05,M06,06,M07,07,0
offset3 .table 0,M08,08,M09,09,M10,10,M11,11,0
offset4 .table 0,M12,12,M13,13,M14,14,M15,15,0
offset5 .table 0,M16,16,M17,17,M18,18,M19,19,0
offset6 .table 0,M20,20,M21,21,M22,22,M23,23,0
offset7 .table 0,M24,24,M25,25,M26,26,M27,27,0
offset8 .table 0,M28,28,M29,29,M30,30,M31,31,0
get_cell
  add offset,A    ; A=offset+position
  ftl A           ; lookup address
  jn get_cell_hi  ; if M use high digit
  swap A,B
  mov [B],A       ; get cell value
  lodig A         ; extract low digit
  ret
get_cell_hi       ; 
  swap A,B
  mov [B],A       ; get cell value
  swapdig A       ;
  lodig A         ; get high digit
  ret

; Sets the next value of cell at position A to D
set_cell
  add offset,A    ; A=offset+position
  ftl A           ; lookup address
  jn set_cell_hi  ; if M use high digit
  ; Update low digit
  add next_grid,A ; point into next_grid
  swap A,B
  mov [B],A       ; get cell value
  swapdig A       ; hl -> lh
  lodig A         ; 0h
  swapdig A       ; 0h -> h0
  add D,A         ; hD
  mov A,[B]       ; update cell value
  ret
  ; Update hi digit
set_cell_hi
  flipn           ; clear sign of offset
  add next_grid,A ; point into next_grid
  swap A,B
  mov [B],A       ; get cell value
  lodig A         ; 0l
  swapdig A       ; l0
  add D,A         ; lD
  swapdig A       ; Dl
  mov A,[B]       ; update cell value
  ret

; copy new grid state over old grid state
copy_grid
  mov 7,A
  loadacc A 
  clr A
  storeacc A
  mov 8,A
  loadacc A 
  mov 1,A
  storeacc A
  mov 9,A
  loadacc A 
  mov 2,A
  storeacc A
  mov 10,A
  loadacc A 
  mov 3,A
  storeacc A
  mov 11,A
  loadacc A 
  mov 4,A
  storeacc A
  mov 12,A
  loadacc A 
  mov 5,A
  storeacc A
  mov 13,A
  loadacc A 
  mov 6,A
  storeacc A
  ret