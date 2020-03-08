#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <utility>

typedef uint64_t u64;

struct State {
  int isa_version = 0;
  int mswap_pc = 300;

  // Register file
  union {
    int rf[5]{};
    struct {
      int a;
      int b;
      int c;
      int d;
      int e;
    };
  };
  // PC and stack
  int pc = 100;
  int stack[2]{};
  int q = 0;
  // IR and execution scratch
  u64 ir = 0;
  u64 ex = 0;
  // Load store scratch
  union {
    int ls[5]{};
    struct {
      int z;
      int j;
    };
  };
  // Memory
  int m[15][5]{};

  // ROM, essentially
  u64 function_table[400]{};
};

static void usage() {
  fprintf(stderr, "Usage: chsim program.lst\n");
}

static inline u64 pack(u64 a, u64 b, u64 c, u64 d, u64 e, u64 f) {
  return a | (b << 8) | (c << 16) | (d << 24) | (e << 32) | (f << 40);
}

static bool read_state_from_file(const char* filename, State* state) {
  FILE* fp = fopen(filename, "r");
  if (!fp) {
    return false;
  }
  char line[128];
  if (!fgets(line, 128, fp) || strcmp(line, "; isa=v3") != 0) {
    fprintf(stderr, "unrecognized input format\n");
    fclose(fp);
    return false;
  }
  state->isa_version = 3;
  int line_number = 2;
  while (fgets(line, 128, fp)) {
    int index;
    int a, b, c, d, e, f;
    if (sscanf(line, "%d: %02d%02d%02d%02d%02d%02d",
               &index, &f, &e, &d, &c, &b, &a) != 2) {
      fprintf(stderr, "%s:%d: expecting addr:value\n",
              filename, line_number);
      fclose(fp);
      return false;
    }
    if (index < 100 || index > 399) {
      fprintf(stderr, "%s:%d: invalid function table index: '%d'\n",
              filename, line_number, index);
      fclose(fp);
      return false;
    }
    state->function_table[index] = pack(a, b, c, d, e, f);
    line_number++;
  }
  fclose(fp);
  return true;
}

static void step(State* state) {
  // If IR is empty, fetch the next ft row and inc PC.
  // Note this copies 6 words, but the shift below fixes that.
  if (state->ir == 0) {
    state->ir = state->function_table[state->pc];
    state->pc++;
  }
  // Copy the next instruction into the execute reg.
  state->ex = state->ir;
  state->ir >>= 8;
  switch (state->ex & 0xff) {
    case 0: break; // nop
    case 1: std::swap(state->rf, state->m[0]); break;
    case 2: std::swap(state->rf, state->m[1]); break;
    case 3: std::swap(state->rf, state->m[2]); break;
    case 4: std::swap(state->rf, state->m[3]); break;
    case 5: std::swap(state->rf, state->m[4]); break;
    case 10: std::swap(state->rf, state->m[5]); break;
    case 11: std::swap(state->rf, state->m[6]); break;
    case 12: std::swap(state->rf, state->m[7]); break;
    case 13: std::swap(state->rf, state->m[8]); break;
    case 14: std::swap(state->rf, state->m[9]); break;
    case 15: std::swap(state->rf, state->m[10]); break;
    case 20: std::swap(state->rf, state->m[11]); break;
    case 21: std::swap(state->rf, state->m[12]); break;
    case 22: std::swap(state->rf, state->m[13]); break;
    case 23: std::swap(state->rf, state->m[14]); break;
    case 24: std::swap(state->rf, state->ls); break;
    case 25: { // ftl
      u64 data = state->function_table[state->a + 300];
      state->a = data & 0xff;
      state->b = (data >> 8) & 0xff;
      state->c = (data >> 16) & 0xff;
      state->d = (data >> 24) & 0xff;
      state->e = (data >> 32) & 0xff;
      break;
    }
    case 30: // indexjmp1 (jmp +J/5)
      state->pc += state->j / 5;
      state->ir = 0;
      break;
    case 31: // indexjmp2 (jmp +J%5)
      state->pc += state->j % 5;
      state->ir = 0;
      break;
#define jsr(addr) \
  state->stack[state->q] = state->pc;\
  state->q ^= 1;\
  state->pc = addr;\
  state->ir = 0
    case 32: // mov A, [addr]
      state->b = (state->ex >> 8) & 0xff;
      [[fallthrough]];
    case 33: // mov A, [B]
      [[fallthrough]];
    case 34: // mov [B], A
      jsr(state->mswap_pc);
      break;
    case 35: // mov A, imm
      state->a = (state->ex >> 8) & 0xff;
      state->ir >>= 8;
      break;
    case 40: state->a = state->b; break; // mov A, B
    case 41: state->a = state->c; break; // mov A, C
    case 42: state->a = state->d; break; // mov A, D
    case 43: state->a = state->e; break; // mov A, E
    case 44: state->z = state->a; break; // mov Z, A
    case 45: std::swap(state->a, state->b); break; // swap A, B
    case 50: std::swap(state->a, state->c); break; // swap A, C
    case 51: std::swap(state->a, state->d); break; // swap A, D
    case 52: std::swap(state->a, state->e); break; // swap A, E
    case 70: std::swap(state->a, state->z); break; // swap A, Z
    case 71: state->a = (state->a + 1) % 100; break; // inc A
    case 72: state->b = (state->b + 1) % 100; break; // inc B
#define near_address 100 * (state->pc / 100) + ((state->ex >> 8) & 0xff)
#define far_address  100 * ((state->ex >> 16) % 10) + ((state->ex >> 8) & 0xff)
    case 73: // jmp
      state->pc = near_address;
      state->ir = 0;
      break;
    case 74: // jmp far
      state->pc = far_address;
      state->ir = 0;
      break;
    case 80: // jn
      if (state->a >= 50) {
        state->pc = near_address;
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 81: // jz
      if (state->a == 0) {
        state->pc = near_address;
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 82: // loop
      state->c = (state->c + 99) % 100;
      if (state->c != 0) {
        state->pc = near_address;
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 83: // jsr
      jsr(far_address);
      break;
#undef near_address
#undef far_address
#undef jsr
    case 84: // ret
      state->q ^= 1;
      state->pc = state->stack[state->q];
      state->ir = 0;
      break;
    case 85: state->a = (state->a + state->d) % 100; break; // add A,D
    case 90: state->a = (state->a + (100 - state->d)) % 100; break; // sub A,D
    case 91: state->a = (100 - state->a) % 100; break; // neg A
    case 92: state->a = 0; break; // clr A
    case 93: // read AB
      break;
    case 94: // print AB
      break;
    case 95: // halt
      state->ir = 95;
      break;
  }
}

#ifndef TEST  // Defined by chsim_test.cc for unit testing.
int main(int argc, char *argv[]) {
  if (argc != 2) {
    usage();
    exit(1);
  }
  State state;
  if (!read_state_from_file(argv[1], &state)) {
    exit(1);
  }
  step(&state);
  return 0;
}
#endif  // TEST