; - move -
; Modifies board in place to move [fromp] from [from] to [target] removing
; [targetp] if any.
move
  ; is there a capture (i.e. targetp)?
  mov targetp,A<->B
  mov [B],A         ; A=[targetp]
  jz .clear_from
  ; is targetp a rook or king stored outside the board array?
  lodig A
  addn ROOK,A       ; test if piece >= ROOK
  flipn
  jn .clear_from    ; if not, no need to clear
  ; so that we never have two pieces on the same square, clear position for
  ; captured rooks and kings before moving fromp to target
  mov target,A<->B  ;
  mov [B],A<->D     ; D=[target]
  mov 6,A           ; wking div 5 
  loadacc A
  mov H,A           ; wking
  sub D,A
  jz .take_wking
  mov I,A           ; bking
  sub D,A
  jz .take_bking
  mov J,A           ; wrook1
  sub D,A
  jz .take_wrook1
  mov wrook2,A
  swap A,B
  mov [B],A         ; wrook2
  sub D,A
  jz .take_wrook2
  jmp .clear_from   ; brook has no aux position
.take_wking
  mov wking,A<->B
  jmp .take
.take_bking
  mov bking,A<->B
  jmp .take
.take_wrook1
  mov wrook1,A<->B
  jmp .take
.take_wrook2
  mov wrook2,A<->B
.take
  clr A
  mov A,[B]         ; [pos]=0

  ; clear from square in board array
.clear_from
  mov from,A<->B
  mov [B],A         ; A=[from]
  add offset-11,A
  ftl A             ; lookup square offset
  jn .clear_low     ; square mod 2 == 1?

  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (clearing high digit)
  mov A,[B]         ; update board
  jmp .move_fromp

.clear_low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (clearing low digit)
  swapdig A
  mov A,[B]         ; update board

  ; move fromp to its new square
.move_fromp
  mov fromp,A<->B
  mov [B],A         ; A=[fromp]
  mov A,C           ; C=save player_piece 
  ; special case for kings/rooks stored outside board array
  lodig A
  addn ROOK,A       ; test if piece >= ROOK
  jn .fromp_other   ; if so, update other piece pos
  ; encode pawn/knight/bishop/queen for board array
  mov C,A
  swapdig A
  lodig A           ; isolate piece color (0=white, 1=black)
  ;add pbase,A       ; lookup base piece for color
  ;ftl A
  ;swap A,D
  mov A,D           ; map to WPAWN=2 or BPAWN=6
  add D,A           ; A=2*piece color
  add D,A           ; A=3*piece color
  add D,A           ; A=4*piece color
  inc A             ; A+=WPAWN-1 (i.e. 1 for w, 5 for b) 
  swap A,D          ; D=base piece for player-1
  mov C,A
  lodig A           ; isolate piece kind
  add D,A           ; encode piece (e.g. for BPAWN, A=5+1)
  ; update board array
  ; A=piece kind
.set_target
  swap A,D          ; D=piece kind
  mov target,A<->B
  mov [B],A         ; A=[target]
  add offset-11,A
  ftl A             ; lookup square offset
  jn .low           ; square mod 2 == 1?

  swap A,B          ;
  mov [B],A         ; get board at offset
  lodig A           ; isolate low digit (replacing high digit)
  swapdig A
  add D,A           ; add in piece kind 
  swapdig A
  mov A,[B]         ; update board
  ret

.low
  swap A,B          ;
  mov [B],A         ; get board at offset
  swapdig A
  lodig A           ; isolate high digit (replacing low digit)
  swapdig A
  add D,A           ; add in piece kind 
  mov A,[B]         ; update board
  ret

  ; scan other positions to see which matches "from"
.fromp_other
  mov target,A<->B  ;
  mov [B],A<->C     ; C=target square
  mov from,A<->B    ;
  mov [B],A<->D     ; D=from square
  mov 6,A           ; wking div 5 
  loadacc A
  mov H,A           ; wking
  sub D,A
  jz .from_wking
  mov I,A           ; bking
  sub D,A
  jz .from_bking
  mov J,A           ; wrook1
  sub D,A
  jz .from_wrook1
  mov wrook2,A
  swap A,B
  mov [B],A         ; wrook2
  sub D,A
  jz .from_wrook2
.other
  mov OTHER,A       ; A=piece kind (OTHER) 
  jmp .set_target   ; update board array
.from_wking
  mov wking,A<->B
  jmp .from_other
.from_bking
  mov bking,A<->B
  jmp .from_other
.from_wrook1
  mov wrook1,A<->B
  jmp .from_other
.from_wrook2
  mov wrook2,A<->B
.from_other
  swap C,A
  mov A,[B]         ; [pos]=target
  jmp .other
