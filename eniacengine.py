import math

from uciengine import UCIEngine
from game import Board, Position, ReferenceMoveGen, Square, Move, make_move
from subprocess import run, PIPE, Popen
import signal
import time
import sys

class EniacEngine(UCIEngine):
  """Wraps eniac chess simulation for uci tournament play."""

  def __init__(self):
    super().__init__(name="ENIAC Chess", author="Jonathan Stray and Jered Wierzbicki")
    self.sim = None
    self.sent_eniacsim_g = False

  def start(self):
    run('python chasm/chasm.py asm/chess.asm chess.e', shell=True, check=True)
    run('python easm/easm.py -ECHESS chessvm/chessvm.easm chessvm.e', shell=True, check=True)
    run('make -C chsim lib', shell=True, check=True)
    # note: include -W vis to run visualizations
    # leaving this out to try speeding up eniacsim temporarily
    self.sim = Popen('./eniacsim -q -v chsim/vm.so chessvm.e', shell=True, stdin=PIPE, stdout=PIPE)
    super().start()

  def join(self):
    self.sim.kill()
    super().join()

  def evaluate(self, position):
    """Write position as cards and return response from eniac"""
    memory = init_memory(position)
    deck = convert_memory_to_deck(memory)
    output_deck(deck)
    if self.sent_eniacsim_g:
      self.sim.send_signal(signal.SIGINT)
    self.sim.stdin.write('f r /tmp/chess.deck\n'.encode())
    self.sim.stdin.write('g\n'.encode())
    self.sim.stdin.flush()
    self.sent_eniacsim_g = True
    self.log.debug(f'eniac is pondering {position}')
    raw_move = self.sim.stdout.readline().decode().strip()
    self.log.debug(f'eniac raw move: {raw_move}')
    if raw_move == '0000':
      # XXX UCI doesn't seem to have an actual way to resign...
      return
    return Move(fro=Square(y=int(raw_move[0]), x=int(raw_move[1])),
                to=Square(y=int(raw_move[2]), x=int(raw_move[3])))


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
  memory[35] = 0 if position.to_move == 'w' else 10
  memory[55] = 50  # score
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
