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

TEST_CASE(ls_alignment) {
  State state;
  state.a = 1;
  state.b = 2;
  state.z = 3;
  state.j = 4;
  // union { struct } is technically implementation defined but
  // swapacc 14 needs to exchange A<->Z, B<->J for mswap to work.
  state.function_table[100] = pack(24, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 3);
  assert(state.b == 4);
  assert(state.z == 1);
  assert(state.j == 2);
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

TEST_CASE(step_swapacc) {
  int rf[] = {0, 1, 2, 3, 4};
  int m[] = {5, 6, 7, 8, 9};
  auto make_state = [rf, m](int op, int acc) {
    State state;
    state.function_table[100] = pack(op, 95, 0, 0, 0, 0);
    memcpy(state.rf, rf, 5 * sizeof(int));
    memcpy(state.m[acc], m, 5 * sizeof(int));
    return state;
  };

  State state;
  state = make_state(1, 0);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[0], rf);
  state = make_state(2, 1);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[1], rf);
  state = make_state(3, 2);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[2], rf);
  state = make_state(4, 3);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[3], rf);
  state = make_state(5, 4);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[4], rf);

  state = make_state(10, 5);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[5], rf);
  state = make_state(11, 6);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[6], rf);
  state = make_state(12, 7);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[7], rf);
  state = make_state(13, 8);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[8], rf);
  state = make_state(14, 9);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[9], rf);
  state = make_state(15, 10);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[10], rf);

  state = make_state(20, 11);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[11], rf);
  state = make_state(21, 12);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[12], rf);
  state = make_state(22, 13);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[13], rf);
  state = make_state(23, 14);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[14], rf);
  state = make_state(23, 14);
  step(&state);
  assert_array_eq(state.rf, m);
  assert_array_eq(state.m[14], rf);

  {
    State state;
    memcpy(state.rf, rf, 5 * sizeof(int));
    memcpy(state.ls, m, 5 * sizeof(int));
    state.function_table[100] = pack(24, 95, 0, 0, 0, 0);
    step(&state);
    assert_array_eq(state.rf, m);
    assert_array_eq(state.ls, rf);
  }
}

TEST_CASE(step_ftl) {
  State state;
  state.function_table[100] = pack(25, 95, 0, 0, 0, 0);
  state.function_table[320] = pack(1, 2, 3, 4, 5, 6);
  state.a = 20;
  step(&state);
  assert(state.a == 1);
  assert(state.b == 2);
  assert(state.c == 3);
  assert(state.d == 4);
  assert(state.e == 5);
}

TEST_CASE(step_indexjmp1) {
  State state;
  state.function_table[100] = pack(30, 95, 0, 0, 0, 0);
  state.j = 23;
  step(&state);
  assert(state.pc == 101 + 4);
  assert(state.ir == 0);
}

TEST_CASE(step_indexjmp2) {
  State state;
  state.function_table[100] = pack(31, 95, 0, 0, 0, 0);
  state.j = 23;
  step(&state);
  assert(state.pc == 101 + 3);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_a_addr) {
  State state;
  state.mswap_pc = 300;
  state.function_table[100] = pack(32, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.b == 42);
  assert(state.stack[0] == 101);
  assert(state.q == 1);
  assert(state.pc == 300);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_a_mb) {
  State state;
  state.mswap_pc = 300;
  state.function_table[100] = pack(33, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.stack[0] == 101);
  assert(state.q == 1);
  assert(state.pc == 300);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_mb_a) {
  State state;
  state.mswap_pc = 300;
  state.function_table[100] = pack(34, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.stack[0] == 101);
  assert(state.q == 1);
  assert(state.pc == 300);
  assert(state.ir == 0);
}

TEST_CASE(step_mov_a_imm) {
  State state;
  state.mswap_pc = 300;
  state.function_table[100] = pack(35, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.a == 42);
}

TEST_CASE(step_mov_a_b) {
  State state;
  state.a = 0;
  state.b = 1;
  state.function_table[100] = pack(40, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.b == 1);
}

TEST_CASE(step_mov_a_c) {
  State state;
  state.a = 0;
  state.c = 1;
  state.function_table[100] = pack(41, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.c == 1);
}

TEST_CASE(step_mov_a_d) {
  State state;
  state.a = 0;
  state.d = 1;
  state.function_table[100] = pack(42, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.d == 1);
}

TEST_CASE(step_mov_a_e) {
  State state;
  state.a = 0;
  state.e = 1;
  state.function_table[100] = pack(43, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.e == 1);
}

TEST_CASE(step_mov_z_a) {
  State state;
  state.z = 0;
  state.a = 1;
  state.function_table[100] = pack(44, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.z == 1);
  assert(state.a == 1);
}

TEST_CASE(step_swap_a_b) {
  State state;
  state.a = 0;
  state.b = 1;
  state.function_table[100] = pack(45, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.b == 0);
}

TEST_CASE(step_swap_a_c) {
  State state;
  state.a = 0;
  state.c = 1;
  state.function_table[100] = pack(50, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.c == 0);
}

TEST_CASE(step_swap_a_d) {
  State state;
  state.a = 0;
  state.d = 1;
  state.function_table[100] = pack(51, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.d == 0);
}

TEST_CASE(step_swap_a_e) {
  State state;
  state.a = 0;
  state.e = 1;
  state.function_table[100] = pack(52, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.e == 0);

}

TEST_CASE(step_swap_a_z) {
  State state;
  state.a = 0;
  state.z = 1;
  state.function_table[100] = pack(70, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
  assert(state.z == 0);
}

TEST_CASE(step_inc_a) {
  State state;
  state.a = 0;
  state.function_table[100] = pack(71, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 1);
}

TEST_CASE(step_inc_b) {
  State state;
  state.b = 0;
  state.function_table[100] = pack(72, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.b == 1);
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

TEST_CASE(step_loop_not_taken) {
  State state;
  state.pc = 100;
  state.c = 1;
  state.function_table[100] = pack(82, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.c == 0);
  assert(state.pc == 101);
  assert(state.ir == pack(95, 0, 0, 0, 0, 0));
}

TEST_CASE(step_loop_taken) {
  State state;
  state.pc = 100;
  state.c = 2;
  state.function_table[100] = pack(82, 42, 95, 0, 0, 0);
  step(&state);
  assert(state.c == 1);
  assert(state.pc == 142);
  assert(state.ir == 0);
}

TEST_CASE(step_jsr) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(83, 42, 3, 95, 0, 0);
  step(&state);
  assert(state.stack[0] == 101);
  assert(state.q == 1);
  assert(state.pc == 342);
  assert(state.ir == 0);
}

TEST_CASE(step_ret) {
  State state;
  state.q = 1;
  state.pc = 342;
  state.stack[0] = 101;
  state.function_table[342] = pack(84, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.q == 0);
  assert(state.ir == 0);
}

TEST_CASE(step_nested_jsr) {
  State state;
  state.pc = 100;
  state.function_table[100] = pack(83, 0, 2, 0, 0, 0);
  state.function_table[101] = pack(83, 0, 3, 0, 0, 0);
  state.function_table[200] = pack(83, 0, 3, 0, 0, 0);
  state.function_table[201] = pack(84, 95, 0, 0, 0, 0);
  state.function_table[300] = pack(84, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.pc == 200);
  assert(state.stack[0] == 101);
  assert(state.q == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 300);
  assert(state.stack[1] == 201);
  assert(state.q == 0);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 201);
  assert(state.q == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 101);
  assert(state.q == 0);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 300);
  assert(state.stack[0] == 102);
  assert(state.q == 1);
  assert(state.ir == 0);
  step(&state);
  assert(state.pc == 102);
  assert(state.q == 0);
  assert(state.ir == 0);
}

TEST_CASE(step_add) {
  State state;
  state.pc = 100;
  state.a = 10;
  state.d = 72;
  state.function_table[100] = pack(85, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 82);
}

TEST_CASE(step_sub) {
  State state;
  state.pc = 100;
  state.a = 10;
  state.d = 32;
  state.function_table[100] = pack(90, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 100 - 22);
}

TEST_CASE(step_neg) {
  State state;
  state.pc = 100;
  state.a = 10;
  state.function_table[100] = pack(91, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 100 - 10);
}

TEST_CASE(step_clr) {
  State state;
  state.pc = 100;
  state.a = 42;
  state.function_table[100] = pack(92, 95, 0, 0, 0, 0);
  step(&state);
  assert(state.a == 0);
}

int main() {
  for (auto* test: tests) {
    test->run();
  }
  printf("Ran %ld tests.", tests.size());
  return 0;
}
