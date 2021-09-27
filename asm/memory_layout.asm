; - MEMORY LAYOUT -

; The board is stored as 64 digits in 32 words
; Digit coding:
EMPTY   .equ 0
OTHER   .equ 1
WPAWN   .equ 2
WKNIGHT .equ 3
WBISHOP .equ 4
WQUEEN  .equ 5
BPAWN   .equ 6
BKNIGHT .equ 7
BBISHOP .equ 8
BQUEEN  .equ 9

; OTHER means white/black rook/king. We store the squares of these pieces in another six words
; We'll always have only one queen and two rooks per side (no reason to promote to rook)
; This allows us to represent any number of promoted queens
wking  .equ 32
bking  .equ 33
wrook1 .equ 34
wrook2 .equ 35
; brook1 .equ 36      not needed, if square is occupied and not king or wrook, it's brook
; brook2 .equ 37

; Generic spill space
tmp    .equ 36
; Current movegen square
square .equ 37
; Current player (high digit) and piece type (low digit)
pp     .equ 38

; - Piece and Player constants -
; While the board is stored in a two-level encoding, get_square returns piece, player as below
; Note BRQK need to be in sequential order for movegen
PAWN    .equ  1
KNIGHT  .equ  2
BISHOP  .equ  3
QUEEN   .equ  4
ROOK    .equ  5
KING    .equ  6

WHITE   .equ  0
BLACK   .equ  1
