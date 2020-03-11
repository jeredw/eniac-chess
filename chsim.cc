#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <utility>
#include <algorithm>

typedef uint64_t u64;

struct State {
  int isa_version = 0;
  int load_pc = 300;
  int store_pc = 320;

  // Register file
  int rf[5]{};
  int &a = rf[0];
  int &b = rf[1];
  int &c = rf[2];
  int &d = rf[3];
  int &e = rf[4];
  // PC and stack
  int pc = 100;
  int stack[2]{};
  int sp = 0;
  // Current row of instructions
  u64 ir = 0;
  // Load store scratch
  int ls[5]{};
  int &z = ls[0];
  int &j = ls[1];
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
  if (!fgets(line, 128, fp) || strcmp(line, "; isa=v4") != 0) {
    fprintf(stderr, "unrecognized input format\n");
    fclose(fp);
    return false;
  }
  state->isa_version = 4;
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

static inline void jsr(State* state, int addr) {
  state->stack[state->sp] = state->pc;
  state->sp ^= 1;
  state->pc = addr;
  state->ir = 0;
}

static inline int near_address(State* state) {
  return 100 * (state->pc / 100) + (state->ir & 0xff);
}

static inline int far_address(State* state) {
  return 100 * ((state->ir >> 8) % 10) + (state->ir & 0xff);
}

static void assert_sanity(State* state) {
  assert(state->a >= 0 && state->a < 100);
  assert(state->b >= 0 && state->b < 100);
  assert(state->c >= 0 && state->c < 100);
  assert(state->d >= 0 && state->d < 100);
  assert(state->e >= 0 && state->e < 100);
  assert(state->ls[0] >= 0 && state->ls[0] < 100);
  assert(state->ls[1] >= 0 && state->ls[1] < 100);
  assert(state->ls[2] >= 0 && state->ls[2] < 100);
  assert(state->ls[3] >= 0 && state->ls[3] < 100);
  assert(state->ls[4] >= 0 && state->ls[4] < 100);
  assert(state->pc >= 100 && state->pc < 400);
  assert(state->stack[0] >= 0 && state->stack[0] < 400);
  assert(state->stack[1] >= 0 && state->stack[1] < 400);
  assert(state->sp == 0 || state->sp == 1);
  assert(state->ir <= 0xff'ff'ff'ff'ffull);
  assert(state->j >= 0 && state->j < 100);
  assert(state->z >= 0 && state->z < 100);
  for (int i = 0; i < 15; i++) {
    for (int j = 0; j < 5; j++) {
      assert(state->m[i][j] >= 0 && state->m[i][j] < 100);
    }
  }
}

static void step(State* state) {
  // If IR is empty, fetch the next ft row and inc PC.
  // Note this copies 6 words, but the shift below fixes that.
  if (state->ir == 0) {
    state->ir = state->function_table[state->pc];
    state->pc++;
  }
  int opcode = state->ir & 0xff;
  state->ir >>= 8;
  switch (opcode) {
    case 0: break; // nop
    case 1: std::swap(state->a, state->b); break; // swap A, B
    case 2: std::swap(state->a, state->c); break; // swap A, C
    case 3: std::swap(state->a, state->d); break; // swap A, D
    case 4: std::swap(state->a, state->e); break; // swap A, E
    case 5: std::swap(state->a, state->z); break; // swap A, Z
    case 10: // loadacc A
      std::copy(state->m[state->a], state->m[state->a] + 5, state->ls);
      break;
    case 11: // storeacc A
      std::copy(state->ls, state->ls + 5, state->m[state->a]);
      break;
    case 12: std::copy(state->rf, state->rf + 5, state->ls); break; // save
    case 13: std::copy(state->ls, state->ls + 5, state->rf); break; // restore
    case 14: std::swap(state->rf, state->ls); break; // swapsave
    case 15: { // ftl
      u64 data = state->function_table[state->a + 300];
      state->ls[0] = data & 0xff;
      state->ls[1] = (data >> 8) & 0xff;
      state->ls[2] = (data >> 16) & 0xff;
      state->ls[3] = (data >> 24) & 0xff;
      state->ls[4] = (data >> 32) & 0xff;
      break;
    }
    case 20: state->a = state->b; break; // mov A, B
    case 21: state->a = state->c; break; // mov A, C
    case 22: state->a = state->d; break; // mov A, D
    case 23: state->a = state->e; break; // mov A, E
    case 24: state->a = state->z; break; // mov A, Z
    case 30: // mov A, imm
      state->a = state->ir & 0xff;
      state->ir >>= 8;
      break;
    case 31: // mov A, [addr]
      state->b = state->ir & 0xff;
      [[fallthrough]];
    case 33: // mov A, [B]
      jsr(state, state->load_pc);
      break;
    case 32: // mov [addr], A
      state->b = state->ir & 0xff;
      [[fallthrough]];
    case 34: // mov [B], A
      jsr(state, state->store_pc);
      break;
    case 40: state->a = state->b / 5; break; // indexhi
    case 41: state->a = state->b % 5; break; // indexlo
    case 42: state->ir = (state->ir & ~0xff) | state->a; break; // selfmodify
    case 43: { // scan
      int value_to_find = state->a;
      state->a = 99;
      for (int i = 0; i < 5; i++) {
        if (state->ls[i] == value_to_find) {
          state->a = i;
          break;
        }
        state->ls[i] = 0;
      }
      break;
    }
    case 50: state->a = (state->a + 1) % 100; break; // inc A
    case 51: state->b = (state->b + 1) % 100; break; // inc B
    case 52: state->a = (state->a + 99) % 100; break; // dec A
    case 70: state->a = (state->a + state->d) % 100; break; // add A,D
    case 71: state->a = (100 - state->a) % 100; break; // neg A
    case 72: state->a = (state->a + (100 - state->d)) % 100; break; // sub A,D
    case 73: // jmp
      state->pc = near_address(state);
      state->ir = 0;
      break;
    case 74: // jmp far
      state->pc = far_address(state);
      state->ir = 0;
      break;
    case 75: // jmp +A
      state->pc += state->a;
      state->ir = 0;
      break;
    case 80: // jn
      if (state->a >= 50) {
        state->pc = near_address(state);
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 81: // jz
      if (state->a == 0) {
        state->pc = near_address(state);
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 82: // loop
      state->c = (state->c + 99) % 100;
      if (state->c != 0) {
        state->pc = near_address(state);
        state->ir = 0;
      } else {
        state->ir >>= 8;
      }
      break;
    case 83: // jsr
      jsr(state, far_address(state));
      break;
    case 84: // ret
      state->sp ^= 1;
      state->pc = state->stack[state->sp];
      state->ir = 0;
      break;
    case 93: // read AB
      break;
    case 94: // print AB
      break;
    case 95: // halt
      state->ir = 95;
      break;
  }
  assert_sanity(state);
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