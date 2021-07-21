CCFLAGS=--std=c++17 -Wall -Werror -pedantic

chsim: chsim.cc
	c++ $(CCFLAGS) -O2 -o chsim -lreadline chsim.cc

chsim_test: chsim_test.cc chsim.cc
	c++ $(CCFLAGS) -Wno-unused-function -o chsim_test chsim_test.cc

.PHONY: test clean
clean:
	rm -f chsim chsim_test chsim.o
