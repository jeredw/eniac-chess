import math

from uciengine import UCIEngine
from game import ReferenceMoveGen, empty

class TestEngine(UCIEngine):
  """A really dumb reference engine."""

  def __init__(self):
    super().__init__(name="Cheetah", author="et al")
    self.node_count = 0
    self.fail_hard = 0
    self.leaf_non_captures = 0
    self.move_gen = ReferenceMoveGen(allow_castling=False,
                                     allow_en_passant_captures=False,
                                     allowed_promotions='q')

  def evaluate(self, position, depth=4):
    """Depth-first negamax search.

    position is the start position for the search and h is the heuristic function
    for evaluating positions.  h values should be relative to the player to move.
    """
    self.node_count = 0
    self.fail_hard = 0
    self.leaf_non_captures = 0
    best_move = None
    best_score = -math.inf
    for move, p2 in self.move_gen.legal_moves(position):
      score = -self._dfs(p2, -math.inf, math.inf, depth - 1)
      if score > best_score:
        best_move = move
        best_score = score
      if self.stop.is_set():
        break
    self.log.debug(f'{self.node_count} nodes searched, {self.fail_hard} ab pruned')
    self.log.debug(f'{self.leaf_non_captures} leaf non capture moves')
    return best_move

  def _dfs(self, position, alpha, beta, depth):
    if depth == 0:
      self.node_count += 1
      return _coarse_material(position)
    for move, p2 in self.move_gen.legal_moves(position):
      if depth == 1 and position.board[move.to] == empty:
        self.leaf_non_captures += 1
      score = -self._dfs(p2, -beta, -alpha, depth - 1)
      if score >= beta:
        self.fail_hard += 1
        return beta
      if score > alpha:
        alpha = score
    return alpha


_coarse_piece_value = {
  "k": 0, "p": -1, "b": -3, "n": -3, "r": -5, "q": -9,
  "K": 0, "P": +1, "B": +3, "N": +3, "R": +5, "Q": +9
}
def _coarse_material(position):
  """Returns a coarse material evaluation of a position."""
  score = 0
  for sq, piece in position.board:
    score += _coarse_piece_value[piece]
  return score if position.to_move == "w" else -score
