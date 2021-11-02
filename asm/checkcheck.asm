; CHECKCHECK.ASM 
; Check if the king is in check

; NOTE: Not currently used in chess.asm, though tested in movegen_test.asm
; The last ply of a 4 ply search is always the opponent move, where we detect check


; To call: jump to checkcheck
; Returns via far jump to checkcheckret
;
; Inputs:
;   board, [fromp] to define current player
; Outputs:
;   A=1 if in current player king in check, 0 otherwise
; Trashes:
;   everything
;
; Approach:
; - look for pawns
; - check for sliding pieces in 8 directions
; - check for knights

; Initialize D=king square, E=current player
checkcheck
  mov fromp,A
  swap A,B
  mov [B],A         ; A = current player|piece
  swapdig A
  lodig A
  mov A,E           ; current player
  
  add wking,A       ; get addr of current king pos
  swap A,B
  mov [B],A  
  jz not_in_check   ; we have no king. should only happen in tests.
  swap A,D          ; D=current king square

; Look for enemy pawn captures, equivalent to pawn captures for current side from king's position
  mov E,A
  add pawndir,A
  ftl A 			      ; A = +10 (white) or -10 (black)

  add D,A           ; king square minus a pawn push
  dec A 			      ; left diagonal 
  swap A,D
  jil .checkpawn2   ; legal square?
  jsr get_square    ; yes, what's here?
  jz .checkpawn2    ; nothing, try other dir
  jmp .isitpawn     ; something, what is it?

.checkpawn2
  swap A,D
  add 2,A  			    ; right diagonal
  jil .checksliding ; legal square?
  swap A,D        
  jsr get_square    ; yes, what's here
  jz .checksliding  ; nothing, next piece type

; There's a piece on a pawn capture square. Is it an enemy pawn?
.isitpawn
  mov A,B 		      ; B=player_piece of capture square
  lodig A           ; A=piece on capture square
  dec A 
  jz .itsapawn
  jmp .checksliding

; is this pawn on our side?
.itsapawn
  mov E,A       
  swap A,D          ; D = current player
  mov B,A
  swapdig A
  lodig A 			    ; A = pawn player
  sub D,A
  jz .checksliding 	; same player? not in check
  jmp far checkcheckret ; enemy pawn, A!=0 here, return "in check"


; Check all sliding pieces (BRQK)
; Iterate over each direction until a piece is found, then check potential capture
; C=first_step|dir, D=current square, E=player
; first_step is used to tell if enemy king is too far away to put us in check

.checksliding
  mov 17,A
  swap A,C          ; C = 17 = first_step | current_dir

startslide
  mov E,A           ; get king square for player E
  add wking,A
  swap A,B
  mov [B],A
  swap A,D          ; D = king square

; C=first_step|current_dir, D=current square, E=player
checkslidesquare
  mov C,A
  lodig A           ; clear first_step if set
  add bqrkdir,A
  ftl A 			
  add D,A 			    ; A=square after step
  jil nextslidedir ; off the board
  swap D,A          ; D=new square
  jsr get_square
  jz nextslidesquare
  swap A,B          ; B=player|piece

; something here, is it our piece?
  mov E,A
  swap A,D          ; D = E = player
  mov B,A 			    ; A=player|piece
  swapdig A
  lodig A           ; A = player
  sub D,A
  jz nextslidedir  ; it's our piece, try next direction
  
; It's an enemy piece. Can it capture us?
  swap A,B
  lodig A 			    ; A=piece
  addn BISHOP,A
  flipn
  jn nextslidedir  ; not brqk, can't capture
  jz .ccbishop
  dec A
  jz in_check 	    ; it's a queen, can always capture us
  dec A
  jz .ccrook

; enemy king. Can capture our king only if first_step set
  mov C,A
  swapdig A
  lodig A           ; A = first_step flag
  jz nextslidedir   ; not first step in this direction, too far for capture
  jmp in_check
  
; rook can only capture if dir<4
.ccrook
  mov C,A
  lodig A           ; clear first_step
  add 96,A
  jn nextslidedir 	; dir >= 4
  jmp in_check

; bishop can only capture if dir>=4
.ccbishop
  mov C,A           ; A=dir
  lodig A           ; clear first_step
  add 96,A
  flipn
  jn nextslidedir   ; dir < 4
  ; fall through

in_check
  mov 1,A
  jmp far checkcheckret

not_in_check
  clr A
  jmp far checkcheckret

nextslidesquare
  swap A,C          ; load direction
  lodig A           ; clear first_step flag
  swap A,C          ; store cleared flag
  jmp checkslidesquare

nextslidedir
  mov C,A
  lodig A           ; clear first_step (could already be clear if more than one step)
  dec A             ; next direction
  jn checkknight    ; out of directions
  add 10,A          ; set first_step
  swap A,C          ; C = first_step|current_dur
  jmp startslide

; No sliding captures, can a knight get us?
checkknight
  mov ndir,A
  swap A,C          ; C = current_dir

.checkknightsquare
  mov E,A           ; get king square for player E
  add wking,A
  swap A,B
  mov [B],A
  swap A,D          ; D = king square

  mov C,A           ; C = index into knight move table
  ftl A
  add D,A
  jil .nextknightdir ; square off the board
  swap A,D          ; D = new square
  jsr get_square
  jz .nextknightdir  ; nothing here

; is this an enemy knight?
  mov A,B           ; save player|piece
  lodig A
  addn KNIGHT,A
  jz .itsaknight
  jmp .nextknightdir ; it's not a knight

; it's knight, is it an enemy knight?
; B=player|piece, C=dir, D=king sq, E=current player
.itsaknight
  mov E,A
  swap A,D          ; D = E = player
  swap A,B          ; A = knight player|piece
  swapdig A
  lodig A           ; A = knight player
  sub D,A
  jz .nextknightdir ; it's our knight, nevermind
  jmp in_check

.nextknightdir
  swap A,C
  add 10,A          ; advance to next index in knight direction table
  jn not_in_check   ; ran out of directions
  swap A,C
  jmp .checkknightsquare


