#!/usr/bin/env python3
# note https://www.chess-poster.com/english/fen/fen_epd_viewer.htm is a handy
# web page for visualizing FEN/EPD strings used to represent chess positions
import unittest
from subprocess import run, PIPE, Popen
from game import Board, Position, Square, Move

# must match data in memory_layout.asm
PAWN_SCORE=3
BISHOP_SCORE=9
KNIGHT_SCORE=9
ROOK_SCORE=15
QUEEN_SCORE=24
KING_SCORE=25

# defined in update_center_score
CENTER_SCORE=1

class SimTestCase(unittest.TestCase):
  def setUp(self):
    self.memory = [0] * 75

  def simulate(self, program, deck, max_cycles=500000):
    with open('/tmp/test.deck', 'w') as f:
      f.write(deck)
    result = run(f'./chsim/chsim -t {max_cycles} -f /tmp/test.deck {program}', shell=True, stdin=PIPE, stdout=PIPE)
    self.assertEqual(result.returncode, 0)
    return result.stdout.decode('utf-8').strip().split()

  def initBoard(self, position):
    piece_code = '??PNBQpnbq'
    rook = 0
    for square, piece in position.board:
      yx = square.y * 10 + square.x
      offset = ((square.y-1) * 8 + (square.x-1)) // 2
      shift = 10 if square.x % 2 == 1 else 1
      if piece in piece_code:
        code = piece_code.index(piece)
        self.memory[offset] += shift * code
      elif piece != '.':
        self.memory[offset] += shift * 1
        if piece == 'K':
          self.memory[32] = yx
        elif piece == 'k':
          self.memory[33] = yx
        elif piece == 'R' and rook == 0:
          self.memory[34] = yx
          rook += 1
        elif piece == 'R' and rook == 1:
          self.memory[45] = yx
          rook += 1
        else:
          assert piece == 'r'
    self.memory[35] = 0 if position.to_move == 'w' else 10
    self.initScore(position)

  def initScore(self, position):
    # We score each move incrementally instead of evaluating board positions
    # always start at 50, giving us headroom for two captures on either side
    self.memory[55] = 50

  def initMove(self, position, move):
    encode_piece = lambda k: '.PNBQRK????pnbqrk'.find(k)
    self.memory[35] = encode_piece(position.board[move.fro])
    self.memory[36] = encode_piece(position.board[move.to])
    self.memory[37] = move.fro.y * 10 + move.fro.x
    self.memory[38] = move.to.y * 10 + move.to.x
    if move.promo:
      self.memory[39] = 90

  def convertMemoryToDeck(self):
    deck = []
    for address, data in enumerate(self.memory):
      if data != 0:
        deck.append(f'{address:02}{data:02}0{" "*75}')
    deck.append(f'99000{" "*75}')
    return '\n'.join(deck)

  def readBoard(self, state):
    board = Board.unpack('8/8/8/8/8/8/8/8')
    decode_piece = lambda k: '.PNBQRK????pnbqrk'[int(k)]
    score = 0
    for line in state:
      if line.startswith('99'):
        score = int(line[2:4]) - 50
        continue
      pos = Square(y=int(line[0]), x=int(line[1]))
      piece = decode_piece(line[2:4])
      board[pos] = piece
    board.score = score
    return board


class TestMoveGen(SimTestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/movegen_test.asm movegen_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def computeMoves(self, fen):
    position = Position.fen(fen)
    self.initBoard(position)
    deck = self.convertMemoryToDeck()
    return self.simulate('movegen_test.e', deck)

  def testMoveOwnPiecesB(self):
    moves = self.computeMoves('8/8/8/8/8/8/1P6/8 b - - 0 1')
    self.assertEqual(moves, [])

  def testMoveOwnPiecesB2(self):
    moves = self.computeMoves('8/3p4/8/8/8/8/3P4/8 b - - 0 1')
    self.assertEqual(moves, ['7464', '7454'])

  def testMoveOwnPiecesW(self):
    moves = self.computeMoves('8/8/8/8/8/8/1p6/8 w - - 0 1')
    self.assertEqual(moves, [])

  def testMoveOwnPiecesW2(self):
    moves = self.computeMoves('8/3p4/8/8/8/8/3P4/8 w - - 0 1')
    self.assertEqual(moves, ['2434', '2444'])

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

  def testPawnB2_CaptureL(self):
    moves = self.computeMoves('8/8/8/8/8/p7/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['2231', '2232', '2242'])

  def testPawnB2_CaptureR(self):
    moves = self.computeMoves('8/8/8/8/8/2p5/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['2233', '2232', '2242'])

  def testPawnB2_CaptureRL(self):
    moves = self.computeMoves('8/8/8/8/8/n1p5/1P6/8 w - - 0 1')
    self.assertEqual(moves, ['2231', '2233', '2232', '2242'])

  def testPawnA3_CaptureR(self):
    moves = self.computeMoves('8/8/8/8/pp6/P7/8/8 w - - 0 1')
    self.assertEqual(moves, ['3142'])

  def testPawnH3_CaptureL(self):
    moves = self.computeMoves('8/8/8/8/6pp/7P/8/8 w - - 0 1')
    self.assertEqual(moves, ['3847'])

  def testPawnG7(self):
    moves = self.computeMoves('8/6p1/8/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['7767', '7757'])

  def testPawnG7_Blocked1(self):
    moves = self.computeMoves('8/6p1/6p1/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['6757'])

  def testPawnG7_Blocked2(self):
    moves = self.computeMoves('8/6p1/8/6p1/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['5747', '7767'])

  def testPawnG7(self):
    moves = self.computeMoves('8/6p1/8/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['7767', '7757'])

  def testPawnG7_CaptureRL(self):
    moves = self.computeMoves('8/6p1/5PPP/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['7766', '7768'])

  def testPawnH7_CaptureL(self):
    moves = self.computeMoves('8/7p/6PP/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['7867'])

  def testPawnG6(self):
    moves = self.computeMoves('8/8/6p1/8/8/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['6757'])

  def testKnightAtD4(self):
    moves = self.computeMoves('8/8/8/8/3N4/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4452', '4456', '4463', '4465', '4423', '4425', '4432', '4436'])

  def testKnightAtD1(self):
    moves = self.computeMoves('8/8/8/8/8/8/8/3N4 w - - 0 1')
    self.assertEqual(moves, ['1422', '1426', '1433', '1435'])

  def testKnightAtH1(self):
    moves = self.computeMoves('8/8/8/8/8/8/8/7N w - - 0 1')
    self.assertEqual(moves, ['1826', '1837'])

  def testKnightAtH4(self):
    moves = self.computeMoves('8/8/8/8/7N/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4856', '4867', '4827', '4836'])

  def testKnightAtH8(self):
    moves = self.computeMoves('7N/8/8/8/8/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['8867', '8876'])

  def testKnightAtD8(self):
    moves = self.computeMoves('3N4/8/8/8/8/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['8463', '8465', '8472', '8476'])

  def testKnightAtA8(self):
    moves = self.computeMoves('N7/8/8/8/8/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['8162', '8173'])

  def testKnightAtA4(self):
    moves = self.computeMoves('8/8/8/8/N7/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4153', '4162', '4122', '4133'])

  def testKnightAtA1_Blocked(self):
    moves = self.computeMoves('8/8/8/8/8/1P6/2P5/N7 w - - 0 1')
    self.assertEqual(moves, ['2333', '2343', '3242'])

  def testKnightAtA1_Capture1(self):
    moves = self.computeMoves('8/8/8/8/8/1P6/2p5/N7 w - - 0 1')
    self.assertEqual(moves, ['1123', '3242'])

  def testKnightAtA1_Capture2(self):
    moves = self.computeMoves('8/8/8/8/8/1p6/2p5/N7 w - - 0 1')
    self.assertEqual(moves, ['1123', '1132'])

  def testBishopAtE4(self):
    moves = self.computeMoves('8/8/8/8/4B3/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4554', '4563', '4572', '4581',
                             '4556', '4567', '4578',
                             '4534', '4523', '4512',
                             '4536', '4527', '4518'])

  def testBishopAtD4_Blocked(self):
    moves = self.computeMoves('8/8/8/2P1P3/3B4/2P1P3/8/8 w - - 0 1')
    self.assertEqual(moves, ['3343', '3545', '5363', '5565'])

  def testBishopAtD4_Capture1(self):
    moves = self.computeMoves('8/8/1p6/4P3/3B4/2P1P3/8/8 w - - 0 1')
    self.assertEqual(moves, ['3343', '3545',
                             '4453', '4462',
                             '5565'])

  def testBishopAtD4_Capture2(self):
    moves = self.computeMoves('8/8/1p6/4p3/3B4/2P1P3/8/8 w - - 0 1')
    self.assertEqual(moves, ['3343', '3545',
                             '4453', '4462', '4455'])

  def testBishopAtD4_Capture3(self):
    moves = self.computeMoves('8/8/1p6/4p3/3B4/2P1p3/8/8 w - - 0 1')
    self.assertEqual(moves, ['3343',
                             '4453', '4462', '4455', '4435'])

  def testBishopAtD4_Capture4(self):
    moves = self.computeMoves('8/8/8/2p1p3/3B4/2p1p3/8/8 w - - 0 1')
    self.assertEqual(moves, ['4453', '4455', '4433', '4435'])

  def testQueenAtE4(self):
    moves = self.computeMoves('8/8/8/8/4Q3/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4546', '4547', '4548',
                             '4544', '4543', '4542', '4541',
                             '4555', '4565', '4575', '4585',
                             '4535', '4525', '4515',
                             '4554', '4563', '4572', '4581',
                             '4556', '4567', '4578',
                             '4534', '4523', '4512',
                             '4536', '4527', '4518'])

  def testQueenAtD4_Blocked(self):
    moves = self.computeMoves('8/8/8/2PPP3/2PQP3/2PPP3/8/8 w - - 0 1')
    self.assertEqual(moves, ['5363', '5464', '5565'])

  def testQueenAtD4_Capture8(self):
    moves = self.computeMoves('8/8/8/2ppp3/2pQp3/2ppp3/8/8 w - - 0 1')
    self.assertEqual(moves, ['4445', '4443', '4454', '4434', '4453', '4455', '4433', '4435'])

  def testKingAtE4(self):
    moves = self.computeMoves('8/8/8/8/4K3/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4546', '4544', '4555', '4535', '4554', '4556', '4534', '4536'])

  def testKingAtD4_Blocked(self):
    moves = self.computeMoves('8/8/8/2PPP3/2PKP3/2PPP3/8/8 w - - 0 1')
    self.assertEqual(moves, ['5363', '5464', '5565'])

  def testKingAtD4_Capture8(self):
    moves = self.computeMoves('8/8/8/2ppp3/2pKp3/2ppp3/8/8 w - - 0 1')
    self.assertEqual(moves, ['4445', '4443', '4454', '4434', '4453', '4455', '4433', '4435'])

  def testRookAtE4(self):
    moves = self.computeMoves('8/8/8/8/4R3/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4546', '4547', '4548',
                             '4544', '4543', '4542', '4541',
                             '4555', '4565', '4575', '4585',
                             '4535', '4525', '4515'])

  def testRookAtE4_Black(self):
    moves = self.computeMoves('8/8/8/8/4r3/8/8/8 b - - 0 1')
    self.assertEqual(moves, ['4546', '4547', '4548',
                             '4544', '4543', '4542', '4541',
                             '4555', '4565', '4575', '4585',
                             '4535', '4525', '4515'])

  def testRookAtD4_Blocked(self):
    moves = self.computeMoves('8/8/8/3P4/2PRP3/3P4/8/8 w - - 0 1')
    self.assertEqual(moves, ['4353', '4555', '5464'])

  def testRookAtD4_Capture4(self):
    moves = self.computeMoves('8/8/8/3p4/2pRp3/3p4/8/8 w - - 0 1')
    self.assertEqual(moves, ['4445', '4443', '4454', '4434'])
 
  # removed because we do not currently do check detection in movegen

  # def testKingAtD4_PawnCheck(self):
  #   moves = self.computeMoves('8/8/4p3/8/3K4/8/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4445', '4443', '4434', '4453', '4455', '4433', '4435'])

  # def testKingAtD4_BishopCheck(self):
  #   moves = self.computeMoves('8/8/4b3/8/3K4/8/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4445', '4434', '4453', '4455', '4433', '4435'])

  # def testKingAtD4_RookCheck(self):
  #   moves = self.computeMoves('8/8/4r3/8/3K4/8/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4443', '4454', '4434', '4453', '4433'])

  # def testKingAtD4_KingCheck(self):
  #   moves = self.computeMoves('8/8/4k3/8/3K4/8/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4445', '4443', '4434', '4453', '4433', '4435'])

  # def testKingAtD4_QueenCheck(self):
  #   moves = self.computeMoves('8/8/4q3/8/3K4/8/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4434', '4453', '4433'])

  # def testKingAtD4_KnightCheck(self):
  #   moves = self.computeMoves('8/8/5n2/8/3K4/5n2/8/8 w - - 0 1')
  #   self.assertEqual(moves, ['4443', '4434', '4453', '4433', '4435'])

  # def testKingAtD4_Black_KnightCheck(self):
  #   moves = self.computeMoves('8/8/5N2/8/3k4/5N2/8/8 b - - 0 1')
  #   self.assertEqual(moves, ['4443', '4434', '4453', '4433', '4435'])

  def testRookTakesPawn_Black(self):
    moves = self.computeMoves('8/8/8/8/3k4/1P1r4/8/8 b - - 0 1')
    self.assertEqual(moves, ['3435', '3436', '3437', '3438', '3433', '3432', '3424',
                             '3414', '4445', '4443', '4454', '4453', '4455', '4433', '4435'])

  def testInitialPosition_White(self):
    moves = self.computeMoves('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1')
    self.assertEqual(moves, ['1231', '1233',
                             '1736', '1738',
                             '2131', '2141',
                             '2232', '2242',
                             '2333', '2343',
                             '2434', '2444',
                             '2535', '2545',
                             '2636', '2646',
                             '2737', '2747',
                             '2838', '2848'])

  def testInitialPosition_Black(self):
    moves = self.computeMoves('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b - - 0 1')
    self.assertEqual(moves, ['7161', '7151',
                             '7262', '7252',
                             '7363', '7353',
                             '7464', '7454',
                             '7565', '7555',
                             '7666', '7656',
                             '7767', '7757',
                             '7868', '7858',
                             '8261', '8263',
                             '8766', '8768'])


class TestMove(SimTestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/move_test.asm move_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def makeMove(self, fen, move):
    position = Position.fen(fen)
    self.initBoard(position)
    self.initMove(position, move)
    deck = self.convertMemoryToDeck()
    output = self.simulate('move_test.e', deck)
    return self.readBoard(output)

  def testMovePawnE2(self):
    board = self.makeMove('8/8/8/8/8/8/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.e4))
    self.assertEqual(str(board), '8/8/8/8/4P3/8/8/8')
    self.assertEqual(board.score, CENTER_SCORE)

  def testPromoteWhitePawn(self):
    board = self.makeMove('8/3P4/8/8/8/8/8/8 w - - 0 1',
                          Move(fro=Square.d7, to=Square.d8, promo='Q'))
    self.assertEqual(str(board), '3Q4/8/8/8/8/8/8/8')
    self.assertEqual(board.score, QUEEN_SCORE-PAWN_SCORE)

  def testPromoteBlackPawn(self):
    board = self.makeMove('8/8/8/8/8/8/3p4/8 b - - 0 1',
                          Move(fro=Square.d2, to=Square.d1, promo='q'))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/3q4')
    self.assertEqual(board.score, -QUEEN_SCORE+PAWN_SCORE)

  def testMoveKnightB1ToC3(self):
    board = self.makeMove('8/8/8/8/8/8/8/1N6 w - - 0 1',
                          Move(fro=Square.b1, to=Square.c3))
    self.assertEqual(str(board), '8/8/8/8/8/2N5/8/8')
    self.assertEqual(board.score, CENTER_SCORE)

  def testMoveBishopC1ToA3(self):
    board = self.makeMove('8/8/8/8/8/8/8/2B5 w - - 0 1',
                          Move(fro=Square.c1, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/B7/8/8')
    self.assertEqual(board.score, 0)

  def testMoveQueenD1ToD8(self):
    board = self.makeMove('8/8/8/8/8/8/8/3Q4 w - - 0 1',
                          Move(fro=Square.d1, to=Square.d8))
    self.assertEqual(str(board), '3Q4/8/8/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testMoveKingE1ToF2(self):
    board = self.makeMove('8/8/8/8/8/8/8/4K3 w - - 0 1',
                          Move(fro=Square.e1, to=Square.f2))
    self.assertEqual(str(board), '8/8/8/8/8/8/5K2/8')

  def testMoveRookA1ToA4(self):
    board = self.makeMove('8/8/8/8/8/8/8/R7 w - - 0 1',
                          Move(fro=Square.a1, to=Square.a4))
    self.assertEqual(str(board), '8/8/8/8/R7/8/8/8')
    self.assertEqual(board.score, 0)

  def testMovePawnD7(self):
    board = self.makeMove('8/3p4/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.d5))
    self.assertEqual(str(board), '8/8/8/3p4/8/8/8/8')
    self.assertEqual(board.score, -CENTER_SCORE)

  def testMoveKnightG8ToH6(self):
    board = self.makeMove('6n1/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.g8, to=Square.h6))
    self.assertEqual(str(board), '8/8/7n/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testMoveBishopF8ToA3(self):
    board = self.makeMove('5b2/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.f8, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/b7/8/8')
    self.assertEqual(board.score, 0)

  def testMoveQueenD8ToD1(self):
    board = self.makeMove('3q4/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d8, to=Square.d1))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/3q4')
    self.assertEqual(board.score, 0)

  def testMoveKingE8ToF7(self):
    board = self.makeMove('4k3/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.e8, to=Square.f7))
    self.assertEqual(str(board), '8/5k2/8/8/8/8/8/8')

  def testMoveRookH8ToH5(self):
    board = self.makeMove('7r/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.h8, to=Square.h5))
    self.assertEqual(str(board), '8/8/8/7r/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testMovePawnE2_CapturePawn(self):
    board = self.makeMove('8/8/8/8/8/5p2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')
    self.assertEqual(board.score, PAWN_SCORE+CENTER_SCORE)

  def testMovePawnE2_CaptureKing(self):
    board = self.makeMove('8/8/8/8/8/5k2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')
    self.assertEqual(board.score, KING_SCORE+CENTER_SCORE)

  def testMovePawnE2_CaptureRook(self):
    board = self.makeMove('8/8/8/8/8/5r2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')
    self.assertEqual(board.score, ROOK_SCORE+CENTER_SCORE)

  def testMovePawnD7_CapturePawn(self):
    board = self.makeMove('8/3p4/2P5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')
    self.assertEqual(board.score, -PAWN_SCORE-CENTER_SCORE)

  def testMovePawnD7_CaptureRook(self):
    board = self.makeMove('8/3p4/2R5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')
    self.assertEqual(board.score, -ROOK_SCORE-CENTER_SCORE)

  def testMovePawnD7_CaptureRook1(self):
    board = self.makeMove('8/3p4/2R1R3/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p1R3/8/8/8/8/8')
    self.assertEqual(board.score, -ROOK_SCORE-CENTER_SCORE)

  def testMovePawnD7_CaptureKing(self):
    board = self.makeMove('8/3p4/2K5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')
    self.assertEqual(board.score, -KING_SCORE-CENTER_SCORE)


class TestUndoMove(SimTestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/undo_move_test.asm undo_move_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def undoMove(self, from_fen, to_fen, move):
    from_position = Position.fen(from_fen)
    to_position = Position.fen(to_fen)
    # assume the move was made correctly so current board state is to_position
    self.initBoard(to_position)
    # initialize move's fromp and targetp from from_position
    self.initMove(from_position, move)
    deck = self.convertMemoryToDeck()
    output = self.simulate('undo_move_test.e', deck)
    return self.readBoard(output)

  def testUndoMovePawnE2(self):
    board = self.undoMove('8/8/8/8/8/8/4P3/8 w - - 0 1',
                          '8/8/8/8/4P3/8/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.e4))
    self.assertEqual(str(board), '8/8/8/8/8/8/4P3/8')
    self.assertEqual(board.score, -CENTER_SCORE)

  def testUndoPromoteWhitePawn(self):
    board = self.undoMove('8/3P4/8/8/8/8/8/8 w - - 0 1',
                          '3Q4/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.d8, promo='Q'))
    self.assertEqual(str(board), '8/3P4/8/8/8/8/8/8')
    self.assertEqual(board.score, -QUEEN_SCORE+PAWN_SCORE)

  def testUndoPromoteBlackPawn(self):
    board = self.undoMove('8/8/8/8/8/8/3p4/8 b - - 0 1',
                          '8/8/8/8/8/8/8/3q4 w - - 0 1',
                          Move(fro=Square.d2, to=Square.d1, promo='q'))
    self.assertEqual(str(board), '8/8/8/8/8/8/3p4/8')
    self.assertEqual(board.score, QUEEN_SCORE-PAWN_SCORE)

  def testUndoMoveKnightB1ToC3(self):
    board = self.undoMove('8/8/8/8/8/8/8/1N6 w - - 0 1',
                          '8/8/8/8/8/2N5/8/8 b - - 0 1',
                          Move(fro=Square.b1, to=Square.c3))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/1N6')
    self.assertEqual(board.score, -CENTER_SCORE)

  def testUndoMoveBishopC1ToA3(self):
    board = self.undoMove('8/8/8/8/8/8/8/2B5 w - - 0 1',
                          '8/8/8/8/8/B7/8/8 b - - 0 1',
                          Move(fro=Square.c1, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/2B5')
    self.assertEqual(board.score, 0)

  def testUndoMoveQueenD1ToD8(self):
    board = self.undoMove('8/8/8/8/8/8/8/3Q4 w - - 0 1',
                          '3Q4/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d1, to=Square.d8))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/3Q4')
    self.assertEqual(board.score, 0)

  def testUndoMoveKingE1ToF2(self):
    board = self.undoMove('8/8/8/8/8/8/8/4K3 w - - 0 1',
                          '8/8/8/8/8/8/5K2/8 b - - 0 1',
                          Move(fro=Square.e1, to=Square.f2))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/4K3')

  def testUndoMoveRookA1ToA4(self):
    board = self.undoMove('8/8/8/8/8/8/8/R7 w - - 0 1',
                          '8/8/8/8/R7/8/8/8 b - - 0 1',
                          Move(fro=Square.a1, to=Square.a4))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/R7')
    self.assertEqual(board.score, 0)

  def testUndoMovePawnD7(self):
    board = self.undoMove('8/3p4/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/3p4/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.d5))
    self.assertEqual(str(board), '8/3p4/8/8/8/8/8/8')
    self.assertEqual(board.score, CENTER_SCORE)

  def testUndoMoveKnightG8ToH6(self):
    board = self.undoMove('6n1/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/7n/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.g8, to=Square.h6))
    self.assertEqual(str(board), '6n1/8/8/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testUndoMoveBishopF8ToA3(self):
    board = self.undoMove('5b2/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/8/8/b7/8/8 w - - 0 2',
                          Move(fro=Square.f8, to=Square.a3))
    self.assertEqual(str(board), '5b2/8/8/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testUndoMoveQueenD8ToD1(self):
    board = self.undoMove('3q4/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/8/8/8/8/3q4 w - - 0 2',
                          Move(fro=Square.d8, to=Square.d1))
    self.assertEqual(str(board), '3q4/8/8/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testUndoMoveKingE8ToF7(self):
    board = self.undoMove('4k3/8/8/8/8/8/8/8 b - - 0 1',
                          '8/5k2/8/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.e8, to=Square.f7))
    self.assertEqual(str(board), '4k3/8/8/8/8/8/8/8')

  def testUndoMoveRookH8ToH5(self):
    board = self.undoMove('7r/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/7r/8/8/8/8 w - - 0 2',
                          Move(fro=Square.h8, to=Square.h5))
    self.assertEqual(str(board), '7r/8/8/8/8/8/8/8')
    self.assertEqual(board.score, 0)

  def testUndoMovePawnE2_CapturePawn(self):
    board = self.undoMove('8/8/8/8/8/5p2/4P3/8 w - - 0 1',
                          '8/8/8/8/8/5P2/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5p2/4P3/8')
    self.assertEqual(board.score, -PAWN_SCORE-CENTER_SCORE)

  def testUndoMovePawnE2_CaptureRook(self):
    board = self.undoMove('8/8/8/8/8/5r2/4P3/8 w - - 0 1',
                          '8/8/8/8/8/5P2/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5r2/4P3/8')
    self.assertEqual(board.score, -ROOK_SCORE-CENTER_SCORE)

  def testUndoMovePawnD7_CapturePawn(self):
    board = self.undoMove('8/3p4/2P5/8/8/8/8/8 b - - 0 1',
                          '8/8/2p5/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2P5/8/8/8/8/8')
    self.assertEqual(board.score, PAWN_SCORE+CENTER_SCORE)

  def testUndoMovePawnD7_CaptureRook(self):
    board = self.undoMove('8/3p4/2R5/8/8/8/8/8 b - - 0 1',
                          '8/8/2p5/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2R5/8/8/8/8/8')
    self.assertEqual(board.score, ROOK_SCORE+CENTER_SCORE)

  def testUndoMovePawnD7_CaptureRook1(self):
    board = self.undoMove('8/3p4/2R1R3/8/8/8/8/8 b - - 0 1',
                          '8/8/2p1R3/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2R1R3/8/8/8/8/8')
    self.assertEqual(board.score, ROOK_SCORE+CENTER_SCORE)

  def testUndoMoveKingF3_CapturePawn(self):
    board = self.undoMove('8/8/8/8/8/5k2/4P3/8 b - - 0 1',
                          '8/8/8/8/8/8/4k3/8 w - - 0 2',
                          Move(fro=Square.f3, to=Square.e2))
    self.assertEqual(str(board), '8/8/8/8/8/5k2/4P3/8')
    self.assertEqual(board.score, PAWN_SCORE-CENTER_SCORE)

  # black rooks worth testing because they are a special case in the piece list
  def testUndoMoveQueenG7_CaptureBRook(self):
    board = self.undoMove('5r2/6Q1/8/8/8/8/8/8 w - - 0 1',
                          '5Q2/8/8/8/8/8/8/8 b - - 0 2',
                          Move(fro=Square.g7, to=Square.f8))
    self.assertEqual(str(board), '5r2/6Q1/8/8/8/8/8/8')
    self.assertEqual(board.score, -ROOK_SCORE)

  def testUndoMoveQueenB8_CaptureBRook(self):
    board = self.undoMove('1Q3r2/8/8/8/8/8/8/8 w - - 0 1',
                          '5Q2/8/8/8/8/8/8/8 b - - 0 2',
                          Move(fro=Square.b8, to=Square.f8))
    self.assertEqual(str(board), '1Q3r2/8/8/8/8/8/8/8')
    self.assertEqual(board.score, -ROOK_SCORE)

  def testUndoMoveBRookF8_CaptureQueen(self):
    board = self.undoMove('1Q3r2/8/8/8/8/8/8/8 b - - 0 1',
                          '1r6/8/8/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.f8, to=Square.b8))
    self.assertEqual(str(board), '1Q3r2/8/8/8/8/8/8/8')
    self.assertEqual(board.score, QUEEN_SCORE)

  def testUndoMoveBishopB3toC4(self):
    board = self.undoMove('8/8/8/8/8/1b6/8/8 b - - 0 1',
                          '8/8/8/8/2b5/8/8/8 w - - 0 2',
                          Move(fro=Square.b3, to=Square.c4))
    self.assertEqual(str(board), '8/8/8/8/8/1b6/8/8')
    self.assertEqual(board.score, CENTER_SCORE)

class TestChess(SimTestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/chess_test.asm chess_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def findBestMove(self, fen):
    position = Position.fen(fen)
    self.initBoard(position)
    deck = self.convertMemoryToDeck()
    moves = self.simulate('chess_test.e', deck, max_cycles=1000000000)
    self.assertEqual(1, len(moves))
    return moves[0]

  def testInitialPosition(self):
    best = self.findBestMove('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
    self.assertEqual(best, '1233') # Currently always opens with knight b1c3

  def testPuzzle(self):
    best = self.findBestMove('1k1r1q1r/pb3ppp/4p3/3p2b1/3P4/PP1B4/KBP2PPP/2R1Q2R w KQkq - 0 1')
    self.assertEqual(best, '1555')

  def testAvoidRecapture1(self):
    best = self.findBestMove('8/8/8/8/8/1b1bk3/2P5/7K w KQkq - 0 1')
    self.assertEqual(best, '2332')

  def testAvoidRecapture2(self):
    best = self.findBestMove('8/8/8/8/8/kb1b4/2P5/7K w KQkq - 0 1')
    self.assertEqual(best, '2334')

  # Mate in 1 cases taken from
  # https://thechessworld.com/articles/training-techniques/13-checkmates-you-must-know/

  def testMateIn1Rooks(self):
    best = self.findBestMove('7k/1R6/R7/8/8/8/8/3K4 w KQkq - 0 1')
    #self.assertEqual(best, '6181')
    self.assertEqual(best, '6167')

  def testMateIn1Rooks_Resign(self):
    best = self.findBestMove('7K/1r6/r7/8/8/8/8/3k4 w KQkq - 0 1')
    self.assertEqual(best, '0000')

  def testMateIn1Pawns(self):
    best = self.findBestMove('4k3/4P3/3PK3/8/8/8/8/8 w KQkq - 0 1')
    self.assertEqual(best, '6474')

  def testMateIn1Pawns_Resign(self):
    best = self.findBestMove('8/8/8/8/8/3pk3/4p3/4K3 w KQkq - 0 1')
    self.assertEqual(best, '0000')

  def testMateIn1BackRank(self):
    best = self.findBestMove('6k1/5ppp/6r1/8/8/7P/5PP1/R5K1 w KQkq - 0 1')
    self.assertEqual(best, '1181')

  def testMateIn1Diagonal(self): # fail
    best = self.findBestMove('r4rk1/ppp2ppp/8/8/8/1P6/PQ3PPP/B4RK1 w KQkq - 0 1')
    self.assertEqual(best, '2277')

  # Can't solve this because we can't detect checkmate in the 4th move
  #def testMateIn2Morphy(self):
  #  best = self.findBestMove('kbK5/pp6/1P6/8/8/8/8/R7 w KQkq - 0 1')
  #  self.assertEqual(best, '1161')

  def testMateByPromotion(self):
    best = self.findBestMove('3k4/1P6/3K4/8/8/8/8/8 w KQkq - 0 1')
    self.assertEqual(best, '7282')


if __name__ == "__main__":
  unittest.main()
