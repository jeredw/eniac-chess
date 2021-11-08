#!/usr/bin/env python
from dataclasses import dataclass
from typing import List

@dataclass
class Move:
  depth: str
  from_square: str
  to_square: str
  best_score: str
  children: List['Move']
  best: 'Move'

  def __repr__(self):
    if self.best:
      return f'{self.depth} {self.from_square}{self.to_square} best={self.best}/{self.best.best_score}'
    return f'{self.depth} {self.from_square}{self.to_square} best=0'

def print_tree(move):
  if move.children:
    print(f'<details class=indent>')
    print(f'<summary>{move}</summary>')
    for child_move in move.children:
      print_tree(child_move)
    print(f'</details>')
  else:
    print(f'<div class=indent>{move}</div>')

stack = [Move(0, '00', '00', '00', [], None)]
with open('/tmp/debug', 'r') as f:
  pop = False
  part = 0
  depth, score = '', ''
  for line in f.readlines():
    line = line.strip()
    if line[:2] == '99':
      pop = True
      part = 0
    elif part == 0:
      depth, best_score = line[:2], line[2:4]
      part = 1
    elif part == 1:
      from_square, to_square = line[:2], line[2:4]
      move = Move(depth, from_square, to_square, best_score, [], None)
      if depth == '04':
        stack[-1].children.append(move)
      elif not pop:
        if stack: stack[-1].children.append(move)
        stack.append(move)
      else:
        if stack: stack[-1].best = move
        stack.pop()
      assert len(stack) < 5
      pop = False
      part = 0
assert len(stack) == 1
print('<style>.indent { padding-left: 40px }</style>')
print_tree(stack[0])