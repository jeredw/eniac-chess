#include <stdlib.h>
#include <utility>
#include <algorithm>

#include "vm.h"

// Reset state for a new VM instance
static void init(VM* vm) {
  vm->cycles = 0;
  vm->status = 0;
  vm->error = 0;
  vm->pc = 100;
  vm->old_pc = 0;
  for (int i = 0; i < 6; i++)
    vm->ir[i] = 0;
  vm->ir_index = 6;
  vm->a = 0;
  vm->b = 0;
  vm->c = 0;
  vm->d = 0;
  vm->e = 0;
  vm->f = 0;
  vm->g = 0;
  vm->h = 0;
  vm->i = 0;
  vm->j = 0;
  for (int i = 0; i < 15; i++)
    for (int j = 0; j < 5; j++)
      vm->mem[i][j] = 0;
  vm->ft_initialized = 0;
  for (int i = 0; i < 400; i++)
    for (int j = 0; j < 6; j++)
      vm->function_table[i][j] = 0;
  for (int i = 0; i < 400; i++)
    for (int j = 0; j < 7; j++)
      vm->profile[i][j] = 0;
}

// Returns a newly allocated VM instance
extern "C" VM *vm_new() {
  VM *vm = (VM *)malloc(sizeof(VM));
  init(vm);
  return vm;
}

// Releases a VM instance previously returned by vm_new
extern "C" void vm_free(VM* vm) {
  free(vm);
}

static void pack_acc(int a, int b, int c, int d, int e, char* arr) {
#define PACK_WORD(n, x)\
  arr[n] = '0' + (((x) / 10) % 10);\
  arr[n+1] = '0' + ((x) % 10)
  if (a < 0) {
    arr[0] = 'M';
    PACK_WORD(1, 100+a);
  } else {
    arr[0] = 'P';
    PACK_WORD(1, a);
  }
  PACK_WORD(3, b);
  PACK_WORD(5, c);
  PACK_WORD(7, d);
  PACK_WORD(9, e);
#undef PACK_WORD
}

static int unpack_word(char* arr, int n) {
  return 10 * (arr[n] - '0') + (arr[n+1] - '0');
}

static void unpack_acc(char* arr, int* a, int* b, int* c, int* d, int* e) {
  int a_digits = unpack_word(arr, 1);
  *a = arr[0] == 'M' ? a_digits - 100 : a_digits;
  *b = unpack_word(arr, 3);
  *c = unpack_word(arr, 5);
  *d = unpack_word(arr, 7);
  *e = unpack_word(arr, 9);
}

extern "C" int vm_import(VM* vm, ENIAC* eniac) {
  vm->cycles = eniac->cycles;
  vm->status &= ~(BREAK | IO_READ | IO_PRINT);

  int old_bank = unpack_word(eniac->acc[0], 3);
  int old_pc = unpack_word(eniac->acc[0], 5);
  switch (old_bank) {
    case 9: vm->old_pc = 100 + old_pc; break;
    case 90: vm->old_pc = 200 + old_pc; break;
    case 99: vm->old_pc = 300 + old_pc; break;
    // old_pc may be 0 initially
    default: vm->old_pc = 0; break;
  }
  int bank = unpack_word(eniac->acc[0], 7);
  int pc = unpack_word(eniac->acc[0], 9);
  switch (bank) {
    case 9: vm->pc = 100 + pc; break;
    case 90: vm->pc = 200 + pc; break;
    case 99: vm->pc = 300 + pc; break;
    default: return 1;
  }
  vm->ir_index = 6;

  unpack_acc(eniac->acc[3], &vm->f, &vm->g, &vm->h, &vm->i, &vm->j); // LS
  unpack_acc(eniac->acc[12], &vm->a, &vm->b, &vm->c, &vm->d, &vm->e); // RF
  int a = 4;
  for (int i = 0; i < 15; i++, a++) {
    if (a == 12) a++; // Skip over RF
    unpack_acc(eniac->acc[a], &vm->mem[i][0], &vm->mem[i][1], &vm->mem[i][2], &vm->mem[i][3], &vm->mem[i][4]);
  }

  if (!vm->ft_initialized) {
    for (int t = 0; t < 3; t++) {
      for (int r = 2; r < 104; r++) {
        int offset = (t+1)*100 + (r-2);
        int b_sign = t == 2 ? eniac->ft[2][r][13] : 0;
        int i1_digits = 10 * eniac->ft[t][r][1] + eniac->ft[t][r][2];
        vm->function_table[offset][0] = b_sign ? i1_digits - 100 : i1_digits;
        vm->function_table[offset][1] = 10 * eniac->ft[t][r][3] + eniac->ft[t][r][4];
        vm->function_table[offset][2] = 10 * eniac->ft[t][r][5] + eniac->ft[t][r][6];
        vm->function_table[offset][3] = 10 * eniac->ft[t][r][7] + eniac->ft[t][r][8];
        vm->function_table[offset][4] = 10 * eniac->ft[t][r][9] + eniac->ft[t][r][10];
        vm->function_table[offset][5] = 10 * eniac->ft[t][r][11] + eniac->ft[t][r][12];
      }
    }
    vm->ft_initialized = 1;
  }

  return 0;
}

extern "C" void vm_export(VM* vm, ENIAC* eniac) {
  eniac->cycles = vm->cycles;
  eniac->error_code = vm->error;
  eniac->rollback = vm->status != 0;
  for (int i = 0; i < 20; i++)
    eniac->acc[i][11] = 0;

  // PC = 00RRRRPPPP
  int bank = (vm->pc / 100) % 10;
  int old_bank = (vm->old_pc / 100) % 10;
  eniac->acc[0][0] = 'P';
  eniac->acc[0][1] = '0';
  eniac->acc[0][2] = '0';
  eniac->acc[0][3] = "0099"[old_bank];
  eniac->acc[0][4] = "0909"[old_bank];
  eniac->acc[0][5] = '0' + ((vm->old_pc / 10) % 10);
  eniac->acc[0][6] = '0' + (vm->old_pc % 10);
  eniac->acc[0][7] = "0099"[bank];
  eniac->acc[0][8] = "0909"[bank];
  eniac->acc[0][9] = '0' + ((vm->pc / 10) % 10);
  eniac->acc[0][10] = '0' + (vm->pc % 10);

  pack_acc(vm->f, vm->g, vm->h, vm->i, vm->j, eniac->acc[3]); // LS
  pack_acc(vm->a, vm->b, vm->c, vm->d, vm->e, eniac->acc[12]); // RF
  int a = 4;
  for (int i = 0; i < 15; i++, a++) {
    if (a == 12) a++; // Skip over RF
    int m0 = vm->mem[i][0];
    int m1 = vm->mem[i][1];
    int m2 = vm->mem[i][2];
    int m3 = vm->mem[i][3];
    int m4 = vm->mem[i][4];
    pack_acc(m0, m1, m2, m3, m4, eniac->acc[a]);
  }
}

static void check_register_bounds(VM* vm) {
#define CHECK(code, condition) if (!(condition)) vm->error |= code
  CHECK(ERROR_A_BOUNDS, vm->a >= -100 && vm->a < 100);
  CHECK(ERROR_B_BOUNDS, vm->b >= 0 && vm->b < 100);
  CHECK(ERROR_C_BOUNDS, vm->c >= 0 && vm->c < 100);
  CHECK(ERROR_D_BOUNDS, vm->d >= 0 && vm->d < 100);
  CHECK(ERROR_E_BOUNDS, vm->e >= 0 && vm->e < 100);
  CHECK(ERROR_F_BOUNDS, vm->f >= -100 && vm->f < 100);
  CHECK(ERROR_G_BOUNDS, vm->g >= 0 && vm->g < 100);
  CHECK(ERROR_H_BOUNDS, vm->h >= 0 && vm->h < 100);
  CHECK(ERROR_I_BOUNDS, vm->i >= 0 && vm->i < 100);
  CHECK(ERROR_J_BOUNDS, vm->j >= 0 && vm->j < 100);
  CHECK(ERROR_PC_BOUNDS, vm->pc >= 100 && vm->pc < 400);
  CHECK(ERROR_RR_BOUNDS, vm->old_pc == 0 || (vm->old_pc >= 100 && vm->old_pc < 400));
  CHECK(ERROR_IR_BOUNDS, vm->ir_index >= 0 && vm->ir_index <= 6);
  for (int i = 0; i < 15; i++) {
    for (int j = 0; j < 5; j++) {
      // First word of each memory accumulator can be negative; this is visible
      // through loadacc but not word mov.
      int min_value = j == 0 ? -100 : 0;
      if (!(vm->mem[i][j] >= min_value && vm->mem[i][j] < 100)) {
        vm->error = ERROR_MEM_BOUNDS | (5*i + j);
        break;
      }
    }
  }
  if (vm->error) vm->status |= HALT;
#undef CHECK
}

static int drop_sign(int a) {
  if (a >= 0) {
    return a;
  }
  return a + 100;  // e.g. M99 (-1) -> P99
}

static int copy_sign(int f, int a) {
  int digits = drop_sign(a);
  if (f >= 0) {
    return digits;
  }
  return digits - 100;  // e.g. P99 -> -1
}

static void swap_dropping_sign(int& a, int& x) {
  int tmp = drop_sign(a);
  a = x;
  x = tmp;
}

static int consume_ir(VM* vm) {
  if (vm->ir_index == 6) {
    vm->ir_index = vm->pc >= 300 ? 1 : 0;
    std::copy(vm->function_table[vm->pc], vm->function_table[vm->pc] + 6, vm->ir);
    vm->pc++;
    if (vm->pc == 200 || vm->pc == 300) {
      vm->error |= ERROR_PC_WRAPPED;
      vm->status |= HALT;
      return 95; // halt
    }
  }
  return vm->ir[vm->ir_index++];
}

static int consume_operand(VM* vm) {
  if (vm->ir_index == 6) {
    vm->error |= ERROR_OPERAND_MISALIGNED;
    vm->status |= HALT;
    return 95; // halt
  }
  vm->ir[vm->ir_index]++;
  int sled_start = 6;
  while (sled_start > 0 && vm->ir[sled_start-1] == 99) {
    sled_start--;
  }
  for (int i = vm->ir_index; i < 6; i++) {
    if (vm->ir[i] == 100) {
      vm->ir[i] = 0;
      // Do not carry into sled
      if (i < sled_start-1) {
        vm->ir[i+1]++;
      }
    }
  }
  return vm->ir[vm->ir_index++];
}

static int consume_near_address(VM* vm) {
  int target = consume_operand(vm);
  return 100 * (vm->pc / 100) + target;
}

static int consume_far_address(VM* vm) {
  int target = consume_operand(vm);
  int bank = consume_ir(vm);
  if (!(bank == 9 || bank == 90 || bank == 99)) {
    vm->error |= ERROR_ILLEGAL_BANK;
    vm->status |= HALT;
    return vm->pc;
  }
  if (bank == 9)
    return 100 + target;
  else if (bank == 90)
    return 200 + target;
  else
    return 300 + target;
}

static inline void copy_mem_to_ls(VM *vm, int acc) {
  vm->f = vm->mem[acc][0];
  vm->g = vm->mem[acc][1];
  vm->h = vm->mem[acc][2];
  vm->i = vm->mem[acc][3];
  vm->j = vm->mem[acc][4];
}

static inline void copy_ls_to_mem(VM *vm, int acc) {
  vm->mem[acc][0] = vm->f;
  vm->mem[acc][1] = vm->g;
  vm->mem[acc][2] = vm->h;
  vm->mem[acc][3] = vm->i;
  vm->mem[acc][4] = vm->j;
}

static void update_bank(VM* vm) {
  int bank = (vm->pc / 100) % 10;
  // Signs of a18, a19, and a20 reflect the current ft bank
  vm->mem[12][0] = copy_sign(bank == 1 ? +1 : -1, vm->mem[12][0]);
  vm->mem[13][0] = copy_sign(bank == 2 ? +1 : -1, vm->mem[13][0]);
  vm->mem[14][0] = copy_sign(bank == 3 ? +1 : -1, vm->mem[14][0]);
}

static void step_one_instruction(VM* vm) {
  if (vm->status & HALT) return;
  vm->profile[vm->pc][vm->ir_index]++;
  int fetch_cost = vm->ir_index < 6 ? 6 : vm->pc < 300 ? 12 : 13;
  int opcode = consume_ir(vm);
  if (opcode == 99) fetch_cost = 0;
  vm->cycles += fetch_cost;
  switch (opcode) {
    case 0: // clrall
      vm->a = 0;
      vm->b = 0;
      vm->c = 0;
      vm->d = 0;
      vm->e = 0;
      vm->cycles += 4;
      break;
    case 1: // swap A, B
      swap_dropping_sign(vm->a, vm->b);
      vm->cycles += 4;
      break;
    case 2: // swap A, C
      swap_dropping_sign(vm->a, vm->c);
      vm->cycles += 4;
      break;
    case 3: // swap A, D
      swap_dropping_sign(vm->a, vm->d);
      vm->cycles += 4;
      break;
    case 4: // swap A, E
      swap_dropping_sign(vm->a, vm->e);
      vm->cycles += 4;
      break;
    case 10: // loadacc A
      if (!(0 <= vm->a && vm->a < 15)) {
        vm->error |= ERROR_ILLEGAL_ACC;
        vm->status |= HALT;
        break;
      }
      copy_mem_to_ls(vm, vm->a);
      vm->cycles += 11;
      break;
    case 11: // storeacc A
      if (!(0 <= vm->a && vm->a < 15)) {
        vm->error |= ERROR_ILLEGAL_ACC;
        vm->status |= HALT;
        break;
      }
      vm->f = copy_sign(vm->mem[vm->a][0], vm->f);
      copy_ls_to_mem(vm, vm->a);
      vm->cycles += 13;
      break;
    case 12: // swapall
      std::swap(vm->a, vm->f);
      std::swap(vm->b, vm->g);
      std::swap(vm->c, vm->h);
      std::swap(vm->d, vm->i);
      std::swap(vm->e, vm->j);
      vm->cycles += 5;
      break;
    case 14: { // ftl A
      int offset = drop_sign(vm->a);
      if (!(8 <= offset && offset <= 99)) {
        vm->error |= ERROR_ILLEGAL_FTL;
        vm->status |= HALT;
        break;
      }
      vm->a = vm->function_table[300 + offset][0];
      vm->cycles += 7;
      break;
    }
    case 20: // mov B, A
      vm->a = vm->b;
      vm->cycles += 9;
      break;
    case 21: // mov C, A
      vm->a = vm->c;
      vm->cycles += 9;
      break;
    case 22: // mov D, A
      vm->a = vm->d;
      vm->cycles += 9;
      break;
    case 23: // mov E, A
      vm->a = vm->e;
      vm->cycles += 9;
      break;
    case 34: // mov F, A
      vm->a = drop_sign(vm->f);
      vm->cycles += 9;
      break;
    case 30: // mov G, A
      vm->a = vm->g;
      vm->cycles += 9;
      break;
    case 31: // mov H, A
      vm->a = vm->h;
      vm->cycles += 9;
      break;
    case 32: // mov I, A
      vm->a = vm->i;
      vm->cycles += 9;
      break;
    case 33: // mov J, A
      vm->a = vm->j;
      vm->cycles += 9;
      break;
    case 40: // mov imm, A
      vm->a = consume_operand(vm);
      vm->cycles += 4;
      break;
    case 41: { // mov [B], A
      if (vm->b < 0 || vm->b >= 75) {
        vm->error |= ERROR_ILLEGAL_ADDRESS;
        vm->status |= HALT;
        break;
      }
      int acc = vm->b / 5;
      int word = vm->b % 5;
      copy_mem_to_ls(vm, acc);
      switch (word) {
        case 0: vm->a = drop_sign(vm->f); break;
        case 1: vm->a = vm->g; break;
        case 2: vm->a = vm->h; break;
        case 3: vm->a = vm->i; break;
        case 4: vm->a = vm->j; break;
      }
      vm->cycles += 28;
      break;
    }
    case 42: { // mov A, [B]
      if (vm->b < 0 || vm->b >= 75) {
        vm->error |= ERROR_ILLEGAL_ADDRESS;
        vm->status |= HALT;
        break;
      }
      int acc = vm->b / 5;
      int word = vm->b % 5;
      copy_mem_to_ls(vm, acc);
      switch (word) {
        case 0: vm->f = copy_sign(vm->f, vm->a); break;
        case 1: vm->g = drop_sign(vm->a); break;
        case 2: vm->h = drop_sign(vm->a); break;
        case 3: vm->i = drop_sign(vm->a); break;
        case 4: vm->j = drop_sign(vm->a); break;
      }
      copy_ls_to_mem(vm, acc);
      vm->cycles += 37;
      break;
    }
    case 43: // lodig A
      if (vm->a >= 0) {
        vm->a = vm->a % 10;
      } else {
        // lodig M99 = M09 (-91)
        int digits = 100 + vm->a;
        int tens_digit = digits % 10; // M99 (-1) -> 9
        vm->a = tens_digit - 100; // 9 -> M09 (-91)
      }
      vm->cycles += 5;
      break;
    case 44: // swapdig A
      if (vm->a >= 0) {
        int tens_digit = vm->a / 10;
        int ones_digit = vm->a % 10;
        vm->a = 10 * ones_digit + tens_digit;
      } else {
        // swapdig M98 = M89
        int digits = 100 + vm->a; // M98 (-2) -> 98
        int tens_digit = digits / 10;
        int ones_digit = digits % 10;
        int swapped_digits = 10 * ones_digit + tens_digit;
        vm->a = swapped_digits - 100; // 89 -> M89 (-11)
      }
      vm->cycles += 5;
      break;
    case 52: // inc A
      vm->a++;
      if (vm->a == 100)
        vm->a = -100;
      vm->cycles += 1;
      break;
    case 53: // dec A
      vm->a--;
      if (vm->a == -101)
        vm->a = 99;
      vm->cycles += 1;
      break;
    case 54: // flipn
      if (vm->a < 0)
        vm->a += 100;
      else
        vm->a -= 100;
      vm->cycles += 2;
      break;
    case 70: // add D,A
      vm->a += vm->d;
      if (vm->a >= 100)
        vm->a -= 200;
      vm->cycles += 5;
      break;
    case 71: // add imm,A
      vm->a += consume_operand(vm);
      if (vm->a >= 100)
        vm->a -= 200;
      vm->cycles += 2;
      break;
    case 72: // sub D,A
      vm->a -= vm->d;
      if (vm->a >= 100)
        vm->a -= 200;
      if (vm->a < -100)
        vm->a += 200;
      vm->cycles += 5;
      break;
    case 73: { // jmp
      vm->pc = consume_near_address(vm);
      vm->ir_index = 6;
      vm->cycles += 2;
      break;
    }
    case 74: { // jmp far
      vm->pc = consume_far_address(vm);
      update_bank(vm);
      vm->ir_index = 6;
      vm->cycles += 6;
      break;
    }
    case 80: { // jn
      int taken_pc = consume_near_address(vm);
      if (vm->a < 0) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      vm->cycles += 6;
      break;
    }
    case 81: { // jz
      int taken_pc = consume_near_address(vm);
      if (vm->a == 0 || vm->a == -100) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      vm->cycles += 10;
      break;
    }
    case 82: { // jil
      int taken_pc = consume_near_address(vm);
      int digits = vm->a < 0 ? 100 + vm->a : vm->a;
      int d1 = digits % 10;
      int d2 = (digits / 10) % 10;
      if (d1 == 0 || d1 == 9 || d2 == 0 || d2 == 9) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      vm->cycles += 10;
      break;
    }
    case 84: { // jsr
      vm->old_pc = vm->pc;
      assert(vm->ir_index <= 5);
      vm->pc = consume_far_address(vm);
      update_bank(vm);
      vm->ir_index = 6;
      vm->cycles += 6;
      break;
    }
    case 85: // ret
      vm->pc = vm->old_pc;
      update_bank(vm);
      vm->old_pc = 0;
      vm->ir_index = 6;
      vm->cycles += 6;
      break;
    case 90: // clr A
      vm->a = 0;
      vm->cycles += 2;
      break;
    case 91: // read
      vm->status |= IO_READ;
      break;
    case 92: // print
      vm->status |= IO_PRINT;
      break;
    case 94: // brk
      vm->status |= BREAK;
      break;
    case 95: // halt
      vm->status |= HALT;
      break;
    case 99: // sled
      break;
    default: // illegal opcode
      vm->error |= ERROR_ILLEGAL_OPCODE;
      vm->status |= HALT;
      break;
  }
  check_register_bounds(vm);
}

extern "C" void vm_step(VM* vm) {
  if (vm->error != 0) {
    return;
  }
  vm->status &= ~(BREAK | IO_READ | IO_PRINT);
  for (;;) {
    step_one_instruction(vm);
    // Step until a new FT line is needed, or until I/O or break/halt.
    if (vm->ir_index == 6 || vm->status != 0 || vm->error != 0)
      break;
  }
}

extern "C" void vm_step_to(VM* vm, unsigned long long cycle) {
  if (vm->error != 0) {
    return;
  }
  vm->status &= ~(BREAK | IO_READ | IO_PRINT);
  VM next_vm = *vm;
  for (;;) {
    step_one_instruction(&next_vm);
    if (next_vm.error != 0) {
      *vm = next_vm;
      return;
    }
    if (next_vm.cycles > cycle || next_vm.status != 0)
      return;
    if (next_vm.ir_index == 6)
      *vm = next_vm;
  }
}