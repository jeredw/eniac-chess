#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""High-level models for chess gameplay and interchange formats."""

import re
import copy

white_pieces = "RNBQKP"
black_pieces = "rnbqkp"
rook, knight, bishop, queen, king, pawn = range(6)

def _piece_for_color(piece, color):
  return piece.upper() if color == "w" else piece.lower()


empty = "."
rook_deltas = [(0, -1), (0, 1), (-1, 0), (1, 0)]
bishop_deltas = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
queen_deltas = rook_deltas + bishop_deltas
king_deltas = queen_deltas
knight_deltas = [(-1, -2), (-2, -1), (-1, 2), (-2, 1), (1, -2), (2, -1), (1, 2), (2, 1)]
file_names = " abcdefgh"
rank_names = " 12345678"


class Square(object):
  def __init__(self, x=0, y=0):
    if isinstance(x, str):
      assert len(x) == 2
      self.x = file_names.index(x[0])
      self.y = rank_names.index(x[1])
    else:
      self.x = x
      self.y = y
    self.in_bounds = 1 <= self.x <= 8 and 1 <= self.y <= 8

  def __str__(self):
    return file_names[self.x] + rank_names[self.y]

  def __repr__(self):
    return 'Square("{}")'.format(self)

  def __eq__(self, other):
    if isinstance(other, str):
      return self == Square(other)
    return self.x == other.x and self.y == other.y

  def __add__(self, deltas):
    dx, dy = deltas
    return Square(x=self.x + dx, y=self.y + dy)

Square.a1 = Square("a1")
Square.h1 = Square("h1")
Square.a8 = Square("a8")
Square.h8 = Square("h8")


class Board(object):
  def __init__(self, ranks=None, white_king_square=None, black_king_square=None):
    self.ranks = ranks
    self.white_king_square = white_king_square or self.find("K")
    self.black_king_square = black_king_square or self.find("k")

  @staticmethod
  def unpack(fen):
    ranks = []
    for packed_rank in fen.split("/"):
      rank = []
      for ch in packed_rank:
        if ch in white_pieces + black_pieces:
          rank.append(ch)
        else:
          rank.extend(empty * int(ch, 10))
      assert len(rank) == 8
      ranks.append(rank)
    assert len(ranks) == 8
    return Board(ranks=ranks)

  def pack(self):
    fen = "/".join("".join(rank) for rank in self.ranks)
    for num_dots in range(8, 0, -1):
      fen = fen.replace(empty * num_dots, str(num_dots))
    return fen

  def pretty_print(self):
    for rank in self.ranks:
      print(''.join(rank))

  def __iter__(self):
    for y, rank in enumerate(self.ranks):
      for x, piece in enumerate(rank):
        if piece != empty:
          yield (Square(x=x+1, y=8-y), piece)

  def __getitem__(self, pos):
    if isinstance(pos, str):
      pos = Square(pos)
    assert pos.in_bounds
    return self.ranks[8 - pos.y][pos.x - 1]

  def __setitem__(self, pos, piece):
    if isinstance(pos, str):
      pos = Square(pos)
    assert pos.in_bounds
    if piece == "K":
      self.white_king_square = pos
    elif piece == "k":
      self.black_king_square = pos
    self.ranks[8 - pos.y][pos.x - 1] = piece

  def __eq__(self, other):
    return all(a == b for a, b in zip(self, other))

  def find(self, piece):
    for sq, there in self:
      if there == piece:
        return sq


class Position(object):
  def __init__(self, board=None, to_move=None, castling=None, ep_target=None, ops=None):
    self.board = board
    self.to_move = to_move
    # Just the move history part of eligibility for castling.
    self.castling = castling
    # This is the square skipped in the last double pawn push, regardless of
    # whether an en passant capture is actually possible; this code doesn't
    # sanitize it.  This field is contentious:
    # http://www.talkchess.com/forum3/viewtopic.php?t=37879
    self.ep_target = ep_target
    self.ops = ops

  def __deepcopy__(self, memodict={}):
    # Really helps with runtime for perft tests because copy.deepcopy() is slow.
    board = Board(ranks=[[p for p in rank] for rank in self.board.ranks],
                  white_king_square=self.board.white_king_square,
                  black_king_square=self.board.black_king_square)
    # These are treated as immutable.
    to_move = self.to_move
    ep_target = self.ep_target
    castling = self.castling
    ops = self.ops
    return Position(board=board,
                    to_move=to_move,
                    castling=castling,
                    ep_target=ep_target,
                    ops=ops)

  @staticmethod
  def start():
    return Position.fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

  @staticmethod
  def fen(fen):
    # rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
    (packed_board, to_move, castling, ep_target, halfmove_clock, fullmove) = fen.split()
    assert to_move in ("w", "b")
    assert castling == "-" or all(ch in "KQkq" for ch in castling)
    assert ep_target == "-" or ep_target[1] in ("3", "6")
    return Position(board=Board.unpack(packed_board),
                    to_move=to_move,
                    castling=(castling if castling != "-" else ""),
                    ep_target=(Square(ep_target) if ep_target != "-" else None),
                    ops={"hmvc": halfmove_clock, "fmvn": fullmove})

  def to_fen(self):
    fen = []
    fen.append(self.board.pack())
    fen.append(self.to_move)
    fen.append("".join(sorted(self.castling)) if self.castling else "-")
    fen.append(str(self.ep_target) if self.ep_target else "-")
    fen.append(self.ops["hmvc"])
    fen.append(self.ops["fmvn"])
    return " ".join(fen)

  @staticmethod
  def epd(epd):
    # 1kr5/3n4/q3p2p/p2n2p1/PppB1P2/5BP1/1P2Q2P/3R2K1 w - - bm f5; id "Undermine.001"; c0 "f5=10, Be5+=2, Bf2=3, Bg4=2";
    (packed_board, to_move, castling, ep_target, ops) = (epd + " ").split(" ", 4)
    assert to_move in ("w", "b")
    assert castling == "-" or all(ch in "KQkq" for ch in castling)
    assert ep_target == "-" or ep_target[1] in ("3", "6")
    return Position(board=Board.unpack(packed_board),
                    to_move=to_move,
                    castling=(castling if castling != "-" else ""),
                    ep_target=(Square(ep_target) if ep_target != "-" else None),
                    ops=_parse_epd_ops(ops))


def _parse_epd_ops(s):
  # bm f5; id "Undermine.001"; c0 "f5=10, Be5+=2, Bf2=3, Bg4=2";
  ops = {}
  i = 0; n = len(s)
  def skip_of(chars):
    nonlocal i
    while i < n and s[i] in chars:
      i += 1
  def take_not_of(chars):
    nonlocal i
    start = i
    while i < n and s[i] not in chars:
      i += 1
    return s[start:i]
  def expect(ch):
    nonlocal i
    assert i < n and s[i] == ch
    i += 1
  while i < n:
    skip_of(" \t")
    if i >= n: break
    op = take_not_of(" \t")
    skip_of(" \t")
    arg = ""
    if s[i] == ";":
      pass
    elif s[i] == '"':
      i += 1; arg = take_not_of('"'); i += 1
    else:
      arg = take_not_of(";")
    expect(";")
    ops[op] = arg
  return ops


class Move(object):
  def __init__(self, fro=None, to=None, promo=""):
    self.fro = fro
    self.to = to
    self.promo = promo  # lowercase

  @staticmethod
  def lan(s):
    assert 4 <= len(s) <= 5
    fro = Square(s[0:2])
    to = Square(s[2:4])
    promo = ""
    if len(s) == 5:
      assert(s[4] in "rnbq")
      promo = s[4]
    return Move(fro=fro, to=to, promo=promo)

  def __str__(self):
    return "".join([str(self.fro), str(self.to), self.promo])

  def __repr__(self):
    return 'Move.lan("{}")'.format(str(self))

  @staticmethod
  def san(s, position):
    s = s.rstrip("+#")
    if s == "O-O" or s == "0-0":
      return Move.black_oo if position.to_move == "b" else Move.white_oo
    if s == "O-O-O" or s == "0-0-0":
      return Move.black_ooo if position.to_move == "b" else Move.white_ooo
    m = re.match(r"^([RNBQK])([a-h]|[1-8]|[a-h][1-8])x?([a-h][1-8])$", s)
    if m:
      piece, from_desc, to_desc = m.groups()
      piece = _piece_for_color(piece, position.to_move)
      return _disambiguate_san(position, piece, from_desc, to_desc)
    m = re.match(r"^([RNBQK])x?([a-h][1-8])$", s)
    if m:
      piece, to_desc = m.groups()
      piece = _piece_for_color(piece, position.to_move)
      return _disambiguate_san(position, piece, '', to_desc)
    m = re.match(r"^([a-h]|[a-h][1-8])x?([a-h][1-8])=?([RNBQ]?)$", s)
    if m:
      from_desc, to_desc, promo = m.groups()
      piece = _piece_for_color("p", position.to_move)
      return _disambiguate_san(position, piece, from_desc, to_desc, promo.lower())
    m = re.match(r"^([a-h][1-8])=?([RNBQ]?)$", s)
    assert m
    to_desc, promo = m.groups()
    piece = _piece_for_color("p", position.to_move)
    return _disambiguate_san(position, piece, '', to_desc, promo.lower())

  def __eq__(self, other):
    return (self.fro == other.fro and
            self.to == other.to and
            self.promo == other.promo)

Move.white_ooo = Move.lan("e1c1")
Move.white_oo = Move.lan("e1g1")
Move.black_ooo = Move.lan("e8c8")
Move.black_oo = Move.lan("e8g8")

def _is_castling_move(position, move):
  piece = position.board[move.fro]
  if piece.lower() == "k":
    if move == Move.white_oo:
      assert "K" in position.castling
      return True
    if move == Move.white_ooo:
      assert "Q" in position.castling
      return True
    if move == Move.black_oo:
      assert "k" in position.castling
      return True
    if move == Move.black_ooo:
      assert "q" in position.castling
      return True
  return False

def _disambiguate_san(position, piece, from_desc, to_desc, promo=''):
  to = Square(to_desc)
  result = None
  if len(from_desc) < 2:
    from_desc = from_desc or "-"
    from_rank = rank_names.find(from_desc)
    from_file = file_names.find(from_desc)
    for move in legal_moves(position):
      if ((from_rank == -1 or move.fro.y == from_rank) and
          (from_file == -1 or move.fro.x == from_file) and
          (move.to == to and position.board[move.fro] == piece and move.promo == promo)):
        assert not result
        result = move
    assert result
  else:
    result = Move(fro=Square(from_desc), to=to)
  return result

def make_move(position, move):
  piece = position.board[move.fro]
  p2 = copy.deepcopy(position)
  p2.to_move = "w" if position.to_move == "b" else "b"
  p2.ep_target = None
  if piece.lower() == "p":
    dx = move.to.x - move.fro.x
    dy = move.to.y - move.fro.y
    if abs(dy) == 2:
      p2.ep_target = move.fro + (0, dy/2)
    if dx != 0 and p2.board[move.to] == empty:
      ep_capture_square = Square(x=move.to.x, y=move.fro.y)
      ep_capture_piece = p2.board[ep_capture_square]
      assert ep_capture_piece.lower() == "p" and ep_capture_piece != piece
      p2.board[ep_capture_square] = empty
  _update_castling_eligibility(p2, move, piece)
  if _is_castling_move(position, move):
    _do_castling(p2, move)
  else:
    p2.board[move.fro] = empty
    if not move.promo:
      p2.board[move.to] = piece
    else:
      p2.board[move.to] = _piece_for_color(move.promo, position.to_move)
  return p2

def _update_castling_eligibility(position, move, piece):
  mask = position.castling
  if (piece == "R" and move.fro == Square.h1) or move.to == Square.h1:
    mask = mask.replace("K", "")
  if (piece == "R" and move.fro == Square.a1) or move.to == Square.a1:
    mask = mask.replace("Q", "")
  if piece == "K":
    mask = mask.replace("K", "")
    mask = mask.replace("Q", "")
  if (piece == "r" and move.fro == Square.h8) or move.to == Square.h8:
    mask = mask.replace("k", "")
  if (piece == "r" and move.fro == Square.a8) or move.to == Square.a8:
    mask = mask.replace("q", "")
  if piece == "k":
    mask = mask.replace("k", "")
    mask = mask.replace("q", "")
  position.castling = mask

def _do_castling(position, move):
  if move == Move.white_oo:
    position.board["e1"] = empty
    position.board["f1"] = "R"
    position.board["g1"] = "K"
    position.board["h1"] = empty
  elif move == Move.white_ooo:
    position.board["a1"] = empty
    position.board["c1"] = "K"
    position.board["d1"] = "R"
    position.board["e1"] = empty
  elif move == Move.black_oo:
    position.board["e8"] = empty
    position.board["f8"] = "r"
    position.board["g8"] = "k"
    position.board["h8"] = empty
  elif move == Move.black_ooo:
    position.board["a8"] = empty
    position.board["c8"] = "k"
    position.board["d8"] = "r"
    position.board["e8"] = empty

def _slide_moves(position, fro, own_pieces, deltas):
  for dx, dy in deltas:
    for n in range(1, 8):
      to = fro + (dx * n, dy * n)
      if not to.in_bounds:
        break
      there = position.board[to]
      if there == empty:
        yield Move(fro=fro, to=to)
      else:
        if there not in own_pieces:
          yield Move(fro=fro, to=to)
        break

def _step_moves(position, fro, own_pieces, deltas):
  for dx, dy in deltas:
    to = fro + (dx, dy)
    if to.in_bounds:
      there = position.board[to]
      if there == empty or there not in own_pieces:
        yield Move(fro=fro, to=to)

def _pawn_push(fro, to):
  if to.y == 1 or to.y == 8:
    for promo in "rnbq":
      yield Move(fro=fro, to=to, promo=promo)
  else:
    yield Move(fro=fro, to=to)

def _pawn_moves(position, fro, own_pieces, dy):
  from_start_rank = (fro.y == 2 and dy == 1) or (fro.y == 7 and dy == -1)
  deltas = [dy, 2 * dy] if from_start_rank else [dy]
  for d in deltas:
    to = fro + (0, d)
    there = position.board[to]
    if there == empty:
      yield from _pawn_push(fro, to)
    else:
      break
  for dx in (-1, 1):
    to = fro + (dx, dy)
    if to.in_bounds:
      there = position.board[to]
      if position.ep_target and to == position.ep_target:
        passed_to = to + (0, -dy)
        if passed_to.in_bounds:
          there = position.board[passed_to]
          if there.lower() == "p" and there not in own_pieces:
            yield from _pawn_push(fro, to)
      elif there != empty and there not in own_pieces:
        yield from _pawn_push(fro, to)

def _castling_moves(position, own_pieces):
  r1 = lambda f: f + ("1" if position.to_move == "w" else "8")
  def can_castle(between, king_visits):
    # Can't castle out of check or through an occupied or attacked square.
    # It's ok that position.board has the king on the e file for all the
    # threatened() calls because it would not block any new threats.
    ok = (all(position.board[r1(fi)] == empty for fi in between) and
          not any(_threatened(position, position.to_move, Square(r1(fi)))
                  for fi in king_visits))
    return ok
  if own_pieces[king] in position.castling:
    assert position.board[r1("e")] == own_pieces[king]
    assert position.board[r1("h")] == own_pieces[rook]
    if can_castle(["f", "g"], ["e", "f", "g"]):
      yield Move.lan(r1("e") + r1("g"))
  if own_pieces[queen] in position.castling:
    assert position.board[r1("e")] == own_pieces[king]
    assert position.board[r1("a")] == own_pieces[rook]
    if can_castle(["b", "c", "d"], ["e", "d", "c"]):
      yield Move.lan(r1("e") + r1("c"))

def pseudo_legal_moves(position):
  own_pieces = black_pieces if position.to_move == "b" else white_pieces
  pawn_delta = -1 if position.to_move == "b" else +1
  for fro, piece in position.board:
    if piece == own_pieces[pawn]:
      yield from _pawn_moves(position, fro, own_pieces, pawn_delta)
    elif piece == own_pieces[rook]:
      yield from _slide_moves(position, fro, own_pieces, rook_deltas)
    elif piece == own_pieces[knight]:
      yield from _step_moves(position, fro, own_pieces, knight_deltas)
    elif piece == own_pieces[bishop]:
      yield from _slide_moves(position, fro, own_pieces, bishop_deltas)
    elif piece == own_pieces[queen]:
      yield from _slide_moves(position, fro, own_pieces, queen_deltas)
    elif piece == own_pieces[king]:
      yield from _step_moves(position, fro, own_pieces, king_deltas)
  yield from _castling_moves(position, own_pieces)

def _threatened(position, player, square):
  """Returns true if, after moving to position, square would be threatened.
     This is used to prune pseudo-legal moves that would lead to check, and so
     does not subject attacker moves to pins or check restrictions."""
  enemy_pieces = black_pieces if player == "w" else white_pieces
  for dx, dy in knight_deltas:
    fro = square + (dx, dy)
    if fro.in_bounds:
      there = position.board[fro]
      if there == enemy_pieces[knight]:
        return True
  for dx, dy in queen_deltas:
    for n in range(1, 8):
      fro = square + (dx * n, dy * n)
      if not fro.in_bounds:
        break
      there = position.board[fro]
      if there == empty:
        continue
      if there not in enemy_pieces:
        break
      # NB: Ignore en passant pawn captures.
      if (n == 1 and
          ((there == "p" and abs(dx) == 1 and dy == +1) or
           (there == "P" and abs(dx) == 1 and dy == -1))):
        return True
      if there.lower() == "r" and (dx == 0 or dy == 0):
        return True
      if there.lower() == "b" and not (dx == 0 or dy == 0):
        return True
      if there.lower() == "q":
        return True
      if there.lower() == "k" and n == 1:
        return True
      break
  return False

def legal_moves(position):
  for move in pseudo_legal_moves(position):
    if _is_castling_move(position, move):
      yield move
      continue
    p2 = make_move(position, move)
    king_square = (p2.board.white_king_square if position.to_move == "w" else
                   p2.board.black_king_square)
    assert king_square
    if not _threatened(p2, position.to_move, king_square):
      yield move

def perft(position, depth=1):
  if depth == 0: return 1
  moves = list(legal_moves(position))
  count = 0
  for move in moves:
    p2 = make_move(position, move)
    count += perft(p2, depth=depth-1)
  return count

if __name__ == "__main__":
  import cProfile
  p = Position.fen("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 0")
  cProfile.run("perft(p, depth=3)")
