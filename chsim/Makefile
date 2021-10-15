CCFLAGS=--std=c++17 -Wall -Werror

chsim: main.cc vm.cc vm.h
	c++ -g $(CCFLAGS) -O2 -o chsim -lreadline main.cc

test: vm_test.cc main.cc vm.cc vm.h
	c++ $(CCFLAGS) -o chsim_test vm_test.cc
	./chsim_test

lib: vm.cc vm.h
	c++ $(CCFLAGS) -O2 -shared -fPIC -nostartfiles vm.cc -o vm.so

.PHONY: test clean
clean:
	rm -f chsim chsim_test
