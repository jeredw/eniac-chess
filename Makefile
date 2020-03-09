chsim: chsim.cc
	c++ --std=c++14 -Wall -Werror -O2 -o chsim chsim.cc

chsim_test: chsim_test.cc chsim.cc
	c++ --std=c++14 -Wall -Werror -Wno-unused-function -o chsim_test chsim_test.cc

.PHONY: test clean
test:
	python chasm_test.py
	python chasm.py ucode.asm test.asm > /tmp/test.lst
	cmp /tmp/test.lst test.lst
	make chsim_test
	./chsim_test

clean:
	rm -f chsim chsim_test chsim.o *.pyc
