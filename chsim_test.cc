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

#define FT(row, f0, f1, f2, f3, f4, f5)\
  vm.function_table[row][0] = f0;\
  vm.function_table[row][1] = f1;\
  vm.function_table[row][2] = f2;\
  vm.function_table[row][3] = f3;\
  vm.function_table[row][4] = f4;\
  vm.function_table[row][5] = f5;\

#define assert_array_eq(actual, expected) assert(!memcmp(actual, expected, 5 * sizeof(int)))

TEST_CASE(step_fetch) {
  VM vm;
  FT(100, 0, 0, 0, 0, 0, 1);
  FT(101, 95, 0, 0, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 101);
  step(&vm);
  assert(vm.pc == 102);
}

TEST_CASE(step_swap_a_b) {
  VM vm;
  vm.a = 0;
  vm.b = 1;
  FT(100, 1, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.b == 0);
}

TEST_CASE(step_swap_a_c) {
  VM vm;
  vm.a = 0;
  vm.c = 1;
  FT(100, 2, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.c == 0);
}

TEST_CASE(step_swap_a_d) {
  VM vm;
  vm.a = 0;
  vm.d = 1;
  FT(100, 3, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.d == 0);
}

TEST_CASE(step_swap_a_e) {
  VM vm;
  vm.a = 0;
  vm.e = 1;
  FT(100, 4, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.e == 0);
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
    VM vm;
    memcpy(vm.mem, seq, sizeof(seq));
    assert_array_eq(vm.mem[i], seq[i]);
    vm.a = i;
    FT(100, 10, 95, 0, 0, 0, 0);
    step(&vm);
    assert_array_eq(vm.ls, vm.mem[i]);
  }
}

TEST_CASE(step_storeacc) {
  int ls[5] = {42, 42, 42, 42, 42};
  for (int i = 0; i < 15; i++) {
    VM vm;
    memcpy(vm.mem, seq, sizeof(seq));
    memcpy(vm.ls, ls, sizeof(ls));
    vm.a = i;
    FT(100, 11, 95, 0, 0, 0, 0);
    step(&vm);
    assert_array_eq(vm.mem[i], ls);
  }
}

TEST_CASE(step_swapall) {
  int rf[5] = {0, 1, 2, 3, 4};
  int ls[5] = {42, 42, 42, 42, 42};
  VM vm;
  memcpy(vm.ls, ls, sizeof(ls));
  memcpy(vm.rf, rf, sizeof(rf));
  FT(100, 12, 95, 0, 0, 0, 0);
  step(&vm);
  assert_array_eq(vm.rf, ls);
  assert_array_eq(vm.ls, rf);
}

TEST_CASE(step_mov_b_a) {
  VM vm;
  vm.a = 0;
  vm.b = 1;
  FT(100, 20, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.b == 1);
}

TEST_CASE(step_mov_c_a) {
  VM vm;
  vm.a = 0;
  vm.c = 1;
  FT(100, 21, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.c == 1);
}

TEST_CASE(step_mov_d_a) {
  VM vm;
  vm.a = 0;
  vm.d = 1;
  FT(100, 22, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.d == 1);
}

TEST_CASE(step_mov_e_a) {
  VM vm;
  vm.a = 0;
  vm.e = 1;
  FT(100, 23, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.e == 1);
}

TEST_CASE(step_mov_f_a) {
  VM vm;
  vm.a = 0;
  vm.f = 1;
  FT(100, 34, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.f == 1);
}

TEST_CASE(step_mov_g_a) {
  VM vm;
  vm.a = 0;
  vm.g = 1;
  FT(100, 30, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.g == 1);
}

TEST_CASE(step_mov_h_a) {
  VM vm;
  vm.a = 0;
  vm.h = 1;
  FT(100, 31, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.h == 1);
}

TEST_CASE(step_mov_i_a) {
  VM vm;
  vm.a = 0;
  vm.i = 1;
  FT(100, 32, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.i == 1);
}

TEST_CASE(step_mov_j_a) {
  VM vm;
  vm.a = 0;
  vm.j = 1;
  FT(100, 33, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
  assert(vm.j == 1);
}

TEST_CASE(step_mov_imm_a) {
  VM vm;
  FT(100, 40, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.a == 42);
}

TEST_CASE(step_inc_a) {
  VM vm;
  vm.a = 0;
  FT(100, 52, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 1);
}

TEST_CASE(step_dec_a) {
  VM vm;
  vm.a = 20;
  FT(100, 53, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 19);
}

TEST_CASE(step_add) {
  VM vm;
  vm.a = 10;
  vm.d = 72;
  FT(100, 70, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == 82);
}

TEST_CASE(step_sub) {
  VM vm;
  vm.a = 10;
  vm.d = 32;
  FT(100, 72, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.a == -22);
}

TEST_CASE(step_jmp) {
  VM vm;
  vm.pc = 200;
  FT(200, 73, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 242);
}

TEST_CASE(step_jmp_far) {
  VM vm;
  vm.pc = 200;
  FT(200, 74, 41, 99, 95, 0, 0);
  step(&vm);
  assert(vm.pc == 342);
}

TEST_CASE(step_jn_not_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = 42;
  FT(100, 80, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jn_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = -1;
  FT(100, 80, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jz_not_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = 1;
  FT(100, 81, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jz_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = 0;
  FT(100, 81, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jil_not_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = 11;
  FT(100, 82, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jil_taken) {
  VM vm;
  vm.pc = 100;
  vm.a = 91;
  FT(100, 82, 41, 95, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jsr) {
  VM vm;
  vm.pc = 100;
  FT(100, 84, 41, 99, 95, 0, 0);
  step(&vm);
  assert(vm.old_pc == 101);
  assert(vm.pc == 342);
}

TEST_CASE(step_ret) {
  VM vm;
  vm.pc = 342;
  vm.old_pc = 101;
  FT(342, 85, 95, 0, 0, 0, 0);
  step(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_halt) {
  VM vm;
  vm.pc = 100;
  FT(100, 95, 0, 0, 0, 0, 0);
  step(&vm);
  assert(vm.halted);
}

int main() {
  for (auto* test: tests) {
    test->run();
  }
  printf("Ran %ld tests.", tests.size());
  return 0;
}
