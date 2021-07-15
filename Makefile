CCFLAGS=--std=c++17 -Wall -Werror -pedantic

chsim: chsim/chsim.cc
	c++ $(CCFLAGS) -O2 -o chsim -lreadline chsim/chsim.cc

chsim_test: chsim/chsim_test.cc chsim/chsim.cc
	c++ $(CCFLAGS) -Wno-unused-function -o chsim_test chsim/chsim_test.cc

.PHONY: test clean
test:
	python easm/test_easm.py
	python chasm/chasm_test.py
	python chasm/chasm.py asm/chasm_test.asm /tmp/chasm_test.easm
	cmp /tmp/chasm_test.easm chasm/chasm_test.easm
	make chsim_test
	./chsim_test

clean:
	rm -f chsim chsim_test chsim.o *.pyc

vmtest: chasm/chasm.py asm/vmtest.asm easm/easm.py chessvm/chessvm.easm
	python chasm/chasm.py asm/vmtest.asm vmtest.e
	python easm/easm.py chessvm/chessvm.easm chessvm.e

