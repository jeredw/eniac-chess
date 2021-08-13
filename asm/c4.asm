; "Connect Four" search program for ENIAC chess VM
  .isa v4
  .org 100

; The board is stored as a matrix in row major order in 42 (6x7) words in
; accs 0-8.  NB the board is assumed in many places to begin at address 0.
; TODO Investigate packing the board into 21 words by using one digit per
; piece instead.
;board      .equ 0   ; 42 words, 0=none, 1=player1, 2=player2
boardsize  .equ 42
; Locations 42, 43, and 44 are used as auxiliary storage
winner     .equ 42  ; 0=no winner, 1=player1, 2=player2, 3=draw
tmpcol     .equ 42  ; winner doubles up as a tmp for column in win routine
tmp        .equ 43  ; generic spill
sp         .equ 44  ; reserved to spill sp
; Accs 9-14 are used as working memory and stack for a 5-level search
stack00    .equ 45  ; first word of stack (with best move)
stackbase  .equ 9   ; base of stack = acc 9
stackbase1 .equ 10  ; stack base + 1
stackmax   .equ 14  ; max stack

; Inner columns are generally better than outer columns, so searching columns
; from inside out reduces search time 5-6x due to better pruning.
; colorder is indexed by last_move which decreases from 7 to 1.
colorder .table 0, 1, 7, 2, 6, 3, 5, 4

  ; eniac always goes first and plays in the middle
  mov 1,A<->D       ; D=player1
  mov 4,A           ; A=column 4
  jsr move
  jsr printb

game
  read              ; human plays next, read move into LS
  mov 2,A<->D       ; D=player2
  mov F,A           ; A=column played
  jsr move
  jsr printb

  ; set up the initial search stack frame
  mov 99,A<->E      ; beta=99
  clr A
  swap A,D          ; alpha=0
  mov szero,A<->C   ; best_score=30 (zero)
  clr A
  swap A,B          ; last_move=0
  mov 10,A          ; player|best_move=10 (eniac to play)
  swapall           ;
  mov stackbase,A   ; write to stack
  storeacc A        ;
  mov sp,A<->B
  mov stackbase1,A  ; init sp to stackbase+1
  mov A,[B]

search
  mov sp,A<->B
  mov [B],A         ; A=sp
  mov A,C           ; stash C=sp
  addn stackbase,A  ; test sp with base of stack
  jz search_done    ; if sp==base, search is done
  jn no_underflow
  jmp underflow     ; if sp<base, underflow
no_underflow
  swap C,A          ; A=sp
  dec A             ; sp-=1
  mov A,[B]         ; write back sp

  ; load search state from stack
  loadacc A         ; F=player|best_move, G=last_move, H=best_score, I=a, J=b
  ; check if last_move is none (i.e. 0)
  ; this signals the start of a search at new depth
  mov G,A           ; A=last_move
  jz new_depth      ; if last_move is 0, new recursive search

  ; iterating over possible moves at current depth
  add colorder,A    ; A=colorder+move#
  ftl A             ; lookup A=column# for move
  jsr undo_move     ; undo last move
  ; update the best move at current depth
  mov sp,A<->B
  mov [B],A         ; A=sp
  mov A,B           ; stash B=sp
  inc A             ;
  loadacc A         ; load previous recursive frame
  mov H,A<->D       ; D=value (best_score from previous frame)
  mov B,A           ; A=sp (keeping sp stashed in B)
  loadacc A         ; restore current frame
  mov F,A           ; get player|best_move (1x=eniac, 2x=human)
  addn 20,A         ;
  jn cd_min         ; if >= 20 then human (min) else eniac (max)

  ; evaluate move value (in D) for max player
;cd_max
  mov I,A           ; A=alpha
  sub D,A           ; A=alpha - value(D)
  jn update_alpha   ; if value > alpha, update alpha
  jmp max_best      ; else check for new best move
update_alpha
  swapall
  swap D,A
  mov I,A           ; set alpha=value (from D=I)
  swap A,D
  swapall
  mov B,A           ; A=sp
  storeacc A        ; update frame
max_best
  mov H,A           ; A=best_score
  sub D,A           ; A=best_score - value(D)
  jn update_max_best ; if value > best_score, update best move
  jmp next_move
update_max_best
  swapall
  swap C,A
  mov I,A           ; set best_score=value (from D=I)
  swap A,C
  mov B,A           ; set best_move=last_move
  add 10,A          ; add player (eniac=1x)
  swapall
  swap B,A          ; A=sp
  storeacc A        ; update frame
  jmp next_move

  ; evaluate move value (in D) for min player
cd_min
  swap D,A
  swap A,E          ; swap value into E
  mov J,A<->D       ; D=beta
  mov E,A           ; A=value
  sub D,A           ; A=value - beta
  jn update_beta    ; if value < beta, update beta
  jmp min_best      ; else check for new best move
update_beta
  swapall
  swap E,A
  mov J,A           ; set beta=value (from E=J)
  swap A,E
  swapall
  mov B,A           ; A=sp
  storeacc A        ; update frame
min_best
  mov H,A<->D       ; D=best_score
  mov E,A           ; A=value
  sub D,A           ; A=value - best_score
  jn update_min_best ; if value < best_score, update best move
  jmp next_move
update_min_best
  swapall
  swap C,A
  mov J,A           ; set best_score=value (from E=J)
  swap A,C
  mov B,A           ; set best_move=last_move
  add 20,A          ; add player (human=2x)
  swapall
  swap B,A          ; A=sp
  storeacc A        ; update frame
  jmp next_move

next_move
  ; before iterating to next move, apply alpha/beta pruning
  ; can stop searching moves at this depth if alpha >= beta
  mov I,A<->D       ; D=alpha
  mov J,A           ; A=beta
  sub D,A           ; A=beta - alpha
  ;jn dump_ab        ;
  ;jz dump_ab        ; if beta <= alpha, stop iteration
  jn search         ;
  jz search         ; if beta <= alpha, stop iteration

  mov G,A           ; A=last_move
  dec A             ;
  jmp check_move    ; start searching from last_move-1

; dump alpha beta values for checking the algorithm
;dump_ab
;  mov J,A<->B
;  mov I,A
;  print
;  jmp search

new_depth
  ; begin search at new depth, unless search should terminate here
  mov winner,A<->B  ;
  mov [B],A         ; A=winner for current board
  jz first_move     ; if no winner, continue search from first move

  ; 1=eniac won (score=99)
  ; 2=human won (score=0)
  ; 3=draw      (score=30)
score .table 0, 99, 0, szero
  add score,A       ; A=score+winner
  ftl A             ; lookup score for this winner
  jmp save_score

search_cutoff
  jmp far score1    ; depth cutoff (score=heuristic)
; save new best_score into stack[sp]
save_score
score1_ret          ; score1 returns here
  swap A,C          ; C=score
  mov sp,A<->B
  mov [B],A         ; read sp
  loadacc A         ; restore stack frame
  swapall
  swap C,A
  mov H,A           ; set best_score=score (from H=C)
  swap A,C
  swapall
  storeacc A        ; save frame
  jmp search

first_move
  mov sp,A<->B      ; check stack depth
  mov [B],A         ; A=sp
  addn stackmax,A   ; test sp against stack max
  jz search_cutoff  ; if sp==stack max, cutoff search
  jn overflow       ; if sp>stack max, error
  mov 7,A           ; search moves best column first

; On entry to check_move, A is the next move# to play.
check_move
  jz search         ; if A=0 no more moves at this depth
  mov A,C           ; C=move#
  add colorder,A    ; A=colorder+move#
  ftl A             ; lookup next A=column#
  dec A             ;
  swap A,B          ; B=column offset
  mov [B],A         ; check top of column
  jz do_move        ; if empty, play in this column
  swap C,A          ; A=C which is move#
  dec A             ; try next move
  jmp check_move

; B has column offset for move, C has move#
do_move
  swap B,A
  inc A             ; A=column# (which is offset+1)
  swap A,D          ; D=column#

  ; save iteration state on stack
  mov sp,A<->B      ;
  mov [B],A         ; A=sp
  loadacc A         ; restore stack frame
  swapall
  swap B,A
  mov H,A           ; update last_move (from H=C)
  swap A,B
  swapall
  storeacc A        ; update frame
  ; (update sp later to preserve player in LS here)
  ; apply move and push recursive frame
  mov F,A           ; A=1x for eniac, 2x for human
  addn 20,A         ;
  jn do_move_p2     ; if >= 20 then human (min) else eniac (max)

;do_move_p1
  swap D,A
  swap A,C          ; C=column#
  mov 1,A<->D       ; D=player1
  swap C,A          ; A=column#
  jsr move
  ; set up new recursive frame for p2
  mov sp,A<->B      ;
  mov [B],A         ; A=sp
  loadacc A         ; restore frame
  swapall
  ; keep alpha and beta from D+E
  mov 99,A
  swap A,C          ; best_score=99
  clr A
  swap A,B          ; last_move=0
  mov 20,A          ; player|best_move=20
  swapall
  inc A             ; inc sp (past cur frame)
  storeacc A
  inc A             ; inc sp (past new frame)
  mov A,[B]         ; save sp
  jmp search

do_move_p2
  swap D,A
  swap A,C          ; C=column#
  mov 2,A<->D       ; D=player2
  swap C,A          ; A=column#
  jsr move
  ; set up new frame for p1
  mov sp,A<->B      ;
  mov [B],A         ; A=sp
  loadacc A         ; restore frame
  swapall
  ; keep alpha and beta from D+E
  clr A
  swap A,C          ; best_score=0
  clr A
  swap A,B          ; last_move=0
  mov 10,A          ; player|best_move=10
  swapall
  inc A             ; inc sp (past cur frame)
  storeacc A
  inc A             ; inc sp (past new frame)
  mov A,[B]         ; save sp
  jmp search

search_done
  mov stack00,A<->B
  mov [B],A         ; load player|best_move from top of stack
  lodig A           ; A=move#
  add colorder,A    ; A=colorder+move#
  ftl A             ; lookup column# for move
  swap A,B          ; B=column#
  mov 1,A<->D       ; D=player1 (eniac)
  swap B,A          ; A=column#
  jsr move          ; play best move for eniac
  jsr printb
  jmp game

underflow
  mov 96,A          ; stack underflow
  jmp far error

overflow
  mov 95,A          ; stack overflow
  jmp far error

  .org 200

; score the current board for player 1
; called in just one place from game loop and branches back there statically
; so it can use subroutines to save code space
; returns A=score
szero   .equ 30     ; zero value for heuristic score
scenter .equ 3      ; +3 for pieces in center col
srun3   .equ 5      ; +5 for run of length 3
srun2   .equ 2      ; +2 for run of length 2
sorun3  .equ 96     ; -4 for opponent run of length 3
score1
  mov szero,A<->C   ; C=zero score

  ; apply center column bonus
  mov 3,A
  jsr s_bonus       ; check row 1
  mov 10,A
  jsr s_bonus       ; check row 2
  mov 17,A
  jsr s_bonus       ; check row 3
  mov 24,A
  jsr s_bonus       ; check row 4
  mov 31,A
  jsr s_bonus       ; check row 5
  mov 38,A
  jsr s_bonus       ; check row 6

  ; count horizontal runs
  ; B=offset, C=score, D=player|empty, E=column
  clr A
  swap A,B          ; B=offset (0)
score1_h
  mov B,A
  addn boardsize,A  ; test offset with boardsize
  jn score1_h_out   ; if offset>boardsize, done
  clr A
  swap A,D          ; D=player|empty (00)
  clr A
  swap A,E          ; E=column (0)
score1_row
  mov E,A
  addn 4,A          ; test column with 4
  jn score1_row_u   ; if column>=4, must uncount col-4
  jmp score1_row_c
score1_row_u
  mov B,A
  addn 4,A          ; offset-=4
  swap A,B
  jsr s_uncount     ;
  swap B,A
  add 4,A           ; offset+=4
  swap A,B
score1_row_c
  jsr s_count       ; count at offset, update score
  swap B,A
  inc A             ; offset += 1
  swap A,B
  swap E,A
  inc A             ; column += 1
  mov A,E
  addn 7,A          ; test column with 7
  jn score1_h       ; if column>=7 start of new row
  jmp score1_row
score1_h_out

  ; count vertical runs
  ; B=offset, C=score, D=player|empty, E=row
  mov 41,A<->B      ; B=offset, score1_v will init to 0
score1_v
  swap B,A
  addn 41,A         ; offset-=41 (top of next column)
  swap A,B          ; B=top
  mov B,A           ; A=top
  addn 7,A          ;
  jn score1_v_out   ; if offset>=7, done
  clr A
  swap A,D          ; D=player|empty (00)
  clr A
  swap A,E          ; E=row (0)
score1_col
  mov E,A
  addn 4,A          ; test row with 4
  jn score1_col_u   ; if row>=4, must uncount row-4
  jmp score1_col_c
score1_col_u
  mov B,A
  addn 28,A         ; offset-=4*7
  swap A,B
  jsr s_uncount     ;
  swap B,A
  add 28,A          ; offset+=4*7
  swap A,B
score1_col_c
  jsr s_count       ; count at offset
  swap B,A
  add 7,A           ; offset += 7
  swap A,B
  swap E,A
  inc A             ; row += 1
  mov A,E
  addn 6,A          ; test row with 6
  jn score1_v       ; if row>=6 start of new col
  jmp score1_col
score1_v_out

  ; count right \ diagonal runs
drstart .table 14, 7, 0, 1, 2, 3

  ; B=offset, C=score, D=player|empty, E=row, [tmp]=diag#
  mov tmp,A<->B
  mov 6,A
  mov A,[B]         ; initialize diag#
score1_dr
  mov tmp,A<->B     ;
  mov [B],A         ; get diag#
  jz score1_dr_out  ; if diag#==0, all done
  dec A
  mov A,[B]         ; diag#-=1
  add drstart,A
  ftl A             ; lookup start of r-diagonal
  swap A,B          ; B=start offset
  clr A
  swap A,D          ; D=player|empty (00)
  clr A
  swap A,E          ; E=row (0)
score1_dr_row
  mov E,A
  addn 4,A          ; test row with 4
  jn score1_dr_u    ; if row>=4, must uncount row-4
  jmp score1_dr_c
score1_dr_u
  mov B,A
  addn 32,A         ; offset-=4*8
  swap A,B
  jsr s_uncount     ;
  swap B,A
  add 32,A          ; offset+=4*8
  swap A,B
score1_dr_c
  jsr s_count       ; count at offset
  ; skip down to next column in next row of diagonal
  swap B,A
  add 8,A           ; offset += 8
  mov A,B
  ; most right diagonals will end >= end of board
  addn boardsize,A  ; compare offset with boardsize
  jn score1_dr      ; if offset>=boardsize, done
  ; the diagonal (3,11,19,27) ends at 35
  mov B,A           ;
  addn 35,A         ; compare with 35 (lower left)
  jz score1_dr      ; if offset==lower left, wrapped (done)
  swap E,A
  inc A             ; row += 1
  swap A,E
  jmp score1_dr_row ; next row
score1_dr_out

  ; count left / diagonal runs
dlstart .table 20, 13, 6, 5, 4, 3

  ; B=offset, C=score, D=player|empty, E=row, [tmp]=diag#
  mov tmp,A<->B
  mov 6,A
  mov A,[B]         ; initialize diag#
score1_dl
  mov tmp,A<->B     ;
  mov [B],A         ; get diag#
  jz score1_dl_out  ; if diag#==0, all done
  dec A
  mov A,[B]         ; diag#-=1
  add dlstart,A
  ftl A             ; lookup start of l-diagonal
  swap A,B          ; B=start offset
  clr A
  swap A,D          ; D=player|empty (00)
  clr A
  swap A,E          ; E=row (0)
score1_dl_row
  mov E,A
  addn 4,A          ; test row with 4
  jn score1_dl_u    ; if row>=4, must uncount row-4
  jmp score1_dl_c
score1_dl_u
  mov B,A
  addn 24,A         ; offset-=4*6
  swap A,B
  jsr s_uncount     ;
  swap B,A
  add 24,A          ; offset+=4*6
  swap A,B
score1_dl_c
  jsr s_count       ; count at offset
  ; skip down to next column in next row of diagonal
  swap B,A
  add 6,A           ; offset += 6
  mov A,B
  ; most left diagonals will end >= 41
  addn 41,A         ; compare offset with 41
  jn score1_dl      ; if offset>=41, done
  ; the diagonal (4,10,16,22,28) ends at 34
  mov B,A           ;
  addn 34,A         ; compare with 34
  jz score1_dl      ; if offset==34, wrapped (done)
  ; the diagonal (3,9,15,21) ends at 27
  mov B,A           ;
  addn 27,A         ; compare with 27
  jz score1_dl      ; if offset==27, wrapped (done)
  swap E,A
  inc A             ; row += 1
  swap A,E
  jmp score1_dl_row ; next row
score1_dl_out
  swap C,A          ; return score
  jmp far score1_ret

; add to counts from board at [B]
s_count
  mov [B],A
  jz s_count0       ; if board==0, count 0
  dec A
  jz s_count1       ; if board==1, count 1
  mov E,A
  addn 3,A          ; test size with 3
  jn s_addscore     ; if size>=3, add to score
  ret
s_count0
  swap D,A
  inc A             ; D += 01 (empty)
  swap A,D
  mov E,A
  addn 3,A          ; test size with 3
  jn s_addscore     ; if size>=3, add to score
  ret
s_count1
  swap D,A
  add 10,A          ; D += 10 (player1)
  swap A,D
  mov E,A
  addn 3,A          ; test size with 3
  jn s_addscore     ; if size>=3, add to score
  ret

; remove counts from board at [B]
s_uncount
  mov [B],A
  jz s_uncount0     ; if board==0, uncount 0
  dec A
  jz s_uncount1     ; if board==1, uncount 1
  ret
s_uncount0
  swap D,A
  dec A             ; D -= 01 (empty)
  swap A,D
  ret
s_uncount1
  swap D,A
  addn 10,A         ; D -= 10 (player1)
  swap A,D
  ret

; adjust score based on piece counts
s_addscore
  mov D,A           ; get counts in A
  addn 40,A
  jz s_win          ; if counts==4(player)0(empty), win
  mov D,A
  addn 31,A
  jz s_run3         ; if counts==3(player)1(empty), run of 3
  mov D,A
  addn 22,A
  jz s_run2         ; if counts==2(player)2(empty), run of 2
  mov D,A
  dec A
  jz s_opprun3      ; if counts==0(player)1(empty), opponent run of 3
  ret
s_run3
  swap C,A
  add srun3,A       ; score += srun3 bonus
  swap A,C
  ret
s_run2
  swap C,A
  add srun2,A       ; score += srun2 bonus
  swap A,C
  ret
s_opprun3
  swap C,A
  add sorun3,A      ; score -= 4
  swap A,C
  ret
s_win
  mov 99,A          ; score=99
  jmp far score1_ret ; short-circuit return

; add bonus to score if piece at A is player1
s_bonus
  swap A,B
  mov [B],A         ; check piece at position
  dec A
  jz s_bonus_yes    ; if player1, apply bonus
  ret
s_bonus_yes
  swap C,A
  add scenter,A     ; apply center column bonus
  swap A,C
  ret

  .org 308

; print out the game board and winner for debugging
; prints one piece per card AABB (A=piece, B=address) then 99BB (B=winner)
; halts if winner != 0
printb
  clr A
  swap A,B          ; B=0 (board data)
printb_loop
  mov [B],A         ; read word of board
  jz printb_skip    ; if nothing here, skip
  print             ; print AABB (A=piece, B=address)
printb_skip
  swap A,B          ;
  inc A             ; next word of board
  mov A,B
  addn boardsize,A  ; test if A==42 (42+58=100)
  jz printb_winner  ; if end of board, done
  jmp printb_loop
printb_winner
  mov winner,A<->B
  mov [B],A<->B     ; winner in B
  mov 99,A          ; A=99 flags end of board
  print
  swap A,B
  jz printb_out
  halt              ; if winner!=0, game over, halt
printb_out
  ret

; play move in column# for player
; A=column# (1-7) D=player
move
  dec A             ; compute top of column offset
  swap A,C          ; C=offset to play
  mov tmpcol,A<->B  ; spill column offset into [tmpcol]
  mov C,A           ;
  mov A,[B]         ;
  swap A,B          ; B=next offset in column (+1 row)
  mov [B],A         ; check top of column
  jz move_drop      ; if top of col has room, drop piece
  mov 98,A          ; column full
  jmp error
move_drop
  mov C,A           ; A=current offset
  add 7,A           ; calc next row offset
  mov A,B           ;
  addn boardsize,A  ; test if offset>=42
  jn move_place     ; if past end of board, place at bottom
  mov [B],A         ; check if next row empty
  jz move_next      ; if so, keep scanning
  jmp move_place    ; if nonempty, C is where to play
move_next
  swap B,A          ;
  swap A,C          ; cur offset = next offset
  jmp move_drop
move_place
  swap C,A          ; C<->A<->B
  swap A,B          ; B=offset for piece
  swap D,A          ; A=player
  mov A,[B]         ; store piece for player
  swap A,D          ; D=player
  swap A,B
  swap A,E          ; E=move offset

; update winner based on the piece just played
; D=player, E=move offset, [tmpcol]=column offset

  ; check move column for win
  clr A
  swap A,C          ; C=0 (run length)
  mov tmpcol,A<->B  ;
  mov [B],A<->B     ; B=column offset from [tmpcol]
win_col
  mov [B],A         ; A=piece at [offset]
  sub D,A           ; A-=player
  jz win_col_run    ; if A==player, count towards run
  clr A             ; else reset run length
  swap A,C          ;   (C=0)
  jmp win_col_next
win_col_run
  swap C,A          ;
  inc A             ;
  mov A,C           ; C+=1 (count run)
  addn 4,A          ;
  jz win_won        ; if run length == 4, player won
win_col_next        ; advance to next  row
  swap B,A          ;
  add 7,A           ;
  mov A,B           ; offset += 7
  addn boardsize,A  ; check if offset past end of board
  jn win_col_done   ; if past end, done scanning col
  jmp win_col
win_col_done

  ; check move row for win
rowstart .table 0,0,0,0,0,0,0, 7,7,7,7,7,7,7, 14,14,14,14,14,14,14, 21,21,21,21,21,21,21, 28,28,28,28,28,28,28, 35,35,35,35,35,35,35

  swap D,A
  swap A,C          ; stash player in C
  mov tmp,A<->B     ; B=tmp
  mov E,A           ; A=move offset (0-41)
  mov A,[B]         ; spill move offset into [tmp]
  add rowstart,A    ; A+=rowstart (base of table)
  ftl A             ; lookup row offset
  swap A,B          ; B=row offset
  swap C,A
  swap A,D          ; D=player
  clr A
  swap A,C          ; C=0 (run length)
  mov 7,A<->E       ; E=7 (columns)
win_row
  mov [B],A         ; A=piece at [offset]
  sub D,A           ; A-=player
  jz win_row_run    ; if A==player, count towards run
  clr A             ; else reset run length
  swap A,C          ; C=0 (reset run)
  jmp win_row_next
win_row_run
  swap C,A          ;
  inc A             ; C+=1 (count run)
  mov A,C           ; (save run length)
  addn 4,A          ;
  jz win_won        ; if run length == 4, player won
win_row_next
  swap B,A          ;
  inc A             ; offset+=1
  swap A,B          ;
  swap A,E
  dec A             ; column-=1
  jz win_row_done   ; if examined 7 columns, done
  swap A,E          ; (store back column)
  jmp win_row
win_row_done

  ; check move \ diagonal for win
  mov tmpcol,A<->B  ;
  mov [B],A<->E     ; E=column offset from [tmpcol]
  mov tmp,A<->B     ;
  mov [B],A<->B     ; B=move offset from [tmp]
  ; rewind to upper left of diagonal
win_ul0
  mov E,A
  jz win_ul0_done   ; if column==0, at start
  dec A
  swap A,E          ; column -= 1
  mov B,A
  addn 8,A          ; offset-=8 (setting sign if A>=8)
  jn win_ul0_prev   ; if A>=8, check next column
  jmp win_ul0_done  ; would go off top row
win_ul0_prev
  swap A,B          ; B=updated start offset
  mov B,A           ; A=start offset
  jmp win_ul0
win_ul0_done        ;
  ; scan down diagonal (B=start offset, E=column)
  clr A
  swap A,C          ; C=run length (0)

win_ul
  mov [B],A         ; read piece at offset
  sub D,A           ; A-=player
  jz win_ul_run     ; if A==player, count towards run
  clr A             ; else reset run length
  swap A,C          ; C=0 (reset run)
  jmp win_ul_next
win_ul_run
  swap C,A          ;
  inc A             ;
  mov A,C           ; C+=1 (count run)
  addn 4,A          ;
  jz win_won        ; if run length == 4, player won
win_ul_next
  swap B,A          ;
  add 8,A           ; offset+=8
  mov A,B
  addn boardsize,A  ;
  jn win_ul_done    ; if A>=42, past last row of board
  swap E,A
  inc A             ; column+=1
  mov A,E
  addn 7,A          ; compare A with 7
  jn win_ul_done    ; if column>=7, past last col of board
  jmp win_ul
win_ul_done

  ; check move / diagonal for win
  mov tmpcol,A<->B  ;
  mov [B],A<->E     ; E=column offset from [tmpcol]
  mov tmp,A<->B     ;
  mov [B],A<->B     ; B=move offset from [tmp]
  ; rewind to upper right of diagonal
win_ur0
  mov E,A
  addn 6,A
  jz win_ur0_done   ; if column==6, at start
  swap E,A
  inc A
  swap A,E          ; column += 1
  mov B,A
  addn 6,A          ; A-=6 (setting sign if A>=6)
  jn win_ur0_prev   ; if A>=6, check next column
  jmp win_ur0_done  ; would go off top row
win_ur0_prev
  swap A,B          ; B=updated start offset
  mov B,A           ; A=start offset
  jmp win_ur0
win_ur0_done        ;
  ; scan down diagonal (B=start offset, E=column)
  clr A
  swap A,C          ; C=run length (0)

win_ur
  mov [B],A         ; read piece at offset
  sub D,A           ; A-=player
  jz win_ur_run     ; if A==player, count towards run
  clr A             ; else reset run length
  swap A,C          ; C=0 (reset run)
  jmp win_ur_next
win_ur_run
  swap C,A          ;
  inc A             ;
  mov A,C           ; C+=1 (count run)
  addn 4,A          ;
  jz win_won        ; if run length == 4, player won
win_ur_next
  swap B,A          ;
  add 6,A           ; offset+=6
  mov A,B
  addn boardsize,A  ;
  jn win_ur_done    ; if A>=42, past last row of board
  swap E,A
  dec A             ; column-=1
  jn win_ur_done    ; if column<0, past first col of board
  swap A,E          ; save column
  jmp win_ur
win_ur_done

  ; if move was in top row, check for draw (after all possible wins)
  mov tmp,A<->B     ;
  mov [B],A         ; A=move offset from [tmp]
  addn 7,A
  jn win_none       ; if A>=7 then no draw possible
  mov 6,A<->B       ; B=end of first row
win_check_draw
  mov [B],A         ; check top of col
  jz win_none       ; if empty no draw
  swap B,A          ;
  dec A             ; offset -= 1
  jn win_draw
  swap A,B          ; save offset
  jmp win_check_draw

win_draw
  mov winner,A<->B  ; B=winner
  mov 3,A           ; A=3
  mov A,[B]         ; set [winner] to player
  ret
win_won
  mov winner,A<->B  ; B=winner
  swap D,A          ; A=player
  mov A,[B]         ; set [winner] to player
  ret
win_none
  mov winner,A<->B  ; B=winner
  clr A             ; A=0
  mov A,[B]         ; set [winner] to player
  ret

; undo the last move in column
; A=column# (1-7)
undo_move
  dec A             ;
  swap A,B          ; B=top of column offset
undo_move_scan
  mov [B],A         ; get piece here
  jz undo_move_next ; if empty, keep scanning
  jmp undo_move_out ; found piece
undo_move_next
  swap B,A
  add 7,A           ; move down one row
  mov A,B
  addn boardsize,A  ; past end of column?
  jn undo_move_err  ; if so, error out
  jmp undo_move_scan
undo_move_out
  clr A
  mov A,[B]         ; remove piece
  ; search stops at the first winning move so undoing the last move
  ; clears any win (or a draw)
  mov winner,A<->B  ; B=winner
  clr A
  mov A,[B]         ; set [winner] to 0
  ret

undo_move_err
  mov 97,A          ; past end of column
  jmp error

; print an error code and halt
error
  mov A,B
  print
  print
  print
  halt