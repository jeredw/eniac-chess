#ifndef VM_H
#define VM_H

// C API for vm.so

// NOTE eniacsim doesn't depend on this file directly, but does rely on the
// exported function names below. It treats VM* as opaque and copies the
// definition of struct ENIAC.

// ENIAC state that corresponds with a VM state at the checkpoint
typedef struct eniac_t {
  unsigned long long cycles;
  int error_code; // vm error if not zero
  // rollback is set to true when VM encounters I/O, break or halt, and
  // indicates eniacsim should skip this snapshot and take over.
  int rollback;
  char acc[20][12]; // ASCII [PM]([0-9]{10})
  int ft[3][104][14];
} ENIAC;

typedef struct vm_t {
  unsigned long long cycles;
  int status;
  int error;

  // Fetch state
  int pc;
  int old_pc;
  int ir[6];
  int ir_index;
  // Register file
  int a;
  int b;
  int c;
  int d;
  int e;
  // Load store scratch
  int f;
  int g;
  int h;
  int i;
  int j;
  // Memory
  int mem[15][5];

  // ROM, essentially
  int function_table[400][6];
  int ft_initialized;

  // For profiling
  int profile[400][7];
} VM;

#ifdef __cplusplus
extern "C" {
#endif

// Allocates a new vm state
VM* vm_new();

// Populates a vm state from eniac state (at checkpoint)
int vm_import(VM* vm, ENIAC* eniac);

// Populates eniac state from vm state (at checkpoint)
void vm_export(VM* vm, ENIAC* eniac);

// Steps program to next checkpoint where vm and eniac state should match
void vm_step(VM* vm);

// Steps program up to but not exceeding cycle
void vm_step_to(VM* vm, unsigned long long cycle);

// Frees vm state previously allocated with vm_new()
void vm_free(VM* vm);

#ifdef __cplusplus
}
#endif

typedef enum vm_status_t {
  HALT = 0x01,
  BREAK = 0x02,
  IO_READ = 0x04,
  IO_PRINT = 0x08,
} VM_Status;

typedef enum vm_error_t {
  ERROR_A_BOUNDS = 1<<0,
  ERROR_B_BOUNDS = 1<<1,
  ERROR_C_BOUNDS = 1<<2,
  ERROR_D_BOUNDS = 1<<3,
  ERROR_E_BOUNDS = 1<<4,
  ERROR_F_BOUNDS = 1<<5,
  ERROR_G_BOUNDS = 1<<6,
  ERROR_H_BOUNDS = 1<<7,
  ERROR_I_BOUNDS = 1<<8,
  ERROR_J_BOUNDS = 1<<9,
  ERROR_PC_BOUNDS = 1<<10,
  ERROR_RR_BOUNDS = 1<<11,
  ERROR_IR_BOUNDS = 1<<12,
  ERROR_MEM_BOUNDS = 1<<13, // addr in lower bits
  ERROR_PC_WRAPPED = 1<<14,
  ERROR_OPERAND_MISALIGNED = 1<<15,
  ERROR_ILLEGAL_BANK = 1<<16,
  ERROR_ILLEGAL_ACC = 1<<17,
  ERROR_ILLEGAL_FTL = 1<<18,
  ERROR_ILLEGAL_ADDRESS = 1<<19,
  ERROR_ILLEGAL_OPCODE = 1<<20,
} VM_Error;

#endif // VM_H
