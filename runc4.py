#!/usr/bin/env python
from subprocess import run, PIPE, Popen
import signal
import time

def read_board(p):
  board = [0] * 42
  for _ in range(43):
    line = p.stdout.readline().decode()
    what, where = int(line[:2]), int(line[2:4])
    if what == 99: return board, where  # where is the winner
    assert 0 <= where <= 41
    assert what == 1 or what == 2
    board[where] = what
  assert False

def print_board(board):
  for y in range(0, 42, 7):
    print(''.join(str(n) for n in board[y:y+7]))
  print()

run('python chasm/chasm.py asm/c4.asm c4.e', shell=True, check=True)
run('python easm/easm.py chessvm/chessvm.easm chessvm.e', shell=True, check=True)
sim = Popen('./eniacsim -q -W chessvm.e', shell=True, stdin=PIPE, stdout=PIPE)

sim.stdin.write('g\n'.encode())
sim.stdin.flush()
# sim prints board initially
board, winner = read_board(sim)
print_board(board)

while winner == 0:
  # waiting for a card now for human move
  text = input('column 1-7?')
  column = int(text)
  with open('/tmp/c4.card', 'w') as f:
    f.write(f'{column:02}000' + ' '*75)
  sim.send_signal(signal.SIGINT)
  sim.stdin.write('f r /tmp/c4.card\n'.encode())
  sim.stdin.write('g\n'.encode())
  sim.stdin.flush()
  # sim prints board again after human moves
  board, winner = read_board(sim)
  print_board(board)
  if winner != 0: break
  # sim will print board again after it moves
  board, winner = read_board(sim)
  print_board(board)

sim.kill()

if winner == 1:
  print('eniac wins')
elif winner == 2:
  print('you win')
elif winner == 3:
  print('draw')
