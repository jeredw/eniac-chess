#!/usr/bin/env python3
# note https://www.chess-poster.com/english/fen/fen_epd_viewer.htm is a handy
# web page for visualizing FEN/EPD strings used to represent chess positions
import unittest
from subprocess import run, PIPE, Popen
from game import Board, Position, Square, Move


class SimTestCase(unittest.TestCase):
  def setUp(self):
    self.memory = [0] * 75

  def simulate(self, program, deck):
    with open('/tmp/test.deck', 'w') as f:
      f.write(deck)
    result = run(f'./chsim/chsim -t 250000 -f /tmp/test.deck {program}', shell=True, stdin=PIPE, stdout=PIPE)
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

  def initMove(self, position, move):
    encode_piece = lambda k: '.PNBQRK????pnbqrk'.find(k)
    self.memory[35] = encode_piece(position.board[move.fro])
    self.memory[36] = encode_piece(position.board[move.to])
    self.memory[37] = move.fro.y * 10 + move.fro.x
    self.memory[38] = move.to.y * 10 + move.to.x

  def convertMemoryToDeck(self):
    deck = []
    for address, data in enumerate(self.memory):
      if data != 0:
        deck.append(f'{address:02}{data:02}0{" "*75}')
    deck.append(f'99000{" "*75}')
    return '\n'.join(deck)


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
    self.assertEqual(moves, ['4454', '4453', '4455', '4433', '4435'])

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

  def testKingAtD4_PawnCheck(self):
    moves = self.computeMoves('8/8/4p3/8/3K4/8/8/8 w - - 0 1')
    self.assertEqual(moves, ['4445', '4443', '4434', '4453', '4455', '4433', '4435'])

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

  def readBoard(self, state):
    board = Board.unpack('8/8/8/8/8/8/8/8')
    decode_piece = lambda k: '.PNBQRK????pnbqrk'[int(k)]
    for line in state:
      pos = Square(y=int(line[0]), x=int(line[1]))
      piece = decode_piece(line[2:4])
      board[pos] = piece
    return board

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

  def testMoveKnightB2ToC3(self):
    board = self.makeMove('8/8/8/8/8/8/8/1N6 w - - 0 1',
                          Move(fro=Square.b1, to=Square.c3))
    self.assertEqual(str(board), '8/8/8/8/8/2N5/8/8')

  def testMoveBishopC1ToA3(self):
    board = self.makeMove('8/8/8/8/8/8/8/2B5 w - - 0 1',
                          Move(fro=Square.c1, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/B7/8/8')

  def testMoveQueenD1ToD8(self):
    board = self.makeMove('8/8/8/8/8/8/8/3Q4 w - - 0 1',
                          Move(fro=Square.d1, to=Square.d8))
    self.assertEqual(str(board), '3Q4/8/8/8/8/8/8/8')

  def testMoveKingE1ToF2(self):
    board = self.makeMove('8/8/8/8/8/8/8/4K3 w - - 0 1',
                          Move(fro=Square.e1, to=Square.f2))
    self.assertEqual(str(board), '8/8/8/8/8/8/5K2/8')

  def testMoveRookA1ToA4(self):
    board = self.makeMove('8/8/8/8/8/8/8/R7 w - - 0 1',
                          Move(fro=Square.a1, to=Square.a4))
    self.assertEqual(str(board), '8/8/8/8/R7/8/8/8')

  def testMovePawnD7(self):
    board = self.makeMove('8/3p4/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.d5))
    self.assertEqual(str(board), '8/8/8/3p4/8/8/8/8')

  def testMoveKnightG8ToH6(self):
    board = self.makeMove('6n1/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.g8, to=Square.h6))
    self.assertEqual(str(board), '8/8/7n/8/8/8/8/8')

  def testMoveBishopF8ToA3(self):
    board = self.makeMove('5b2/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.f8, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/b7/8/8')

  def testMoveQueenD8ToD1(self):
    board = self.makeMove('3q4/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d8, to=Square.d1))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/3q4')

  def testMoveKingE8ToF7(self):
    board = self.makeMove('4k3/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.e8, to=Square.f7))
    self.assertEqual(str(board), '8/5k2/8/8/8/8/8/8')

  def testMoveRookH8ToH5(self):
    board = self.makeMove('7r/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.h8, to=Square.h5))
    self.assertEqual(str(board), '8/8/8/7r/8/8/8/8')

  def testMovePawnE2_CapturePawn(self):
    board = self.makeMove('8/8/8/8/8/5p2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')

  def testMovePawnE2_CaptureKing(self):
    board = self.makeMove('8/8/8/8/8/5k2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')

  def testMovePawnE2_CaptureRook(self):
    board = self.makeMove('8/8/8/8/8/5r2/4P3/8 w - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5P2/8/8')

  def testMovePawnD7_CapturePawn(self):
    board = self.makeMove('8/3p4/2P5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')

  def testMovePawnD7_CaptureRook(self):
    board = self.makeMove('8/3p4/2R5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')

  def testMovePawnD7_CaptureRook1(self):
    board = self.makeMove('8/3p4/2R1R3/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p1R3/8/8/8/8/8')

  def testMovePawnD7_CaptureKing(self):
    board = self.makeMove('8/3p4/2K5/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/8/2p5/8/8/8/8/8')


class TestUndoMove(SimTestCase):
  def setUpClass():
    run('python chasm/chasm.py asm/undo_move_test.asm undo_move_test.e', shell=True, check=True)
    run('make -C chsim chsim', shell=True, check=True)

  def readBoard(self, state):
    board = Board.unpack('8/8/8/8/8/8/8/8')
    decode_piece = lambda k: '.PNBQRK????pnbqrk'[int(k)]
    for line in state:
      pos = Square(y=int(line[0]), x=int(line[1]))
      piece = decode_piece(line[2:4])
      board[pos] = piece
    return board

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

  def testUndoMoveKnightB2ToC3(self):
    board = self.undoMove('8/8/8/8/8/8/8/1N6 w - - 0 1',
                          '8/8/8/8/8/2N5/8/8 b - - 0 1',
                          Move(fro=Square.b1, to=Square.c3))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/1N6')

  def testUndoMoveBishopC1ToA3(self):
    board = self.undoMove('8/8/8/8/8/8/8/2B5 w - - 0 1',
                          '8/8/8/8/8/B7/8/8 b - - 0 1',
                          Move(fro=Square.c1, to=Square.a3))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/2B5')

  def testUndoMoveQueenD1ToD8(self):
    board = self.undoMove('8/8/8/8/8/8/8/3Q4 w - - 0 1',
                          '3Q4/8/8/8/8/8/8/8 b - - 0 1',
                          Move(fro=Square.d1, to=Square.d8))
    self.assertEqual(str(board), '8/8/8/8/8/8/8/3Q4')

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

  def testUndoMovePawnD7(self):
    board = self.undoMove('8/3p4/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/3p4/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.d5))
    self.assertEqual(str(board), '8/3p4/8/8/8/8/8/8')

  def testUndoMoveKnightG8ToH6(self):
    board = self.undoMove('6n1/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/7n/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.g8, to=Square.h6))
    self.assertEqual(str(board), '6n1/8/8/8/8/8/8/8')

  def testUndoMoveBishopF8ToA3(self):
    board = self.undoMove('5b2/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/8/8/b7/8/8 w - - 0 2',
                          Move(fro=Square.f8, to=Square.a3))
    self.assertEqual(str(board), '5b2/8/8/8/8/8/8/8')

  def testUndoMoveQueenD8ToD1(self):
    board = self.undoMove('3q4/8/8/8/8/8/8/8 b - - 0 1',
                          '8/8/8/8/8/8/8/3q4 w - - 0 2',
                          Move(fro=Square.d8, to=Square.d1))
    self.assertEqual(str(board), '3q4/8/8/8/8/8/8/8')

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

  def testUndoMovePawnE2_CapturePawn(self):
    board = self.undoMove('8/8/8/8/8/5p2/4P3/8 w - - 0 1',
                          '8/8/8/8/8/5P2/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5p2/4P3/8')

  def testUndoMovePawnE2_CaptureKing(self):
    board = self.undoMove('8/8/8/8/8/5k2/4P3/8 w - - 0 1',
                          '8/8/8/8/8/5P2/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5k2/4P3/8')

  def testUndoMovePawnE2_CaptureRook(self):
    board = self.undoMove('8/8/8/8/8/5r2/4P3/8 w - - 0 1',
                          '8/8/8/8/8/5P2/8/8 b - - 0 1',
                          Move(fro=Square.e2, to=Square.f3))
    self.assertEqual(str(board), '8/8/8/8/8/5r2/4P3/8')

  def testUndoMovePawnD7_CapturePawn(self):
    board = self.undoMove('8/3p4/2P5/8/8/8/8/8 b - - 0 1',
                          '8/8/2p5/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2P5/8/8/8/8/8')

  def testUndoMovePawnD7_CaptureRook(self):
    board = self.undoMove('8/3p4/2R5/8/8/8/8/8 b - - 0 1',
                          '8/8/2p5/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2R5/8/8/8/8/8')

  def testUndoMovePawnD7_CaptureRook1(self):
    board = self.undoMove('8/3p4/2R1R3/8/8/8/8/8 b - - 0 1',
                          '8/8/2p1R3/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2R1R3/8/8/8/8/8')

  def testUndoMovePawnD7_CaptureKing(self):
    board = self.undoMove('8/3p4/2K5/8/8/8/8/8 b - - 0 1',
                          '8/8/2p5/8/8/8/8/8 w - - 0 2',
                          Move(fro=Square.d7, to=Square.c6))
    self.assertEqual(str(board), '8/3p4/2K5/8/8/8/8/8')


if __name__ == "__main__":
  unittest.main()
