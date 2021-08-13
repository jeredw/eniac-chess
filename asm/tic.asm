; eniac-tac-toe: tic tac toe search program for ENIAC chess vm
; The board is stored in accs 0 and 1, words 1-9, indexed as
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

  ; eniac goes first and always plays X in the center
  ; (avoiding a really long search of the entire game)
  mov 5,A<->B   ; B=center square
  mov 1,A       ; A=play X
  mov A,[B]
  jsr printb

game
  read          ; human plays next; read move into LS
  mov F,A<->B   ; B=where to play
  mov 2,A       ; A=play O
  mov A,[B]
  jsr printb

  mov 2,A<->D
  jsr iswin
  jz end_owins  ; if O wins, exit
  jsr isfull
  jz setup_search ; A=0 means still free squares
  jmp end_draw  ; if draw, exit

setup_search
  ; set up the initial search stack frame
  clr A
  swap A,D      ; DI=best_move=none
  mov 48,A<->C  ; CH=best_score=48
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

  ; iterating over possible moves at current depth
  ; clear out the square for last trial move
  swap A,B      ; B=last_move_index
  clr A         ; A=0
  mov A,[B]     ; erase last trial move

  mov E,A       ; A=SP
  loadacc A     ; reload frame
  mov F,A       ; get player (1=X, 2=O)
  dec A
  jz cd_x       ; if X then max player, else min player
cd_o
  mov H,A<->D   ; D=best_score
  mov E,A       ; A=SP
  inc A
  loadacc A     ; sp+1th stack frame
  mov H,A       ; value = best score from last stack frame
  sub D,A       ; A = value - best_score
  jn better     ; best_score > value (better for min)
  jmp nextmove
cd_x
  mov H,A<->D   ; D=best_score
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
  mov H,A<->C   ; C=new best score
  mov E,A       ; A=SP
  loadacc A     ; reload current frame
  mov G,A<->D   ; D=last_move
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
  mov 1,A<->D
  jsr iswin     ; A=0 if xxx (clobbers LS)
  jz xwin
  mov 2,A<->D
  jsr iswin     ; A=0 if ooo (clobbers LS)
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
  mov A,B       ; get square in B
  mov [B],A     ; lookup this square
  jz domove     ; if square is empty do it
  swap A,B      ; get stashed move #
  dec A         ; try previous square
  jmp checkmove
asearch
  swap A,E
  jmp search

; B has the square to move to
domove
  mov E,A
  loadacc A     ; restore stack frame
  mov F,A       ; A=player
  mov A,[B]     ; mark square for player

  ; push a new stack entry to remember iteration state
  mov E,A       ; A=SP
  loadacc A     ; load current stack frame (already has best* updated)
  swapall
  swap A,B
  mov G,A       ; update B=last_move (still saved in B/G)
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
  mov 48,A<->C  ; best_score C=48
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
  mov 52,A<->C  ; best_score C=52
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
  mov I,A<->B  ; B=best_move
  mov 1,A      ; A=play X
  mov A,[B]
  jsr printb

  mov 1,A<->D
  jsr iswin
  jz end_xwins  ; if X wins, exit
  jsr isfull
  jz game       ; A=0 means still free squares
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
  inc A         ; board begins at [1]
printb_loop
  swap A,B
  ; read next row into E,D,C
  mov [B],A<->E ; get r,0 into E
  swap A,B      ; inc r
  inc A
  swap A,B
  mov [B],A<->D ; get r+1,0 into D
  swap A,B      ; inc r
  inc A
  swap A,B
  mov [B],A<->C ; get r+2,0 into C
  swap A,B      ; inc r
  inc A
  ; rearrange so row is in A,B,C
  swap A,D      ; swap r+1,0 into B
  swap A,B
  swap A,D
  swap A,E      ; swap r,0 into A and stash R in E

  ; multiply B by 10 and add C to it
  swap A,B      ;
  mov A,D       ; A=D=B
  add D,A       ; A=B+9*B
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  add D,A
  swap A,C      ;
  mov A,D       ; D=C
  swap A,C      ; get back 10*B
  add D,A       ; A=10*B+C
  swap A,B      ; now we have A=0a B=bc
  print

  mov E,A
  add 90,A      ; test if square >= 10
  jn printb_out
  swap A,E      ; restore square
  jmp printb_loop
printb_out
  ret

  .org 200

; return A=0 if there are open squares, else nonzero
isfull
  mov 1,A       ; start scan from A=1
isfull_loop
  swap A,B
  mov [B],A     ; get square at [B]
  jz isfull_no  ; if empty, not full
  mov B,A
  addn 9,A      ; test B with 9
  jn isfull_yes
  swap A,B
  inc A
  jmp isfull_loop
isfull_no
  ret           ; A=0 here
isfull_yes
  clr A
  inc A
  ret


; runs of squares to check in the board
runs .table 1,2,3 , 4,5,6 , 7,8,9 , 1,4,7 , 2,5,8 , 3,6,9 , 1,5,9 ,  3,5,7

; return A=0 if player D wins else nonzero
iswin
  clr A         ;
  swap A,C      ; C=0 is the index in the runs table
iswin_run
  mov C,A       ;
  add runs,A    ; lookup runs+index
  ftl A         ; get next square# to check
  swap A,B      ; square in B
  swap C,A
  inc A
  swap A,C      ; C=index++
  mov [B],A     ; check square
  sub D,A       ; test square for player
  jz iswin_run2 ; if square==player goto run2
  swap C,A      ; next run index
  inc A         ; skip to next run
  inc A
  jmp iswin_next
iswin_run2
  mov C,A       ;
  add runs,A
  ftl A         ; get next square# to check
  swap A,B      ; square in B
  swap C,A
  inc A
  swap A,C      ; C=index++
  mov [B],A     ; check square
  sub D,A       ; test square for player
  jz iswin_run3 ; if square==player goto run2
  swap C,A      ; next run index
  inc A         ; skip to next run
  jmp iswin_next
iswin_run3
  mov C,A       ;
  add runs,A
  ftl A         ; get next square# to check
  swap A,B      ; square in B
  swap C,A
  inc A
  swap A,C      ; A=square C=index++
  mov [B],A     ; check square
  sub D,A       ; test square for player
  jz iswin_yes  ; if square==player found run
  swap C,A      ; next run index
  ; fall through to iswin_next
iswin_next
  mov A,C
  addn 24,A     ;
  jn iswin_no   ; if run index >= 24, return
  jmp iswin_run ; else keep scanning
iswin_no:
  clr A
  inc A
  ret
iswin_yes:
  ret           ; A=0 here
