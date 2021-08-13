#!/usr/bin/env python
from subprocess import run, PIPE, Popen
import signal
import time

run('python chasm/chasm.py asm/tic.asm tic.e', shell=True, check=True)
run('python easm/easm.py -ETIC chessvm/chessvm.easm chessvm.e', shell=True, check=True)
sim = Popen('./eniacsim -q chessvm.e', shell=True, stdin=PIPE, stdout=PIPE)

sim.stdin.write('g\n'.encode())
sim.stdin.flush()
# sim prints board initially
line1 = sim.stdout.readline().decode() 
line2 = sim.stdout.readline().decode() 
line3 = sim.stdout.readline().decode() 
winner = sim.stdout.readline().decode()
print(line1 + line2 + line3)

while True:
  # waiting for a card now for human move
  text = input('square 1-9?')
  square = int(text)
  with open('/tmp/tic.card', 'w') as f:
    f.write(f'{square:02}000' + ' '*75)
  sim.send_signal(signal.SIGINT)
  sim.stdin.write('f r /tmp/tic.card\n'.encode())
  sim.stdin.write('g\n'.encode())
  sim.stdin.flush()
  # sim prints board again after human moves
  line1 = sim.stdout.readline().decode() 
  line2 = sim.stdout.readline().decode() 
  line3 = sim.stdout.readline().decode() 
  winner = sim.stdout.readline().decode()
  print(line1 + line2 + line3)
  if winner[0] != '0': break
  # sim will print board again after it moves
  line1 = sim.stdout.readline().decode() 
  line2 = sim.stdout.readline().decode() 
  line3 = sim.stdout.readline().decode() 
  winner = sim.stdout.readline().decode()
  print(line1 + line2 + line3)
  if winner[0] != '0': break

if winner[0] == '1':
  print("eniac wins")
elif winner[0] == '2':
  print("you win")
elif winner[0] == '3':
  print("draw")
