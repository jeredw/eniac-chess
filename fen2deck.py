#!/usr/bin/env python
# Convert FEN notation into a deck that initializes the board
# Reads and writes from stdio
#
import sys

# side, piece representation for this test code. 
WHITE = 0
BLACK = 1

FROMP = 35  # fromp in memory_layout.asm, used to indicate current player

# piece encoding for add_piece
PAWN = 1
KNIGHT = 2
BISHOP = 3
QUEEN = 4
ROOK = 5
KING = 6

# piece encoding in memory
OTHER = 1
WPAWN = 2
WKNIGHT = 3
WBISHOP = 4
WQUEEN = 5
BPAWN = 6
BKNIGHT = 7
BBISHOP = 8
BQUEEN = 9

# addresses of separately encoded pieces in memory_layout.asm
WKING = 32
BKING = 33
WROOK = 34
WROOK2 = 45

# material score difference between white and black (50 is no difference)
MSCORE = 55

# we print the memory when we are done
memory = [0]*75

# player = WHITE,BLACK, piece=PAWN,KNIGHT,..., rank and file are 0..7
def add_piece(player, piece, rank, file):
	global memory
	loc0 = rank*8 + file
	loc = loc0 // 2

	if piece<=QUEEN:
		# pawn, knight, bishop, queen are stored directly
		digit = piece+WPAWN-PAWN if player==WHITE else piece+BPAWN-PAWN
	else:
		# king and rook encoded as other, their positions stored after board
		digit = OTHER
		square = (1+rank)*10+(1+file)
		if piece==KING:
				memory[WKING + player]=square
		else: 
			# piece == ROOK, but we only store positions of white rooks
			if player==WHITE:
				if memory[WROOK]==0:
					memory[WROOK]=square
				else:
					memory[WROOK2]=square

	if loc0%2:
		memory[loc] += digit
	else:
		memory[loc] += digit*10


def read_fen(fen):
	global memory
	fields = fen.split()
	ranks = fields[0].split('/')

	for rank in range(0,8):
		s = ranks[7-rank]   	# fen reverses rank order
#		print(s)
		file = 0
		while s != '':
			c = s[0]
			s = s[1:]
			if c.isdigit():
				file += int(c)
			else:
				piece = 'PNBQRKpnbqrk'.index(c)
				if piece >= 6:
					player = BLACK
					piece -= 6
				else:
					player = WHITE
				add_piece(player, piece+PAWN, rank, file)
				file += 1

	if fields[1] == 'b':
		memory[FROMP] = BLACK*10
		memory[42] = 99  # best_score


# write one card for each nonzero word in memory, just the way load_board.asm likes it
def print_deck():
	global memory
	out = ''
	for (a,d) in enumerate(memory):
		if d!=0:
			out += f'{a:02}{d:02}0' + 75*' ' + '\n'
	out += '99000' + 75*' ' + '\n'
	return out.strip()


read_fen(sys.stdin.read().rstrip())
# initialize starting material score to balanced
memory[MSCORE] = 50
memory[65] = 1   # initial stack depth
memory[44] = 99  # beta
# set up appropriately for black or white play
print(print_deck())



