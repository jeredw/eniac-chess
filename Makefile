CCFLAGS=--std=c++17 -Wall -Werror -pedantic

chsim: chsim.cc
	c++ $(CCFLAGS) -O2 -o chsim chsim.cc

chsim_test: chsim_test.cc chsim.cc
	c++ $(CCFLAGS) -Wno-unused-function -o chsim_test chsim_test.cc

.PHONY: test clean
test:
	python chasm_test.py
	python chasm.py chasm_test.asm > /tmp/chasm_test.easm
	cmp /tmp/chasm_test.easm chasm_test.easm
	make chsim_test
	./chsim_test

clean:
	rm -f chsim chsim_test chsim.o *.pyc
