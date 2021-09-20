#!/usr/bin/env python3
import unittest
from subprocess import run, PIPE, Popen
from game import Board, Position, Square

class TestMoveGen(unittest.TestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/movegen_test.asm movegen_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def simulate(self, deck):
    with open('/tmp/test.deck', 'w') as f:
      f.write(deck)
    result = run('./chsim/chsim -t 100000 -f /tmp/test.deck movegen_test.e', shell=True, stdin=PIPE, stdout=PIPE)
    self.assertEqual(result.returncode, 0)
    return result.stdout.decode('utf-8').strip().split()

  def convertPositionToDeck(self, position):
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
        elif piece == 'R':
          assert rook < 2
          memory[34 + rook] = yx
          rook += 1
        else:
          assert piece == 'r'
    memory[38] = 0 if position.to_move == 'w' else 1

    deck = []
    for address, data in enumerate(memory):
      if data != 0:
        deck.append(f'{address:02}{data:02}0{" "*75}')
    deck.append(f'99000{" "*75}')
    return '\n'.join(deck)

  def computeMoves(self, fen):
    position = Position.fen(fen)
    deck = self.convertPositionToDeck(position)
    return self.simulate(deck)

  def testPawnB2(self):
    moves = self.computeMoves('8/8/8/8/8/8/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['2232', '2242'])

  def testPawnB2_Blocked1(self):
    moves = self.computeMoves('8/8/8/8/8/1P6/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['3242'])

  def testPawnB2_Blocked2(self):
    moves = self.computeMoves('8/8/8/8/1P6/8/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['2232', '4252'])

  def testPawnB3(self):
    moves = self.computeMoves('8/8/8/8/8/1P6/8/8 w - - 0 1')
    self.assertEqual(moves, ['3242'])

  def testPawnG7(self):
    moves = self.computeMoves('8/6p1/8/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['7767', '7757'])

  def testPawnG7_Blocked1(self):
    moves = self.computeMoves('8/6p1/6p1/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['6757'])

  def testPawnG7_Blocked2(self):
    moves = self.computeMoves('8/6p1/8/6p1/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['5747', '7767'])

  def testPawnG6(self):
    moves = self.computeMoves('8/8/6p1/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['6757'])

if __name__ == "__main__":
  unittest.main()