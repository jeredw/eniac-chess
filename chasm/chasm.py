#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assembler for the ENIAC chess VM.

See chasm_test.asm and isa.md for a description of the assembly language and
available assembler directives.
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
import os
from dataclasses import dataclass

def usage():
  print("chasm.py in.asm out.e")

# These REs are all we need for the grammar of the assembly language.
COMMENT = re.compile(r";.*")
LINE = re.compile(r"""^(?P<label>\.?\w*)\s*  # optional label
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
    self.assembled_ops = 0

  def assemble(self, path):
    """Assemble file at path."""
    self.context.assembler_pass = 0
    self._do_pass(path)
    if not self.out.errors:
      self.context.assembler_pass = 1
      self._do_pass(path)
    return self.out

  def _do_pass(self, path):
    self.context.dirname = os.path.dirname(path)
    self.context.filename = os.path.basename(path)
    self.context.line_number = 0
    text = open(path).read()
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
      directive = op.startswith(".")

      if label:
        if len(label) == 1 or re.match(r"[-M]?\d+", label):
          # Labels that are all digits would be ambiguous with addresses.
          # Labels that are single characters would be ambiguous with registers.
          self.out.error(f"invalid label name '{label}'")
          continue
        if not directive:
          # Jumps are only allowed to the start of a function table row, so
          # labels can only point there.
          self.out.pad_to_new_row()

      if label and not op:
        self.builtins.dispatch(label, '.align', '')  # defining a label
      elif directive:
        if op == '.include':
          self._include(arg)
        else:
          self.builtins.dispatch(label, op, arg)
      elif self.context.isa:  # delegate to table for ISA
        self.context.isa.dispatch(label, op, arg)
        self.assembled_ops += (self.context.assembler_pass == 1) # count emitted ops once
      else:
        self.out.error("no isa selected, missing .isa directive? (stopping)")
        self.context.had_fatal_error = True
      if self.context.had_fatal_error:
        break

  def _include(self, filename):
    self.context.push_file()
    # Include paths are relative to the including source file
    path = os.path.join(self.context.dirname, filename)
    self._do_pass(path)
    self.context.pop_file()


class Context(object):
  """Global state for assembly, e.g. the current filename and line number."""
  def __init__(self):
    self.assembler_pass = 0
    self.dirname = None
    self.filename = None
    self.line_number = 0
    self.had_fatal_error = False
    self.isa = None  # object that knows how to assemble the selected isa
    self.isa_version = ''
    self.base_label = ''  # last base label, for .local labels
    self.labels = {}
    self.file_stack = []  # (dirname, filename, line_number)

  def _qualify_label(self, name):
    if name.startswith('.'):
      if not self.base_label:
        raise SyntaxError(f"unknown base label for local label '{name}'")
      return self.base_label + name
    return name

  def update_base_label(self, name):
    if not name.startswith('.'):
      self.base_label = name

  def lookup_label(self, name):
    qualified_name = self._qualify_label(name)
    return self.labels[qualified_name]

  def define_label(self, name, value):
    qualified_name = self._qualify_label(name)
    if qualified_name in self.labels:
      raise SyntaxError(f"redefinition of '{qualified_name}'")
    self.labels[qualified_name] = value

  def push_file(self):
    self.file_stack.append((self.dirname, self.filename, self.line_number))

  def pop_file(self):
    self.dirname, self.filename, self.line_number = self.file_stack.pop()


@dataclass
class Value:
  """An output value for the assembler"""
  word: int
  comment: str
  is_padding: bool
  section: str


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
    self.table_output_row = 6
    self.operand_correction = 0
    self.context = context
    self.wrapped_row = False
    self.section = '*'

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
    self.word_of_output_row = self.row_start()
    self.operand_correction = 0
    self.wrapped_row = False

  def pad_to_new_row(self):
    """Aligns output to start of a new function table row."""
    # If already at the start of a row, no need to pad.
    while not self.context.had_fatal_error and self.word_of_output_row != self.row_start():
      self.emit(99)

  def emit(self, *values, comment=""):
    """Emit one or more opcode/argument words.

    Places values on the same function table row, if necessary padding out the
    current row with 99s and moving to a new row to guarantee this.
    """

    # filling an FT to 99 is fine, but if there is another op before .org, error
    if self.wrapped_row:
      self.error(f"out of space on function table {self.output_row//100 - 1}")
      self.context.had_fatal_error = True
      return

    assert len(values) <= self.row_length()
    assert self.row_start() <= self.word_of_output_row < 6
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
        elif 300 <= self.output_row < 306:
          self.error(f"location {self.output_row} is reserved")
          self.context.had_fatal_error = True
          break
        elif self.output_row >= 400:
          self.error("beyond end of function table 3")
          self.context.had_fatal_error = True
          break
        else:
          if self.operand_correction != 0 and v == 0 and self.word_of_output_row == 5:
            # For e.g. xx xx xx [41 00] [00], we'd emit 41 99 99 - since 00 is clrall,
            # this is illegal. This is a little pathological so just error out.
            self.error("illegal clrall encoding at end of line")
            self.context.had_fatal_error = True
            break
          word = (v + self.operand_correction) % 100
          self.output[index] = Value(word, comment, v == 99, self.section)
          comment = ""  # comment applies to first word output
          # Carry operand correction through 99s
          # For example, for [41 00] [35], emit [41 99] [34] so that after
          # consuming the 99 operand, we're left with 35.
          if self.operand_correction != 0 and word != 99:
            self.operand_correction = 0
          # If this emit() has operands, the next value emitted should be -1
          if i == 0 and len(values) > 1 and self.minus1_operands:
            self.operand_correction = 99

      self.word_of_output_row += 1
      if self.word_of_output_row == 6:
        self.output_row += 1
        self.wrapped_row = self.output_row % 100 == 0
        self.word_of_output_row = self.row_start()
        if self.output_row == 300:
          self.output_row = 306  # skip table at start of ft3
        self.operand_correction = 0

  def get(self, ft, row, word):
    """Lookup value at given offset."""
    assert 1 <= ft <= 3
    assert 0 <= row <= 99
    assert 0 <= word <= 5
    return self.output.get((100 * ft + row, word), Value(0, "", False, '.'))

  def function_table(self):
    """Return the current function table."""
    if self.output_row is not None:
      return self.output_row // 100
    return 0

  # helpers to handle skipping first word for ft3
  def row_length(self):
    return 5 if self.function_table()==3 else 6

  def row_start(self):
    return 1 if self.function_table()==3 else 0

  def emit_table_value(self, row, word, comment=""):
    assert row >= 6
    if row > 99:
      self.error(f"table data overflow")
      self.context.had_fatal_error = True
      return
    if (300 + row, 0) in self.output:
      self.error("overwriting values in table")
      self.context.had_fatal_error = True
      return
    if self.context.assembler_pass == 0:
      self.table_output_row += 1
    else:
      self.output[(300 + row, 0)] = Value(word, comment, False, 'T')


class PrimitiveParsing(object):
  """Parsing utilities shared by builtin directives and ISA parsers.

  Inherit from this to get reusable parsers for numbers, addresses, etc.
  """
  def __init__(self, context, out):
    self.context = context
    self.out = out

  def _address(self, arg):
    """Parse arg as a function table address.

    Two digit addresses are relative to the current function table, and three
    digit addresses are absolute (with the first digit giving FT number).

    Note: You probably want _jump_target, instead.
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
      self.out.error(f"invalid address '{arg}': {e}")
      return 0

  def _jump_target(self, arg, far=False):
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
      address = self.context.lookup_label(arg)
      if address < 0:
        self.out.error(f"expecting address but got negative label '{arg}'")
        return 0
      return check_function_table(address)
    except KeyError:
      self.out.error(f"unrecognized label '{arg}'")
      return 0

  def _immediate(self, arg, require_defined=False):
    """Parse arg as a sum of two digit words or labels.

    If require_defined is true then labels must be defined even on the first
    assembly pass (used by .equ).
    """
    value = 0
    m = re.match(r"([-M]?\d+)(.*)", arg)
    if m and len(m.groups()) == 2:
      # parse unary literal at start of expression
      literal = m.groups()[0]
      value = (int(literal[1:], base=10) - 100 if literal.startswith('M') else
               int(literal, base=10))
      arg = m.groups()[1]
    # rest of expression is +/- separated positive terms which may also be labels
    sign = +1
    for token in re.split(r'([-+])', arg):
      token = token.strip()
      if token == '': continue
      elif token == '-': sign = -1
      elif token == '+': sign = +1
      elif re.match(r'\d+', token):
        value += sign * int(token, base=10)
      elif self.context.assembler_pass == 1 or require_defined:
        try:
          value += sign * self.context.lookup_label(token)
        except KeyError:
          self.out.error(f"unrecognized label '{token}'")
    if value < -100:
      self.out.error(f"invalid value '{value}': underflow")
    if value >= 100:
      self.out.error(f"invalid value '{value}': overflow")
    return value

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
        self.out.error(f"invalid argument '{arg}'")
        return
    elif arg:
      self.out.error(f"unexpected argument '{arg}'")
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
      ".section": self._section,
      ".table": self._table,
    }

  def dispatch(self, label, op, arg):
    """Parse a directive line."""
    try:
      self.dispatch_table[op](label, op, arg)
    except KeyError:
      self.out.error(f"unrecognized directive '{op}'")

  def _define_label(self, label, value):
    try:
      self.context.define_label(label, value)
    except SyntaxError as e:
      self.out.error(str(e))

  def _align(self, label, op, arg):
    """Forces output to the start of a function table row."""
    if arg != "":
      self.out.error(f"invalid .align argument '{arg}'")
      return
    self.out.pad_to_new_row()
    if label:
      self.context.update_base_label(label)
      if self.context.assembler_pass == 0:
        self._define_label(label, self.out.output_row)

  def _dw(self, label, op, arg):
    """Emits a literal value or values at the current output position."""
    values = re.split(r",\s*", arg)
    for value in values:
      # emit only does anything on pass 1 which also requires label defined
      word = self._immediate(value)
      if word < 0:
        self.out.error(".dw argument cannot be negative")
        return
      self.out.emit(word % 100, comment=f"{op} {word}")

  def _table(self, label, op, arg):
    """Emits a table within function table 3, word 0."""
    values = re.split(r",\s*", arg)
    if not values:
      self.out.error("expecting .table data, ...")
      return
    if not label:
      self.out.error("expecting label for .table")
    if self.context.assembler_pass == 0:
      base = self.out.table_output_row
      self._define_label(label, base)
    else:
      base = self.context.lookup_label(label)
    for i, value in enumerate(values):
      word = self._immediate(value)
      self.out.emit_table_value(base + i, word, comment=f"{op} {300 + base}[{i}]={word}")

  def _section(self, label, op, arg):
    """Labels a section of the output for diagnostics."""
    if self.context.assembler_pass == 1:
      self.out.section = arg[0]

  def _equ(self, label, op, arg):
    """Assigns a value to a label directly."""
    if self.context.assembler_pass == 0:
      if not label:
        self.out.error("missing label for '.equ'")
        return
      # argument may be a label to permit things like
      # rook   .equ 1
      # bishop .equ 2
      # last_piece .equ bishop
      # Forward references aren't allowed because they'd require another
      # assembly pass.
      value = self._immediate(arg, require_defined=True)
      self._define_label(label, value)

  def _isa(self, label, op, arg):
    """Selects what isa to use."""
    if self.context.isa_version and self.context.isa_version != arg:
      self.out.error(f"saw isa '{arg}' but already selected isa '{self.context.isa_version}'")
    elif arg == "v4":
      self.context.isa_version = arg
      self.context.isa = V4(self.context, self.out)
    else:
      self.out.error(f"invalid isa '{arg}'")

  def _org(self, label, op, arg):
    """Sets output position for the assembler."""
    self.out.org(self._address(arg))
    if self.context.assembler_pass == 0 and label:
      self._define_label(label, self.out.output_row)


class V4(PrimitiveParsing):
  """Parses V4 of the VM ISA."""
  def __init__(self, context, out):
    PrimitiveParsing.__init__(self, context, out)
    self.dispatch_table = {
      "clrall": self.op(opcode=0),
      "swap": self._swap,
      "loadacc": self.op(want_arg=r"A", opcode=10),
      "storeacc": self.op(want_arg=r"A", opcode=11),
      "swapall": self.op(opcode=12),
      "ftl": self.op(want_arg=r"^A$", opcode=14),
      "mov": self._mov,
      "lodig": self.op(want_arg=r"A", opcode=43),
      "swapdig": self.op(want_arg=r"A", opcode=44),
      "inc": self.op(want_arg=r"A", opcode=52),
      "dec": self.op(want_arg=r"A", opcode=53),
      "flipn": self.op(opcode=54),
      "add": self._add,
      "addn": self._addn,
      "sub": self.op(want_arg=r"D,\s*A", opcode=72),
      "jmp": self._jmp,
      "jn": self._jn,
      "jz": self._jz,
      "jil": self._jil,
      "jsr": self._jsr,
      "ret": self._ret,
      "clr": self.op(want_arg=r"A", opcode=90),
      "read": self._read,
      "print": self.op(opcode=92),
      "brk": self.op(opcode=94),
      "halt": self.op(opcode=95),
    }

  def dispatch(self, label, op, arg):
    """Parse an instruction line."""
    try:
      self.dispatch_table[op](label, op, arg)
    except KeyError:
      self.out.error(f"unrecognized opcode '{op}' (using isa v4)")

  def encode_ft_number(self, ft):
    if ft == 1: return 9
    if ft == 2: return 90
    if ft == 3: return 99
    # Can happen for an unrecognized label, e.g. during the first pass
    return 0

  def _mov(self, label, op, arg):
    # Try each of these regexes in order and assemble the first that matches.
    patterns = [(r"B,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 20, ''),
                (r"C,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 21, ''),
                (r"D,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 22, ''),
                (r"E,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 23, ''),
                (r"F,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 34, ''),
                (r"G,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 30, ''),
                (r"H,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 31, ''),
                (r"I,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 32, ''),
                (r"J,\s*A(\s*<->\s*(?P<target>[BCDE]))?", 33, ''),
                (r"A,\s*B", ('B', 1, 20), 'p'),
                (r"A,\s*C", ('C', 2, 21), 'p'),
                (r"A,\s*D", ('D', 3, 22), 'p'),
                (r"A,\s*E", ('E', 4, 23), 'p'),
                (r"\[B\],\s*A(\s*<->\s*(?P<target>[BCDE]))?", 41, ''),
                (r"A,\s*\[B\]", 42, ''),
                (r"(?P<source>.+),\s*A(\s*<->\s*(?P<target>[BCDE]))?", 40, 'w'),]
    for regex, opcode, arg_type in patterns:
      m = re.match(regex, arg)
      if m:
        if arg_type == 'p':
          # mov A,[BCDE] (from A into BCDE) is a pseudo op assembled as
          #  swap B,A     ; ABxxx -> BAxxx
          #  mov B,A      ; BAxxx -> AAxxx
          self.out.emit(opcode[1], comment=f"mov A,{opcode[0]}")
          self.out.emit(opcode[2])
        elif not arg_type:
          self.out.emit(opcode, comment=f"{op} {arg}")
        else:
          source = m.group('source')
          word = self._immediate(source)
          if word < 0: word += 100
          self.out.emit(opcode, word % 100,
                        comment=self._comment(op, arg, source, word))
        if 'target' in m.groupdict() and m.group('target'):
          target = m.group('target')
          self._swap('', 'swap', f'A,{target}')
        break
    else:
      self.out.error(f"invalid mov argument '{arg}'")

  def _add(self, label, op, arg):
    if re.match(r"D,\s*A$", arg):
      self.out.emit(70, comment=f"{op} {arg}")
    else:
      m = re.match(r"\s*(.+),\s*A$", arg)
      if m:
        source = m.group(1)
        word = self._immediate(source)
        if word < 0: word += 100
        self.out.emit(71, word % 100,
                      comment=self._comment(op, arg, source, word))
      else:
        self.out.error(f"invalid argument '{arg}'")

  def _addn(self, label, op, arg):
    m = re.match(r"\s*(.+),\s*A$", arg)
    if m:
      source = m.group(1)
      word = self._immediate(source)
      if word < 0: word += 100
      self.out.emit(71, ((100 - word) % 100),
                    comment=self._comment(op, arg, source, word))
    else:
      self.out.error(f"invalid argument '{arg}'")

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
      self.out.error(f"invalid swap argument '{arg}'")

  def _jmp(self, label, op, arg):
    if arg.startswith("far "):
      # There is a separate "jmp far" menmonic so that we always know the size
      # of instructions, so we can unambiguously compute label targets on the
      # first pass.  arg[4:] strips off the leading "far ".
      address = self._jump_target(arg[4:], far=True)
      self.out.emit(74, address % 100, self.encode_ft_number(address // 100),
                    comment=self._comment(op, arg, arg[4:], address))
    else:
      address = self._jump_target(arg, far=False)
      self.out.emit(73, address % 100, comment=self._comment(op, arg, arg, address))
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _jn(self, label, op, arg):
    address = self._jump_target(arg, far=False)
    self.out.emit(80, address % 100, comment=self._comment(op, arg, arg, address))

  def _jz(self, label, op, arg):
    address = self._jump_target(arg, far=False)
    self.out.emit(81, address % 100, comment=self._comment(op, arg, arg, address))

  def _jil(self, label, op, arg):
    address = self._jump_target(arg, far=False)
    self.out.emit(82, address % 100, comment=self._comment(op, arg, arg, address))

  def _jsr(self, label, op, arg):
    address = self._jump_target(arg, far=True)
    self.out.emit(84, address % 100, self.encode_ft_number(address // 100),
                  comment=self._comment(op, arg, arg, address))
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _ret(self, label, op, arg):
    self._generic(label, op, arg, opcode=85)
    self.out.pad_to_new_row()  # The rest of the row is unreachable

  def _read(self, label, op, arg):
    if arg:
      self.out.error(f"unexpected argument '{arg}'")
      return
    # help the hw out by clearing LS before read (it does not do so)
    self.out.emit(12, comment=f"{op} sequence")  # swapall
    self.out.emit(0)   # clrall
    self.out.emit(12)  # swapall
    self.out.emit(91)  # read

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
      physical_row = row + 2  # programs use A+2 addressing
      for word_index in range(6):
        value = out.get(ft, row, word_index)
        bank = "A" if word_index < 3 else "B"
        word = value.word
        if word < 0:
          assert ft == 3
          assert word_index == 0
          word = 100 + word
          print(f"s f3.RB{physical_row}S M", file=f)
        for digit in range(2):
          line = 6 - (2 * (word_index%3) + digit)
          s = f"s f{ft}.R{bank}{physical_row}L{line} {(word//10)%10}"
          word *= 10
          if digit == 0 and value.comment:
            s += f"  # {value.comment}"
          print(s, file=f)
      print(file=f)


def print_output_chart(out, assembled_ops):
  table_values = sum((300 + i, 0) in out.output for i in range(6, 100))
  print(f'{assembled_ops} instructions, {table_values} table values')
  for d in range(10):
    print(10 * str(d), end='')
  print()
  for d in range(100):
    print(str(d%10), end='')
  print()
  for ft in [1,2,3]:
    for i in range(6):
      row_bitmap = []
      for row in range(100):
        value = out.get(ft, row, i)
        if ft == 3 and row < 6:
          row_bitmap.append('|')
        elif value.is_padding:
          row_bitmap.append(':')
        else:
          row_bitmap.append(value.section)
      print(''.join(row_bitmap))


def main():
  if len(sys.argv) != 3:
    usage()
    sys.exit(1)
  infile = sys.argv[1]
  outfile = sys.argv[2]
  asm = Assembler()
  out = asm.assemble(infile)
  if out.errors:
    sys.exit(2)
  with open(outfile, 'w') as f:
    print_easm(out, f)

  print_output_chart(out, asm.assembled_ops)

if __name__ == "__main__":
  main()
