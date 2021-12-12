; CHESS.ASM
; ENIAC chess - the best game for the first computer
; By Jonathan Stray and Jered Wierzbicki
; 
; This is the main game file which includes and places all routines and does the search.
; It is a 4-ply minimax search with alpha/beta pruning and simple material scoring,
; and no special opening or endgame logic. ENIAC always plays white.
;
; This file, like all asm files in this project, is written in the custom VM language
; It is assembled by chasm.py into simulator switch settings chess.e, concatenated 
; with VM wiring patch setup chessvm.e, and then executed by eniacsim. 

  .isa v4
  .include memory_layout.asm

  .org 100
  jmp far game       ; the game outer loop is in ft3

  .include movegen.asm    ; 71 lines
  .include get_square.asm ; 15 lines

  .org 200
  .include move.asm       ; 65 lines
  ;.include debug.asm

; Main program - we jump here on reset
  .org 306

game
  ; set memory state from cards
  ; assume this includes the human player's move
  .include load_board.asm

start
  .include search.asm

search_done
  ; print the best move found during the search
  mov TOP1,A
  loadacc A           ; F=bestfrom, G=bestto
  mov G,A
  swap A,B
  mov F,A
  print

  ; Update board so GUI shows it
  .include make_eniac_move.asm

  jmp game
