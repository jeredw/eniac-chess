#!/usr/bin/env python
# Simple model for legal move gen
# We don't bother representing the full VM and packed board, but duplicate some basic 
# mechanics like the square numbering and a JIL equivalent (illegal_square)

# side, piece representation for this test code. 
WHITE = 1
BLACK = 2
EMPTY = 0
PAWN = 1
KNIGHT = 2
BISHOP = 3
ROOK = 4
QUEEN = 5
KING = 6

# the board
board = [[(0,0)] * 8] * 8

def init_board():
  global board
	board = [ 
		[ (WHITE,ROOK), (WHITE,KNIGHT), (WHITE,BISHOP), (WHITE,QUEEN), (WHITE,KING), (WHITE,BISHOP), (WHITE,KNIGHT), (WHITE,ROOK) ],
		[ (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), (WHITE,PAWN), ],
		[ [(0,0)]*8 ],
		[ [(0,0)]*8 ],
		[ [(0,0)]*8 ],
		[ [(0,0)]*8 ],
		[ (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), (BLACK,PAWN), ],
		[ (BLACK,ROOK), (BLACK,KNIGHT), (BLACK,BISHOP), (BLACK,QUEEN), (BLACK,KING), (BLACK,BISHOP), (BLACK,KNIGHT), (BLACK,ROOK) ]
	]

def get_square(sq):
	global board
	f = (sq % 10) - 1
	r = (sq // 10) - 1
	return board[r][f]

def illegal_square(sq):
	f = (sq % 10) - 1
	r = (sq // 10) - 1
	return f<1 or f>8 or r<1 or r>8

# setup
init_board()
from_square=11
enum_dir=9
enum_step=0

# spit out all moves
def next_move():
	global from_square
	global enum_dir
	global enum_step

	must_capture = False
	cant_capture = False

	# find a piece we can move; enum_dir=9 means done previous piece
	while enum_dir == 9:
		(side, piece) = get_square(from_square)

		if side != WHITE:
				# Advance to next square
				from_square += 1
				if illegal_square(from_square):
					from_square += 9	# advance to next rank
				if illegal_square(from_square):
					return 0 					# no more squares!
		else:
			# found one of our pieces, start enumeration
			enum_dir = 0

	# generate next move for current  piece
	to_square = from_square

	if piece==PAWN:
		if enum_dir == 0:
			# push
			to_square += 10				# push
			if enum_step == 1:	
				to_square += 10			# double push

			if from_square < 30:  # pawn has not moved yet
				enum_step += 1
			else:
				enum_dir += 1

			cant_capture = True

		else:

			# capture
			if enum_dir == 1:
				to_square += 9  		# up and left
				enum_dir = 2
			else:
				to_square += 11  		# up and right
				enum_dir = 9

			must_capture = True

	elif piece==BISHOP or piece==ROOK or piece==QUEEN or piece==KING:
		# Direction LUT
		dirlut = [ 
			-1, 	# left
			1,		# right
			10,		# up
			-10,	# down
			9,		# up left
			11,		# up right
			-9,		# down right
			-11		# down left
		]
		startlut = 
			



	else:
		# knight









	



