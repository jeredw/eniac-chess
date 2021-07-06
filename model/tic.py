#!/usr/bin/env python
# Simple model for eniac-tac-toe program

print('eniac-tac-toe model')
print('squares are 1-9 from top to bottom, left to right')

board = [0 for _ in range(9)]
stack = [[0, 0, 0, 0, 'unused'] for _ in range(10)]

NO_MOVE = 0

def isdraw(b):
  return all(sq != 0 for sq in b)

def iswin(b, player=1):
  if (b[0] == b[1] == b[2] == player or 
      b[3] == b[4] == b[5] == player or 
      b[6] == b[7] == b[8] == player):
    return True
  if (b[0] == b[3] == b[6] == player or
      b[1] == b[4] == b[7] == player or
      b[2] == b[5] == b[8] == player):
    return True
  if (b[0] == b[4] == b[8] == player or
      b[2] == b[4] == b[6] == player):
    return True
  return False

def print_board(b):
  print(f'{b[0]}|{b[1]}|{b[2]}')
  print(f'-+-+-')
  print(f'{b[3]}|{b[4]}|{b[5]}')
  print(f'-+-+-')
  print(f'{b[6]}|{b[7]}|{b[8]}')

# eniac goes first and plays an X in the center (because searching to determine
# where to play first searches the entire game, which is a lot of nodes)
board[4] = 1
print_board(board)
print()

while True:
  # human plays o
  o_move = input('move?')
  o_move_pos = int(o_move)
  assert board[o_move_pos-1] == 0
  board[o_move_pos-1] = 2
  print_board(board)
  print()
  if iswin(board, player=2):
    print('you win')
    break
  if isdraw(board):
    print('draw')
    break

  # eniac to move
  # stack layout
  # 0: 1   # player: 1=X, 2=O
  # 1: 0   # last_move: 1-9 = last move tried, 0 = none yet
  # 2: 48  # best_score: 49 = lose, 50 = draw, 51 = win
  # 3: 0   # best_move: 1-9 = square with best value, 0 = none
  # 4: depth
  # 5: comment
  stack[0] = [1, NO_MOVE, 48, NO_MOVE, 1, 'start']
  i = 1
  k = 0
  max_i = i
  while i > 0:
    k += 1
    i -= 1
    (player, last_move, best_score, best_move, depth, comment) = stack[i]
    if last_move == NO_MOVE:
      # Begin search at new depth
      if iswin(board, player=1):
        stack[i][2] = 51
        continue
      elif iswin(board, player=2):
        stack[i][2] = 49
        continue
      elif isdraw(board):
        stack[i][2] = 50
        continue
      last_move = 9
    else:
      # Iterate over moves at current depth
      board[last_move-1] = 0
      # The "previous" stack frame will have the best recursive move score
      value = stack[i+1][2]
      assert value != 0
      if player == 1:
        if value > best_score:
          best_move = last_move
          best_score = value
      else:
        if value < best_score:
          best_move = last_move
          best_score = value
      # Update ours
      stack[i][2] = best_score
      stack[i][3] = best_move
      # Now try the next move.
      last_move -= 1
    while last_move > 0:
      if board[last_move-1] != 0:
        last_move -= 1
      else:
        break
    if last_move == 0:
      continue
    board[last_move-1] = player
    stack[i] = [player, last_move, best_score, best_move, depth,
                f'iter player={player} move={last_move} best={best_move} ({best_score})']
    i += 1
    if player == 1:
      other_player = 2
      other_best_score = 52
    else:
      other_player = 1
      other_best_score = 48
    stack[i] = [other_player, NO_MOVE, other_best_score, NO_MOVE, depth + 1,
                f'recurse player={other_player} best=0 ({other_best_score})']
    i += 1
    max_i = max(i, max_i)

  # place an X at the final "best_move" position
  print(f'eniac move:{stack[0][3]} ({k} {max_i})')
  board[stack[0][3]-1] = 1
  print_board(board)
  if iswin(board, player=1):
    print('eniac wins')
    break
  if isdraw(board):
    print('draw')
    break
