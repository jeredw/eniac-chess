import math

from uciengine import UCIEngine
from game import ReferenceMoveGen, empty, white_pieces, black_pieces, Square

class TestEngine(UCIEngine):
  """A simple model of the eniac chess algorithm for experimentation."""

  def __init__(self):
    super().__init__(name="Cheetah", author="et al")
    self.debug_file = open("/tmp/moves.out", "w")
    self.node_count = 0
    self.pruned = 0
    self.leaf_non_captures = 0
    self.update_ab_at_depth_1 = True
    self.move_gen = ReferenceMoveGen(allow_castling=False,
                                     allow_en_passant_captures=False,
                                     allowed_promotions='q')

  def evaluate(self, position, depth=4):
    """Depth-first minimax search"""
    self.node_count = 0
    self.pruned = 0
    self.leaf_non_captures = 0
    best_move, best_score = self._search(position, 0, 99, depth)
    self.log.debug(f'best move {best_move} score {best_score}')
    self.log.debug(f'{self.node_count} nodes searched, {self.pruned} pruned')
    self.log.debug(f'{self.leaf_non_captures} leaf non capture moves')
    return best_move

  def _score(self, position):
    return 50 + _coarse_material(position) + _center_score(position)

  def _search(self, position, alpha, beta, depth):
    if depth == 0:
      self.node_count += 1
      return None, self._score(position)

    best_move = None
    best_score = 0 if position.to_move == 'w' else 99
    for move, p2 in self.move_gen.legal_moves(position):
      print(_numeric(move), file=self.debug_file)
      if self.stop.is_set():
        break
      if beta <= alpha:
        print('pruned', file=self.debug_file)
        self.pruned += 1
        break
      if depth == 1 and position.board[move.to] == empty:
        self.leaf_non_captures += 1
        score = self._score(position)
      else:
        _, score = self._search(p2, alpha, beta, depth - 1)
      if self.update_ab_at_depth_1 or depth != 1:
        if position.to_move == 'w' and score > alpha:
          alpha = score
        elif position.to_move == 'b' and score < beta:
          beta = score
      if ((position.to_move == 'w' and score > best_score) or
          (position.to_move == 'b' and score < best_score)):
        best_move = move
        best_score = score
    return best_move, best_score


_coarse_piece_value = {
  "k": 0, "p": -3, "b": -6, "n": -6, "r": -15, "q": -27,
  "K": 0, "P": +3, "B": +6, "N": +6, "R": +15, "Q": +27
}
def _coarse_material(position):
  """Returns a coarse material evaluation of a position."""
  score = 0
  for sq, piece in position.board:
    score += _coarse_piece_value[piece]
  return score

def _center_score(position):
  """Returns center occupancy bonus for position."""
  score = 0
  for x in range(3, 6+1):
    for y in range(3, 6+1):
      here = position.board[Square(x, y)]
      score += (1 if here in white_pieces else
               -1 if here in black_pieces else 0)
  return score

def _numeric(move):
  return f"{move.fro.y}{move.fro.x}{move.to.y}{move.to.x}"
