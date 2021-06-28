#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from chasm import *

class AssemblerTestCase(unittest.TestCase):
  def assertOutputValues(self, values):
    self.assertEqual(len(self.out.output), len(values))
    for address in values:
      self.assertTrue(address in self.out.output)
      self.assertEqual(self.out.output[address].word, values[address])


class TestOutput(AssemblerTestCase):
  def setUp(self):
    self.context = Context()
    self.context.filename = "file"
    self.out = Output(context=self.context,
                      print_errors=False)
    self.out.output_row = 100

  def testError(self):
    self.out.error("foo")
    self.assertEqual(self.out.errors, ["file:1: foo"])

  def testEmitPass0(self):
    self.context.assembler_pass = 0
    self.out.emit(42)
    self.assertFalse(self.out.errors)
    self.assertFalse(self.out.output)
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 1)

  def testEmitPass1(self):
    self.context.assembler_pass = 1
    self.out.emit(42)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 1)

  def testEmit2(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = False
    self.out.emit(42, 43)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 43})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 2)

  def testEmit2Pad1(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = False
    self.out.word_of_output_row = 5
    self.out.emit(42, 43)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 5): 99, (101, 0): 42, (101, 1): 43})
    self.assertEqual(self.out.output_row, 101)
    self.assertEqual(self.out.word_of_output_row, 2)

  def testEmit3(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = False
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 43, (100, 2): 44})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmit3Pad1(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = False
    self.out.word_of_output_row = 5
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 5): 99, (101, 0): 42, (101, 1): 43, (101, 2): 44})
    self.assertEqual(self.out.output_row, 101)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmit3Pad2(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = False
    self.out.word_of_output_row = 4
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 4): 99, (100, 5): 99, (101, 0): 42, (101, 1): 43, (101, 2): 44})
    self.assertEqual(self.out.output_row, 101)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmitMinus1OperandsNoCarry(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = True
    self.out.word_of_output_row = 0
    self.out.emit(41, 20)
    self.out.emit(35)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 19, (100, 2): 35})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmitMinus1OperandsCarry(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = True
    self.out.word_of_output_row = 0
    self.out.emit(41, 0)
    self.out.emit(35)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 99, (100, 2): 34})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmitMinus1OperandsCarryNops(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = True
    self.out.word_of_output_row = 0
    self.out.emit(41, 0)
    self.out.emit(0)
    self.out.emit(0)
    self.out.emit(35)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 99, (100, 2): 99, (100, 3): 99, (100, 4): 34})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 5)

  def testEmitMinus1OperandsJmpFar(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = True
    self.out.word_of_output_row = 0
    self.out.emit(74, 0, 99)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 74, (100, 1): 99, (100, 2): 98})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 3)

  def testEmitMinus1OperandsCarry2(self):
    self.context.assembler_pass = 1
    self.out.minus1_operands = True
    self.out.word_of_output_row = 0
    self.out.emit(41, 0)
    self.out.emit(0)
    self.out.emit(0)
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 99, (100, 2): 99, (100, 3): 99})
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 4)

  def testEmit_ErrorNoOutputRow(self):
    self.context.assembler_pass = 1
    self.out.output_row = None
    self.out.emit(42)
    self.assertEqual(self.out.errors, ["file:1: .org not set"])

  def testEmit_ErrorOverwriting(self):
    self.context.assembler_pass = 1
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.out.emit(42)
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.out.emit(42)
    self.assertEqual(self.out.errors, ["file:1: overwriting output, conflicting .org?"])

  def testEmit_ErrorReservedLocation(self):
    self.context.assembler_pass = 1
    self.out.output_row = 300
    self.out.word_of_output_row = 0
    self.out.emit(42)
    self.assertEqual(self.out.errors, ["file:1: location 300 is reserved"])

  def testEmit_ErrorPastEnd(self):
    self.context.assembler_pass = 1
    self.out.output_row = 400
    self.out.emit(42)
    self.assertEqual(self.out.errors, ["file:1: beyond end of function table 3"])

  def testGet(self):
    self.context.assembler_pass = 1
    for i in range(6 * 200 + 6 * 92):
      self.out.emit(i % 100)
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 400)
    self.assertEqual(self.out.word_of_output_row, 0)
    self.assertEqual(self.out.get(1, 42, 0), Value(word=52, comment=""))
    self.assertEqual(self.out.get(2, 42, 5), Value(word=57, comment=""))
    self.assertEqual(self.out.get(3, 42, 0), Value(word=4, comment=""))

  def testFunctionTable(self):
    self.out.output_row = 236
    self.assertEqual(self.out.function_table(), 2)


class TestBuiltins(AssemblerTestCase):
  def setUp(self):
    self.context = Context()
    self.context.filename = "file"
    self.out = Output(context=self.context, print_errors=False)
    self.builtins = Builtins(self.context, self.out)

  def testBogus(self):
    self.builtins.dispatch("", ".bogus", "")
    self.assertEqual(self.out.errors,
                     ["file:1: unrecognized directive '.bogus'"])

  def testAlign(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 5
    self.builtins.dispatch("", ".align", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 101)
    self.assertEqual(self.out.word_of_output_row, 0)

  def testAlignAtStartOfRow(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.builtins.dispatch("", ".align", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 0)

  def testAlignWithLabel(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 5
    self.builtins.dispatch("here", ".align", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.context.labels, {"here": 101})

  def testAlign_ErrorArg(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.builtins.dispatch("", ".align", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid .align argument 'bogus'"])

  def testAlign_ErrorLabelRedefinition(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 5
    self.context.labels = {"here": 42}
    self.builtins.dispatch("here", ".align", "")
    self.assertEqual(self.out.errors, ["file:1: redefinition of 'here'"])

  def testDw(self):
    self.out.output_row = 100
    self.context.labels = {"stuff": 43}
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 43})

  def testDwFar(self):
    self.out.output_row = 100
    self.context.labels = {"stuff": 399}
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 99})

  def testDw_ErrorUnrecognizedLabel(self):
    self.out.output_row = 100
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertEqual(self.out.errors, ["file:1: unrecognized label 'stuff'"])

  def testEquValue(self):
    self.builtins.dispatch("foo", ".equ", "42")
    self.assertEqual(self.context.labels, {"foo": 42})

  def testEquLabel(self):
    self.context.labels = {"bar": 55}
    self.builtins.dispatch("foo", ".equ", "bar")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.context.labels, {"foo": 55, "bar": 55})

  def testEquNegative(self):
    self.builtins.dispatch("foo", ".equ", "-42")
    self.assertEqual(self.context.labels, {"foo": 58})

  def testEqu_ErrorUnderflow(self):
    self.builtins.dispatch("foo", ".equ", "-51")
    self.assertEqual(self.out.errors, ["file:1: invalid value '-51': underflow"])

  def testEqu_ErrorOverflow(self):
    self.builtins.dispatch("foo", ".equ", "100")
    self.assertEqual(self.out.errors, ["file:1: invalid value '100': overflow"])

  def testEqu_ErrorNoLabel(self):
    self.builtins.dispatch("", ".equ", "42")
    self.assertEqual(self.out.errors, ["file:1: missing label for '.equ'"])

  def testEqu_ErrorLabelRedefinition(self):
    self.context.labels = {"foo": 27}
    self.builtins.dispatch("foo", ".equ", "42")
    self.assertEqual(self.out.errors, ["file:1: redefinition of 'foo'"])

  def testEqu_ErrorUnrecognizedLabel(self):
    self.builtins.dispatch("foo", ".equ", "bar")
    self.assertEqual(self.out.errors, ["file:1: unrecognized label 'bar'"])

  def testIsa(self):
    self.builtins.dispatch("", ".isa", "v4")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.context.isa_version, "v4")

  def testIsa_ErrorInvalid(self):
    self.builtins.dispatch("", ".isa", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid isa 'bogus'"])

  def testIsa_ErrorMultipleSpecified(self):
    self.builtins.dispatch("", ".isa", "v4")
    self.context.line_number += 1
    self.builtins.dispatch("", ".isa", "bogus")
    self.assertEqual(self.out.errors, ["file:2: saw isa 'bogus' but already selected isa 'v4'"])

  def testOrg(self):
    self.builtins.dispatch("", ".org", "100")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 100)
    self.assertEqual(self.out.word_of_output_row, 0)

  def testOrgRelative(self):
    self.builtins.dispatch("", ".org", "100")
    self.context.line_number += 1
    self.builtins.dispatch("", ".org", "50")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 150)
    self.assertEqual(self.out.word_of_output_row, 0)

  def testOrgWithLabel(self):
    self.builtins.dispatch("foo", ".org", "204")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output_row, 204)
    self.assertEqual(self.out.word_of_output_row, 0)
    self.assertEqual(self.context.labels, {"foo": 204})

  def testOrg_ErrorRange(self):
    self.builtins.dispatch("", ".org", "000")
    self.assertEqual(self.out.errors,
                     ["file:1: invalid address '000': expect address between 100 and 399"])

  def testOrg_ErrorUnexpectedRelative(self):
    self.builtins.dispatch("", ".org", "00")
    self.assertEqual(self.out.errors,
                     ["file:1: invalid address '00': relative address but no .org set"])

  def testOrg_ErrorInvalid(self):
    self.builtins.dispatch("", ".org", "pants")
    self.assertEqual(self.out.errors,
                     ["file:1: invalid address 'pants': invalid literal for int() with base 10: 'pants'"])


def pad(values):
  line = {(100, n): 99 for n in range(6)}
  line.update(values)
  return line


class TestV4(AssemblerTestCase):
  def setUp(self):
    self.context = Context()
    self.context.filename = "file"
    self.context.assembler_pass = 1
    self.out = Output(context=self.context, print_errors=False)
    self.out.output_row = 100
    self.isa = V4(self.context, self.out)

  def testBogus(self):
    self.isa.dispatch("", "bogus", "")
    self.assertEqual(self.out.errors,
                     ["file:1: unrecognized opcode 'bogus' (using isa v4)"])

  def testNop(self):
    self.isa.dispatch("", "nop", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 0})

  def testNop_ErrorArgument(self):
    self.isa.dispatch("", "nop", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])

  def testSwapBA(self):
    self.isa.dispatch("", "swap", "B, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 1})

  def testSwapAB(self):
    self.isa.dispatch("", "swap", "A, B")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 1})

  def testSwapCA(self):
    self.isa.dispatch("", "swap", "C, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 2})

  def testSwapAC(self):
    self.isa.dispatch("", "swap", "A, C")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 2})

  def testSwapDA(self):
    self.isa.dispatch("", "swap", "D, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 3})

  def testSwapAD(self):
    self.isa.dispatch("", "swap", "A, D")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 3})

  def testSwapEA(self):
    self.isa.dispatch("", "swap", "E, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 4})

  def testSwapAE(self):
    self.isa.dispatch("", "swap", "A, E")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 4})

  def testSwapFA(self):
    self.isa.dispatch("", "swap", "F, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 5})

  def testSwapAF(self):
    self.isa.dispatch("", "swap", "A, F")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 5})

  def testSwap_ErrorInvalidArgument(self):
    self.isa.dispatch("", "swap", "G")
    self.assertEqual(self.out.errors, ["file:1: invalid swap argument 'G'"])

  def testLoadacc(self):
    self.isa.dispatch("", "loadacc", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 10})

  def testLoadacc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "loadacc", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'bogus'"])

  def testStoreacc(self):
    self.isa.dispatch("", "storeacc", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 11})

  def testStoreacc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "storeacc", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'bogus'"])

  def testSwapall(self):
    self.isa.dispatch("", "swapall", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 12})

  def testSwapall_ErrorArgument(self):
    self.isa.dispatch("", "swapall", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])

  def testScanall(self):
    self.isa.dispatch("", "scanall", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 13})

  def testScanall_ErrorArgument(self):
    self.isa.dispatch("", "scanall", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])

  def testFtload(self):
    self.isa.dispatch("", "ftload", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 14})

  def testFtload_ErrorArgument(self):
    self.isa.dispatch("", "ftload", "B")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'B'"])

  def testFtlookup(self):
    self.isa.dispatch("", "ftlookup", "A, 99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 15, (100, 1): 98})

  def testFtlookupLabel(self):
    self.context.labels = {"label": 99}
    self.isa.dispatch("", "ftlookup", "A, label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 15, (100, 1): 98})

  def testFtlookupLabel_ErrorOutOfRange(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "ftlookup", "A, label")
    self.assertEqual(self.out.errors, ["file:1: ftlookup argument out of range '199'"])

  def testFtlookupLabel_ErrorInvalidArgument(self):
    self.isa.dispatch("", "ftlookup", "B, 99")
    self.assertEqual(self.out.errors, ["file:1: invalid ftlookup argument 'B, 99'"])

  def testMovBA(self):
    self.isa.dispatch("", "mov", "B, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 20})

  def testMovCA(self):
    self.isa.dispatch("", "mov", "C, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 21})

  def testMovDA(self):
    self.isa.dispatch("", "mov", "D, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 22})

  def testMovEA(self):
    self.isa.dispatch("", "mov", "E, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 23})

  def testMovFA(self):
    self.isa.dispatch("", "mov", "F, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 34})
    #self.assertOutputValues({(100, 0): 93})

  def testMovGA(self):
    self.isa.dispatch("", "mov", "G, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 30})

  def testMovHA(self):
    self.isa.dispatch("", "mov", "H, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 31})

  def testMovIA(self):
    self.isa.dispatch("", "mov", "I, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 32})

  def testMovJA(self):
    self.isa.dispatch("", "mov", "J, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 33})

  def testMovAB(self):
    self.isa.dispatch("", "mov", "A, B")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 1, (100, 1): 20})

  def testMovAC(self):
    self.isa.dispatch("", "mov", "A, C")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 2, (100, 1): 21})

  def testMovAD(self):
    self.isa.dispatch("", "mov", "A, D")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 3, (100, 1): 22})

  def testMovAE(self):
    self.isa.dispatch("", "mov", "A, E")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 4, (100, 1): 23})

  def testMovLoadAImmediate(self):
    self.isa.dispatch("", "mov", "99, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 40, (100, 1): 98})

  def testMovLoadAImmediateLabel(self):
    self.context.labels = {"label": 99}
    self.isa.dispatch("", "mov", "label, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 40, (100, 1): 98})

  def testMovLoadDImmediate(self):
    self.isa.dispatch("", "mov", "99, D")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 98})

  def testMovLoadDImmediateLabel(self):
    self.context.labels = {"label": 99}
    self.isa.dispatch("", "mov", "label, D")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 41, (100, 1): 98})

  def testMovLoadDirect(self):
    self.isa.dispatch("", "mov", "[42], A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 41})

  def testMovLoadDirectLabel(self):
    self.context.labels = {"label": 42}
    self.isa.dispatch("", "mov", "[label], A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 42, (100, 1): 41})

  def testMovLoadDirectLabel_ErrorOutOfRange(self):
    self.context.labels = {"label": 123}
    self.isa.dispatch("", "mov", "[label], A")
    self.assertEqual(self.out.errors, ["file:1: address out of mov range '123'"])

  def testMovStoreDirect(self):
    self.isa.dispatch("", "mov", "A, [42]")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 44, (100, 1): 41})

  def testMovStoreDirectLabel(self):
    self.context.labels = {"label": 42}
    self.isa.dispatch("", "mov", "A, [label]")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 44, (100, 1): 41})

  def testMovStoreDirectLabel_ErrorOutOfRange(self):
    self.context.labels = {"label": 123}
    self.isa.dispatch("", "mov", "A, [label]")
    self.assertEqual(self.out.errors, ["file:1: address out of mov range '123'"])

  def testMovLoadDirectB(self):
    self.isa.dispatch("", "mov", "[B], A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 43})

  def testMovStoreDirectB(self):
    self.isa.dispatch("", "mov", "A, [B]")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 45})

  def testMov_ErrorInvalidArgument(self):
    self.isa.dispatch("", "mov", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid mov argument 'bogus'"])

  def testIncA(self):
    self.isa.dispatch("", "inc", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 52})

  def testIncB(self):
    self.isa.dispatch("", "inc", "B")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 54})

  def testInc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "inc", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid inc argument 'bogus'"])

  def testDecA(self):
    self.isa.dispatch("", "dec", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 53})

  def testDec_ErrorInvalidArgument(self):
    self.isa.dispatch("", "dec", "B")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'B'"])

  def testAddDA(self):
    self.isa.dispatch("", "add", "D, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 70})

  def testAdd_ErrorInvalidArgument(self):
    self.isa.dispatch("", "add", "B, A")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'B, A'"])

  def testSubDA(self):
    self.isa.dispatch("", "sub", "D, A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 72})

  def testSub_ErrorInvalidArgument(self):
    self.isa.dispatch("", "sub", "B, A")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'B, A'"])

  def testJmp(self):
    self.isa.dispatch("", "jmp", "99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 73, (100, 1): 98}))

  def testJmpLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jmp", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 73, (100, 1): 98}))

  def testJmpLabel_ErrorUnrecognized(self):
    self.isa.dispatch("", "jmp", "label")
    self.assertEqual(self.out.errors, ["file:1: unrecognized label 'label'"])

  def testJmpLabel_ErrorFar(self):
    self.context.labels = {"label": 342}
    self.isa.dispatch("", "jmp", "label")
    self.assertEqual(self.out.errors, ["file:1: expecting address in current function table"])

  def testJmpFarFt1(self):
    self.isa.dispatch("", "jmp", "far 142")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 74, (100, 1): 41, (100, 2): 9}))

  def testJmpFarFt2(self):
    self.isa.dispatch("", "jmp", "far 242")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 74, (100, 1): 41, (100, 2): 90}))

  def testJmpFarFt3(self):
    self.isa.dispatch("", "jmp", "far 342")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 74, (100, 1): 41, (100, 2): 99}))

  def testJmpFarWithNearTarget(self):
    self.isa.dispatch("", "jmp", "far 42")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 74, (100, 1): 41, (100, 2): 9}))

  def testJmpFarLabel(self):
    self.context.labels = {"label": 342}
    self.isa.dispatch("", "jmp", "far label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 74, (100, 1): 41, (100, 2): 99}))

  def testJmpFarLabel_ErrorUnrecognized(self):
    self.isa.dispatch("", "jmp", "far label")
    self.assertEqual(self.out.errors, ["file:1: unrecognized label 'label'"])

  def testJmpA(self):
    self.isa.dispatch("", "jmp", "+A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 75}))

  def testJn(self):
    self.isa.dispatch("", "jn", "199")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 80, (100, 1): 98})

  def testJnRelative(self):
    self.isa.dispatch("", "jn", "99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 80, (100, 1): 98})

  def testJnLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jn", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 80, (100, 1): 98})

  def testJn_ErrorFar(self):
    self.isa.dispatch("", "jn", "299")
    self.assertEqual(self.out.errors, ["file:1: expecting address in current function table"])

  def testJz(self):
    self.isa.dispatch("", "jz", "199")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 81, (100, 1): 98})

  def testJzRelative(self):
    self.isa.dispatch("", "jz", "99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 81, (100, 1): 98})

  def testJzLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jz", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 81, (100, 1): 98})

  def testJz_ErrorFar(self):
    self.isa.dispatch("", "jz", "299")
    self.assertEqual(self.out.errors, ["file:1: expecting address in current function table"])

  def testJil(self):
    self.isa.dispatch("", "jil", "199")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 82, (100, 1): 98})

  def testJilRelative(self):
    self.isa.dispatch("", "jil", "99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 82, (100, 1): 98})

  def testJilLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jil", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 82, (100, 1): 98})

  def testJil_ErrorFar(self):
    self.isa.dispatch("", "jil", "299")
    self.assertEqual(self.out.errors, ["file:1: expecting address in current function table"])

  def testLoop(self):
    self.isa.dispatch("", "loop", "199")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 83, (100, 1): 98})

  def testLoopRelative(self):
    self.isa.dispatch("", "loop", "99")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 83, (100, 1): 98})

  def testLoopLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "loop", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 83, (100, 1): 98})

  def testLoop_ErrorFar(self):
    self.isa.dispatch("", "loop", "299")
    self.assertEqual(self.out.errors, ["file:1: expecting address in current function table"])

  def testJsr(self):
    self.isa.dispatch("", "jsr", "342")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 84, (100, 1): 41, (100, 2): 99}))

  def testJsrLabel(self):
    self.context.labels = {"label": 142}
    self.isa.dispatch("", "jsr", "label")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 84, (100, 1): 41, (100, 2): 9}))

  def testJsr_ErrorUnrecognizedLabel(self):
    self.isa.dispatch("", "jsr", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unrecognized label 'bogus'"])

  def testRet(self):
    self.isa.dispatch("", "ret", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues(pad({(100, 0): 85}))

  def testRet_ErrorInvalidArgument(self):
    self.isa.dispatch("", "ret", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])

  def testReadAB(self):
    self.isa.dispatch("", "read", "AB")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 91})

  def testRead_ErrorInvalidArgument(self):
    self.isa.dispatch("", "read", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'bogus'"])

  def testClrA(self):
    self.isa.dispatch("", "clr", "A")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 90})

  def testClr_ErrorInvalidArgument(self):
    self.isa.dispatch("", "clr", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'bogus'"])

  def testPrintAB(self):
    self.isa.dispatch("", "print", "AB")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 92})

  def testPrint_ErrorInvalidArgument(self):
    self.isa.dispatch("", "print", "bogus")
    self.assertEqual(self.out.errors, ["file:1: invalid argument 'bogus'"])

  def testNextline(self):
    self.isa.dispatch("", "nextline", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 94})

  def testNextline_ErrorInvalidArgument(self):
    self.isa.dispatch("", "nextline", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])

  def testHalt(self):
    self.isa.dispatch("", "halt", "")
    self.assertFalse(self.out.errors)
    self.assertOutputValues({(100, 0): 95})

  def testHalt_ErrorInvalidArgument(self):
    self.isa.dispatch("", "halt", "bogus")
    self.assertEqual(self.out.errors, ["file:1: unexpected argument 'bogus'"])


if __name__ == "__main__":
  unittest.main()
