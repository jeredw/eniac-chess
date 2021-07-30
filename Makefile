.PHONY: test
test:
	python easm/test_easm.py
	python chasm/chasm_test.py
	python chasm/chasm.py asm/chasm_test.asm /tmp/chasm_test.easm
	cmp /tmp/chasm_test.easm chasm/chasm_test.easm
	make -C chsim chsim_test
	./chsim/chsim_test

vmtest: chasm/chasm.py asm/vmtest.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/vmtest.asm vmtest.e
	python easm/easm.py chessvm/chessvm.easm chessvm.e

tic: chasm/chasm.py asm/tic.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/tic.asm tic.e
	python easm/easm.py chessvm/chessvm.easm chessvm.e

c4: chasm/chasm.py asm/c4.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/c4.asm c4.e
	python easm/easm.py chessvm/chessvm.easm chessvm.e

chess: chasm/chasm.py asm/chess.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/chess.asm chess.e
	python easm/easm.py chessvm/chessvm.easm chessvm.e
