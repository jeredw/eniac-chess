#!/usr/bin/env python
from game import Board, Position, ReferenceMoveGen, Square, Move, make_move
from subprocess import run, PIPE, Popen
import signal
import time

def init_memory(position):
  memory = [0] * 75
  piece_code = '??PNBQpnbq'
  rook = 0
  for square, piece in position.board:
    yx = square.y * 10 + square.x
    offset = ((square.y-1) * 8 + (square.x-1)) // 2
    shift = 10 if square.x % 2 == 1 else 1
    if piece in piece_code:
      code = piece_code.index(piece)
      memory[offset] += shift * code
    elif piece != '.':
      memory[offset] += shift * 1
      if piece == 'K':
        memory[32] = yx
      elif piece == 'k':
        memory[33] = yx
      elif piece == 'R' and rook == 0:
        memory[34] = yx
        rook += 1
      elif piece == 'R' and rook == 1:
        memory[45] = yx
        rook += 1
      else:
        assert piece == 'r'
  memory[55] = 50  # initial score
  memory[65] = 1   # initial stack depth
  memory[44] = 99  # beta
  # set up appropriately for black or white play
  memory[35] = 0 if position.to_move == 'w' else 10  # fromp
  memory[42] = 0 if position.to_move == 'w' else 99  # best_score
  return memory

def convert_memory_to_deck(memory):
  deck = []
  for address, data in enumerate(memory):
    # note we must explicitly reset unoccupied squares to zero, or pieces will
    # get incorrectly duplicated from before the player's move
    deck.append(f'{address:02}{data:02}0{" "*75}')
  deck.append(f'99000{" "*75}')
  return '\n'.join(deck)

def output_deck(deck):
  with open('/tmp/chess.deck', 'w') as f:
    f.write(deck)

def send_position_to_sim(sim, position):
  memory = init_memory(position)
  deck = convert_memory_to_deck(memory)
  output_deck(deck)
  sim.stdin.write('f r /tmp/chess.deck\n'.encode())
  sim.stdin.write('g\n'.encode())
  sim.stdin.flush()

def is_legal(position, move):
  for legal_move, _ in ReferenceMoveGen().legal_moves(position):
    if move == legal_move:
      return True
  return False

def print_board(position):
  print('  abcdefgh')
  for y, rank in enumerate(position.board.ranks):
    s = f'{8-y} '
    for p in rank:
      s += p
    print(s)

def do_eniac_move(position, raw_move):
  if len(raw_move) != 4:
    print(f'invalid sim output "{raw_move}"')
    return
  if raw_move == '0000':
    print('eniac resigns; you win')
    return
  move = Move(fro=Square(y=int(raw_move[0]), x=int(raw_move[1])),
              to=Square(y=int(raw_move[2]), x=int(raw_move[3])))
  if is_legal(position, move):
    print(f'eniac plays {move}')
  else:
    print(f'oops. eniac resigns by illegal move {move}. you win')
    return
  return make_move(position, move)

def do_human_move(position):
  move = None
  while not move:
    raw_move = input('your move?')
    if len(raw_move) != 4:
      print('please use long algebraic notation e.g. e2e4')
      continue
    if raw_move == '0000':
      print('you resign, eniac wins')
      return
    try:
      move = Move.lan(raw_move)
    except:
      print('please use long algebraic notation e.g. e2e4')
      continue
    if not is_legal(position, move):
      print(f'oops. {move} is illegal, please try again')
      move = None
      continue
    return make_move(position, move)

position = Position.initial()

run('python chasm/chasm.py asm/chess.asm chess.e', shell=True, check=True)
run('python easm/easm.py -ECHESS chessvm/chessvm.easm chessvm.e', shell=True, check=True)
run('make -C chsim lib', shell=True, check=True)
sim = Popen('./eniacsim -q -W vis -v chsim/vm.so chessvm.e', shell=True, stdin=PIPE, stdout=PIPE)

human_color = ''
while not human_color:
  human_color = input('do you want b or w pieces?')
  if human_color not in 'bw':
    print('please enter b or w')
    continue
  break

if human_color == 'w':
  print_board(position)
  position = do_human_move(position)

send_position_to_sim(sim, position)

while True:
  print_board(position)

  # wait for eniac's move
  print('ENIAC is thinking...')
  raw_move = sim.stdout.readline().decode().strip()
  position = do_eniac_move(position, raw_move)
  if not position: break

  print_board(position)
  position = do_human_move(position)

  # tell the simulator about the new board state
  sim.send_signal(signal.SIGINT)
  send_position_to_sim(sim, position)

sim.kill()
