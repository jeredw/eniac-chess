chsim: chsim.cc
	c++ -o chsim chsim.cc

.PHONY: test clean
test:
	python chasm_test.py
	python chasm.py test.asm > /tmp/test.lst
	cmp /tmp/test.lst test.lst

clean:
	rm -f chsim chsim.o *.pyc
