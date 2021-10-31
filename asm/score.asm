; These helpers update incremental material score.
; TODO Ideally these would just be inline in move.asm

; update material score when capturing a piece
; A=player_piece captured
score
  mov A,C           ; C=save [targetp]
  lodig A
  dec A             ; map PAWN=1 to 0
  swapdig A         ; 10*(piece type-1)
  add pval,A        ; index piece values
  ftl A             ; lookup value
  swap A,D          ; D=value
  mov mscore,A<->B
  mov C,A
  swapdig A
  lodig A           ; get player
  jz .white
;.black
  mov [B],A
  add D,A           ; mscore += piece value
  jmp .score
.white
  mov [B],A
  sub D,A           ; mscore -= piece value
.score
  mov A,[B]         ; update mscore
  swap C,A          ; restore A=[targetp]
  jmp far score_ret

; update material score when undoing a capture
; A=player_piece captured
; returns with C=player_piece
unscore
  mov A,C           ; C=save [targetp]
  lodig A
  dec A             ; map PAWN=1 to 0
  swapdig A         ; 10*(piece type-1)
  add pval,A        ; index piece values
  ftl A             ; lookup value
  swap A,D          ; D=value
  mov mscore,A<->B
  mov C,A
  swapdig A
  lodig A           ; get player
  jz .white
;.black
  mov [B],A
  sub D,A           ; mscore -= piece value
  jmp .score
.white
  mov [B],A
  add D,A           ; mscore += piece value
.score
  mov A,[B]         ; update mscore
  jmp far unscore_ret
