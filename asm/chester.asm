; BISHOP/ROOK/QUEEN/KING MOVE GEN
; Input:
;    A = -1 if piece found on last_to, otherwise 0
;    B = piece_type (derivable from piece_index, but explicit here)
;    F = enum state or 99 for first move 
;    G = piece index
;    H = last_to - last generated move
; Output:
;    A = next_to, a square index, or 99 if no more moves
;    F = next enum state
;
; Generates all legal moves on an empty board
; Does not check for a piece already on the square, or reachability
; Does not check for check when moving king
; Ensure A=0 if enumstate=0
;
; Works by indexing over an array of start and end directions, up/down/left/right then diagonals
; So we put these values into two four-entry lookup tables on ft3 and index by piece_type:
;   ROW     START     END
;   bishop  4         7
;   rook    0         3
;   queen   0         7
;   king    0         7

brqkgen:
  ; should we immediately advance to next direction?
  jn nextdir    ; a piece blocks

  ; initialize direction if needed
  mov A,F       ; enum_state
  inc A         ; overflow 99 to -100 
  jn initstate

  ; immediately advance direction if it's a king 
  mov D, #KINGTYPE
  mov A,B       ; piece_type
  sub A,D
  jz nextdir

  ; move one step in the current direction
takemove:
  mov A,F       ; enum_state
  ftlookup A,#DIRDELTA
  swap A,D      ; D=direction delta

  ; add the delta to the last square we enumerated, detect off board
  mov A,H     ; last_to
  add A,D
  jil nextdir ; try next direction if this move goes off board
  ret

  ; advance the enum_state
nextdir:
  ; get end index for this piece
  mov A,B       ; piecetype
  ftlookup A,#BRQK_STATE_END
  swap A,D      ; D=last valid enum_state + 1

  ; did we reach the end?
  mov A,F       ; enum_state
  sub A,D
  jn done       ; no more directions, no more moves

  ; no, advance enumeration state and try again
  mov A,F       ; enum_state
  inc A         ; try next direction
  swap A,F      ; save modified enum_state
  jmp takemove

; set start direction (enum_state) depending on piece type
initstate:
  mov A,B       ; piecetype
  ftlookup A,#BRQK_STATE_START
  swap A,F
  jmp takemove

done:
  ret         ; A=-1 signaling no more moves

