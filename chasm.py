#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assembler for the ENIAC chess VM.

See chasm_test.asm and vm-instruction-set.txt for a description of the assembly
language and available assembler directives.
"""

# This is a simple two pass table-driven assembler.
# - Pass 0: compute values for labels
# - Pass 1: emit code
#
# Because the ISA is under construction, programs are versioned using an .isa
# directive which selects the correct table for that ISA version - the "tables"
# are classes like V4 which implement a dispatch() method to assemble a given
# mnemonic.

import sys
import re
from dataclasses import dataclass

def usage():
  print("chasm.py in.asm out.e")

# These REs are all we need for the grammar of the assembly language.
COMMENT = re.compile(r";.*")
LINE = re.compile(r"""^(?P<label>\w*)\s*  # optional label
                       (?P<op>\.?\w*)\s*  # directive or mnemonic
                       (?P<arg>.*)$       # optional argument""", re.X)


class Assembler(object):
  """Assembles one file at a time and collects the output.

  - minus1_operands applies a -1 correction to operand words.
  - print_errors is to avoid spamming errors from unit tests.
  """
  def __init__(self,
               minus1_operands=True,
               print_errors=True):
    self.context = Context()
    self.out = Output(context=self.context,
                      minus1_operands=minus1_operands,
                      print_errors=print_errors)
    self.builtins = Builtins(self.context, self.out)

  def assemble(self, filename, text):
    """Assemble one file of text.

    filename is the name of the input file, used for printing error messages,
    and text is all the file's text as a string.
    """
    self.context.filename = filename
    self.context.assembler_pass = 0
    # We don't know where in the function tables assembly will begin.
    self.out.org(None)
    self._scan(text)
    if not self.out.errors:
      self.context.assembler_pass = 1
      self._scan(text)
    return self.out

  def _scan(self, text):
    # Do a single assembly pass (which one: context.assembler_pass) over text.
    for line_number, line in enumerate(text.splitlines()):
      self.context.line_number = line_number
      line = COMMENT.sub("", line).rstrip()  # Strip comments and newlines
      if not line: continue
      m = LINE.match(line)
      assert m  # should always match because "arg" group slurps everything
      label, op, arg = m.groups()

      if label:
        if len(label) == 1 or all(c.isdigit() for c in label):
          # Labels that are all digits would be ambiguous with addresses.
          # Labels that are single characters would be ambiguous with registers.
          self.out.error(f"invalid label name '{label}'")
          continue
        if op not in (".align", ".equ", ".org"):
          # Jumps are only allowed to the start of a function table row, so
          # labels can only point there.
          self.out.pad_to_new_row()

      if label and not op:
        self.builtins.dispatch(label, '.align', '')  # defining a label
      elif op.startswith('.'):  # directive
        self.builtins.dispatch(label, op, arg)
      elif self.context.isa:  # delegate to table for ISA
        self.context.isa.dispatch(label, op, arg)
      else:
        self.out.error("no isa selected, missing .isa directive? (stopping)")
        self.context.had_fatal_error = True
      if self.context.had_fatal_error:
        break


class Context(object):
  """Global state for assembly, e.g. the current filename and line number."""
  def __init__(self):
    self.assembler_pass = 0
    self.filename = None
    self.line_number = 0
    self.had_fatal_error = False
    self.isa = None  # object that knows how to assemble the selected isa
    self.isa_version = ''
    self.labels = {}


@dataclass
class Value:
  """An output value for the assembler"""
  word: int
  comment: str


class Output(object):
  """Collects assembler output, both errors and code.

  This class tracks the current output position in ENIAC function tables, and
  enforces packing constraints.
  """
  def __init__(self,
               context=None,
               minus1_operands=True,
               print_errors=True):
    self.minus1_operands = minus1_operands
    self.print_errors = print_errors
    self.errors = []
    self.output = {}
    self.output_row = None
    self.word_of_output_row = 0
    self.operand_correction = 0
    self.context = context

  def error(self, what):
    """Log an error message with context about where it happened."""
    message = "{}:{}: {}".format(self.context.filename,
                                 1 + self.context.line_number,
                                 what)
    self.errors.append(message)
    if self.print_errors:  # Disabled for unit tests to avoid spam
      print(message, file=sys.stderr)

  def org(self, output_row):
    """Change output location."""
    self.output_row = output_row
    self.word_of_output_row = 0
    self.operand_correction = 0

  def pad_to_new_row(self):
    """Aligns output to start of a new function table row."""
    # If already at the start of a row, no need to pad.
    while self.word_of_output_row != 0:
      self.emit(99)

  def emit(self, *values, comment=""):
    """Emit one or more opcode/argument words.

    Places values on the same function table row, if necessary padding out the
    current row with 99s and moving to a new row to guarantee this.
    """
    assert len(values) <= 6
    assert 0 <= self.word_of_output_row < 6
    space_left_in_row = 6 - self.word_of_output_row
    if len(values) > space_left_in_row:
      # values don't all fit, pad row with 99s and move to new row.
      self.pad_to_new_row()

    for i, v in enumerate(values):
      assert 0 <= v <= 99
      if self.output_row is None:
        self.error(".org not set")
        self.context.had_fatal_error = True
        break
      if self.context.assembler_pass == 1:
        # This is the second pass where we're actually emitting code.  (In the
        # first pass, we track output indices but don't generate code, because
        # we don't know label addresses yet.)
        index = (self.output_row, self.word_of_output_row)
        if index in self.output:
          self.error("overwriting output, conflicting .org?")
          self.context.had_fatal_error = True
          break
        elif 300 <= self.output_row < 308:
          self.error(f"location {self.output_row} is reserved")
          self.context.had_fatal_error = True
          break
        elif self.output_row >= 400:
          self.error("beyond end of function table 3")
          self.context.had_fatal_error = True
          break
        else:
          word = (v + self.operand_correction) % 100
          self.output[index] = Value(word, comment)
          comment = ""  # comment applies to first word output
          # Carry operand correction through 99s
          # For example, for [41 00] [35], emit [41 99] [34] so that after
          # consuming the 99 operand, we're left with 35.
          # NB for e.g. xx xx xx 41 00 00, we'll emit 41 99 99 - but this is ok
          # because nop at the end of a line and 99 are equivalent.
          if self.operand_correction != 0 and word != 99:
            self.operand_correction = 0
          # If this emit() has operands, the next value emitted should be -1
          if i == 0 and len(values) > 1 and self.minus1_operands:
            self.operand_correction = 99
      self.word_of_output_row += 1
      if self.word_of_output_row == 6:
        self.word_of_output_row = 0
        self.output_row += 1
        if self.output_row == 300:
          self.output_row = 308  # skip table at start of ft3
        self.operand_correction = 0

  def get(self, ft, row, word):
    """Lookup value at given offset."""
    assert 1 <= ft <= 3
    assert 0 <= row <= 99
    assert 0 <= word <= 5
    return self.output.get((100 * ft + row, word), Value(0, ""))

  def function_table(self):
    """Return the current function table."""
    if self.output_row is not None:
      return self.output_row // 100
    return 0


class PrimitiveParsing(object):
  """Parsing utilities shared by builtin directives and ISA parsers.

  Inherit from this to get reusable parsers for numbers, addresses, etc.
  """
  def __init__(self, context, out):
    self.context = context
    self.out = out

  def _word(self, arg):
    """Parse arg as a two digit word.
  
    Turns signed numbers into 10's complement without an explicit sign.
    """
    try:
      value = int(arg, base=10)
      if value < -50:
        raise ValueError("underflow")
      if value < 0:
        value = 100 + value
      if value >= 100:
        raise ValueError("overflow")
      return value
    except ValueError as e:
      self.out.error("invalid value '{}': {}".format(arg, e))
      return 0

  def _address(self, arg):
    """Parse arg as a function table address.

    Two digit addresses are relative to the current function table, and three
    digit addresses are absolute (with the first digit giving FT number).

    Note: You probably want _address_or_label, instead.
    """
    try:
      value = int(arg, base=10)
      if len(arg) <= 2:  # relative address
        if self.out.output_row is None:
          raise ValueError("relative address but no .org set")
        address = (self.out.function_table() * 100) + value
        return address
      else:  # absolute address
        if value < 100 or value > 399:
          raise ValueError("expect address between 100 and 399")
        return value
    except ValueError as e:
      self.out.error("invalid address '{}': {}".format(arg, e))
      return 0

  def _address_or_label(self, arg, far=False):
    """Parse arg as a function table address, possibly given by a label.

    If far is false, the address must reside in the current output function
    table.
    """
    def check_function_table(address):
      if not far and self.out.function_table() != address // 100:
        self.out.error("expecting address in current function table")
        return 0  # keep going to find more errors
      return address

    if re.match(r"\d+", arg):  # all digits - not a label
      return check_function_table(self._address(arg))
    if self.context.assembler_pass == 0:
      # Labels aren't resolved yet on the first pass.
      return 0
    try:
      return check_function_table(self.context.labels[arg])
    except KeyError:
      self.out.error("unrecognized label '{}'".format(arg))
      return 0

  def _word_or_label(self, arg, require_defined=False):
    """Parse arg as a two digit word or label with a two digit word value.

    If require_defined is true then labels must be defined even on the first
    assembly pass (used by .equ).
    """
    if re.match(r"-?\d+", arg):
      return self._word(arg)
    if self.context.assembler_pass == 0 and not require_defined:
      return 0
    try:
      return self.context.labels[arg]
    except KeyError:
      self.out.error("unrecognized label '{}'".format(arg))
      return 0

  def op(self, opcode='', want_arg=''):
    """Make a function to parse a simple instruction.

    Used to make filling out dispatch tables simpler.  opcode is the opcode to
    return and, if set, want_arg is a regex that must match the argument field.
    """
    return lambda label, op, arg: self._generic(label, op, arg,
                                                opcode=opcode,
                                                want_arg=want_arg)

  def _generic(self, label, op, arg, opcode=0, want_arg=''):
    """Generic parser for simple instructions."""
    if want_arg:
      if not re.match(want_arg, arg):
        self.out.error("invalid argument '{}'".format(arg))
        return
    elif arg:
      self.out.error("unexpected argument '{}'".format(arg))
      return
    self.out.emit(opcode, comment=f"{op} {arg}")


class Builtins(PrimitiveParsing):
  """Parses and applies side-effects from assembler directives."""
  def __init__(self, context, out):
    PrimitiveParsing.__init__(self, context, out)
    self.dispatch_table = {
      ".align": self._align,
      ".dw": self._dw,
      ".equ": self._equ,
      ".isa": self._isa,
      ".org": self._org,
    }

  def dispatch(self, label, op, arg):
    """Parse a directive line."""
    try:
      self.dispatch_table[op](label, op, arg)
    except KeyError:
      self.out.error("unrecognized directive '{}'".format(op))

  def _align(self, label, op, arg):
    """Forces output to the start of a function table row."""
    if arg != "":
      self.out.error("invalid .align argument '{}'".format(arg))
      return
    self.out.pad_to_new_row()
    if self.context.assembler_pass == 0:
      if label in self.context.labels:
        self.out.error("redefinition of '{}'".format(label))
        return
      if label: self.context.labels[label] = self.out.output_row

  def _dw(self, label, op, arg):
    """Emits a literal value or values at the current output position."""
    values = re.split(r",\s*", arg)
    for value in values:
      # emit only does anything on pass 1 which also requires label defined
      word = self._word_or_label(value)
      self.out.emit(word % 100, comment=f"{op} {word}")

  def _equ(self, label, op, arg):
    """Assigns a value to a label directly."""
    if self.context.assembler_pass == 0:
      if not label:
        self.out.error("missing label for '.equ'")
        return
      if label in self.context.labels:
        self.out.error("redefinition of '{}'".format(label))
        return
      # argument may be a label to permit things like
      # rook   .equ 1
      # bishop .equ 2
      # last_piece .equ bishop
      # Forward references aren't allowed because they'd require another
      # assembly pass.
      self.context.labels[label] = self._word_or_label(arg, require_defined=True)

  def _isa(self, label, op, arg):
    """Selects what isa to use."""
    if self.context.isa_version and self.context.isa_version != arg:
      self.out.error("saw isa '{}' but already selected isa '{}'".format(
                     arg, self.context.isa_version))
    elif arg == "v4":
      self.context.isa_version = arg
      self.context.isa = V4(self.context, self.out)
    else:
      self.out.error("invalid isa '{}'".format(arg))

  def _org(self, label, op, arg):
    """Sets output position for the assembler."""
    self.out.org(self._address(arg))
    if label: self.context.labels[label] = self.out.output_row


class V4(PrimitiveParsing):
  """Parses V4 of the VM ISA."""
  def __init__(self, context, out):
    PrimitiveParsing.__init__(self, context, out)
    self.dispatch_table = {
      "nop": self.op(opcode=0),
      "swap": self._swap,
      "loadacc": self.op(want_arg=r"A", opcode=10),
      "storeacc": self.op(want_arg=r"A", opcode=11),
      "swapall": self.op(opcode=12),
      "scanall": self.op(opcode=13),
      "ftload": self.op(want_arg=r"A", opcode=14),
      "ftlookup": self._ftlookup,
      "mov": self._mov,
      "inc": self._inc,
      "dec": self.op(want_arg=r"A", opcode=53),
      "add": self.op(want_arg=r"D,\s*A", opcode=70),
      "sub": self.op(want_arg=r"D,\s*A", opcode=72),
      "jmp": self._jmp,
      "jn": self._jn,
      "jz": self._jz,
      "jil": self._jil,
      "loop": self._loop,
      "jsr": self._jsr,
      "ret": self._ret,
      "clr": self.op(want_arg=r"A", opcode=90),
      "read": self.op(opcode=91),
      "print": self.op(opcode=92),
      "nextline": self.op(opcode=94),
      "halt": self.op(opcode=95),
    }

  def dispatch(self, label, op, arg):
    """Parse an instruction line."""
    try:
      self.dispatch_table[op](label, op, arg)
    except KeyError:
      self.out.error("unrecognized opcode '{}' (using isa v4)".format(op))

  def encode_ft_number(self, ft):
    if ft == 1: return 9
    if ft == 2: return 90
    if ft == 3: return 99
    # Can happen for an unrecognized label, e.g. during the first pass
    return 0

  def _mov(self, label, op, arg):
    # Try each of these regexes in order and assemble the first that matches
    # arg.  Note that [label] would also match [B] so order is important.
    # 'a' means the captured pattern is a direct address, and 'w' means
    # it is an immediate word.
    patterns = [(r"B,\s*A", 20, ''),
                (r"C,\s*A", 21, ''),
                (r"D,\s*A", 22, ''),
                (r"E,\s*A", 23, ''),
                (r"F,\s*A", 34, ''),
                (r"G,\s*A", 30, ''),
                (r"H,\s*A", 31, ''),
                (r"I,\s*A", 32, ''),
                (r"J,\s*A", 33, ''),
                (r"A,\s*B", ('B', 1, 20), 'p'),
                (r"A,\s*C", ('C', 2, 21), 'p'),
                (r"A,\s*D", ('D', 3, 22), 'p'),
                (r"A,\s*E", ('E', 4, 23), 'p'),
                (r"\[B\],\s*A", 43, ''),
                (r"\[(.+?)\],\s*A", 42, 'a'),
                (r"A,\s*\[B\]", 45, ''),
                (r"A,\s*\[(.+?)\]", 44, 'a'),
                (r"(.+),\s*A", 40, 'w'),
                (r"(.+),\s*D", 41, 'w'),]
    for regex, opcode, arg_type in patterns:
      m = re.match(regex, arg)
      if m:
        if arg_type == 'p':
          # mov A,[BCDE] (from A into BCDE) is a pseudo op assembled as
          #  swap B,A     ; ABxxx -> BAxxx
          #  mov B,A      ; BAxxx -> AAxxx
          self.out.emit(opcode[1], comment=f"mov {opcode[0]},A")
          self.out.emit(opcode[2])
        elif not arg_type:
          self.out.emit(opcode, comment=f"{op} {arg}")
        else:
          symbol = m.group(1)
          word = self._word_or_label(symbol)
          # Check that arg is a valid direct address (valid memory locations
          # are 0-74).
          if arg_type != 'a' or 0 <= word <= 74:
            self.out.emit(opcode, word % 100,
                          comment=self._comment(op, arg, symbol, word))
          else:
            self.out.error("address out of mov range '{}'".format(word))
        break
    else:
      self.out.error("invalid mov argument '{}'".format(arg))

  def _swap(self, label, op, arg):
    if re.match(r"B,\s*A|A,\s*B", arg):
      self.out.emit(1, comment=f"{op} {arg}")
    elif re.match(r"C,\s*A|A,\s*C", arg):
      self.out.emit(2, comment=f"{op} {arg}")
    elif re.match(r"D,\s*A|A,\s*D", arg):
      self.out.emit(3, comment=f"{op} {arg}")
    elif re.match(r"E,\s*A|A,\s*E", arg):
      self.out.emit(4, comment=f"{op} {arg}")
    elif re.match(r"F,\s*A|A,\s*F", arg):
      self.out.emit(5, comment=f"{op} {arg}")
    else:
      self.out.error("invalid swap argument '{}'".format(arg))

  def _ftlookup(self, label, op, arg):
    m = re.match(r"A,\s*(.+)", arg)
    if m:
      symbol = m.group(1)
      word = self._word_or_label(symbol)
      if 0 <= word <= 99:
        self.out.emit(15, word, comment=self._comment(op, arg, symbol, word))
      else:
        self.out.error("ftlookup argument out of range '{}'".format(word))
    else:
      self.out.error("invalid ftlookup argument '{}'".format(arg))

  def _inc(self, label, op, arg):
    if arg == "A":
      self.out.emit(52, comment=f"{op} {arg}")
    elif arg == "B":
      self.out.emit(54, comment=f"{op} {arg}")
    else:
      self.out.error("invalid inc argument '{}'".format(arg))

  def _jmp(self, label, op, arg):
    if arg == "+A":
      self.out.emit(75, comment=f"{op} {arg}")
    elif arg.startswith("far "):
      # There is a separate "jmp far" menmonic so that we always know the size
      # of instructions, so we can unambiguously compute label targets on the
      # first pass.  arg[4:] strips off the leading "far ".
      address = self._address_or_label(arg[4:], far=True)
      self.out.emit(74, address % 100, self.encode_ft_number(address // 100),
                    comment=self._comment(op, arg, arg[4:], address))
    else:
      address = self._address_or_label(arg, far=False)
      self.out.emit(73, address % 100, comment=self._comment(op, arg, arg, address))
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _jn(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(80, address % 100, comment=self._comment(op, arg, arg, address))

  def _jz(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(81, address % 100, comment=self._comment(op, arg, arg, address))

  def _jil(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(82, address % 100, comment=self._comment(op, arg, arg, address))

  def _loop(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(83, address % 100, comment=self._comment(op, arg, arg, address))

  def _jsr(self, label, op, arg):
    address = self._address_or_label(arg, far=True)
    self.out.emit(84, address % 100, self.encode_ft_number(address // 100),
                  comment=self._comment(op, arg, arg, address))
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _ret(self, label, op, arg):
    self._generic(label, op, arg, opcode=85)
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _comment(self, op, arg, symbol, word):
    # helper to symbolize comments
    if symbol != str(word):
      return f"{op} {arg} # {symbol}={word}"
    return f"{op} {arg}"


def print_easm(out, f):
  print(f"# isa={out.context.isa_version}", file=f)
  for ft in range(1, 3+1):
    for row in range(100):
      # omit rows which are all zero
      if all(out.get(ft, row, i).word == 0 for i in range(6)):
        continue
      logical_address = 100 * ft + row
      pc = 100 * out.context.isa.encode_ft_number(ft) + row
      print(f"# address={logical_address}  PC={pc:04}", file=f)
      for word_index in range(6):
        value = out.get(ft, row, word_index)
        bank = "A" if word_index < 3 else "B"
        word = value.word
        for digit in range(2):
          line = 6 - (2 * (word_index%3) + digit)
          s = f"s f{ft}.R{bank}{row}L{line} {(word//10)%10}"
          word *= 10
          if digit == 0 and value.comment:
            s += f"  # {value.comment}"
          print(s, file=f)
      print(file=f)


def main():
  if len(sys.argv) != 3:
    usage()
    sys.exit(1)
  infile = sys.argv[1]
  outfile = sys.argv[2]
  asm = Assembler()
  with open(infile) as f:
    text = f.read()
    out = asm.assemble(infile, text)
  if out.errors:
    sys.exit(2)
  with open(outfile, 'w') as f:
    print_easm(out, f)

if __name__ == "__main__":
  main()
