#include <assert.h>
#include <vector>
#include "vm.cc"

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

TEST_CASE(step_fetch) {
  VM vm;
  init(&vm);
  FT(100, 0, 0, 0, 0, 0, 1);
  FT(101, 95, 0, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
  step_one_instruction(&vm);
  assert(vm.pc == 102);
}

TEST_CASE(step_swap_a_b) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.b = 1;
  FT(100, 1, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.error == 0);
  assert(vm.a == 1);
  assert(vm.b == 0);
}

TEST_CASE(step_swap_a_c) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.c = 1;
  FT(100, 2, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.c == 0);
}

TEST_CASE(step_swap_a_d) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.d = 1;
  FT(100, 3, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.d == 0);
}

TEST_CASE(step_swap_a_e) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.e = 1;
  FT(100, 4, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
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
    init(&vm);
    memcpy(vm.mem, seq, sizeof(seq));
    vm.a = i;
    FT(100, 10, 95, 0, 0, 0, 0);
    step_one_instruction(&vm);
    assert(vm.f == vm.mem[i][0]);
    assert(vm.g == vm.mem[i][1]);
    assert(vm.h == vm.mem[i][2]);
    assert(vm.i == vm.mem[i][3]);
    assert(vm.j == vm.mem[i][4]);
  }
}

TEST_CASE(step_storeacc) {
  for (int i = 0; i < 15; i++) {
    VM vm;
    init(&vm);
    memcpy(vm.mem, seq, sizeof(seq));
    vm.f = 42;
    vm.g = 42;
    vm.h = 42;
    vm.i = 42;
    vm.j = 42;
    vm.a = i;
    FT(100, 11, 95, 0, 0, 0, 0);
    step_one_instruction(&vm);
    assert(vm.mem[i][0] == vm.f);
    assert(vm.mem[i][1] == vm.g);
    assert(vm.mem[i][2] == vm.h);
    assert(vm.mem[i][3] == vm.i);
    assert(vm.mem[i][4] == vm.j);
  }
}

TEST_CASE(step_swapall) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.b = 1;
  vm.c = 2;
  vm.d = 3;
  vm.e = 4;
  vm.f = 42;
  vm.g = 42;
  vm.h = 42;
  vm.i = 42;
  vm.j = 42;
  FT(100, 12, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 42);
  assert(vm.b == 42);
  assert(vm.c == 42);
  assert(vm.d == 42);
  assert(vm.e == 42);
  assert(vm.f == 0);
  assert(vm.g == 1);
  assert(vm.h == 2);
  assert(vm.i == 3);
  assert(vm.j == 4);
}

TEST_CASE(step_mov_b_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.b = 1;
  FT(100, 20, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.b == 1);
}

TEST_CASE(step_mov_c_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.c = 1;
  FT(100, 21, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.c == 1);
}

TEST_CASE(step_mov_d_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.d = 1;
  FT(100, 22, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.d == 1);
}

TEST_CASE(step_mov_e_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.e = 1;
  FT(100, 23, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.e == 1);
}

TEST_CASE(step_mov_f_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.f = 1;
  FT(100, 34, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.f == 1);
}

TEST_CASE(step_mov_g_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.g = 1;
  FT(100, 30, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.g == 1);
}

TEST_CASE(step_mov_h_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.h = 1;
  FT(100, 31, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.h == 1);
}

TEST_CASE(step_mov_i_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.i = 1;
  FT(100, 32, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.i == 1);
}

TEST_CASE(step_mov_j_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  vm.j = 1;
  FT(100, 33, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
  assert(vm.j == 1);
}

TEST_CASE(step_mov_imm_a) {
  VM vm;
  init(&vm);
  FT(100, 40, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 42);
}

TEST_CASE(step_inc_a) {
  VM vm;
  init(&vm);
  vm.a = 0;
  FT(100, 52, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 1);
}

TEST_CASE(step_dec_a) {
  VM vm;
  init(&vm);
  vm.a = 20;
  FT(100, 53, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 19);
}

TEST_CASE(step_add) {
  VM vm;
  init(&vm);
  vm.a = 10;
  vm.d = 72;
  FT(100, 70, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == 82);
}

TEST_CASE(step_sub) {
  VM vm;
  init(&vm);
  vm.a = 10;
  vm.d = 32;
  FT(100, 72, 95, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.a == -22);
}

TEST_CASE(step_jmp) {
  VM vm;
  init(&vm);
  vm.pc = 200;
  FT(200, 73, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 242);
}

TEST_CASE(step_jmp_far) {
  VM vm;
  init(&vm);
  vm.pc = 200;
  FT(200, 74, 41, 99, 95, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 342);
}

TEST_CASE(step_jn_not_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = 42;
  FT(100, 80, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jn_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = -1;
  FT(100, 80, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jz_not_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = 1;
  FT(100, 81, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jz_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = 0;
  FT(100, 81, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jil_not_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = 11;
  FT(100, 82, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_jil_taken) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  vm.a = 91;
  FT(100, 82, 41, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 142);
}

TEST_CASE(step_jsr) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  FT(100, 84, 41, 99, 95, 0, 0);
  step_one_instruction(&vm);
  assert(vm.old_pc == 101);
  assert(vm.pc == 342);
}

TEST_CASE(step_ret) {
  VM vm;
  init(&vm);
  vm.old_pc = 101;
  vm.pc = 342;
  vm.ir_index = 6;
  FT(342, 0, 85, 95, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.pc == 101);
}

TEST_CASE(step_halt) {
  VM vm;
  init(&vm);
  vm.pc = 100;
  FT(100, 95, 0, 0, 0, 0, 0);
  step_one_instruction(&vm);
  assert(vm.status & HALT);
}

TEST_CASE(vm_import) {
  ENIAC e = {
    .cycles = 1024,
    .error_code = 0,
    .rollback = 0,
    .acc[0] = "P0099429020",
    .acc[1] = "M0000000000",
    .acc[2] = "P0000000000",
    .acc[3] = "P0102030405",
    .acc[12] = "M9907080910",
    .acc[19] = "P9596979899",
    .ft[0][2] = {0, 9, 2, 5, 2, 9, 2, 5, 2, 0, 1, 5, 2, 0},
    .ft[2][10] = {0, 9, 9, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 1},
  };
  VM v = {
    .cycles = 1000,
    .error = 0,
    .status = IO_READ,
    .ft_initialized = 0,
  };
  int result = vm_import(&v, &e);
  assert(v.cycles == e.cycles);
  assert(v.status == 0);
  assert(v.error == 0);
  assert(result == 0);
  assert(v.old_pc == 342);
  assert(v.pc == 220);
  assert(v.ir_index == 6);
  assert(v.a == -1);
  assert(v.b == 7);
  assert(v.c == 8);
  assert(v.d == 9);
  assert(v.e == 10);
  assert(v.f == 1);
  assert(v.g == 2);
  assert(v.h == 3);
  assert(v.i == 4);
  assert(v.j == 5);
  assert(v.mem[14][0] == 95);
  assert(v.mem[14][1] == 96);
  assert(v.mem[14][2] == 97);
  assert(v.mem[14][3] == 98);
  assert(v.mem[14][4] == 99);
  assert(v.ft_initialized);
  assert(v.function_table[100][0] == 92);
  assert(v.function_table[100][1] == 52);
  assert(v.function_table[100][2] == 92);
  assert(v.function_table[100][3] == 52);
  assert(v.function_table[100][4] == 1);
  assert(v.function_table[100][5] == 52);
  assert(v.function_table[308][0] == -1);
  assert(v.function_table[308][1] == 2);
  assert(v.function_table[308][2] == 3);
  assert(v.function_table[308][3] == 4);
  assert(v.function_table[308][4] == 5);
  assert(v.function_table[308][5] == 6);
}

TEST_CASE(vm_export) {
  VM v = {
    .cycles = 1000,
    .error = 0,
    .status = IO_READ,
    .pc = 220,
    .old_pc = 342,
    .ir_index = 6,
    .f = 1,
    .g = 2,
    .h = 3,
    .i = 4,
    .j = 5,
    .a = -1,
    .b = 7,
    .c = 8,
    .d = 9,
    .e = 10,
    .mem[14] = {95, 96, 97, 98, 99},
  };
  ENIAC e = {
    .cycles = 1024,
    .error_code = 0,
    .rollback = 0,
    .acc[0] = "???????????",
    .acc[1] = "xxxxxxxxxxx",
    .acc[2] = "xxxxxxxxxxx",
    .acc[3] = "???????????",
    .acc[12] = "???????????",
    .acc[19] = "???????????",
  };
  vm_export(&v, &e);
  assert(e.cycles == 1000);
  assert(e.error_code == 0);
  assert(e.rollback);
  assert(strcmp(e.acc[0], "P0099429020") == 0);
  assert(strcmp(e.acc[1], "xxxxxxxxxxx") == 0);
  assert(strcmp(e.acc[2], "xxxxxxxxxxx") == 0);
  assert(strcmp(e.acc[3], "P0102030405") == 0);
  assert(strcmp(e.acc[12], "M9907080910") == 0);
  // when stepping, would be M because ft bank 2 is selected
  assert(strcmp(e.acc[19], "P9596979899") == 0);
}

int main() {
  for (auto* test: tests) {
    test->run();
  }
  printf("Ran %ld tests.", tests.size());
  return 0;
}
