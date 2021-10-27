; - MEMORY LAYOUT -

; The board is stored as 64 digits in 32 words in addresses 0-31.
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
wrook2 .equ 45  ; not adjacent to wrook1 so movegen state fits in a7
; if square is occupied and not king or wrook, it's brook

; Player and piece currently to move - player in high digit, piece in low digit.
; TODO This is redundant. Should we remove it? It saves looking up what is
; on the from square when doing trial moves, but maybe we don't need it.
fromp  .equ 35


; 36 words of memory form a 4-level software stack for alpha/beta search.
; Since the top of the stack is working memory, this allows us to search up
; to 3 ply.
;
; Instead of indirecting through a stack pointer, the top of stack is kept at
; a fixed address to save code space. This requires copying on push and pop.
; To make that copying more efficient using loadacc/storeacc, stack entries are
; stored with a stride of 10 words at offsets 36, 46, 56, and 66.
;
; a7  |xx 36 37 38 39
; a8   40 41 42 43 44|
; a9  |xx 46 47 48 49
; a10  50 51 52 53 54|
; a11 |xx 56 57 58 59
; a12  60 61 62 63 64|
; a13 |xx 66 67 68 69
; a14  70 71 72 73 74|

; Top of stack:
; Current move
; targetp - player_piece captured, or zero if square is empty
; from - from square index
; target - to square index
; movestate - iterator for move generation
targetp   .equ 36
from      .equ 37
target    .equ 38
movestate .equ 39
; Best move
bestfrom  .equ 40
bestto    .equ 41
; Score after best move
bestscore .equ 42
; Pruning thresholds for alpha/beta search
alpha     .equ 43
beta      .equ 44
; Remaining stack entries begin at 46, 56, 66

; TODO Material score for current position, updated incrementally on calls to
; move and undo_move.
;score  .equ 55

; TODO Current search stack depth
;depth  .equ 65


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
tab9    .table 10, -10,   0,   0

; ft3-relative base address for table data
tables  .equ 6

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
