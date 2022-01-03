#!/usr/bin/env python
from dataclasses import dataclass
from typing import List

@dataclass
class Move:
  depth: str
  from_square: str
  to_square: str
  best_score: str
  alpha: str
  beta: str
  children: List['Move']
  best: 'Move'
  is_best: bool

  def __repr__(self):
    if self.best:
      return f'{self.best_score} {self.from_square}{self.to_square} {self.alpha}/{self.beta} best={self.best}'
    return f'{self.best_score} {self.from_square}{self.to_square} {self.alpha}/{self.beta}'

def print_tree(move):
  if move.children:
    print(f'<details class=indent>')
    print(f'<summary>{move}</summary>')
    for child_move in move.children:
      print_tree(child_move)
    print(f'</details>')
  else:
    print(f'<div class=indent>{move}</div>')

stack = [Move(0, '00', '00', '00', '00', '99', [], None, False)]
with open('/tmp/debug', 'r') as f:
  pop = False
  part = 0
  depth, best_score = '', ''
  alpha, beta = '', ''
  for num, line in enumerate(f.readlines()):
    line = line.strip()
    if line[:2] == '99':
      pop = True
      part = 0
    elif part == 0:
      depth, best_score = line[:2], line[2:4]
      part = 1
    elif part == 1:
      from_square, to_square = line[:2], line[2:4]
      part = 2
    elif part == 2:
      alpha, beta = line[:2], line[2:4]
      move = Move(depth=depth,
                  from_square=from_square,
                  to_square=to_square,
                  best_score=best_score,
                  alpha=alpha,
                  beta=beta,
                  children=[],
                  best=None,
                  is_best=False)
      if depth == '04':
        stack[-1].children.append(move)
      elif not pop:
        if stack: stack[-1].children.append(move)
        stack.append(move)
      else:
        if depth != stack[-1].depth:
          stack.pop()
        stack.pop()
        if stack:
          stack[-1].best = move
          stack[-1].best_score = move.best_score
          move.is_best = True
      assert len(stack) < 5
      pop = False
      part = 0
assert len(stack) == 1
print('''
<style>
.indent { padding-left: 40px }
.best { background: #ccc }
</style>
''')
print_tree(stack[0])