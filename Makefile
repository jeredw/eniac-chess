CCFLAGS=--std=c++17 -Wall -Werror

.PHONY: test
test:
	python easm/test_easm.py
	python chasm/chasm_test.py
	python chasm/chasm.py asm/chasm_test.asm /tmp/chasm_test.easm
	cmp /tmp/chasm_test.easm chasm/chasm_test.easm
	make -C chsim test
	python asm_test.py

client: client.cc chasm/chasm.py asm/chess.asm
	python chasm/chasm.py asm/chess.asm chess_data.cc
	c++ -g $(CCFLAGS) -DMAIN -O2 -o client client.cc

vmtest: chasm/chasm.py asm/vmtest.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/vmtest.asm vmtest.e
	python easm/easm.py -ETEST chessvm/chessvm.easm chessvm.e

tic: chasm/chasm.py asm/tic.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/tic.asm tic.e
	python easm/easm.py -ETIC chessvm/chessvm.easm chessvm.e

c4: chasm/chasm.py asm/c4.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/c4.asm c4.e
	python easm/easm.py -EC4 chessvm/chessvm.easm chessvm.e

life: chasm/chasm.py asm/life.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/life.asm life.e
	python easm/easm.py -ELIFE chessvm/chessvm.easm chessvm.e

chess: chasm/chasm.py asm/chess.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/chess.asm chess.e
	python easm/easm.py -ECHESS chessvm/chessvm.easm chessvm.e

vm.pdf: vm.dot
	dot -Tpdf vm.dot > vm.pdf
