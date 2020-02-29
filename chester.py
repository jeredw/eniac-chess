#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Model for ENIAC chess program.

This is a hacky prototype of a search program for the ENIAC chess VM.
TODO(jered):
- Write a short, high-level version of the logic to validate the algorthm.
- Split into parts with traceable inputs and outputs for cross-validation with
  an assembly implementation.
"""

# machine model
# - 78 two digit words
M = [0 for _ in range(78)]
# 0 reserved
white_pawn_1   = 1
white_pawn_2   = 2
white_pawn_3   = 3
white_pawn_4   = 4
white_pawn_5   = 5
white_pawn_6   = 6
white_pawn_7   = 7
white_pawn_8   = 8
white_rook_1   = 9
white_knight_1 = 10
white_bishop_1 = 11
white_queen    = 12
white_king     = 13
white_bishop_2 = 14
white_knight_2 = 15
white_rook_2   = 16
min_white_piece_index = white_pawn_1
max_white_piece_index = white_rook_2
# 17 reserved
# 18 reserved
# 19 reserved
# 20 reserved
black_pawn_1   = 21
black_pawn_2   = 22
black_pawn_3   = 23
black_pawn_4   = 24
black_pawn_5   = 25
black_pawn_6   = 26
black_pawn_7   = 27
black_pawn_8   = 28
black_rook_1   = 29
black_knight_1 = 30
black_bishop_1 = 31
black_queen    = 32
black_king     = 33
black_bishop_2 = 34
black_knight_2 = 35
black_rook_2   = 36
min_black_piece_index = black_pawn_1
max_black_piece_index = black_rook_2
# 37 reserved
# 38 reserved
board_value = 39
move_piece_index = 40
move_original_position = 41
move_new_position = 42
move_captured_piece_index = 43
move_enumeration_state = 44
best_board_value = 45
# 46-75 reserved for move stack
move_stack_start = 46
move_stack_end = 75
best_move_piece_index = 76
best_move_new_position = 77

# board (32 words + 4? for queens)
# - 32 words, one per piece. tens' digit is y and ones' digit is x coordinate
# - location 0 isn't used so that 0 may be used as an "invalid" piece index
# - first digit of piece index is 0/1 for white and 2/3 for black
# - position 00 means that piece is captured
# - initial state
# -- assume stored in function tables
# -- maybe eventually make it load from punch card instead
# -- should include a board value
def encode_position(x, y):
  return x*10 + y

def decode_position(value):
  return (value // 10, value % 10)

def white(index):
  return index < 20

def init_board():
  global M
  M[white_rook_1]   = encode_position(1, 1)
  M[white_knight_1] = encode_position(2, 1)
  M[white_bishop_1] = encode_position(3, 1)
  M[white_queen]    = encode_position(4, 1)
  M[white_king]     = encode_position(5, 1)
  M[white_bishop_2] = encode_position(6, 1)
  M[white_knight_2] = encode_position(7, 1)
  M[white_rook_2]   = encode_position(8, 1)
  M[white_pawn_1]   = encode_position(1, 2)
  M[white_pawn_2]   = encode_position(2, 2)
  M[white_pawn_3]   = encode_position(3, 2)
  M[white_pawn_4]   = encode_position(4, 2)
  M[white_pawn_5]   = encode_position(5, 2)
  M[white_pawn_6]   = encode_position(6, 2)
  M[white_pawn_7]   = encode_position(7, 2)
  M[white_pawn_8]   = encode_position(8, 2)
  M[black_pawn_1]   = encode_position(1, 7)
  M[black_pawn_2]   = encode_position(2, 7)
  M[black_pawn_3]   = encode_position(3, 7)
  M[black_pawn_4]   = encode_position(4, 7)
  M[black_pawn_5]   = encode_position(5, 7)
  M[black_pawn_6]   = encode_position(6, 7)
  M[black_pawn_7]   = encode_position(7, 7)
  M[black_pawn_8]   = encode_position(8, 7)
  M[black_rook_1]   = encode_position(1, 8)
  M[black_knight_1] = encode_position(2, 8)
  M[black_bishop_1] = encode_position(3, 8)
  M[black_queen]    = encode_position(4, 8)
  M[black_king]     = encode_position(5, 8)
  M[black_bishop_2] = encode_position(6, 8)
  M[black_knight_2] = encode_position(7, 8)
  M[black_rook_2]   = encode_position(8, 8)

def print_board():
  print('  A B C D E F G H ')
  pieces = ((white_pawn_1, '♙'), (white_pawn_2, '♙'), (white_pawn_3, '♙'), (white_pawn_4, '♙'), (white_pawn_5, '♙'), (white_pawn_6, '♙'), (white_pawn_7, '♙'), (white_pawn_8, '♙'),
            (white_rook_1, '♖'), (white_knight_1, '♘'), (white_bishop_1, '♗'), (white_queen, '♕'), (white_king, '♔'), (white_bishop_2, '♗'), (white_knight_2, '♘'), (white_rook_2, '♖'),
            (black_pawn_1, '♟'), (black_pawn_2, '♟'), (black_pawn_3, '♟'), (black_pawn_4, '♟'), (black_pawn_5, '♟'), (black_pawn_6, '♟'), (black_pawn_7, '♟'), (black_pawn_8, '♟'),
            (black_rook_1, '♜'), (black_knight_1, '♞'), (black_bishop_1, '♝'), (black_queen, '♛'), (black_king, '♚'), (black_bishop_2, '♝'), (black_knight_2, '♞'), (black_rook_2, '♜'))
  for y in range(8, 1 - 1, -1):
    line = [str(y) + ' ']
    for x in range(1, 8 + 1):
      for (index, char) in pieces:
        if M[index] == encode_position(x, y):
          line.append(char + ' ')
          break
      else:
        line.append('. ')
    print(''.join(line))
  print('value: {}'.format(M[board_value]))
  print('')

# move (4-5 words? x 4-ply x 2 = 40 words)
# - piece index to move (1 word)
# - original position (1 word)
# - new position (1 word)
# - captured piece index (1 word)
# - enumeration state for move generator (1 word)
# board value (1 word)
# - value = a*(white pawns - black pawns)
#           b*(white rooks - black rooks)
#           c*(white bishops - black bishops)
#           d*(white knights - black knights)
#           e*(white queens - black queens)
# - consider clamping at 50 so it fits in 2-digit 10s complement
# - update incrementally when applying moves
def capture_value(index):
  return (-1 if white_pawn_1 <= index <= white_pawn_8 else
          -3 if (white_bishop_1 == index or white_bishop_2 == index) else
          -3 if (white_knight_1 == index or white_knight_2 == index) else
          -5 if (white_rook_1 == index or white_rook_2 == index) else
          -9 if white_queen == index else
          +1 if black_pawn_1 <= index <= black_pawn_8 else
          +3 if (black_bishop_1 == index or black_bishop_2 == index) else
          +3 if (black_knight_1 == index or black_knight_2 == index) else
          +5 if (black_rook_1 == index or black_rook_2 == index) else
          +9 if black_queen == index else
          0)

def apply_move():
  global M
  M[M[move_piece_index]] = M[move_new_position]
  captured_piece = M[move_captured_piece_index]
  if captured_piece != 0:
    M[captured_piece] = 0
    M[board_value] += capture_value(captured_piece)

def unapply_move():
  global M
  M[M[move_piece_index]] = M[move_original_position]
  captured_piece = M[move_captured_piece_index]
  if captured_piece != 0:
    M[captured_piece] = M[move_new_position]
    M[board_value] -= capture_value(captured_piece)

def print_move():
  if M[move_piece_index] == 0:
    print('move (nil)')
    return
  print('move index:{} from:{} to:{} capturing:{} state:{}'.format(
      M[move_piece_index],
      decode_position(M[move_original_position]),
      decode_position(M[move_new_position]),
      M[move_captured_piece_index],
      M[move_enumeration_state]))

# move generation (1-2 words)
# option 2
# - iterator which takes (move, board_state) -> move'
# -- series of if statements that update state vector
# option 1
# - coroutine with separate code per piece to move
# -- retain coroutine pc as "enumeration state"
# - generate next move into a fixed location, then yield
# - entry points at first piece type for each color;
#   return/stop after last piece type per color.

# an initial piece index of 0 means white to move
#                           20 means black to move
# return with piece index 0 means no moves remain
def generate_next_move():
  global M
  while True:
    if M[move_enumeration_state] == 0:  # next piece
      M[move_piece_index] = (min_white_piece_index if M[move_piece_index] == 0 else
                             min_black_piece_index if M[move_piece_index] == 20 else
                             0                     if M[move_piece_index] == max_white_piece_index else
                             0                     if M[move_piece_index] == max_black_piece_index else
                             M[move_piece_index] + 1)
      if M[move_piece_index] == 0: return
      if M[M[move_piece_index]] == 0:  # captured, try the next piece
        continue
      # start at enumeration state 1, from/to current position
      M[move_enumeration_state] = 1
      M[move_original_position] = M[M[move_piece_index]]
      M[move_new_position]      = M[M[move_piece_index]]
      M[move_captured_piece_index] = 0

    # the previous move collided with a piece
    # reset new_position
    if M[move_captured_piece_index] != 0:
      M[move_new_position] = M[move_original_position]
 
    # generate the next possible position to move to
    (x, y)         = decode_position(M[M[move_piece_index]])
    (new_x, new_y) = decode_position(M[move_new_position])
 
    if white_pawn_1 <= M[move_piece_index] <= white_pawn_8:
      # push 1/maybe push 2, capture -x, capture +x
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(x, new_y + 1)
        if y == 2 and new_y != 4: pass
        elif y != new_y:
          M[move_enumeration_state] += 1
          continue
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(x - 1, y + 1)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(x + 1, y + 1)
      elif M[move_enumeration_state] == 4:
        M[move_enumeration_state] = 0
        continue

    elif black_pawn_1 <= M[move_piece_index] <= black_pawn_8:
      # push 1/maybe push 2, capture -x, capture +x
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(x, new_y - 1)
        if y == 7 and new_y != 5: pass
        elif y != new_y:
          M[move_enumeration_state] += 1
          continue
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(x - 1, y - 1)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(x + 1, y - 1)
      elif M[move_enumeration_state] == 4:
        M[move_enumeration_state] = 0
        continue

    elif (white_rook_1 == M[move_piece_index] or white_rook_2 == M[move_piece_index] or
          black_rook_1 == M[move_piece_index] or black_rook_2 == M[move_piece_index]):
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(new_x, new_y - 1)
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(new_x, new_y + 1)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(new_x - 1, new_y)
      elif M[move_enumeration_state] == 4:
        M[move_new_position] = encode_position(new_x + 1, new_y)
      elif M[move_enumeration_state] == 5:
        M[move_enumeration_state] = 0
        continue

    elif (white_knight_1 == M[move_piece_index] or white_knight_2 == M[move_piece_index] or
          black_knight_1 == M[move_piece_index] or black_knight_2 == M[move_piece_index]):
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(x - 1, y - 2)
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(x - 1, y + 2)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(x + 1, y - 2)
      elif M[move_enumeration_state] == 4:
        M[move_new_position] = encode_position(x + 1, y + 2)
      elif M[move_enumeration_state] == 5:
        M[move_new_position] = encode_position(x - 2, y - 1)
      elif M[move_enumeration_state] == 6:
        M[move_new_position] = encode_position(x - 2, y + 1)
      elif M[move_enumeration_state] == 7:
        M[move_new_position] = encode_position(x + 2, y - 1)
      elif M[move_enumeration_state] == 8:
        M[move_new_position] = encode_position(x + 2, y + 1)
      elif M[move_enumeration_state] == 9:
        M[move_enumeration_state] = 0
        continue

    elif (white_bishop_1 == M[move_piece_index] or white_bishop_2 == M[move_piece_index] or
          black_bishop_1 == M[move_piece_index] or black_bishop_2 == M[move_piece_index]):
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(new_x - 1, new_y - 1)
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(new_x - 1, new_y + 1)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(new_x + 1, new_y - 1)
      elif M[move_enumeration_state] == 4:
        M[move_new_position] = encode_position(new_x + 1, new_y + 1)
      elif M[move_enumeration_state] == 5:
        M[move_enumeration_state] = 0
        continue

    elif white_queen == M[move_piece_index] or black_queen == M[move_piece_index]:
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(new_x - 1, new_y - 1)
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(new_x - 1, new_y)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(new_x - 1, new_y + 1)
      elif M[move_enumeration_state] == 4:
        M[move_new_position] = encode_position(new_x, new_y - 1)
      elif M[move_enumeration_state] == 5:
        M[move_new_position] = encode_position(new_x, new_y + 1)
      elif M[move_enumeration_state] == 6:
        M[move_new_position] = encode_position(new_x + 1, new_y - 1)
      elif M[move_enumeration_state] == 7:
        M[move_new_position] = encode_position(new_x + 1, new_y)
      elif M[move_enumeration_state] == 8:
        M[move_new_position] = encode_position(new_x + 1, new_y + 1)
      elif M[move_enumeration_state] == 9:
        M[move_enumeration_state] = 0
        continue

    elif white_king == M[move_piece_index] or black_king == M[move_piece_index]:
      # NOTE the king and queen could share logic if we reset the king's position
      # properly between enumeration states.  that could be done by introducing
      # a "fake capture" notion of some sort?
      if M[move_enumeration_state] == 1:
        M[move_new_position] = encode_position(x - 1, y - 1)
      elif M[move_enumeration_state] == 2:
        M[move_new_position] = encode_position(x - 1, y)
      elif M[move_enumeration_state] == 3:
        M[move_new_position] = encode_position(x - 1, y + 1)
      elif M[move_enumeration_state] == 4:
        M[move_new_position] = encode_position(x, y - 1)
      elif M[move_enumeration_state] == 5:
        M[move_new_position] = encode_position(x, y + 1)
      elif M[move_enumeration_state] == 6:
        M[move_new_position] = encode_position(x + 1, y - 1)
      elif M[move_enumeration_state] == 7:
        M[move_new_position] = encode_position(x + 1, y)
      elif M[move_enumeration_state] == 8:
        M[move_new_position] = encode_position(x + 1, y + 1)
      elif M[move_enumeration_state] == 9:
        M[move_enumeration_state] = 0
        continue
 
    # if the new position is off the board, time to consider next state
    (new_x, new_y) = decode_position(M[move_new_position])
    if new_x == 0 or new_x == 9 or new_y == 0 or new_y == 9:
      M[move_enumeration_state] += 1
      M[move_new_position] = M[move_original_position]
      continue

    # look at whats there i.e. get_board_at(position)
    M[move_captured_piece_index] = 0
    for i in range(min_white_piece_index, max_white_piece_index + 1):
      if M[i] == M[move_new_position]:
        M[move_captured_piece_index] = i
        break
    for i in range(min_black_piece_index, max_black_piece_index + 1):
      if M[i] == M[move_new_position]:
        M[move_captured_piece_index] = i
        break

    # special case pawn captures
    if (white_pawn_1 <= M[move_piece_index] <= white_pawn_8 or 
        black_pawn_1 <= M[move_piece_index] <= black_pawn_8):
      captured = M[move_captured_piece_index] != 0
      moving_to_capture = M[move_enumeration_state] >= 2
      if captured != moving_to_capture:
        # can't capture straight ahead; and if moving to capture, must capture something.
        M[move_enumeration_state] += 1
        continue
 
    if M[move_captured_piece_index] != 0:
      # hit something -> next enumeration state for next move
      M[move_enumeration_state] += 1
      # skip this move if the piece here is same color
      if white(M[move_piece_index]) == white(M[move_captured_piece_index]):
        continue
    else:
      # knights and kings always advance enumeration_state
      # even if they didn't hit anything
      if (white_king == M[move_piece_index] or black_king == M[move_piece_index] or 
          white_knight_1 == M[move_piece_index] or white_knight_2 == M[move_piece_index] or
          black_knight_1 == M[move_piece_index] or black_knight_2 == M[move_piece_index]):
        M[move_enumeration_state] += 1
 
    # we have a valid move to try
    break

# - piece index to move (1 word)
# - original position (1 word)
# - new position (1 word)
# - captured piece index (1 word)
# - enumeration state for move generator (1 word)

# game rules
# - yes double pawn push
# - no castling
# - no en passant capture
# - intitially leave out promotion, possible plan to add:
# -- only support queen promotion,
# -- a few extra queen slots per side
# - no 50-move rule
# - no stalemate

# best value (1 word), best move found (2 words: piece index, board value)
move_stack_pointer = move_stack_start  # use reg for this?

def push_move():
  global M
  global move_stack_pointer
  M[move_stack_pointer + 0] = M[move_piece_index]
  M[move_stack_pointer + 1] = M[move_original_position]
  M[move_stack_pointer + 2] = M[move_new_position]
  M[move_stack_pointer + 3] = M[move_captured_piece_index]
  M[move_stack_pointer + 4] = M[move_enumeration_state]
  M[move_stack_pointer + 5] = M[best_board_value]
  move_stack_pointer += 6
  assert move_stack_pointer <= move_stack_end

def pop_move():
  global M
  global move_stack_pointer
  move_stack_pointer -= 6
  assert move_stack_pointer >= move_stack_start
  M[move_piece_index]          = M[move_stack_pointer + 0]
  M[move_original_position]    = M[move_stack_pointer + 1]
  M[move_new_position]         = M[move_stack_pointer + 2]
  M[move_captured_piece_index] = M[move_stack_pointer + 3]
  M[move_enumeration_state]    = M[move_stack_pointer + 4]
  M[best_board_value]          = M[move_stack_pointer + 5]

def print_search_state(depth):
  print('D={} cur={} best={}'.format(depth, M[board_value], M[best_board_value]))
  print_move()

# negamax search
def find_best_move(max_depth=2):
  neg_infinity = -49
  M[best_board_value] = neg_infinity
  M[best_move_piece_index] = 0
  M[best_move_new_position] = 0
  depth = 0
  while True:
    generate_next_move()
    #print_search_state(depth)
    if M[move_piece_index] == 0:
      # done exploring moves at this depth
      if depth == 0: break
      score = -M[best_board_value]
      pop_move()
      unapply_move()
      depth -= 1
      if score >= M[best_board_value]:
        M[best_board_value] = score
        if depth == 0:
          M[best_move_piece_index] = M[move_piece_index]
          M[best_move_new_position] = M[move_new_position]
      continue

    apply_move()
    if depth == max_depth:
      # i.e. -negamax(0)
      score = M[board_value]
      if not white(M[move_piece_index]):
        score = -score
      if score > M[best_board_value]:
        M[best_board_value] = score
      unapply_move()
      continue

    # recurse
    push_move()
    M[move_enumeration_state] = 0
    if white(M[move_piece_index]):
      M[move_piece_index] = 20
    else:
      M[move_piece_index] = 0
    M[best_board_value] = neg_infinity
    depth += 1
    continue

def notate_move(piece, from_pos, to_pos, capture):
  name = ('B' if piece in (white_bishop_1, white_bishop_2, black_bishop_1, black_bishop_2) else
          'N' if piece in (white_knight_1, white_knight_2, black_knight_1, black_knight_2) else
          'R' if piece in (white_rook_1, white_rook_2, black_rook_1, black_rook_2) else
          'K' if piece in (white_king, black_king) else
          'Q' if piece in (white_queen, black_queen) else '')
  disambig = ''
  from_x, from_y = from_pos
  dest = ' abcdefgh'[from_x] + str(from_y)
  return '{}{}{}{}'.format(name, disambig, ('x' if capture else ''), dest)

def print_best_move():
  print('best:{} piece:{} to:{}'.format(M[best_board_value],
                                        M[best_move_piece_index],
                                        decode_position(M[best_move_new_position])))

#init_board()
#M[white_queen] = encode_position(4, 4)
#M[black_queen] = encode_position(4, 3)
#M[black_pawn_3] = encode_position(3, 3)
#M[white_pawn_1] = encode_position(1, 6)

init_board()
find_best_move(max_depth=4)
print_best_move()

#
#print('move (the initial state)')
#print_board()
#while True:
#  generate_next_move()
#  if M[move_piece_index] == 0:
#    break
#  print_move()
#  apply_move()
#  print_board()
#  unapply_move()