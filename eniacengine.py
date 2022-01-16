import math

from uciengine import UCIEngine
from game import Move
from subprocess import run, PIPE, Popen

class EniacEngine(UCIEngine):
  """Wraps eniac chess client for uci tournament play."""

  def __init__(self):
    super().__init__(name="ENIAC Chess 1.0", author="Jonathan Stray and Jered Wierzbicki")
    self.client = None

  def start(self):
    run('make client', shell=True, check=True)
    self.client = Popen('./client', shell=True, stdin=PIPE, stdout=PIPE)
    super().start()

  def join(self):
    self.client.kill()
    super().join()

  def evaluate(self, position):
    """Write position as cards and return response from eniac"""
    self.client.stdin.write(f'{position}\n'.encode())
    self.client.stdin.flush()
    self.log.debug(f'eniac evaluating {position}')
    move = self.client.stdout.readline().decode().strip()
    self.log.debug(f'foo')
    if move == '':
      # UCI doesn't seem to have an actual way to resign, so return None
      # This will make the move the literal string "None", which a board
      # program ought to adjudicate as resignation by invalid move.
      self.log.debug(f'eniac resigns')
      return
    self.log.debug(f'eniac plays {move}')
    return Move.lan(move)
