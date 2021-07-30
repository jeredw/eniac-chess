#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <utility>
#include <algorithm>
#include <readline/readline.h>
#include <readline/history.h>
#include <signal.h>

struct VM {
  int isa_version = 0;
  bool halted = false;
  bool breakpoint = false;

  // Fetch state
  int pc = 100;
  int old_pc = 0;
  int ir[6]{};
  int ir_index = 6;
  // Register file
  int rf[5]{};
  int &a = rf[0];
  int &b = rf[1];
  int &c = rf[2];
  int &d = rf[3];
  int &e = rf[4];
  // Load store scratch
  int ls[5]{};
  int &f = ls[0];
  int &g = ls[1];
  int &h = ls[2];
  int &i = ls[3];
  int &j = ls[4];
  // Memory
  int mem[15][5]{};

  // ROM, essentially
  int function_table[400][6]{};
};

static void usage() {
  fprintf(stderr, "Usage: chsim program.e\n");
}

static bool read_program(const char* filename, VM* vm) {
  FILE* fp = fopen(filename, "r");
  if (!fp) {
    fprintf(stderr, "could not open %s\n", filename);
    return false;
  }
  char line[128];
  int line_number = 2;
  if (!fgets(line, 128, fp) || strcmp(line, "# isa=v4\n") != 0) {
    fprintf(stderr, "expecting # isa=v4\n");
    goto error;
  }
  vm->isa_version = 4;
  while (fgets(line, 128, fp)) {
    if (line[0] == '#' || line[0] == '\n') {
      continue;
    }
    int ft, row, index, digit;
    char bank;
    if (sscanf(line, "s f%d.R%c%dL%d %d", &ft, &bank, &row, &index, &digit) != 5) {
      fprintf(stderr, "%s:%d: unrecognized directive\n", filename, line_number);
      goto error;
    }
    if (ft < 1 || ft > 3) {
      fprintf(stderr, "%s:%d: expecting ft 1-3 %d\n", filename, line_number, ft);
      goto error;
    }
    if (bank != 'A' && bank != 'B') {
      fprintf(stderr, "%s:%d: expecting ft bank A or B %c\n", filename, line_number, bank);
      goto error;
    }
    if (row < 0 || row >= 100) {
      fprintf(stderr, "%s:%d: expecting ft row 0-99 %d\n", filename, line_number, row);
      goto error;
    }
    if (index < 1 || index > 6) {
      fprintf(stderr, "%s:%d: expecting ft row index 1-6 %d\n", filename, line_number, index);
      goto error;
    }
    if (digit < 0 || digit > 9) {
      fprintf(stderr, "%s:%d: expecting ft digit %d\n", filename, line_number, digit);
      goto error;
    }
    int row_index = ft * 100 + row;
    int word_index = (bank == 'A' ? 0 : 3) + (6 - index) / 2;
    int shifted_digit = index % 2 == 0 ? 10 * digit : digit;
    vm->function_table[row_index][word_index] += shifted_digit;
    assert(0 <= vm->function_table[row_index][word_index]);
    assert(vm->function_table[row_index][word_index] <= 99);
    line_number++;
  }
  fclose(fp);
  return true;

error:
  fclose(fp);
  return false;
}

static void assert_sanity(VM* vm) {
  assert(vm->a >= -100 && vm->a < 100);
  assert(vm->b >= 0 && vm->b < 100);
  assert(vm->c >= 0 && vm->c < 100);
  assert(vm->d >= 0 && vm->d < 100);
  assert(vm->e >= 0 && vm->e < 100);
  assert(vm->f >= -100 && vm->f < 100);
  assert(vm->g >= 0 && vm->g < 100);
  assert(vm->h >= 0 && vm->h < 100);
  assert(vm->i >= 0 && vm->i < 100);
  assert(vm->j >= 0 && vm->j < 100);
  assert(vm->pc >= 100 && vm->pc < 400);
  assert(vm->old_pc == 0 || (vm->old_pc >= 100 && vm->old_pc < 400));
  assert(vm->ir_index >= 0 && vm->ir_index <= 6);
  for (int i = 0; i < 15; i++) {
    for (int j = 0; j < 5; j++) {
      assert(vm->mem[i][j] >= 0 && vm->mem[i][j] < 100);
    }
  }
}

static int drop_sign(int a) {
  if (a >= 0) {
    return a;
  }
  return a + 100;  // e.g. M99 (-1) -> P99
}

static void swap_with_a_sign(int& a, int& x) {
  if (a >= 0) {
    std::swap(a, x);
  } else {
    int tmp = a;
    a = x - 100;  // e.g. x=P01 -> a=M01 (-99)
    x = tmp + 100;  // e.g. a=M01 (-99) -> x=P01
  }
}

static int consume_ir(VM* vm) {
  if (vm->ir_index == 6) {
    vm->ir_index = vm->pc >= 300 ? 1 : 0;
    std::copy(vm->function_table[vm->pc], vm->function_table[vm->pc] + 6, vm->ir);
    vm->pc++;
    if (vm->pc == 200 || vm->pc == 300) {
      fprintf(stderr, "function table wrapping unsupported\n");
      return 95; // halt
    }
  }
  return vm->ir[vm->ir_index++];
}

static void dump_regs(VM* vm);
static int consume_operand(VM *vm) {
  if (vm->ir_index == 6) {
    fprintf(stderr, "misaligned operand\n");
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

static int consume_near_address(VM *vm) {
  int target = consume_operand(vm);
  return 100 * (vm->pc / 100) + target;
}

static int consume_far_address(VM *vm) {
  int target = consume_operand(vm);
  int bank = consume_ir(vm);
  if (!(bank == 9 || bank == 90 || bank == 99)) {
    fprintf(stderr, "illegal bank in far address %d at %d\n", bank, vm->pc);
    vm->halted = true;
    return vm->pc;
  }
  if (bank == 9)
    return 100 + target;
  else if (bank == 90)
    return 200 + target;
  else
    return 300 + target;
}

static void step(VM* vm) {
  if (vm->halted) return;
  int opcode = consume_ir(vm);
  switch (opcode) {
    case 0: // clrall
      vm->a = 0;
      vm->b = 0;
      vm->c = 0;
      vm->d = 0;
      vm->e = 0;
      break;
    case 1: swap_with_a_sign(vm->a, vm->b); break; // swap A, B
    case 2: swap_with_a_sign(vm->a, vm->c); break; // swap A, C
    case 3: swap_with_a_sign(vm->a, vm->d); break; // swap A, D
    case 4: swap_with_a_sign(vm->a, vm->e); break; // swap A, E
    case 10: // loadacc A
      assert(0 <= vm->a && vm->a < 15);
      std::copy(vm->mem[vm->a], vm->mem[vm->a] + 5, vm->ls);
      break;
    case 11: // storeacc A
      assert(0 <= vm->a && vm->a < 15);
      vm->f = drop_sign(vm->f);
      std::copy(vm->ls, vm->ls + 5, vm->mem[vm->a]);
      break;
    case 12: std::swap(vm->rf, vm->ls); break; // swapall
    case 14: { // ftl A,D
      int offset = drop_sign(vm->a);
      if (!(8 <= offset && offset <= 99)) {
        fprintf(stderr, "ftl %d out of bounds\n", vm->a);
        vm->halted = true;
        break;
      }
      vm->d = vm->function_table[300 + offset][0];
      consume_operand(vm);
      break;
    }
    case 20: vm->a = vm->b; break; // mov B, A
    case 21: vm->a = vm->c; break; // mov C, A
    case 22: vm->a = vm->d; break; // mov D, A
    case 23: vm->a = vm->e; break; // mov E, A
    case 34: vm->a = drop_sign(vm->f); break; // mov F, A
    case 30: vm->a = vm->g; break; // mov G, A
    case 31: vm->a = vm->h; break; // mov H, A
    case 32: vm->a = vm->i; break; // mov I, A
    case 33: vm->a = vm->j; break; // mov J, A
    case 40: vm->a = consume_operand(vm); break; // mov imm, A
    case 41: { // mov [B], A
      if (vm->b < 0 || vm->b >= 75) {
        fprintf(stderr, "mem %d out of bounds\n", vm->b);
        vm->halted = true;
        break;
      }
      int acc = vm->b / 5;
      int word = vm->b % 5;
      std::copy(vm->mem[acc], vm->mem[acc] + 5, vm->ls);
      vm->a = vm->ls[word];
      break;
    }
    case 42: { // mov A, [B]
      if (vm->b < 0 || vm->b >= 75) {
        fprintf(stderr, "mem %d out of bounds\n", vm->b);
        vm->halted = true;
        break;
      }
      int acc = vm->b / 5;
      int word = vm->b % 5;
      std::copy(vm->mem[acc], vm->mem[acc] + 5, vm->ls);
      vm->ls[word] = drop_sign(vm->a);
      std::copy(vm->ls, vm->ls + 5, vm->mem[acc]);
      break;
    }
    case 52: // inc A
      vm->a++;
      if (vm->a == 100)
        vm->a = -100;
      break;
    case 53: // dec A
      vm->a--;
      if (vm->a == -101)
        vm->a = 99;
      break;
    case 70: // add D,A
      vm->a += vm->d;
      if (vm->a >= 100)
        vm->a -= 200;
      break;
    case 71: // add imm,A
      vm->a += consume_operand(vm);
      if (vm->a >= 100)
        vm->a -= 200;
      break;
    case 72: // sub D,A
      vm->a -= vm->d;
      if (vm->a >= 100)
        vm->a -= 200;
      if (vm->a < -100)
        vm->a += 200;
      break;
    case 73: { // jmp
      vm->pc = consume_near_address(vm);
      vm->ir_index = 6;
      break;
    }
    case 74: { // jmp far
      vm->pc = consume_far_address(vm);
      vm->ir_index = 6;
      break;
    }
    case 80: { // jn
      int taken_pc = consume_near_address(vm);
      if (vm->a < 0) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      break;
    }
    case 81: { // jz
      int taken_pc = consume_near_address(vm);
      if (vm->a == 0 || vm->a == -100) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      break;
    }
    case 82: { // jil
      int taken_pc = consume_near_address(vm);
      int d1 = abs(vm->a) % 10;
      int d2 = (abs(vm->a) / 10) % 10;
      if (d1 == 0 || d1 == 9 || d2 == 0 || d2 == 9) {
        vm->pc = taken_pc;
        vm->ir_index = 6;
      }
      break;
    }
    case 84: { // jsr
      vm->old_pc = vm->pc;
      assert(vm->ir_index <= 5);
      vm->pc = consume_far_address(vm);
      vm->ir_index = 6;
      break;
    }
    case 85: // ret
      vm->pc = vm->old_pc;
      vm->old_pc = 0;
      vm->ir_index = 6;
      break;
    case 90: vm->a = 0; break; // clr A
    case 91: { // read
      int f, g, h1;
      fprintf(stderr, "?");
      fflush(stderr);
      while (scanf("%02d%02d%d", &f, &g, &h1) != 3) {
        fprintf(stderr, "expect ffggh e.g. 01020\n");
      }
      vm->f = f;
      vm->g = g;
      vm->h = 10 * h1 + (vm->h % 10);
      break;
    }
    case 92: // print
      printf("%02d%02d\n", drop_sign(vm->a), vm->b);
      break;
    case 94: // brk
      vm->breakpoint = true;
      break;
    case 95: // halt
      vm->halted = true;
      break;
    case 99: // sled
      break;
    default: // invalid opcode
      vm->halted = true;
      break;
  }
  assert_sanity(vm);
}

// Pass VM state by value because IR updates needed for operand decoding are destructive.
// Returns true if op should be skipped over while single stepping.
static bool disassemble(char* buf, size_t size, VM vm) {
  int opcode = consume_ir(&vm);
  switch (opcode) {
    case 0: snprintf(buf, size, "clrall"); break;
    case 1: snprintf(buf, size, "swap A,B"); break;
    case 2: snprintf(buf, size, "swap A,C"); break;
    case 3: snprintf(buf, size, "swap A,D"); break;
    case 4: snprintf(buf, size, "swap A,E"); break;
    case 10: snprintf(buf, size, "loadacc A"); break;
    case 11: snprintf(buf, size, "storeacc A"); break;
    case 12: snprintf(buf, size, "swapall"); break;
    case 14: snprintf(buf, size, "ftl A,D"); break;
    case 20: snprintf(buf, size, "mov B,A"); break;
    case 21: snprintf(buf, size, "mov C,A"); break;
    case 22: snprintf(buf, size, "mov D,A"); break;
    case 23: snprintf(buf, size, "mov E,A"); break;
    case 34: snprintf(buf, size, "mov F,A"); break;
    case 30: snprintf(buf, size, "mov G,A"); break;
    case 31: snprintf(buf, size, "mov H,A"); break;
    case 32: snprintf(buf, size, "mov I,A"); break;
    case 33: snprintf(buf, size, "mov J,A"); break;
    case 40: snprintf(buf, size, "mov %d,A", consume_operand(&vm)); break;
    case 41: snprintf(buf, size, "mov [B],A"); break;
    case 42: snprintf(buf, size, "mov A,[B]"); break;
    case 52: snprintf(buf, size, "inc A"); break;
    case 53: snprintf(buf, size, "dec A"); break;
    case 70: snprintf(buf, size, "add D,A"); break;
    case 71: snprintf(buf, size, "add %d,A", consume_operand(&vm)); break;
    case 72: snprintf(buf, size, "sub D,A"); break;
    case 73: snprintf(buf, size, "jmp %d", consume_near_address(&vm)); break;
    case 74: snprintf(buf, size, "jmp %d", consume_far_address(&vm)); break;
    case 80: snprintf(buf, size, "jn %d", consume_near_address(&vm)); break;
    case 81: snprintf(buf, size, "jz %d", consume_near_address(&vm)); break;
    case 82: snprintf(buf, size, "jil %d", consume_near_address(&vm)); break;
    case 84: snprintf(buf, size, "jsr %d", consume_far_address(&vm)); break;
    case 85: snprintf(buf, size, "ret"); break;
    case 90: snprintf(buf, size, "clr A"); break;
    case 91: snprintf(buf, size, "read"); break;
    case 92: snprintf(buf, size, "print"); break;
    case 94: snprintf(buf, size, "brk"); break;
    case 95: snprintf(buf, size, "halt"); break;
    case 99: snprintf(buf, size, "sled");
             return true;
    default:
      snprintf(buf, size, "???  # invalid opcode %02d", opcode);
      break;
  }
  return false;
}

static void dump_regs(VM* vm) {
  printf("PC  RR  A   B  C  D  E  F  G  H  I  J  %*s\n", 1 + 2 * vm->ir_index, "v");
  printf("%03d %03d %c%02d %02d %02d %02d %02d %02d %02d %02d %02d %02d %02d%02d%02d%02d%02d%02d...\n",
         vm->pc, vm->old_pc,
         vm->a < 0 ? 'M' : 'P',
         drop_sign(vm->a), vm->b, vm->c, vm->d, vm->e,
         vm->f, vm->g, vm->h, vm->i, vm->j,
         vm->ir[0], vm->ir[1], vm->ir[2], vm->ir[3], vm->ir[4], vm->ir[5]);
}

static void dump_current_instruction(VM *vm, char *dis) {
  const char* state = vm->halted ? " [halted]" :
                      vm->breakpoint ? " [break]" :
                      "";
  printf("  %s%s\n", dis, state);
}

static void dump_memory(VM *vm) {
  printf("   x0 x1 x2 x3 x4 x5 x6 x7 x8 x9\n");
  size_t mem_size = sizeof(vm->mem) / sizeof(vm->mem[0]);
  for (int i = 0; i < mem_size; i += 2) {
    printf("%dx %02d %02d %02d %02d %02d",
           i/2, vm->mem[i][0], vm->mem[i][1], vm->mem[i][2], vm->mem[i][3], vm->mem[i][4]);
    if (i+1 < mem_size) {
      printf(" %02d %02d %02d %02d %02d\n",
             vm->mem[i+1][0], vm->mem[i+1][1], vm->mem[i+1][2], vm->mem[i+1][3], vm->mem[i+1][4]);
    } else {
      printf("\n");
    }
  }
}

static void dump_memory_accs(VM *vm) {
  printf("   A B C D E\n");
  for (int i = 0; i < sizeof(vm->mem) / sizeof(vm->mem[0]); i++) {
    printf("%02d %02d%02d%02d%02d%02d\n",
           i, vm->mem[i][0], vm->mem[i][1], vm->mem[i][2], vm->mem[i][3], vm->mem[i][4]);
  }
}

static bool interrupted = false;
static void interrupt(int) {
  interrupted = true;
}

#ifndef TEST  // Defined by chsim_test.cc for unit testing.
int main(int argc, char *argv[]) {
  if (argc != 2) {
    usage();
    exit(1);
  }
  VM vm;
  if (!read_program(argv[1], &vm)) {
    exit(1);
  }
  signal(SIGINT, interrupt);
  while (true) {
    char* command = readline("> ");
    if (strcmp(command, "h") == 0) {
      printf("supported commands:\n");
      printf("h - print help\n");
      printf("q - quit\n");
      printf("r - print vm registers\n");
      printf("m - print vm memory (linear addresses)\n");
      printf("ma - print vm memory (accumulators)\n");
      printf("g - run (until halt or ^C)\n");
      printf("n - step one instruction and print\n");
    } else if (strcmp(command, "q") == 0) {
      break;
    } else if (strcmp(command, "r") == 0) {
      dump_regs(&vm);
    } else if (strcmp(command, "n") == 0) {
      vm.breakpoint = false;
      bool skip = true;
      while (skip) {
        char dis[128];
        skip = disassemble(dis, sizeof(dis)-1, vm);
        if (!skip) {
          dump_regs(&vm);
          dump_current_instruction(&vm, dis);
        }
        step(&vm);
      }
    } else if (strcmp(command, "m") == 0) {
      dump_memory(&vm);
    } else if (strcmp(command, "ma") == 0) {
      dump_memory_accs(&vm);
    } else if (strcmp(command, "g") == 0) {
      interrupted = false;
      while (!interrupted && !vm.breakpoint && !vm.halted) {
        step(&vm);
      }
      {
        dump_regs(&vm);
        char dis[128];
        disassemble(dis, sizeof(dis)-1, vm);
        dump_current_instruction(&vm, dis);
      }
    }
    free(command);
  }
  return 0;
}
#endif  // TEST