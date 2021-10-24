; CHECKCHECK - Check if the king is in check
; Current player defined by high digit of fromp. Not a subroutine, calls get_square 
; "Returns" with a far jump to checkcheckret, A=nonzero if current player king in check

; Approach:
; - look for pawns
; - check for sliding pieces in 8 directions
; - check for knights

; Initialize D=king square, E=current player
  mov fromp,A
  swap A,B
  mov [B],A         ; A = current player|piece
  swapdig A
  lodig A
  mov A,E           ; current player
  
  add wking,A       ; get addr of current king pos
  swap A,B
  mov [B],A  
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
  jmp checkcheckret ; enemy pawn, A!=0 here, return "in check"


; Check all sliding pieces (BRQK)
; Iterate over each direction until a piece is found, then check potential capture
; C=first_step|dir, D=current square, E=player
; first_step is used to tell if enemy king is too far away to put us in check

.checksliding
  mov 8,A
  swap A,C          ; C = initial direction of 7 + 1 (we pre-decrement)

.nextslidedir
  mov E,A           ; get king square for player E
  add wking,A
  swap A,B
  mov [B],A
  swap A,D 			    ; D = king square

  mov C,A
  dec A
  jn .checkknight   ; out of directions
  add 10,A          ; set first_step flag
  swap A,C 			    ; C=dir after decrement, A=dir before decrement 

.checkslidesquare
  add bqrkdir,A
  ftl A 			
  add D,A 			    ; A=square after step
  jil .nextslidedir ; off the board
  swap D,A          ; D=new square
  jsr get_square
  jz .nextslidesquare

; something here, is it our piece?
  mov E,A
  swap A,D          ; D = E = player
  mov A,B 			    ; A=B=player|piece
  swapdig A
  lodig A 			    ; A=player of occupied square
  sub D,A
  jz .nextslidedir  ; it's our piece, try next direction
  
; It's an enemy piece. Can it capture us?
  swap A,B
  lodig A 			    ; A=piece
  addn 3,A
  jn .nextslidedir  ; not brqk, can't capture
  jz .ccbishop
  dec A
  jz in_check 	    ; it's a queen, can always capture us
  dec A
  jz .ccrook

; enemy king. Can capture our king only if first_step set
  mov C,A
  swapdig A
  lodig A           ; A = first_step flag
  jz .nextslidedir  ; not first step in this direction, too far for capture
  jmp in_check
  
; rook can only capture if dir<4
.ccrook
  mov C,A  
  add 96,A
  jn .nextslidedir 	; dir >= 4
  jmp in_check

; bishop can only capture if dir>=4
.ccbishop
  mov C,A           ; A=dir
  add 96,A
  flipn
  jn .nextslidedir  ; dir < 4
  ; fall through

in_check
  mov 1,A
  jmp checkcheckret ; pseudo-return

.nextslidesquare
  swap C,A          ; load direction
  lodig A           ; clear first_step flag
  mov A,C           ; store cleared first_step
  jmp .checkslidesquare

; No sliding captures, can a knight get us?
.checkknight
  



