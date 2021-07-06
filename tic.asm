; eniac-tac-toe: tic tac toe search program for ENIAC chess vm
; The board is stored in A,B,C in accs 0,1,2, indexed as
;  123
;  456
;  789
; where each position contains 0=open, 1=X, or 2=O
; Remaining accumulators (3+) are used to keep a software
; stack for minimax search. Each entry has format
;  F=player G=last_move H=best_score I=best_move
; player: 1=X, 2=O
; last_move: 1-9=last move tried, 0=none
; best_score: 49=lose, 50=draw, 51=win
;             values 48 and 52 used as min/max inits for minimax
; best_move: 1-9=square w best value, 0=none
; The stack pointer, abbreviated SP, is kept in E.
  .isa v4
  .org 100

  ; Slightly faster initial game state for testing...
  mov 2,A
  swap A,B ; B=play O
  mov 2,A  ; A=top middle
  jsr move
  mov 1,A
  swap A,B ; B=play X
  mov 9,A  ; A=bottom right
  jsr move

  ; eniac goes first and always plays X in the center
  ; (avoiding a really long search of the entire game)
  mov 1,A
  swap A,B  ; B=play X
  mov 5,A   ; A=center square
  jsr move
  jsr printb

game
  read            ; human plays next; read move into LS
  mov 2,A         ;
  swap A,B        ; B=play O
  mov F,A         ; A=where to play
  jsr move
  jsr printb

  jsr isooo
  jz end_owins    ; if O wins, exit
  jsr isfull
  jz setup_search ; A=0 means still free squares
  jmp end_draw    ; if draw, exit

setup_search
  ; set up the initial search stack frame
  clr A
  swap A,D      ; DI=best_move=none
  mov 48,A
  swap A,C      ; CH=best_score=48
  clr A
  swap A,B      ; BG=last_move=none
  mov 1,A       ; AF=player=X
  swapall       ;
  mov 3,A       ; write to top of stack
  storeacc A    ;
  inc A         ; SP=4 (i.e. one entry, this one)

search
  dec A         ; compare SP with 3
  dec A
  dec A
  jn bug        ; stack underflow
  jz search_out ; if empty (i.e. 3), done
  inc A         ; inc SP to net -1
  inc A
  mov A,E       ; E=SP
  ; load search state from stack
  loadacc A     ; F=player, G=last_move, H=best_score, I=best_move

  ; check if last_move is none (i.e. 0)
  ; this signals the start of a search at new depth
  mov G,A       ; A=last_move
  jz new_depth  ; if last_move is 0, new recursive search
cur_depth
  ; iterating over possible moves at current depth
  ; clear out the square for last trial move
  clr A
  swap A,B      ; B=0
  mov G,A       ; A=last_move index
  jsr move      ; erase last trial move

  mov E,A       ; A=SP
  loadacc A     ; reload frame
  mov F,A       ; get player (1=X, 2=O)
  dec A
  jz cd_x       ; if X then max player, else min player
cd_o
  mov H,A       ; D=best_score
  swap A,D      ;
  mov E,A       ; A=SP
  inc A
  loadacc A     ; sp+1th stack frame
  mov H,A       ; value = best score from last stack frame
  sub D,A       ; A = value - best_score
  jn better     ; best_score > value (better for min)
  jmp nextmove
cd_x
  mov H,A       ; D=best_score
  swap A,D      ;
  mov E,A       ; A=SP
  inc A
  loadacc A     ; sp+1th stack frame
  mov H,A       ; value = best score from last stack frame
  sub D,A       ; A = value - best_score
  jn nextmove   ; best_score > value
  jz nextmove   ; best_score == value
  ; best_score < value (fall through to better)

; better means the most recent recursive search had a better
; best_move than the current one, so we need to replace it
; LS has the most recent recursive stack frame
; on exit LS has the current stack frame again
better
  mov H,A       ; new best score
  swap A,C      ; C=value (i.e. better score)
  mov E,A       ; A=SP
  loadacc A     ; reload current frame
  mov G,A       ; D=last_move
  swap A,D      ;
  swapall
  swap A,C      ; best_score = value
  mov H,A       ; 
  swap A,C      ;
  swap A,D      ; best_move = last_move
  mov I,A       ;
  swap A,D      ;
  swapall
  mov E,A       ; A=SP
  storeacc A    ; update stack frame

nextmove
  mov E,A
  loadacc A     ; reload stack frame
  mov G,A       ; last_move
  dec A         ; advance to next move
  jmp checkmove

new_depth
  ; begin search at new depth
  jsr isxxx     ; A=0 if xxx (clobbers LS)
  jz xwin
  jsr isooo     ; A=0 if ooo (clobbers LS)
  jz owin
  jsr isfull    ; A=0 means still free squares
  jz initmove

draw
  swap A,E      ; get sp
  loadacc A     ; get cur stack frame
  swapall
  swap A,C      ; put draw score = 50 into best_score
  mov 50,A      ;
  swap A,C      ;
  swapall
  storeacc A    ; update stack
  jmp search
xwin
  swap A,E      ; get sp
  loadacc A     ; get cur stack frame
  swapall
  swap A,C      ; put win score = 51 into best_score
  mov 51,A      ;
  swap A,C      ;
  swapall
  storeacc A    ; update stack
  jmp search
owin
  swap A,E      ; get sp
  loadacc A     ; get cur stack frame
  swapall
  swap A,C      ; put win score = 49 into best_score
  mov 49,A      ;
  swap A,C      ;
  swapall
  storeacc A    ; update stack
  jmp search

initmove
  mov 9,A       ; start search from square 9

; on entry to checkmove, A is the square we want to search
checkmove
  jz asearch    ; if A is 0 no more moves at this depth
  mov A,D       ; stash A since peek destroys it
  jsr peek
  jz domove     ; if square is empty do it
  swap A,D      ; get stashed move #
  dec A         ; try previous square
  jmp checkmove
asearch
  swap A,E
  jmp search

; D has the square to move to
domove
  mov E,A
  loadacc A     ; restore stack frame
  mov F,A       ; B=player
  swap A,B      ; 
  mov D,A       ; A=square
  jsr move      ; mark square for player

  ; push a new stack entry to remember iteration state
  mov E,A       ; A=SP
  loadacc A     ; load current stack frame (already has best* updated)
  swapall
  swap A,B
  mov I,A       ; update B=last_move (still saved in D/I)
  swap A,B
  swapall
  storeacc A    ; push new entry
  inc A         ; increment SP
  mov A,E       ; save sp+1 in E

  mov F,A       ; test player#
  dec A
  jz newo       ; if player is X, create new O frame
newx
  ; set up new frame for X
  clr A         ; best_move D=none
  swap A,D
  mov 48,A      ; best_score C=48
  swap A,C
  clr A         ; last_move B=none
  swap A,B
  mov 1,A       ; player A=1
  swapall       ; 
  mov J,A       ; A=SP
  storeacc A
  inc A         ; push
  jmp search
newo
  ; set up new frame for O
  clr A         ; best_move D=none
  swap A,D
  mov 52,A      ; best_score C=52
  swap A,C
  clr A         ; last_move B=none
  swap A,B
  mov 2,A       ; player A=2
  swapall       ; 
  mov J,A       ; A=SP
  storeacc A
  inc A         ; push
  jmp search

search_out
  ; place an X at the final best move position
  mov 3,A
  loadacc A
  mov 1,A
  swap A,B  ; B=play X
  mov I,A   ; A=best_move
  jsr move
  jsr printb

  jsr isxxx
  jz end_xwins ; if X wins, exit
  jsr isfull
  jz game      ; A=0 means still free squares
  jmp end_draw

; stack underflow
bug
  mov 99,A
  mov A,B
  print 
  print 
  print 
  halt

; reached when the ending is a draw
end_draw
  mov 0,A
  mov A,B
  print 
  print 
  print 
  halt

; reached when the ending is a win for X
end_xwins
  mov 11,A
  mov A,B
  print 
  print 
  print 
  halt

; reached when the ending is a win for O
end_owins:
  mov 22,A
  mov A,B
  print 
  print 
  print 
  halt


; print the current board state
printb
  clr A
printb_loop
  loadacc A
  swapall
  ; multiply B by 10 and add C to it
  swap A,B    ;
  mov A,D     ; A=D=B
  add D,A     ; A=B+9*B
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  swap A,C    ; 
  mov A,D     ; D=C
  swap A,C    ; get back 10*B
  add D,A     ; A=10*B+C
  swap A,B    ; now we have A=0a B=bc
  print
  swapall
  inc A
  dec A       ; -2 to test for A=2
  dec A       ; XXX sub D,A/add D,A hits an assert!
  dec A
  jz printb_out
  inc A
  inc A
  inc A
  jmp printb_loop
printb_out
  ret

  .org 200

; put a word in the board array
; A: board location (1-9)
; B: what to put there
move
  dec A
  jz move_0A
  dec A
  jz move_0B
  dec A
  jz move_0C
  dec A
  jz move_1A
  dec A
  jz move_1B
  dec A
  jz move_1C
  dec A
  jz move_2A
  dec A
  jz move_2B
move_2C
  mov 2,A
  loadacc A
  jmp move_C
move_2B
  mov 2,A
  loadacc A
  jmp move_B
move_2A
  mov 2,A
  loadacc A
  jmp move_A
move_1C
  mov 1,A
  loadacc A
  jmp move_C
move_1B
  mov 1,A
  loadacc A
  jmp move_B
move_1A
  mov 1,A
  loadacc A
  jmp move_A
move_0C
  clr A
  loadacc A
  jmp move_C
move_0B
  clr A
  loadacc A
  jmp move_B
move_0A
  clr A
  loadacc A
move_A
  swapall
  mov G,A         ; put G (i.e. B) into A position
  swapall
  storeacc A
  ret
move_B
  swapall
  swap A,B        ; put G (i.e. B) into B position
  mov G,A         ;
  swap A,B        ;
  swapall
  storeacc A
  ret
move_C
  swapall
  swap A,C        ; put G (i.e. B) into C position
  mov G,A         ;
  swap A,C        ;
  swapall
  storeacc A
  ret

; peek in board array
; A=board location (1-9)
; return board data in A
peek
  dec A
  jz peek_0A
  dec A
  jz peek_0B
  dec A
  jz peek_0C
  dec A
  jz peek_1A
  dec A
  jz peek_1B
  dec A
  jz peek_1C
  dec A
  jz peek_2A
  dec A
  jz peek_2B
peek_2C
  mov 2,A
  loadacc A
  jmp peek_C
peek_2B
  mov 2,A
  loadacc A
  jmp peek_B
peek_2A
  mov 2,A
  loadacc A
  jmp peek_A
peek_1C
  mov 1,A
  loadacc A
  jmp peek_C
peek_1B
  mov 1,A
  loadacc A
  jmp peek_B
peek_1A
  mov 1,A
  loadacc A
  jmp peek_A
peek_0C
  clr A
  loadacc A
  jmp peek_C
peek_0B
  clr A
  loadacc A
  jmp peek_B
peek_0A
  clr A
  loadacc A
peek_A
  mov F,A
  ret
peek_B
  mov G,A
  ret
peek_C
  mov H,A
  ret

  .org 310

; return A=0 if there are open squares, else nonzero
isfull
  mov 2,A
isfull_loop
  loadacc A
  swapall
  jz isfull_no    ; if A==0 return 0
  swap A,B
  jz isfull_no    ; if B==0 return 0
  swap A,C
  jz isfull_no    ; if C==0 return 0
  swapall
  dec A
  jn isfull_yes   ; if all squares occupied return P02
  jmp isfull_loop
isfull_no
  swapall
  clr A
  ret
isfull_yes
  inc A
  inc A
  ret


; return A=0 if X wins else nonzero
isxxx
; check rows for XXX
  mov 2,A
rowxxx
  loadacc A
  swapall
  dec A           ; if A=='X' goto _1
  jz rowxxx_1     ;
  jmp rowxxx_next ; return nonzero
rowxxx_1
  swap A,B
  dec A           ; if A=='X' goto _2
  jz rowxxx_2     ;
  jmp rowxxx_next ; return nonzero
rowxxx_2
  swap A,C
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
rowxxx_next
  swapall
  dec A
  jn rowxxx_out   ; all rows checked
  jmp rowxxx
rowxxx_out

; check col A for XXX
  clr A
  loadacc A       ; load row 0
  swapall
  dec A           ; if A=='X' goto _1
  jz colaxxx_1    ;
  jmp colaxxx_out ; return nonzero
colaxxx_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  dec A           ; if A=='X' goto _2
  jz colaxxx_2    ;
  jmp colaxxx_out ; return nonzero
colaxxx_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
colaxxx_out
  swapall

; check col B for XXX
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,B
  dec A           ; if A=='X' goto _1
  jz colbxxx_1    ;
  jmp colbxxx_out ; return nonzero
colbxxx_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='X' goto _2
  jz colbxxx_2    ;
  jmp colbxxx_out ; return nonzero
colbxxx_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,B
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
colbxxx_out
  swapall

; check col C for xxx
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,B
  dec A           ; if A=='X' goto _1
  jz colcxxx_1    ;
  jmp colcxxx_out ; return nonzero
colcxxx_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,C
  dec A           ; if A=='X' goto _2
  jz colcxxx_2    ;
  jmp colcxxx_out ; return nonzero
colcxxx_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,C
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
colcxxx_out
  swapall

; check \ diagonal for xxx
  clr A
  loadacc A       ; load row 0
  swapall
  dec A           ; if A=='X' goto _1
  jz diag0xxx_1    ;
  jmp diag0xxx_out ; return nonzero
diag0xxx_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='X' goto _2
  jz diag0xxx_2    ;
  jmp diag0xxx_out ; return nonzero
diag0xxx_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,C
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
diag0xxx_out
  swapall

; check / diagonal for xxx
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,C
  dec A           ; if A=='X' goto _1
  jz diag1xxx_1   ;
  swapall
  clr A
  inc A
  ret             ; return nonzero
diag1xxx_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='X' goto _2
  jz diag1xxx_2   ;
  swapall
  clr A
  inc A
  ret             ; return nonzero
diag1xxx_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  dec A           ; if A=='X' return 0
  jz isxxx_out_yes
  swapall
  clr A
  inc A
  ret
isxxx_out_yes
  swapall
  clr A
  ret


; return A=0 if O wins else nonzero
isooo
; check rows for ooo
  mov 2,A
rowooo
  loadacc A
  swapall
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz rowooo_1     ;
  jmp rowooo_next ; return nonzero
rowooo_1
  swap A,B
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz rowooo_2     ;
  jmp rowooo_next ; return nonzero
rowooo_2
  swap A,C
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
rowooo_next
  swapall
  dec A
  jn rowooo_out   ; all rows checked
  jmp rowooo
rowooo_out

; check col A for ooo
  clr A
  loadacc A       ; load row 0
  swapall
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz colaooo_1    ;
  jmp colaooo_out ; return nonzero
colaooo_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz colaooo_2    ;
  jmp colaooo_out ; return nonzero
colaooo_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
colaooo_out
  swapall

; check col B for ooo
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,B
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz colbooo_1    ;
  jmp colbooo_out ; return nonzero
colbooo_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz colbooo_2    ;
  jmp colbooo_out ; return nonzero
colbooo_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,B
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
colbooo_out
  swapall

; check col C for ooo
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,B
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz colcooo_1    ;
  jmp colcooo_out ; return nonzero
colcooo_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,C
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz colcooo_2    ;
  jmp colcooo_out ; return nonzero
colcooo_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,C
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
colcooo_out
  swapall

; check \ diagonal for ooo
  clr A
  loadacc A       ; load row 0
  swapall
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz diag0ooo_1    ;
  jmp diag0ooo_out ; return nonzero
diag0ooo_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz diag0ooo_2    ;
  jmp diag0ooo_out ; return nonzero
diag0ooo_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  swap A,C
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
diag0ooo_out
  swapall

; check / diagonal for ooo
  clr A
  loadacc A       ; load row 0
  swapall
  swap A,C
  dec A           ; if A=='O' goto _1
  dec A           ;
  jz diag1ooo_1   ;
  swapall
  clr A
  inc A
  ret             ; return nonzero
diag1ooo_1
  swapall
  inc A
  loadacc A       ; load row 1
  swapall
  swap A,B
  dec A           ; if A=='O' goto _2
  dec A           ;
  jz diag1ooo_2   ;
  swapall
  clr A
  inc A
  ret             ; return nonzero
diag1ooo_2
  swapall
  inc A
  loadacc A       ; load row 2
  swapall
  dec A           ; if A=='O' return 0
  dec A           ;
  jz isooo_out_yes
  clr A
  inc A
  ret
isooo_out_yes
  swapall
  clr A
  ret
