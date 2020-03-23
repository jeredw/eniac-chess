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

def usage():
  print("chasm.py infiles...")

# These REs are all we need for the grammar of the assembly language.
COMMENT = re.compile(r";.*")
LINE = re.compile(r"""^(?P<label>\w*)\s*  # optional label
                       (?P<op>\.?\w*)\s*  # directive or mnemonic
                       (?P<arg>.*)$       # optional argument""", re.X)


class Assembler(object):
  """Assembles one file at a time and collects the output.

  operands_in_same_row controls whether instructions and their operands must be
  packed into the same ENIAC function table row.
  print_errors is to avoid spamming errors from unit tests.
  """
  def __init__(self,
               operands_in_same_row=True,
               print_errors=True):
    self.context = Context()
    self.out = Output(context=self.context,
                      operands_in_same_row=operands_in_same_row,
                      print_errors=print_errors)
    self.builtins = Builtins(self.context, self.out)

  def assemble(self, filename, text):
    """Assemble one file of text.

    filename is the name of the file for error messages, and text is all the
    file's text as a string.
    """
    self.context.filename = filename
    self.context.assembler_pass = 0
    # We don't know where in the function tables assembly will begin.
    self.out.output_row = None
    self.out.word_of_output_row = 0
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
        if op not in (".align", ".equ", ".org"):
          # Jumps are only allowed to the start of a function table row, so
          # labels can only point there.  It'd be nicer syntax if labels forced
          # instructions to be aligned, but code space is tight and we might
          # make better coding decisions if we're forced to think about it.
          self.out.error("only '.align', '.equ', or '.org' may be labeled")
          continue
        if len(label) == 1 or all(c.isdigit() for c in label):
          # Labels that are all digits would be ambiguous with addresses.
          # Labels that are single characters would be ambiguous with registers.
          self.out.error("invalid label name '{}'".format(label))
          continue

      if op.startswith('.'):  # directive 
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


class Output(object):
  """Collects assembler output, both errors and code.

  This class tracks the current output position in ENIAC function tables, and
  enforces packing constraints.
  """
  def __init__(self,
               context=None,
               operands_in_same_row=True,
               print_errors=True):
    self.operands_in_same_row = operands_in_same_row
    self.print_errors = print_errors
    self.errors = []
    self.output = {}
    self.output_row = None
    self.word_of_output_row = 0
    self.context = context

  def error(self, what):
    """Log an error message with context about where it happened."""
    message = "{}:{}: {}".format(self.context.filename,
                                 1 + self.context.line_number,
                                 what)
    self.errors.append(message)
    if self.print_errors:  # Disabled for unit tests to avoid spam
      print(message)

  def emit(self, *values):
    """Emit one or more opcode/argument words.

    If operands_in_same_row is true, all the given values must go on the same
    function table row.  If necessary, pad out the current row with 0s (i.e.
    nops) and move to a new row to guarantee this.

    NB: Values that go on the same row need to be in the same emit() call.
    """
    if self.operands_in_same_row:
      assert len(values) <= 6
      assert 0 <= self.word_of_output_row < 6
      space_left_in_row = 6 - self.word_of_output_row
      if len(values) > space_left_in_row:
        # values don't all fit, pad row with 0s and move to new row.
        while self.word_of_output_row != 0:
          self.emit(0)

    for v in values:
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
        elif self.output_row >= 400:
          self.error("beyond end of function table 3")
          self.context.had_fatal_error = True
          break
        else:
          self.output[index] = v
      self.word_of_output_row += 1
      if self.word_of_output_row == 6:
        self.word_of_output_row = 0
        self.output_row += 1

  def to_array(self):
    """Dumps raw output function table contents as an array."""
    result = []
    for i in range(100, 400):
      row = 0
      for j in range(5, 0 - 1, -1):
        row *= 100
        if (i, j) in self.output:
          row += self.output[(i, j)]
      result.append(row)
    return result

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

  def bind(self, opcode='', want_arg=''):
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
    self.out.emit(opcode)


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
    # If already at the start of a row, no need to pad.
    while self.out.word_of_output_row != 0:
      self.out.emit(0)
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
      self.out.emit(word % 100)

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
    self.out.output_row = self._address(arg)
    self.out.word_of_output_row = 0
    if label: self.context.labels[label] = self.out.output_row


class V4(PrimitiveParsing):
  """Parses V4 of the VM ISA."""
  def __init__(self, context, out):
    PrimitiveParsing.__init__(self, context, out)
    self.dispatch_table = {
      "nop": self.bind(opcode=0),
      "swap": self._swap,
      "loadacc": self.bind(want_arg=r"A", opcode=10),
      "storeacc": self.bind(want_arg=r"A", opcode=11),
      "save": self.bind(opcode=12),
      "restore": self.bind(opcode=13),
      "swapsave": self.bind(opcode=14),
      "ftl": self.bind(opcode=15),
      "mov": self._mov,
      "indexhi": self.bind(opcode=40),
      "indexlo": self.bind(opcode=41),
      "selfmodify": self.bind(opcode=42),
      "scan": self.bind(opcode=43),
      "inc": self._inc,
      "dec": self.bind(want_arg=r"A", opcode=52),
      "add": self.bind(want_arg=r"A,\s*D", opcode=70),
      "neg": self.bind(want_arg=r"A", opcode=71),
      "sub": self.bind(want_arg=r"A,\s*D", opcode=72),
      "jmp": self._jmp,
      "jn": self._jn,
      "jz": self._jz,
      "loop": self._loop,
      "jsr": self._jsr,
      "ret": self.bind(opcode=84),
      "read": self.bind(want_arg=r"AB", opcode=93),
      "print": self.bind(want_arg=r"AB", opcode=94),
      "halt": self.bind(opcode=95),
    }

  def dispatch(self, label, op, arg):
    """Parse an instruction line."""
    try:
      self.dispatch_table[op](label, op, arg)
    except KeyError:
      self.out.error("unrecognized opcode '{}' (using isa v4)".format(op))

  def _mov(self, label, op, arg):
    # Try each of these regexes in order and assemble the first that matches
    # arg.  Note that [label] would also match [B] so order is important.
    # 'a' means the captured pattern is a direct address, and 'w' means
    # it is an immediate word.
    patterns = [(r"A,\s*B", 20, ''),
                (r"A,\s*C", 21, ''),
                (r"A,\s*D", 22, ''),
                (r"A,\s*E", 23, ''),
                (r"A,\s*Z", 24, ''),
                (r"A,\s*\[B\]", 33, ''),
                (r"A,\s*\[(.+?)\]", 31, 'a'),
                (r"\[B\],\s*A", 34, ''),
                (r"\[(.+?)\],\s*A", 32, 'a'),
                (r"A,\s*(.+)", 30, 'w'),]
    for regex, opcode, arg_type in patterns:
      m = re.match(regex, arg)
      if m:
        if not arg_type:
          self.out.emit(opcode)
        else:
          word = self._word_or_label(m.group(1))
          # Check that arg is a valid direct address (valid memory locations
          # are 0-74).
          if arg_type != 'a' or 0 <= word <= 74:
            self.out.emit(opcode, word % 100)
          else:
            self.out.error("address out of mov range '{}'".format(word))
        break
    else:
      self.out.error("invalid mov argument '{}'".format(arg))

  def _swap(self, label, op, arg):
    if re.match(r"B,\s*A|A,\s*B", arg):
      self.out.emit(1)
    elif re.match(r"C,\s*A|A,\s*C", arg):
      self.out.emit(2)
    elif re.match(r"D,\s*A|A,\s*D", arg):
      self.out.emit(3)
    elif re.match(r"E,\s*A|A,\s*E", arg):
      self.out.emit(4)
    elif re.match(r"Z,\s*A|A,\s*Z", arg):
      self.out.emit(5)
    else:
      self.out.error("invalid swap argument '{}'".format(arg))

  def _inc(self, label, op, arg):
    if arg == "A":
      self.out.emit(50)
    elif arg == "B":
      self.out.emit(51)
    else:
      self.out.error("invalid inc argument '{}'".format(arg))

  def _jmp(self, label, op, arg):
    if arg == "+A":
      self.out.emit(75)
    elif arg.startswith("far "):
      # There is a separate "jmp far" menmonic so that we always know the size
      # of instructions, so we can unambiguously compute label targets on the
      # first pass.  arg[4:] strips off the leading "far ".
      address = self._address_or_label(arg[4:], far=True)
      self.out.emit(74, address % 100, address // 100)
    else:
      address = self._address_or_label(arg, far=False)
      self.out.emit(73, address % 100)

  def _jn(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(80, address % 100)

  def _jz(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(81, address % 100)

  def _loop(self, label, op, arg):
    address = self._address_or_label(arg, far=False)
    self.out.emit(82, address % 100)

  def _jsr(self, label, op, arg):
    address = self._address_or_label(arg, far=True)
    self.out.emit(83, address % 100, address // 100)


def main():
  if len(sys.argv) == 1:
    usage()
    sys.exit(1)
  asm = Assembler()
  for filename in sys.argv[1:]:
    with open(filename) as f:
      text = f.read()
    out = asm.assemble(filename, text)
  if not out.errors:
    print("; isa={}".format(out.context.isa_version))
    for i, row in enumerate(out.to_array()):
      print("{:03d}: {:012d}".format(100 + i, row))

if __name__ == "__main__":
  main()
