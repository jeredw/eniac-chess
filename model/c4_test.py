#!/usr/bin/env python3

import unittest
import c4
from c4 import *

class TestC4(unittest.TestCase):
  def setUp(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000')

  def setUpBoard(self, *rows):
    c4.winner = 0
    assert len(rows) == 6
    i = 0
    for row in rows:
      assert len(row) == 7
      for value in row:
        c4.board[i] = int(value)
        i += 1

  def assertBoard(self, *rows):
    assert len(rows) == 6
    i = 0
    for row in rows:
      assert len(row) == 7
      self.assertEqual(c4.board[i+0], int(row[0]))
      self.assertEqual(c4.board[i+1], int(row[1]))
      self.assertEqual(c4.board[i+2], int(row[2]))
      self.assertEqual(c4.board[i+3], int(row[3]))
      self.assertEqual(c4.board[i+4], int(row[4]))
      self.assertEqual(c4.board[i+5], int(row[5]))
      self.assertEqual(c4.board[i+6], int(row[6]))
      i += 7

  def testRow6Move(self):
    move(4, 1)
    move(3, 1)
    move(2, 1)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0111000')
    self.assertEqual(c4.winner, 0)
    move(1, 1)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '1111000')
    self.assertEqual(c4.winner, 1)
    undo_move(1)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0111000')
    self.assertEqual(c4.winner, 0)
    move(5, 1)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0111100')
    self.assertEqual(c4.winner, 1)
    undo_move(5)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0000000',
                     '0111000')
    self.assertEqual(c4.winner, 0)

  def testColumn1Move(self):
    move(1, 2)
    move(1, 2)
    move(1, 2)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '2000000',
                     '2000000',
                     '2000000')
    self.assertEqual(c4.winner, 0)
    move(1, 2)
    self.assertBoard('0000000',
                     '0000000',
                     '2000000',
                     '2000000',
                     '2000000',
                     '2000000')
    self.assertEqual(c4.winner, 2)
    undo_move(1)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '2000000',
                     '2000000',
                     '2000000')
    self.assertEqual(c4.winner, 0)

  def testDiagR1(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0001200',
                    '0011120',
                    '0111212')
    move(4, 2)
    self.assertEqual(c4.winner, 2)
    undo_move(4)
    move(5, 1)
    self.assertEqual(c4.winner, 1)

  def testDiagR2(self):
    self.setUpBoard('0000000',
                    '0121000',
                    '0211000',
                    '2212000',
                    '1212000',
                    '2121000')
    move(4, 2)
    self.assertBoard('0002000',
                     '0121000',
                     '0211000',
                     '2212000',
                     '1212000',
                     '2121000')
    self.assertEqual(c4.winner, 2)
 
  def testDiagL1(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0100000',
                    '1210000',
                    '2121212')
    move(1, 2)
    self.assertBoard('0000000',
                     '0000000',
                     '0000000',
                     '2100000',
                     '1210000',
                     '2121212')
    self.assertEqual(c4.winner, 0)
    move(1, 1)
    self.assertBoard('0000000',
                     '0000000',
                     '1000000',
                     '2100000',
                     '1210000',
                     '2121212')
    self.assertEqual(c4.winner, 1)
 
  def testDiagL2(self):
    self.setUpBoard('0000000',
                    '2121000',
                    '2211000',
                    '2211000',
                    '1212000',
                    '2121000')
    move(1, 1)
    self.assertBoard('1000000',
                     '2121000',
                     '2211000',
                     '2211000',
                     '1212000',
                     '2121000')
    self.assertEqual(c4.winner, 1)

  def testDraw(self):
    self.setUpBoard('0111222',
                    '1222111',
                    '2111222',
                    '1222111',
                    '2111222',
                    '1222111')
    move(1, 2)
    self.assertBoard('2111222',
                     '1222111',
                     '2111222',
                     '1222111',
                     '2111222',
                     '1222111')
    self.assertEqual(c4.winner, 3)

  def testScore_Center(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0001000')
    self.assertEqual(score(1), 33)
    self.assertEqual(score(2), 30)
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0002000')
    self.assertEqual(score(2), 33)
    self.assertEqual(score(1), 30)

  def testScore_H4(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '1111000')
    self.assertEqual(score(1), 99)
    self.assertEqual(score(2), 26)
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '2222000')
    self.assertEqual(score(2), 99)
    self.assertEqual(score(1), 26)

  def testScore_H4AtRight(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0001111')
    self.assertEqual(score(1), 99)
    self.assertEqual(score(2), 26)

  def testScore_H3(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '1110000')
    self.assertEqual(score(1), 37)
    self.assertEqual(score(2), 26)
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '0000000',
                    '2220000')
    self.assertEqual(score(2), 37)
    self.assertEqual(score(1), 26)

  def testScore_H2(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000110',
                    '0000020',
                    '0000010',
                    '0000020')
    self.assertEqual(score(1), 34)
    self.assertEqual(score(2), 30)
    self.setUpBoard('0000000',
                    '0000000',
                    '0000220',
                    '0000010',
                    '0000020',
                    '0000010')
    self.assertEqual(score(2), 34)
    self.assertEqual(score(1), 30)

  def testScore_V4(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000010',
                    '0000010',
                    '0000010',
                    '0000010')
    self.assertEqual(score(1), 99)
    self.assertEqual(score(2), 26)
    self.setUpBoard('2000000',
                    '2000000',
                    '2000000',
                    '2000000',
                    '1000000',
                    '1000000')
    self.assertEqual(score(2), 99)
    self.assertEqual(score(1), 30)

  def testScore_V3(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000010',
                    '0000010',
                    '0000010',
                    '0000020')
    self.assertEqual(score(1), 37)
    self.assertEqual(score(2), 26)
    self.setUpBoard('2000000',
                    '2000000',
                    '2000000',
                    '1000000',
                    '2000000',
                    '1000000')
    self.assertEqual(score(2), 30)
    self.assertEqual(score(1), 30)

  def testScore_V2(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0000010',
                    '0000010',
                    '0000020')
    self.assertEqual(score(1), 32)
    self.assertEqual(score(2), 30)

  def testScore_R3(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0002000',
                    '0011200',
                    '0211120')
    self.assertEqual(score(2), 30 + 3 + 2 + 5)
    self.assertEqual(score(1), 30 + 6 + 2 + 2 + 2)

  def testScore_L3(self):
    self.setUpBoard('0000000',
                    '0000000',
                    '0000000',
                    '0002000',
                    '0021100',
                    '0211120')
    self.assertEqual(score(2), 30 + 3 + 2 + 5)
    self.assertEqual(score(1), 30 + 6 + 2 + 2 + 2)

  def testScore_L2(self):
    self.setUpBoard('0000000',
                    '2000200',
                    '1202121',
                    '2121212',
                    '2121212',
                    '2121212')
    self.assertEqual(score(2), 30 + 3 + 5 + 2 + 5 + 5 + 2 + 2)
    self.assertEqual(score(1), 30 + 9 + 2 + 2 - 4 - 4 - 4)

if __name__ == "__main__":
  unittest.main()
