#!/usr/bin/env python3
import unittest
from game import *


class TestSquare(unittest.TestCase):
  def testNamed(self):
    self.assertEqual(Square.named("e4"), Square(x=5, y=4))
    self.assertEqual(Square.named("a1"), Square(x=1, y=1))
    self.assertEqual(Square.named("h1"), Square(x=8, y=1))
    self.assertEqual(Square.named("a8"), Square(x=1, y=8))
    self.assertEqual(Square.named("h8"), Square(x=8, y=8))

  def testClassAttrs(self):
    self.assertEqual(Square.e4, Square(x=5, y=4))
    self.assertEqual(Square.a1, Square(x=1, y=1))
    self.assertEqual(Square.h1, Square(x=8, y=1))
    self.assertEqual(Square.a8, Square(x=1, y=8))
    self.assertEqual(Square.h8, Square(x=8, y=8))

  def testStr(self):
    self.assertEqual(str(Square(x=5, y=4)), "e4")
    self.assertEqual(str(Square(x=1, y=1)), "a1")
    self.assertEqual(str(Square(x=8, y=1)), "h1")
    self.assertEqual(str(Square(x=1, y=8)), "a8")
    self.assertEqual(str(Square(x=8, y=8)), "h8")

  def testInBounds(self):
    self.assertFalse(Square(x=0, y=4).in_bounds)
    self.assertTrue(Square(x=1, y=4).in_bounds)
    self.assertTrue(Square(x=8, y=4).in_bounds)
    self.assertFalse(Square(x=9, y=4).in_bounds)
    self.assertFalse(Square(x=4, y=0).in_bounds)
    self.assertTrue(Square(x=4, y=1).in_bounds)
    self.assertTrue(Square(x=4, y=8).in_bounds)
    self.assertFalse(Square(x=4, y=9).in_bounds)

  def testAdd(self):
    self.assertEqual(Square(x=4, y=4) + (0, 1), Square(x=4, y=5))
    self.assertEqual(Square(x=4, y=4) + (0, -1), Square(x=4, y=3))
    self.assertEqual(Square(x=4, y=4) + (-1, 0), Square(x=3, y=4))
    self.assertEqual(Square(x=4, y=4) + (3, 0), Square(x=7, y=4))


class TestBoard(unittest.TestCase):
  def setUp(self):
    self.initial = Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                          ["p", "p", "p", "p", "p", "p", "p", "p"],
                          [".", ".", ".", ".", ".", ".", ".", "."],
                          [".", ".", ".", ".", ".", ".", ".", "."],
                          [".", ".", ".", ".", ".", ".", ".", "."],
                          [".", ".", ".", ".", ".", ".", ".", "."],
                          ["P", "P", "P", "P", "P", "P", "P", "P"],
                          ["R", "N", "B", "Q", "K", "B", "N", "R"]])

  def testUnpack(self):
    self.assertEqual(Board.unpack("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"), self.initial)

  def testStr(self):
    self.assertEqual(str(self.initial), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")

  def testIter(self):
    self.assertEqual(list(self.initial),
                     [(Square.named(s), p) for s, p in 
                      [("a8", "r"), ("b8", "n"), ("c8", "b"), ("d8", "q"), ("e8", "k"), ("f8", "b"), ("g8", "n"), ("h8", "r"),
                       ("a7", "p"), ("b7", "p"), ("c7", "p"), ("d7", "p"), ("e7", "p"), ("f7", "p"), ("g7", "p"), ("h7", "p"),
                       ("a2", "P"), ("b2", "P"), ("c2", "P"), ("d2", "P"), ("e2", "P"), ("f2", "P"), ("g2", "P"), ("h2", "P"),
                       ("a1", "R"), ("b1", "N"), ("c1", "B"), ("d1", "Q"), ("e1", "K"), ("f1", "B"), ("g1", "N"), ("h1", "R")]])

  def testGet(self):
    self.assertEqual(self.initial[Square.a8], "r")
    self.assertEqual(self.initial[Square.g2], "P")
    self.assertEqual(self.initial[Square(x=1, y=1)], "R")

  def testSet(self):
    self.initial[Square.e2], self.initial[Square.e4] = empty, "P"
    self.assertEqual(self.initial[Square.e2], empty)
    self.assertEqual(self.initial[Square.e4], "P")
    self.initial[Square(x=1, y=1)] = empty
    self.assertEqual(self.initial[Square.a1], empty)

  def testFind(self):
    self.assertEqual(self.initial.find("K"), Square.e1)
    self.assertEqual(self.initial.find("k"), Square.e8)


class TestPosition(unittest.TestCase):
  def testFromFen1(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(p.board, Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                                     ["p", "p", "p", "p", "p", "p", "p", "p"],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     ["P", "P", "P", "P", "P", "P", "P", "P"],
                                     ["R", "N", "B", "Q", "K", "B", "N", "R"]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "KQkq")
    self.assertEqual(p.ep_target, None)
    self.assertEqual(p.ops["hmvc"], "0")
    self.assertEqual(p.ops["fmvn"], "1")

  def testFromFen2(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    self.assertEqual(p.board, Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                                     ["p", "p", "p", "p", "p", "p", "p", "p"],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     ["P", "P", "P", "P", ".", "P", "P", "P"],
                                     ["R", "N", "B", "Q", "K", "B", "N", "R"]]))
    self.assertEqual(p.to_move, "b")
    self.assertEqual(p.castling, "KQkq")
    self.assertEqual(p.ep_target, Square.e3)
    self.assertEqual(p.ops["hmvc"], "0")
    self.assertEqual(p.ops["fmvn"], "1")

  def testFromFen3(self):
    p = Position.fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2")
    self.assertEqual(p.board, Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                                     ["p", "p", ".", "p", "p", "p", "p", "p"],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", "p", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     ["P", "P", "P", "P", ".", "P", "P", "P"],
                                     ["R", "N", "B", "Q", "K", "B", "N", "R"]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "KQkq")
    self.assertEqual(p.ep_target, Square.c6)
    self.assertEqual(p.ops["hmvc"], "0")
    self.assertEqual(p.ops["fmvn"], "2")

  def testFromFen4(self):
    p = Position.fen("rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")
    self.assertEqual(p.board, Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                                     ["p", "p", ".", "p", "p", "p", "p", "p"],
                                     [".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", "p", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     [".", ".", ".", ".", ".", "N", ".", "."],
                                     ["P", "P", "P", "P", ".", "P", "P", "P"],
                                     ["R", "N", "B", "Q", "K", "B", ".", "R"]]))
    self.assertEqual(p.to_move, "b")
    self.assertEqual(p.castling, "KQkq")
    self.assertEqual(p.ep_target, None)
    self.assertEqual(p.ops["hmvc"], "1")
    self.assertEqual(p.ops["fmvn"], "2")

  def testToFen1(self):
    p = Position(board=Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                              ["p", "p", "p", "p", "p", "p", "p", "p"],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              ["P", "P", "P", "P", "P", "P", "P", "P"],
                              ["R", "N", "B", "Q", "K", "B", "N", "R"]]),
                 to_move="w",
                 castling="KQkq",
                 ep_target=None,
                 ops={"hmvc": "0", "fmvn": "1"})
    self.assertEqual(str(p), "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

  def testToFen2(self):
    p = Position(board=Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                              ["p", "p", "p", "p", "p", "p", "p", "p"],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", "P", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              ["P", "P", "P", "P", ".", "P", "P", "P"],
                              ["R", "N", "B", "Q", "K", "B", "N", "R"]]),
                 to_move="b",
                 castling="KQkq",
                 ep_target=Square.named("e3"),
                 ops={"hmvc": "0", "fmvn": "1"})
    self.assertEqual(str(p), "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

  def testToFen3(self):
    p = Position(board=Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                              ["p", "p", ".", "p", "p", "p", "p", "p"],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", "p", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", "P", ".", ".", "."],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              ["P", "P", "P", "P", ".", "P", "P", "P"],
                              ["R", "N", "B", "Q", "K", "B", "N", "R"]]),
                 to_move="w",
                 castling="KQkq",
                 ep_target=Square.named("c6"),
                 ops={"hmvc": "0", "fmvn": "2"})
    self.assertEqual(str(p), "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2")

  def testToFen4(self):
    p = Position(board=Board([["r", "n", "b", "q", "k", "b", "n", "r"],
                              ["p", "p", ".", "p", "p", "p", "p", "p"],
                              [".", ".", ".", ".", ".", ".", ".", "."],
                              [".", ".", "p", ".", ".", ".", ".", "."],
                              [".", ".", ".", ".", "P", ".", ".", "."],
                              [".", ".", ".", ".", ".", "N", ".", "."],
                              ["P", "P", "P", "P", ".", "P", "P", "P"],
                              ["R", "N", "B", "Q", "K", "B", ".", "R"]]),
                 to_move="b",
                 castling="KQkq",
                 ep_target=None,
                 ops={"hmvc": "1", "fmvn": "2"})
    self.assertEqual(str(p), "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2")

  def testEpd(self):
    p = Position.epd('1kr5/3n4/q3p2p/p2n2p1/PppB1P2/5BP1/1P2Q2P/3R2K1 w - - bm f5; id "Undermine.001"; c0 "f5=10, Be5+=2, Bf2=3, Bg4=2";')
    self.assertEqual(p.board, Board([[".", "k", "r", ".", ".", ".", ".", "."],
                                     [".", ".", ".", "n", ".", ".", ".", "."],
                                     ["q", ".", ".", ".", "p", ".", ".", "p"],
                                     ["p", ".", ".", "n", ".", ".", "p", "."],
                                     ["P", "p", "p", "B", ".", "P", ".", "."],
                                     [".", ".", ".", ".", ".", "B", "P", "."],
                                     [".", "P", ".", ".", "Q", ".", ".", "P"],
                                     [".", ".", ".", "R", ".", ".", "K", "."]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "")
    self.assertEqual(p.ep_target, None)
    self.assertEqual(p.ops["bm"], "f5")
    self.assertEqual(p.ops["id"], "Undermine.001")
    self.assertEqual(p.ops["c0"], "f5=10, Be5+=2, Bf2=3, Bg4=2")

  def testEpd2(self):
    p = Position.epd('r3kb1r/1bqn2pp/p3pn2/1pp5/4P3/2NB1N2/PP3PPP/R1BQ1RK1 w kq - bm Bc2 Ng5; c0 "52"; id "kai_openings_nr_102"; eco "D48"; Opn "Semi-Slav Meran";')
    self.assertEqual(p.board, Board([["r", ".", ".", ".", "k", "b", ".", "r"],
                                     [".", "b", "q", "n", ".", ".", "p", "p"],
                                     ["p", ".", ".", ".", "p", "n", ".", "."],
                                     [".", "p", "p", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     [".", ".", "N", "B", ".", "N", ".", "."],
                                     ["P", "P", ".", ".", ".", "P", "P", "P"],
                                     ["R", ".", "B", "Q", ".", "R", "K", "."]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "kq")
    self.assertEqual(p.ep_target, None)
    self.assertEqual(p.ops["bm"], "Bc2 Ng5")
    self.assertEqual(p.ops["c0"], "52")
    self.assertEqual(p.ops["id"], "kai_openings_nr_102")
    self.assertEqual(p.ops["eco"], "D48")
    self.assertEqual(p.ops["Opn"], "Semi-Slav Meran")

  def testEpd3(self):
    p = Position.epd('8/7p/2k1Pp2/pp1p2p1/3P2P1/4P3/P3K2P/8 w - - bm e4;             id "PET001: Pawn endgame";')
    self.assertEqual(p.board, Board([[".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "p"],
                                     [".", ".", "k", ".", "P", "p", ".", "."],
                                     ["p", "p", ".", "p", ".", ".", "p", "."],
                                     [".", ".", ".", "P", ".", ".", "P", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     ["P", ".", ".", ".", "K", ".", ".", "P"],
                                     [".", ".", ".", ".", ".", ".", ".", "."]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "")
    self.assertEqual(p.ep_target, None)
    self.assertEqual(p.ops["bm"], "e4")
    self.assertEqual(p.ops["id"], "PET001: Pawn endgame")

  def testEpd4(self):
    p = Position.epd('8/7p/2k1Pp2/pp1p2p1/3P2P1/4P3/P3K2P/8 w - -')
    self.assertEqual(p.board, Board([[".", ".", ".", ".", ".", ".", ".", "."],
                                     [".", ".", ".", ".", ".", ".", ".", "p"],
                                     [".", ".", "k", ".", "P", "p", ".", "."],
                                     ["p", "p", ".", "p", ".", ".", "p", "."],
                                     [".", ".", ".", "P", ".", ".", "P", "."],
                                     [".", ".", ".", ".", "P", ".", ".", "."],
                                     ["P", ".", ".", ".", "K", ".", ".", "P"],
                                     [".", ".", ".", ".", ".", ".", ".", "."]]))
    self.assertEqual(p.to_move, "w")
    self.assertEqual(p.castling, "")
    self.assertEqual(p.ep_target, None)

  def testEpdSometimesUsesTabs(self):
    p = Position.epd('4rrk1/1bp2ppp/p1q2b1B/1pn2B2/4N1Q1/2P4P/PP3PP1/3RR1K1 w - - bm Nxc5; id	"ECM.1016";')


class TestMove(unittest.TestCase):
  def testLan(self):
    self.assertEqual(Move.lan("e2e4"), Move(fro=Square.e2, to=Square.e4))
    self.assertEqual(Move.lan("b7b8q"), Move(fro=Square.b7, to=Square.b8, promo="q"))

  def testStr(self):
    self.assertEqual(str(Move(fro=Square.e2, to=Square.e4)), "e2e4")
    self.assertEqual(str(Move(fro=Square.b7, to=Square.b8, promo="q")), "b7b8q")

  def testSanPawns(self):
    p = Position.epd("8/7p/2k1Pp2/pp1p2p1/3P2P1/4P3/P3K2P/8 w - -")
    self.assertEqual(Move.san("e4", p), Move(fro=Square.e3, to=Square.e4))
    p = Position.epd("8/4P3/8/N1K5/k7/8/7q/8 w - -")
    self.assertEqual(Move.san("e8=Q+", p), Move(fro=Square.e7, to=Square.e8, promo="q"))
    self.assertEqual(Move.san("e8Q+", p), Move(fro=Square.e7, to=Square.e8, promo="q"))
    p = Position.epd("2rq1rk1/p2nbppp/bp6/2P5/2p5/1PB3P1/P2N1PBP/R2Q1RK1 w - -")
    self.assertEqual(Move.san("cxb6", p), Move(fro=Square.c5, to=Square.b6))
    p = Position.epd("qk4q1/5P2/8/1K6/8/8/8/8 w - -")
    self.assertEqual(Move.san("fxg8=Q+", p), Move(fro=Square.f7, to=Square.g8, promo="q"))
    p = Position.epd("r1bqkb1r/pp2pppp/1nnp4/1B2P3/3P4/5N2/PP3PPP/RNBQK2R b KQkq -")
    self.assertEqual(Move.san("dxe5", p), Move(fro=Square.d6, to=Square.e5))
    p = Position.epd("r1bq1rk1/pppp1ppp/2n2n2/6N1/2P1p3/2b3P1/PP1PPPBP/R1BQ1RK1 w - -")
    self.assertEqual(Move.san("bxc3", p), Move(fro=Square.b2, to=Square.c3))

  def testSanPieceOnly(self):
    p = Position.epd("r3kb1r/1bqn2pp/p3pn2/1pp5/4P3/2NB1N2/PP3PPP/R1BQ1RK1 w kq -")
    self.assertEqual(Move.san("Bc2", p), Move(fro=Square.d3, to=Square.c2))
    p = Position.epd("2rq2k1/1p3pb1/1n4pp/pP2p3/P1b1P3/2N4P/2B1NPP1/R1Q3K1 b - -")
    self.assertEqual(Move.san("Bf8", p), Move(fro=Square.g7, to=Square.f8))
    self.assertEqual(Move.san("Bg7f8", p), Move(fro=Square.g7, to=Square.f8))
    p = Position.epd("r3kb1r/1bqn2pp/p3pn2/1pp5/4P3/2NB1N2/PP3PPP/R1BQ1RK1 w kq -")
    self.assertEqual(Move.san("Ng5", p), Move(fro=Square.f3, to=Square.g5))
    p = Position.epd("1r1rb1k1/5ppp/4p3/1p1p3P/1q2P2Q/pN3P2/PPP4P/1K1R2R1 w - -")
    self.assertEqual(Move.san("Rxg7+", p), Move(fro=Square.g1, to=Square.g7))

  def testSanChecks(self):
    p = Position.epd("8/8/8/8/8/4N3/3N4/K1k1q3 w - -")
    self.assertEqual(Move.san("Nb3#", p), Move(fro=Square.d2, to=Square.b3))
    p = Position.epd("k1q5/2K5/7p/8/8/8/6P1/8 w - -")
    self.assertEqual(Move.san("Kxc8", p), Move(fro=Square.c7, to=Square.c8))
    p = Position.epd("2r1b3/p3kpp1/7p/3P4/7P/2p1KPP1/P7/1BR5 w - -")
    self.assertEqual(Move.san("Kd4", p), Move(fro=Square.e3, to=Square.d4))

  def testSanFromFile(self):
    p = Position.epd("2k4r/pb1r1p2/5P2/2qp4/1pp3Q1/6P1/1P3PBP/R4RK1 w - -")
    self.assertEqual(Move.san("Rfe1", p), Move(fro=Square.f1, to=Square.e1))
    p = Position.epd("5r1k/2p3q1/1p1npr2/pPn1N1pp/P1PN4/R4PPP/4Q1K1/3R4 w - -")
    self.assertEqual(Move.san("Ndc6", p), Move(fro=Square.d4, to=Square.c6))
    p = Position.epd("3r3r/p4pk1/5Rp1/3q4/1p1P2RQ/5N2/P1P4P/2b4K w - -")
    self.assertEqual(Move.san("Rfxg6+", p), Move(fro=Square.f6, to=Square.g6))

  def testSanCastling(self):
    p = Position.epd("r2q1rk1/pp1bppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ -")
    self.assertEqual(Move.san("O-O-O", p), Move(fro=Square.e1, to=Square.c1))
    p = Position.epd("r2qk2r/3n1ppp/p3p3/3nP3/3R4/5N2/1P1N1PPP/3QR1K1 b kq -")
    self.assertEqual(Move.san("O-O", p), Move(fro=Square.e8, to=Square.g8))
    p = Position.epd("4r2k/3qbp2/p3bp1p/8/8/P1RQ4/1PP2PPP/2K1R3 b - -")
    self.assertEqual(Move.san("Qa4", p), Move(fro=Square.d7, to=Square.a4))

  @unittest.skip("useful for debugging but goofy as a test")
  def testAllSanExamples(self):
    import glob
    for filename in glob.glob("benchmarks/*.epd"):
      with open(filename) as f:
        print(filename)
        for line in f:
          print(line)
          p = Position.epd(line.strip())
          if "bm" in p.ops:
            bm = p.ops["bm"].split(" ")
            print(":{}:".format(bm[0]))
            m = Move.san(bm[0], p)


class TestReferenceMoveGen(unittest.TestCase):
  def setUp(self):
    self.move_gen = ReferenceMoveGen()

  def testPerftInitial(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=1), 20)

  def testPerftInitialDepth2(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=2), 400)

  def testPerftInitialDepth3(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=3), 8902)

  @unittest.skip("slow")
  def testPerftInitialDepth4(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=4), 197281)

  @unittest.skip("really slow")
  def testPerftInitialDepth5(self):
    p = Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=5), 4865609)

  def testPerftJones1(self):
    p = Position.fen("r6r/1b2k1bq/8/8/7B/8/8/R3K2R b QK - 3 2")
    self.assertEqual(perft(p, self.move_gen, depth=1), 8)

  def testPerftJones2(self):
    p = Position.fen("8/8/8/2k5/2pP4/8/B7/4K3 b - d3 5 3")
    self.assertEqual(perft(p, self.move_gen, depth=1), 8)

  def testPerftJones3(self):
    p = Position.fen("r1bqkbnr/pppppppp/n7/8/8/P7/1PPPPPPP/RNBQKBNR w QqKk - 2 2")
    self.assertEqual(perft(p, self.move_gen, depth=1), 19)

  def testPerftJones4(self):
    p = Position.fen("r3k2r/p1pp1pb1/bn2Qnp1/2qPN3/1p2P3/2N5/PPPBBPPP/R3K2R b QqKk - 3 2")
    self.assertEqual(perft(p, self.move_gen, depth=1), 5)

  def testPerftJones5(self):
    p = Position.fen("2kr3r/p1ppqpb1/bn2Qnp1/3PN3/1p2P3/2N5/PPPBBPPP/R3K2R b QK - 3 2")
    self.assertEqual(perft(p, self.move_gen, depth=1), 44)

  def testPerftJones6(self):
    p = Position.fen("rnb2k1r/pp1Pbppp/2p5/q7/2B5/8/PPPQNnPP/RNB1K2R w QK - 3 9")
    self.assertEqual(perft(p, self.move_gen, depth=1), 39)

  def testPerftJones7(self):
    p = Position.fen("2r5/3pk3/8/2P5/8/2K5/8/8 w - - 5 4")
    self.assertEqual(perft(p, self.move_gen, depth=1), 9)

  def testPerftJones8(self):
    p = Position.fen("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8")
    self.assertEqual(perft(p, self.move_gen, depth=3), 62379)

  def testPerftJones9(self):
    p = Position.fen("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10")
    self.assertEqual(perft(p, self.move_gen, depth=3), 89890)

  @unittest.skip("slow")
  def testPerftJones10(self):
    p = Position.fen("3k4/3p4/8/K1P4r/8/8/8/8 b - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 1134888)

  @unittest.skip("slow")
  def testPerftJones11(self):
    p = Position.fen("8/8/4k3/8/2p5/8/B2P2K1/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 1015133)

  @unittest.skip("slow")
  def testPerftJones12(self):
    p = Position.fen("8/8/1k6/2b5/2pP4/8/5K2/8 b - d3 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 1440467)

  @unittest.skip("slow")
  def testPerftJones13(self):
    p = Position.fen("5k2/8/8/8/8/8/8/4K2R w K - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 661072)

  @unittest.skip("slow")
  def testPerftJones14(self):
    p = Position.fen("3k4/8/8/8/8/8/8/R3K3 w Q - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 803711)

  @unittest.skip("slow")
  def testPerftJones15(self):
    p = Position.fen("r3k2r/1b4bq/8/8/8/8/7B/R3K2R w KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=2), 1141)
    self.assertEqual(perft(p, self.move_gen, depth=4), 1274206)

  @unittest.skip("slow")
  def testPerftJones16(self):
    p = Position.fen("r3k2r/8/3Q4/8/8/5q2/8/R3K2R b KQkq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=4), 1720476)

  @unittest.skip("slow")
  def testPerftJones17(self):
    p = Position.fen("2K2r2/4P3/8/8/8/8/8/3k4 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 3821001)

  @unittest.skip("slow")
  def testPerftJones18(self):
    p = Position.fen("8/8/1P2K3/8/2n5/1q6/8/5k2 b - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=5), 1004658)

  def testPerftJones19(self):
    p = Position.fen("4k3/1P6/8/8/8/8/K7/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 217342)

  def testPerftJones20(self):
    p = Position.fen("8/P1k5/K7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 92683)

  def testPerftJones21(self):
    p = Position.fen("K1k5/8/P7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=6), 2217)

  def testPerftJones22(self):
    p = Position.fen("8/k1P5/8/1K6/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=7), 567584)

  def testPerftJones23(self):
    p = Position.fen("8/8/2k5/5q2/5n2/8/5K2/8 b - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=4), 23527)

  def testPerftKiwipeteDepth3(self):
    p = Position.fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=3), 97862)

  @unittest.skip("slow")
  def testPerftKiwipeteDepth4(self):
    p = Position.fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=4), 4085603)

  def testPerftCporgPosition3Depth4(self):
    p = Position.fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=4), 43238)

  @unittest.skip("slow")
  def testPerftCporgPosition3Depth5(self):
    p = Position.fen("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=5), 674624)

  def testPerftCporgPosition4Depth3(self):
    p = Position.fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=3), 9467)

  @unittest.skip("slow")
  def testPerftCporgPosition4Depth4(self):
    p = Position.fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=4), 422333)

  def testPerftTalkchess(self):
    p = Position.fen("rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8")
    self.assertEqual(perft(p, self.move_gen, depth=3), 62379)

  def testPerftEdwardsDepth3(self):
    p = Position.fen("r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10")
    self.assertEqual(perft(p, self.move_gen, depth=3), 89890)

  @unittest.skip("slow and sorta redundant")
  def testPerftSuite(self):
    with open("benchmarks/perftsuite.epd") as f:
      for line in f:
        line = line.strip()
        print(line)
        p = Position.epd(line)
        for depth in range(1, 7):
          depth_key = "D" + str(depth)
          if not depth_key in p.ops: break
          node_count = int(p.ops[depth_key], 10)
          if node_count < 200000:
            self.assertEqual(perft(p, self.move_gen, depth=depth), node_count)
          else:
            break

  def testNoEnPassant(self):
    self.move_gen = ReferenceMoveGen(allow_en_passant_captures=False)
    p = Position.fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=2), 2039 - 1)

  def testNoCastling(self):
    self.move_gen = ReferenceMoveGen(allow_castling=False)
    p = Position.fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 0")
    self.assertEqual(perft(p, self.move_gen, depth=1), 48 - 2)

  def testNoPromotion(self):
    self.move_gen = ReferenceMoveGen(allowed_promotions="")
    p = Position.fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=2), 264 - 48)

  def testOnlyQueenPromotion(self):
    self.move_gen = ReferenceMoveGen(allowed_promotions="q")
    p = Position.fen("r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=2), 264 - 36)

  def testIgnoreCheckFalse(self):
    self.move_gen = ReferenceMoveGen(ignore_check=False)
    p = Position.fen("k7/8/K7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=1), 3)

  def testIgnoreCheckFalse_Pin(self):
    self.move_gen = ReferenceMoveGen(ignore_check=False)
    p = Position.fen("k1q5/1R6/K7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=1), 3)

  def testIgnoreCheckTrue(self):
    self.move_gen = ReferenceMoveGen(ignore_check=True)
    p = Position.fen("k7/8/K7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=1), 5)

  def testIgnoreCheckTrue_Pin(self):
    self.move_gen = ReferenceMoveGen(ignore_check=True)
    p = Position.fen("k1q5/1R6/K7/8/8/8/8/8 w - - 0 1")
    self.assertEqual(perft(p, self.move_gen, depth=1), 14 + 4)


if __name__ == "__main__":
  unittest.main()
