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
; We'll always have only one king and two rooks per side (no reason to promote to rook)
; This allows us to represent any number of promoted queens
wking  .equ 32
bking  .equ 33
wrook1 .equ 34
wrook2 .equ 35
; if square is occupied and not king or wrook, it's brook

; Current movegen from square
from   .equ 36
; Current movegen target square
target .equ 37
; Current movegen player_piece on from square
; Note the player field needs to be set to the current player on entry to movegen
from_piece .equ 38
; Flag that current target square is blocked, to stop sliding moves
blocked .equ 39

; - Piece and Player constants -
; While the board is stored in a two-level encoding, get_square returns piece, player as below
PAWN    .equ  1
KNIGHT  .equ  2
BISHOP  .equ  3
QUEEN   .equ  4
ROOK    .equ  5
KING    .equ  6

WHITE   .equ  0
BLACK   .equ  1


; Data tables

; Tables are manually placed because they overlap and use all
; available space.
;               0    1    2    3    4    5    6    7    8    9
tab0    .table  1,  99,  10,  90,   9,  11,  89,  91,   0,  M0
tab1    .table  1,  M1,   2,  M2,   3,  M3,   8,   0,   4,  M4
tab2    .table  5,  M5,   6,  M6,   7,  M7,  12,   0,   8,  M8
tab3    .table  9,  M9,  10, M10,  11, M11,  19,   0,  12, M12
tab4    .table 13, M13,  14, M14,  15, M15,  21,   0,  16, M16
tab5    .table 17, M17,  18, M18,  19, M19,  79,   0,  20, M20
tab6    .table 21, M21,  22, M22,  23, M23,  81,   0,  24, M24
tab7    .table 25, M25,  26, M26,  27, M27,  88,   0,  28, M28
tab8    .table 29, M29,  30, M30,  31, M31,  92,   0,   0,   0
tab9    .table 10, -10

; ft3-relative base address for table data
; TODO modify vm+chasm to use -2 addressing to get 2 more constants
tables  .equ 8

; bqrkdir has ±1,±1 square deltas for sliding piece moves
; note terminated by the 0 which begins the offset table
bqrkdir .equ tables + 0
; offset maps positions 11..88 to address
; value = square div 2, sign = square mod 2, indicates low or high digit
; note x6/x7 entries are padding reused for other tables
offset  .equ tables + 8
; ndir has deltas for L-shaped knight moves
; entries run vertically at ndir + 10*i
ndir    .equ tables + 16
; pawndir has deltas for pawn moves per player
pawndir .equ tables + 90
