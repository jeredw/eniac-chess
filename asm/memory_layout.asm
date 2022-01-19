; MEMORY_LAYOUT.ASM
; We use all 75 words for board, globals, and search stack

; - Piece and Player constants -
; There are two kinds of piece representations used: "board piece" and "player|piece"
; Player|piece is the obvious one, has player in high digit and piece in low digit.
; This is the format returned from get_square and stored in fromp, targetp

; While the board is stored in a two-level encoding, get_square returns player|piece as below
WHITE   .equ  0
BLACK   .equ  1

; Note that 1) OTHER pieces RK are contiguous and 2) sliding pieces BQRK are contiguous
PAWN    .equ  1
KNIGHT  .equ  2
BISHOP  .equ  3
QUEEN   .equ  4
ROOK    .equ  5
KING    .equ  6

; Incremental score for pawn to queen promotion (must be equal to queen-pawn)
PBONUS  .equ  24


; - Board representation - 
; We have room for only a single board, stored as 64 digits in 32 words in addresses 0-31.
; But six pieces times two players plus empty is 13 states, so we encode rooks/king as OTHER.
; This is the "board piece" representation
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

; OTHER means white/black rook/king, so we store their locations in a separate piece list.
; We'll always have only one king and two rooks per side (no reason to promote to rook)
; This allows us to represent any number of promoted queens
wking  .equ 32
bking  .equ 33
wrook1 .equ 34
wrook2 .equ 35

; If square is occupied with OTHER and it's not king or wrook, it's brook
; Hence we only need four words to define the location of six pieces.


; - Globals -

; accumulator with fromp and mscore
STATE .equ 7

; fromp - player and piece currently to move. 
; Player in high digit, piece in low digit, which we write as player|piece.
; It's not in the stack because we can find it by calling get_square with [from] 
; Once initialized that way, it's awfully useful to know whose turn it is.
fromp  .equ 36

; mscore - material score advantage for white
; One word does not have enough resolution for a full board evaluation, but 
; only the delta matters during a search. In 4 ply, we won't overflow.
; Plus 50, so 50 means a tied material score (no captures, or an even trade)  
; Updated incrementally during move and undo_move.
;
mscore  .equ 37

; The zero value for score is set at 50 so values < 50 are negative.
SZERO   .equ 50

; Current search stack depth
depth   .equ 38

; The stack can have at most 4 entries, reduce for debugging
MAXD    .equ 4
; At depth Q and beyond, only captures are evaluated. (Q is short for
; "quiesence" - this is a basic sort of quiesence search.)
DQ      .equ 4

; XXX bounteous free memory!
unused0   .equ 39
unused1   .equ 40
unused2   .equ 41
unused3   .equ 42
unused4   .equ 43
unused5   .equ 44

; Best top level move found
BEST      .equ 14  ; "best" accumulator
bestfrom  .equ 73
bestto    .equ 74


; - Stack - 
; 28 words of memory form a 4-level software stack for alpha/beta search.
; Each stack entry is split into two parts, with 5 words for move state and
; 2 words for alphas and betas per level.
;
; Instead of indirecting through a stack pointer, the top of the move stack
; is kept at a fixed address to save code space. This requires copying on
; push and pop.
;         bestscore targetp from target movestate
; D=1 a9  45        46      47   48     49
; D=2 a10 50        51      52   53     54
; D=3 a11 55        56      57   58     59
; D=4 a12 60        61      62   63     64
;
; Alphas and betas are only accessed in a few places so are stored as
; packed arrarys indexed by depth.
;            D=1 D=2 D=3 D=4
; α   a13    65  66  67  68
; β   a13/14 69  70  71  72

; Top of stack - lastest move in search
TOP       .equ 9  ; accumulator index

; Current move
; bestscore - best score at this depth
; targetp - player_piece captured, or zero if square is empty
; from - from square index
; target - to square index
; movestate - iterator for move generation
bestscore .equ 45
targetp   .equ 46
from      .equ 47
target    .equ 48
movestate .equ 49 	; values >= PROMO indicate pawn promotion

; Flag added to movestate indicating that the current move is a pawn promotion
PROMO   .equ  90

; Equivalent parent stack entries - top of stack minus 1
pbestscore .equ 50
pfrom      .equ 52
ptarget    .equ 53

; Pruning thresholds for alpha/beta search
alpha0  .equ 64  ; alphas in 65, 66, 67, 68
beta0   .equ 68  ; betas in 69, 70, 71, 72


; - Data tables -

; Tables are manually placed because they overlap and use all
; available space.
;               0    1    2    3    4    5    6    7    8    9
tab0    .table  1,  99,  10,  90,   9,  11,  89,  91,   0,  M0
tab1    .table  1,  M1,   2,  M2,   3,  M3,   8,   3,   4,  M4
tab2    .table  5,  M5,   6,  M6,   7,  M7,  12,   9,   8,  M8
tab3    .table  9,  M9,  10, M10,  11, M11,  19,   9,  12, M12
tab4    .table 13, M13,  14, M14,  15, M15,  21,  27,  16, M16
tab5    .table 17, M17,  18, M18,  19, M19,  79,  15,  20, M20
tab6    .table 21, M21,  22, M22,  23, M23,  81,  25,  24, M24
tab7    .table 25, M25,  26, M26,  27, M27,  88,   0,  28, M28
tab8    .table 29, M29,  30, M30,  31, M31,  92,   1,   5,   0
tab9    .table 10, -10,   1,   0

; ft3-relative base address for table data. 
; First 10 ft3 lines are 1-of-10 decoder. But data starts at offset 6 because we use 
; -2 addressing (lines -2..7) for decoding and +2 addressing (lines 8-102) for FTL
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

; pval has material scores for kinds of pieces
; (note king has score 30)
; entries run vertically at pval + 10*i
pval    .equ tables + 17

; pbase is WPAWN-1,BPAWN-1, used to encode color in set_square
pbase   .equ tables + 87

; pawndir has deltas for pawn moves per player
pawndir .equ tables + 90

; oplayer computes 1-A, maps to opposite player
oplayer .equ tables + 92
