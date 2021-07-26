#!/usr/bin/env python3
# Prototype for ENIAC connect four program
#
# This is a really simple algorithm based on a few hobbyist programs, but does
# prove out a plausible path for depth cutoff search with a heuristic function
# and alpha beta pruning.  It does ok in casual play with a human novice.
#
# The board is stored as a 6x7 matrix using 42 words, leaving 33 words for
# temps and search.  Since stack frames take 5 words, this permits only a 6
# level search.
#
# Storing the board as a 6x7 digit matrix instead would use 21 words, leaving
# 54 words for search (in practice we'd probably consume 6x8 digits to keep
# column alignment), in theory making a 10 level search possible.  But the
# packed code is much messier, and board evaluation is likely going to be slow
# enough that depth > 5 is questionable... maybe v2.

# The game board is a 6x7 matrix with 0=open, 1=player 1, 2=player 2.
board = [0 for _ in range(6 * 7)]

# One extra word records which player wins in the current position, if any
# 0=no winner, 1=player 1, 2=player 2, 3=draw
winner = 0

# Reserve 6 accs for stack
stack = [[0, 0, 0, 0, 0] for _ in range(6)]

# Count of memory acesses
debug_mems = 0

def print_board():
  for y in range(6):
    for x in range(7):
      print(board[7 * y + x], end='')
    print()

def read_board(offset):
  global debug_mems
  debug_mems += 1
  return board[offset]

def move(column, player):
  """Play a piece for player in column 1-7, which must have room."""
  offset = column - 1
  assert board[offset] == 0
  while True:
    next_offset = offset + 7
    if next_offset >= 42: break
    if read_board(next_offset) != 0: break
    offset = next_offset
  board[offset] = player
  global debug_mems
  debug_mems += 1
  # The piece just placed may have resulted in a win for player
  return update_winner(column, offset, player)  # tail call

# Table mapping offset to start of row at that offset (42 words)
start_of_row = [7 * (i // 7) for i in range(42)]

def update_winner(move_column, move_offset, player):
  """Update current winner after player moves in column."""
  # Scanning the board to find runs of 4 pieces is expensive - there are 25
  # groups to check via 144 loads, ~1s!  For just telling if someone has won,
  # it's way more efficient to scan around the last placed piece.
  # XXX We have to examine the whole board anyways for the search heuristic, so
  # maybe we could avoid having this incremental scan with the right logic
  # there?  For now we still need it.

  # Assume no winner
  global winner
  winner = 0

  # Check move column for win
  offset = move_column - 1
  run_length = 0
  while offset < 42:
    if read_board(offset) == player: run_length += 1
    else: run_length = 0
    if run_length == 4:
      winner = player
      return
    offset += 7

  # Check move row for win
  # NOTE This could use a binary search instead of a table if table space is tight
  offset = start_of_row[move_offset]
  run_length = 0
  for _ in range(7):
    if read_board(offset) == player: run_length += 1
    else: run_length = 0
    if run_length == 4:
      winner = player
      return
    offset += 1

  # Check \ diagonal for win
  # Rewind to upper left of diagonal
  offset = move_offset
  column = move_column
  while True:
    prev_offset = offset - 8
    if column == 1 or prev_offset < 0: break
    column -= 1
    offset = prev_offset

  # Scan down diagonal
  run_length = 0
  while column <= 7 and offset < 42:
    if read_board(offset) == player: run_length += 1
    else: run_length = 0
    if run_length == 4:
      winner = player
      return
    column += 1
    offset += 8

  # Check / diagonal for win
  # Rewind to upper right of diagonal
  offset = move_offset
  column = move_column
  while True:
    prev_offset = offset - 6
    if column == 7 or prev_offset < 0: break
    column += 1
    offset = prev_offset

  # Scan down diagonal
  run_length = 0
  while column >= 1 and offset < 42:
    if read_board(offset) == player: run_length += 1
    else: run_length = 0
    if run_length == 4:
      winner = player
      return
    column -= 1
    offset += 6

  # If move was in top row, check for draw (after any possible wins)
  if move_offset < 7:
    for i in range(7):
      if read_board(i) == 0:
        return
    winner = 3
    return

def undo_move(column):
  """Undo the last move in column, which must not be empty."""
  offset = column - 1
  while True:
    data = read_board(offset)
    if data != 0:
      board[offset] = 0
      global debug_mems
      debug_mems += 1
      break
    offset += 7
    assert offset < 42
  # Search stops at the first winning move, so undoing the last move always
  # clears any wins.
  global winner
  winner = 0

# Topmost offsets for \ diagonals
right_diagonal_starts = [14, 7, 0, 1, 2, 3]

# Topmost offsets for / diagonals
left_diagonal_starts = [20, 13, 6, 5, 4, 3]

# There are way more reward terms than penalty terms in this heuristic, so we
# need a bit more + range.
zero_score = 30

# In practice this is only called from one place, and only with player=1 So
# very likely this will be part of the top level loop and some of the common
# sequences here can be factored out into subs...
def score(player):
  """Score the current board for player."""
  # Based on https://github.com/KeithGalli/Connect4-Python
  #
  # This rewards playing in the center column and having long runs with empty
  # squares, and penalizes positions where the opponent has three in a row.  It
  # has some questionable behavior, like double counting [ooo-]- (+5) and
  # o[oo--] (+2).  It lacks an explicit penalty for [xxxx] (opponent win),
  # though this shouldn't be necessary by symmetry.
  #
  # TODO Benchmark this against some other options.
  total = zero_score

  # Compute center column bonus (3x count in center column)
  # XXX This term seems large
  if read_board(3) == player: total += 3
  if read_board(10) == player: total += 3
  if read_board(17) == player: total += 3
  if read_board(24) == player: total += 3
  if read_board(31) == player: total += 3
  if read_board(38) == player: total += 3

  # Count horizontal runs
  offset = 0
  while offset < 42:
    count_empty = 0
    count_player = 0
    count_opponent = 0
    for i in range(7):
      if i > 3: 
        data = read_board(offset-4)
        if data == 0: count_empty -= 1
        elif data == 1 and player == 1: count_player -= 1
        elif data == 1 and player == 2: count_opponent -= 1
        elif data == 2 and player == 1: count_opponent -= 1
        elif data == 2 and player == 2: count_player -= 1
      data = read_board(offset)
      if data == 0: count_empty += 1
      elif data == 1 and player == 1: count_player += 1
      elif data == 1 and player == 2: count_opponent += 1
      elif data == 2 and player == 1: count_opponent += 1
      elif data == 2 and player == 2: count_player += 1
      if i >= 3: 
        if count_player == 4: return 99
        elif count_player == 3 and count_empty == 1: total += 5
        elif count_player == 2 and count_empty == 2: total += 2
        elif count_opponent == 3 and count_empty == 1: total -= 4
      offset += 1
      i += 1

  # Count vertical runs
  for column in range(7):
    offset = column
    count_empty = 0
    count_player = 0
    count_opponent = 0
    for i in range(6):
      if i > 3:
        data = read_board(offset-4*7)
        if data == 0: count_empty -= 1
        elif data == 1 and player == 1: count_player -= 1
        elif data == 1 and player == 2: count_opponent -= 1
        elif data == 2 and player == 1: count_opponent -= 1
        elif data == 2 and player == 2: count_player -= 1
      data = read_board(offset)
      if data == 0: count_empty += 1
      elif data == 1 and player == 1: count_player += 1
      elif data == 1 and player == 2: count_opponent += 1
      elif data == 2 and player == 1: count_opponent += 1
      elif data == 2 and player == 2: count_player += 1
      if i >= 3:
        if count_player == 4: return 99
        elif count_player == 3 and count_empty == 1: total += 5
        elif count_player == 2 and count_empty == 2: total += 2
        elif count_opponent == 3 and count_empty == 1: total -= 4
      offset += 7
      i += 1

  # Count \ diagonal runs
  for j in range(6):
    offset = right_diagonal_starts[j]
    x = offset
    if x >= 7: x = 0
    count_empty = 0
    count_player = 0
    count_opponent = 0
    for i in range(6):
      if i > 3: 
        data = read_board(offset-4*8)
        if data == 0: count_empty -= 1
        elif data == 1 and player == 1: count_player -= 1
        elif data == 1 and player == 2: count_opponent -= 1
        elif data == 2 and player == 1: count_opponent -= 1
        elif data == 2 and player == 2: count_player -= 1
      data = read_board(offset)
      if data == 0: count_empty += 1
      elif data == 1 and player == 1: count_player += 1
      elif data == 1 and player == 2: count_opponent += 1
      elif data == 2 and player == 1: count_opponent += 1
      elif data == 2 and player == 2: count_player += 1
      if i >= 3:
        if count_player == 4: return 99
        elif count_player == 3 and count_empty == 1: total += 5
        elif count_player == 2 and count_empty == 2: total += 2
        elif count_opponent == 3 and count_empty == 1: total -= 4
      offset += 8
      i += 1
      x += 1
      if offset > 42 or x > 6: break

  # Count / diagonal runs
  for j in range(6):
    offset = left_diagonal_starts[j]
    x = offset
    if x >= 7: x = 6
    count_empty = 0
    count_player = 0
    count_opponent = 0
    for i in range(6):
      if i > 3: 
        data = read_board(offset-4*6)
        if data == 0: count_empty -= 1
        elif data == 1 and player == 1: count_player -= 1
        elif data == 1 and player == 2: count_opponent -= 1
        elif data == 2 and player == 1: count_opponent -= 1
        elif data == 2 and player == 2: count_player -= 1
      data = read_board(offset)
      if data == 0: count_empty += 1
      elif data == 1 and player == 1: count_player += 1
      elif data == 1 and player == 2: count_opponent += 1
      elif data == 2 and player == 1: count_opponent += 1
      elif data == 2 and player == 2: count_player += 1
      if i >= 3:
        if count_player == 4: return 99
        elif count_player == 3 and count_empty == 1: total += 5
        elif count_player == 2 and count_empty == 2: total += 2
        elif count_opponent == 3 and count_empty == 1: total -= 4
      offset += 6
      i += 1
      x -= 1
      if offset > 42 or x < 0: break

  #assert 0 <= total <= 99
  if not (0 <= total <= 99):
    print(f'!! score={total} out of range')
  return min(max(0, total), 99)

# Table mapping 0-27 to the tens digit (to extract player field from stack)
extract_player = [x // 10 for x in range(27 + 1)]

# Multiply 012 by 10
ten_times = [0, 10, 20]

def play_game():
  # eniac goes first and plays in the center column
  move(4, 1)
  print_board()

  while True:
    # human to move
    column = input('column (1-7)?')
    move(int(column), 2)
    print_board()
    if winner != 0:
      break

    # eniac to move
    # stack layout
    # 0: 10     # player|best_move: 1x=eniac, 2x=human
    #           #                   x1-x7=best move column, x0=none
    # 1: 0      # last_move: 1-7=last move column, 0=none
    # 2: 0      # best_score: 0
    # 3: 0      # alpha: 0
    # 4: 99     # beta: 99
    stack[0] = [10, 0, zero_score, 0, 99]
    sp = 1
    num_positions = 0
    max_sp = sp
    while sp > 0:
      num_positions += 1
      sp -= 1
      (player_and_best_move, last_move, best_score, alpha, beta) = stack[sp]
      player = extract_player[player_and_best_move]
      best_move = player_and_best_move
      if best_move >= 10: best_move -= 10
      if best_move >= 10: best_move -= 10
      if last_move == 0:
        # Possibly begin search at new depth
        if winner == 1:    # eniac won
          stack[sp][2] = 99
          continue
        elif winner == 2:  # human won
          stack[sp][2] = 0
          continue
        elif winner == 3:  # draw
          stack[sp][2] = zero_score
          continue
        if sp == 5:  # max search depth
          stack[sp][2] = score(1)
          continue
        # TODO search moves in a better order!
        last_move = 7
      else:
        # Iterate over moves at current depth
        undo_move(last_move)
        # The "previous" stack frame will have the best recursive move score
        value = stack[sp+1][2]
        if player == 1:
          if value > best_score:
            best_move = last_move
            best_score = value
          if value > alpha:
            alpha = value
        else:
          if value < best_score:
            best_move = last_move
            best_score = value
          if value < beta:
            beta = value
        # Update our stack frame
        stack[sp][0] = ten_times[player] + best_move
        stack[sp][2] = best_score
        stack[sp][3] = alpha
        stack[sp][4] = beta
        if alpha >= beta:
          # Can stop iterating
          continue
        # Now try the next move.
        last_move -= 1
      # TODO try moves in a better order!
      while last_move > 0:
        if read_board(last_move-1) != 0:
          last_move -= 1
        else:
          break
      if last_move == 0:
        continue
      move(last_move, player)
      stack[sp] = [ten_times[player] + best_move, last_move, best_score, alpha, beta]
      sp += 1
      if player == 1:
        other_player = 20
        other_best_score = 99
      else:
        other_player = 10
        other_best_score = 0
      stack[sp] = [other_player, 0, other_best_score, alpha, beta]
      sp += 1
      max_sp = max(sp, max_sp)

    # eniac plays at the final "best_move" position
    best_move = stack[0][0] - 10
    global debug_mems
    print(f'eniac move:{best_move} ({debug_mems} mems/{num_positions} positions, max depth {max_sp})')
    move(best_move, 1)
    debug_mems = 0
    print_board()
    if winner != 0:
      break

  if winner == 1:
    print('eniac wins')
  elif winner == 2:
    print('you win')
  elif winner == 3:
    print('draw')


if __name__ == "__main__":
  play_game()
