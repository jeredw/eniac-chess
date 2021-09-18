#include <assert.h>
#include <stdio.h>
#include <readline/readline.h>
#include <readline/history.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

#include "vm.cc"

static FILE* output_file = nullptr;
const char* deck_filename = nullptr;
static FILE* deck_file = nullptr;
const char* program_filename = nullptr;
static bool interrupted = false;
static int test_cycles = 0;

static void usage() {
  fprintf(stderr, "Usage: chsim [-f data.deck] [-t cycles] program.e\n");
  exit(1);
}

static bool read_program(const char* filename, VM* vm) {
  FILE* fp = fopen(filename, "r");
  if (!fp) {
    fprintf(stderr, "could not open %s\n", filename);
    return false;
  }
  char line[128];
  int line_number = 1;
  if (!fgets(line, 128, fp) || strcmp(line, "# isa=v4\n") != 0) {
    fprintf(stderr, "expecting # isa=v4\n");
    goto error;
  }
  bool ft3_signs[100];
  for (int i = 0; i < 100; i++)
    ft3_signs[i] = false;
  while (fgets(line, 128, fp)) {
    line_number++;
    if (line[0] == '#' || line[0] == '\n') {
      continue;
    }
    int ft, row, index, digit;
    char bank, sign;
    if (sscanf(line, "s f3.RB%dS %c", &row, &sign) == 2) {
      assert(row >= 0 && row < 100);
      ft3_signs[row] = sign == 'M';
      continue;
    }
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
  }
  for (int i = 0; i < 100; i++) {
    if (ft3_signs[i]) {
      vm->function_table[300 + i][0] = vm->function_table[300 + i][0] - 100;
    }
  }
  fclose(fp);
  return true;

error:
  fclose(fp);
  return false;
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
    case 14: snprintf(buf, size, "ftl A"); break;
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
    case 43: snprintf(buf, size, "lodig A"); break;
    case 44: snprintf(buf, size, "swapdig A"); break;
    case 52: snprintf(buf, size, "inc A"); break;
    case 53: snprintf(buf, size, "dec A"); break;
    case 54: snprintf(buf, size, "flipn"); break;
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

static void dump_current_instruction(VM* vm, char* dis) {
  const char* state = (vm->status & HALT) ? " [halted]" :
                      (vm->status & BREAK) ? " [break]" :
                      "";
  printf("  %s%s\n", dis, state);
}

static void dump_memory(VM* vm) {
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

static void dump_memory_accs(VM* vm) {
  printf("   A B C D E\n");
  for (int i = 0; i < sizeof(vm->mem) / sizeof(vm->mem[0]); i++) {
    printf("%02d %02d%02d%02d%02d%02d\n",
           i, vm->mem[i][0], vm->mem[i][1], vm->mem[i][2], vm->mem[i][3], vm->mem[i][4]);
  }
}

static void dump_profile(VM vm) {
  const char* filename = "/tmp/chsim.prof";
  FILE* fp = fopen(filename, "w");
  for (int pc = 100; pc < 400; pc++) {
    for (int i = 0; i < 7; i++) {
      int count = vm.profile[pc][i];
      if (count > 0) {
        if (i != 6) {
          vm.pc = pc - 1;
          vm.ir_index = 6;
          consume_ir(&vm);
        }
        vm.pc = pc;
        vm.ir_index = i;
        char dis[128];
        bool skip = disassemble(dis, sizeof(dis)-1, vm);
        if (!skip) {
          int adjusted_pc = i == 6 ? pc : pc - 1;
          int adjusted_index = i == 6 ? 0 : i - 1;
          fprintf(fp, "%03d/%d  %-15s  ; %d\n", adjusted_pc, adjusted_index, dis, count);
        }
      }
    }
  }
  fclose(fp);
  printf("wrote profile to %s\n", filename);
}

static void interrupt(int) {
  interrupted = true;
}

static void step_and_handle_status(VM* vm) {
  step_one_instruction(vm);
  if (vm->error != 0) {
    fprintf(stderr, "error: %x\n", vm->error);
    return;
  }
  if (vm->status & IO_READ) {
    int f, g, h1;
    if (deck_file == stdin) {
      fprintf(stderr, "?");
      fflush(stderr);
    }
    int result = fscanf(deck_file, "%02d%02d%d ", &f, &g, &h1);
    if (result != 3) {
      fprintf(stderr, "invalid read data\n");
      vm->status |= HALT;
      return;
    }
    vm->f = f;
    vm->g = g;
    vm->h = 10 * h1 + (vm->h % 10);
    vm->status &= ~IO_READ;
  }
  if (vm->status & IO_PRINT) {
    printf("%02d%02d\n", drop_sign(vm->a), vm->b);
    fflush(stdout);
    fprintf(output_file, "%02d%02d\n", drop_sign(vm->a), vm->b);
    vm->status &= ~IO_PRINT;
  }
}

static void parse_command_line(int argc, char **argv) {
  if (argc == 1) usage();
  for (int i = 1; i < argc; i++) {
    if (strcmp(argv[i], "-f") == 0) {
      if (i == argc-1) usage();
      deck_filename = argv[++i];
    } else if (strcmp(argv[i], "-t") == 0) {
      if (i == argc-1) usage();
      test_cycles = atoi(argv[++i]);
    } else if (i == argc-1) {
      program_filename = argv[i];
    }
  }
  if (program_filename == nullptr) usage();
}

int main(int argc, char *argv[]) {
  parse_command_line(argc, argv);

  VM vm;
  init(&vm);
  if (!read_program(program_filename, &vm)) {
    exit(1);
  }

  // open deck file if specified, otherwise read from stdin
  if (deck_filename != nullptr) {
    deck_file = fopen(deck_filename, "r");
    if (!deck_file) {
      fprintf(stderr, "could not open deck file %s\n", deck_filename);
      exit(1);
    }
  } else {
    deck_file = stdin;
  }

  // tee output to a tmp file
  output_file = fopen("/tmp/chsim.out", "w");

  // non-interactive mode for unit tests
  // run for a fixed number of cycles or until halt/brk, then exit
  if (test_cycles > 0) {
    while (vm.cycles < test_cycles && !(vm.status & (BREAK|HALT))) {
      step_and_handle_status(&vm);
    }
    // exit 0 if halted, 1 otherwise
    exit((vm.status & HALT) ? 0 : 1);
  }

  // interactive mode
  rl_outstream = stderr;
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
      printf("pf - print execution profile\n");
      printf("g - run (until halt or ^C)\n");
      printf("n - step one instruction and print\n");
    } else if (strcmp(command, "q") == 0) {
      break;
    } else if (strcmp(command, "r") == 0) {
      dump_regs(&vm);
    } else if (strcmp(command, "n") == 0) {
      vm.status &= ~BREAK;
      bool skip = true;
      while (skip) {
        char dis[128];
        skip = disassemble(dis, sizeof(dis)-1, vm);
        if (!skip) {
          dump_regs(&vm);
          dump_current_instruction(&vm, dis);
        }
        step_and_handle_status(&vm);
      }
    } else if (strcmp(command, "m") == 0) {
      dump_memory(&vm);
    } else if (strcmp(command, "ma") == 0) {
      dump_memory_accs(&vm);
    } else if (strcmp(command, "pf") == 0) {
      dump_profile(vm);
    } else if (strcmp(command, "g") == 0) {
      interrupted = false;
      while (!interrupted && !vm.status) {
        step_and_handle_status(&vm);
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
  fclose(output_file);
  return 0;
}
