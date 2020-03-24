#define TEST
#include <assert.h>
#include <vector>
#include "chsim.cc"

struct test_case { virtual void run() = 0; };
static std::vector<test_case*> tests;
#define TEST_CASE_NAME(x, y) test_case_##x##_##y
#define TEST_CASE(x) \
static struct TEST_CASE_NAME(x, class) : test_case { \
  TEST_CASE_NAME(x, class)() { tests.push_back(this); }\
  void run();\
} TEST_CASE_NAME(x, instance);\
void TEST_CASE_NAME(x, class)::run()

#define assert_array_eq(actual, expected) assert(!memcmp(actual, expected, 5 * sizeof(int)))

TEST_CASE(pack) {
  assert(pack(6, 5, 4, 3, 2, 1) == 0x010203040506ULL);
}

TEST_CASE(step_fetch) {
  State state;
  state.function_table[100] = pack(0, 0, 0, 0, 0, 1);
  state.function_table[101] = pack(95, 0, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0x0100000000);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0x01000000);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0x010000);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0x0100);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0x01);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 102);
  assert(state.ir == 95);
}

TEST_CASE(step_swap_a_b) {
  State state;
  state.a = 0;
  state.b = 1;
  state.function_table[100] = pack(1, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.b == 0);
}

TEST_CASE(step_swap_a_c) {
  State state;
  state.a = 0;
  state.c = 1;
  state.function_table[100] = pack(2, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.c == 0);
}

TEST_CASE(step_swap_a_d) {
  State state;
  state.a = 0;
  state.d = 1;
  state.function_table[100] = pack(3, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.d == 0);
}

TEST_CASE(step_swap_a_e) {
  State state;
  state.a = 0;
  state.e = 1;
  state.function_table[100] = pack(4, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.e == 0);
}

TEST_CASE(step_swap_a_f) {
  State state;
  state.a = 0;
  state.f = 1;
  state.function_table[100] = pack(5, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.f == 0);
}

const int seq[15][5] = {
  { 0,  1,  2,  3,  4}, { 5,  6,  7,  8,  9},
  {10, 11, 12, 13, 14}, {15, 16, 17, 18, 19},
  {20, 21, 22, 23, 24}, {25, 26, 27, 28, 29},
  {30, 31, 32, 33, 34}, {35, 36, 37, 38, 39},
  {40, 41, 42, 43, 44}, {45, 46, 47, 48, 49},
  {50, 51, 52, 53, 54}, {55, 56, 57, 58, 59},
  {60, 61, 62, 63, 64}, {65, 66, 67, 68, 69},
  {70, 71, 72, 73, 74},
};

TEST_CASE(step_loadacc) {
  for (int i = 0; i < 15; i++) {
    State state;
    memcpy(state.m, seq, sizeof(seq));
    assert_array_eq(state.m[i], seq[i]);
    state.a = i;
    state.function_table[100] = pack(10, 95, 0, 0, 0, 0);
    step(&state);
    assert_array_eq(state.ls, state.m[i]);
  }
}

TEST_CASE(step_storeacc) {
  int ls[5] = {42, 42, 42, 42, 42};
  for (int i = 0; i < 15; i++) {
    State state;
    memcpy(state.m, seq, sizeof(seq));
    memcpy(state.ls, ls, sizeof(ls));
    state.a = i;
    state.function_table[100] = pack(11, 95, 0, 0, 0, 0);
    step(&state);
    assert_array_eq(state.m[i], ls);
  }
}

TEST_CASE(step_swapall) {
  int rf[5] = {0, 1, 2, 3, 4};
  int ls[5] = {42, 42, 42, 42, 42};
  State state;
  memcpy(state.ls, ls, sizeof(ls));
  memcpy(state.rf, rf, sizeof(rf));
  state.function_table[100] = pack(12, 95, 0, 0, 0, 0);
  step(&state);
  assert_array_eq(state.rf, ls);
  assert_array_eq(state.ls, rf);
}

TEST_CASE(step_scanall) {
  int ls[5] = {10, 20, 30, 40, 50};
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 42;
    step(&state);
    assert(state.a == 99);
  }
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 10;
    step(&state);
    assert(state.a == 0);
  }
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 20;
    step(&state);
    assert(state.a == 1);
  }
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 30;
    step(&state);
    assert(state.a == 2);
  }
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 40;
    step(&state);
    assert(state.a == 3);
  }
  {
    State state;
    memcpy(state.ls, ls, sizeof(ls));
    state.function_table[100] = pack(13, 95, 0, 0, 0, 0);
    state.a = 50;
    step(&state);
    assert(state.a == 4);
  }
}

TEST_CASE(step_ftl) {
  State state;
  state.function_table[100] = pack(14, 95, 0, 0, 0, 0);
  state.function_table[320] = pack(1, 2, 3, 4, 5, 6);
  state.a = 20;
  step(&state);
  assert(state.f == 1);
  assert(state.g == 2);
  assert(state.h == 3);
  assert(state.i == 4);
  assert(state.j == 5);
}

TEST_CASE(step_ftlookup) {
  State state;
  state.function_table[100] = pack(15, 10, 95, 0, 0, 0);
  state.function_table[320] = pack(1, 2, 3, 4, 5, 6);
  state.a = 10;
  step(&state);
  assert(state.a == 6);
}

TEST_CASE(step_mov_a_b) {
  State state;
  state.a = 0;
  state.b = 1;
  state.function_table[100] = pack(20, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.b == 1);
}

TEST_CASE(step_mov_a_c) {
  State state;
  state.a = 0;
  state.c = 1;
  state.function_table[100] = pack(21, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.c == 1);
}

TEST_CASE(step_mov_a_d) {
  State state;
  state.a = 0;
  state.d = 1;
  state.function_table[100] = pack(22, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.d == 1);
}

TEST_CASE(step_mov_a_e) {
  State state;
  state.a = 0;
  state.e = 1;
  state.function_table[100] = pack(23, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.e == 1);
}

TEST_CASE(step_mov_a_f) {
  State state;
  state.a = 0;
  state.f = 1;
  state.function_table[100] = pack(24, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.f == 1);
}

TEST_CASE(step_mov_a_g) {
  State state;
  state.a = 0;
  state.g = 1;
  state.function_table[100] = pack(25, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.g == 1);
}

TEST_CASE(step_mov_a_h) {
  State state;
  state.a = 0;
  state.h = 1;
  state.function_table[100] = pack(30, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.h == 1);
}

TEST_CASE(step_mov_a_i) {
  State state;
  state.a = 0;
  state.i = 1;
  state.function_table[100] = pack(31, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.i == 1);
}

TEST_CASE(step_mov_a_j) {
  State state;
  state.a = 0;
  state.j = 1;
  state.function_table[100] = pack(32, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.j == 1);
}

TEST_CASE(step_indexswap) {
  State state;
  state.function_table[100] = pack(34, 0, 0, 0, 0, 0);
  state.g = 12;
  step(&state);
  assert(state.ir == 2);
}

TEST_CASE(step_mov_a_imm) {
  State state;
  state.function_table[100] = pack(40, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.a == 42);
  assert(state.ir == 95);
}

TEST_CASE(step_mov_d_imm) {
  State state;
  state.function_table[100] = pack(41, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.d == 42);
  assert(state.ir == 95);
}

TEST_CASE(step_mov_a_addr) {
  State state;
  state.load_pc = 300;
  state.function_table[100] = pack(42, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.b == 42);
  assert(state.stack[0] == 101);
  assert(state.sp == 1);
  assert(state.pc == 300);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_a_mb) {
  State state;
  state.load_pc = 300;
  state.function_table[100] = pack(43, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.stack[0] == 101);
  assert(state.sp == 1);
  assert(state.pc == 300);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_addr_a) {
  State state;
  state.store_pc = 320;
  state.a = 20;
  state.function_table[100] = pack(44, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.a == 20);
  assert(state.b == 42);
  assert(state.stack[0] == 101);
  assert(state.sp == 1);
  assert(state.pc == 320);
  assert(state.ir == 0);
}

TEST_CASE(step_indexacc) {
  State state;
  state.function_table[100] = pack(45, 95, 0, 0, 0, 0);
  state.b = 23;
  step(&state);
  assert(state.a == 4);
}

TEST_CASE(step_inc_a) {
  State state;
  state.a = 0;
  state.function_table[100] = pack(50, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
}

TEST_CASE(step_inc_b) {
  State state;
  state.b = 0;
  state.function_table[100] = pack(51, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.b == 1);
}

TEST_CASE(step_dec_a) {
  State state;
  state.a = 20;
  state.function_table[100] = pack(52, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 19);
}

TEST_CASE(step_add) {
  State state;
  state.a = 10;
  state.d = 72;
  state.function_table[100] = pack(70, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 82);
}

TEST_CASE(step_neg) {
  State state;
  state.a = 10;
  state.function_table[100] = pack(71, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 100 - 10);
}

TEST_CASE(step_sub) {
  State state;
  state.a = 10;
  state.d = 32;
  state.function_table[100] = pack(72, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 100 - 22);
}

TEST_CASE(step_jmp) {
  State state;
  state.pc = 200;
  state.function_table[200] = pack(73, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 242);
  assert(state.ir == 0);
}

TEST_CASE(step_jmp_far) {
  State state;
  state.pc = 200;
  state.function_table[200] = pack(74, 42, 3, 95, 0, 0);
  step(&state);
  assert(state.pc == 342);
  assert(state.ir == 0);
}

TEST_CASE(step_jmp_computed) {
  State state;
  state.pc = 200;
  state.a = 20;
  state.function_table[200] = pack(75, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 221);
  assert(state.ir == 0);
}

TEST_CASE(step_jn_not_taken) {
  State state;
  state.pc = 100;
  state.a = 42;
  state.function_table[100] = pack(80, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_jn_taken) {
  State state;
  state.pc = 100;
  state.a = 99;
  state.function_table[100] = pack(80, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_jz_not_taken) {
  State state;
  state.pc = 100;
  state.a = 1;
  state.function_table[100] = pack(81, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_jz_taken) {
  State state;
  state.pc = 100;
  state.a = 0;
  state.function_table[100] = pack(81, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_jil_not_taken) {
  State state;
  state.pc = 100;
  state.a = 11;
  state.function_table[100] = pack(82, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_jil_taken) {
  State state;
  state.pc = 100;
  state.a = 91;
  state.function_table[100] = pack(82, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_loop_not_taken) {
  State state;
  state.pc = 100;
  state.c = 1;
  state.function_table[100] = pack(83, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.c == 0);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_loop_taken) {
  State state;
  state.pc = 100;
  state.c = 2;
  state.function_table[100] = pack(83, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.c == 1);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_jsr) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(84, 42, 3, 95, 0, 0);
  step(&state);
  assert(state.stack[0] == 101);
  assert(state.sp == 1);
  assert(state.pc == 342);
  assert(state.ir == 0);
}

TEST_CASE(step_ret) {
  State state;
  state.sp = 1;
  state.pc = 342;
  state.stack[0] = 101;
  state.function_table[342] = pack(85, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.sp == 0);
  assert(state.ir == 0);
}

TEST_CASE(step_nested_jsr) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(84, 0, 2, 0, 0, 0);
  state.function_table[101] = pack(84, 0, 3, 0, 0, 0);
  state.function_table[200] = pack(84, 0, 3, 0, 0, 0);
  state.function_table[201] = pack(85, 95, 0, 0, 0, 0);
  state.function_table[300] = pack(85, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 200);
  assert(state.stack[0] == 101);
  assert(state.sp == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 300);
  assert(state.stack[1] == 201);
  assert(state.sp == 0);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 201);
  assert(state.sp == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.sp == 0);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 300);
  assert(state.stack[0] == 102);
  assert(state.sp == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 102);
  assert(state.sp == 0);
  assert(state.ir == 0);
}

TEST_CASE(step_jnz_not_taken) {
  State state;
  state.pc = 100;
  state.a = 0;
  state.function_table[100] = pack(90, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_jnz_taken) {
  State state;
  state.pc = 100;
  state.a = 1;
  state.function_table[100] = pack(90, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_nextline) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(94, 0, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 0);
}

TEST_CASE(step_halt) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(95, 0, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.ir == 95);
}

int main() {
  for (auto* test: tests) {
    test->run();
  }
  printf("Ran %ld tests.", tests.size());
  return 0;
}
