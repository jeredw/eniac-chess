#include <stdio.h>
#include <stdlib.h>

static void usage() {
  printf("Usage: chsim program.lst\n");
}

int main(int argc, char *argv[]) {
  if (argc != 2) {
    usage();
    exit(1);
  }
  return 0;
}