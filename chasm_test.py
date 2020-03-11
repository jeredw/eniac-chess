#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from chasm import *

class TestOutput(unittest.TestCase):
  def setUp(self):
    self.context = Context()
    self.context.filename = "file"
    self.out = Output(context=self.context,
                      operands_in_same_row=True,
                      print_errors=False)
    self.out.output_row = 100

  def testError(self):
    self.out.error("foo")
    self.assertEqual(self.out.errors,
                     [("file", 1, "foo")])

  def testEmitPass0(self):
    self.context.assembler_pass = 0
    self.out.emit(42)
    self.assertFalse(self.out.errors)
    self.assertFalse(self.out.output)
    self.assertEquals(self.out.output_row, 100)
    self.assertEquals(self.out.word_of_output_row, 1)

  def testEmitPass1(self):
    self.context.assembler_pass = 1
    self.out.emit(42)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 0): 42})
    self.assertEquals(self.out.output_row, 100)
    self.assertEquals(self.out.word_of_output_row, 1)

  def testEmit2(self):
    self.context.assembler_pass = 1
    self.out.emit(42, 43)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 0): 42, (100, 1): 43})
    self.assertEquals(self.out.output_row, 100)
    self.assertEquals(self.out.word_of_output_row, 2)

  def testEmit2Pad1(self):
    self.context.assembler_pass = 1
    self.out.word_of_output_row = 5
    self.out.emit(42, 43)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 5): 0, (101, 0): 42, (101, 1): 43})
    self.assertEquals(self.out.output_row, 101)
    self.assertEquals(self.out.word_of_output_row, 2)

  def testEmit3(self):
    self.context.assembler_pass = 1
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 0): 42, (100, 1): 43, (100, 2): 44})
    self.assertEquals(self.out.output_row, 100)
    self.assertEquals(self.out.word_of_output_row, 3)

  def testEmit3Pad1(self):
    self.context.assembler_pass = 1
    self.out.word_of_output_row = 5
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 5): 0, (101, 0): 42, (101, 1): 43, (101, 2): 44})
    self.assertEquals(self.out.output_row, 101)
    self.assertEquals(self.out.word_of_output_row, 3)

  def testEmit3Pad2(self):
    self.context.assembler_pass = 1
    self.out.word_of_output_row = 4
    self.out.emit(42, 43, 44)
    self.assertFalse(self.out.errors)
    self.assertEquals(self.out.output, {(100, 4): 0, (100, 5): 0, (101, 0): 42, (101, 1): 43, (101, 2): 44})
    self.assertEquals(self.out.output_row, 101)
    self.assertEquals(self.out.word_of_output_row, 3)

  def testEmit_ErrorNoOutputRow(self):
    self.context.assembler_pass = 1
    self.out.output_row = None
    self.out.emit(42)
    self.assertEqual(self.out.errors,
                     [("file", 1, ".org not set")])

  def testEmit_ErrorOverwriting(self):
    self.context.assembler_pass = 1
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.out.emit(42)
    self.out.output_row = 100
    self.out.word_of_output_row = 0
    self.out.emit(42)
    self.assertEqual(self.out.errors,
                     [("file", 1, "overwriting output, conflicting .org?")])

  def testEmit_ErrorPastEnd(self):
    self.context.assembler_pass = 1
    self.out.output_row = 400
    self.out.emit(42)
    self.assertEqual(self.out.errors,
                     [("file", 1, "beyond end of function table 3")])

  def testToArray(self):
    self.context.assembler_pass = 1
    for i in range(6 * 300):
      self.out.emit(i % 100)
    self.assertEqual(self.out.output_row, 400)
    self.assertEqual(self.out.word_of_output_row, 0)
    result = self.out.to_array()
    self.assertEqual(len(result), 300)
    self.assertEqual(result[0],   50403020100)
    self.assertEqual(result[5],  353433323130)
    self.assertEqual(result[67],  70605040302)
    self.assertEqual(result[-1], 999897969594)

  def testFunctionTable(self):
    self.out.output_row = 236
    self.assertEqual(self.out.function_table(), 2)


class TestBuiltins(unittest.TestCase):
  def setUp(self):
    self.context = Context()
    self.context.filename = "file"
    self.out = Output(context=self.context, print_errors=False)
    self.builtins = Builtins(self.context, self.out)

  def testBogus(self):
    self.builtins.dispatch("", ".bogus", "")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized directive '.bogus'")])

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
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid .align argument 'bogus'")])

  def testAlign_ErrorLabelRedefinition(self):
    self.out.output_row = 100
    self.out.word_of_output_row = 5
    self.context.labels = {"here": 42}
    self.builtins.dispatch("here", ".align", "")
    self.assertEqual(self.out.errors,
                     [("file", 1, "redefinition of 'here'")])

  def testDw(self):
    self.out.output_row = 100
    self.context.labels = {"stuff": 43}
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 42, (100, 1): 43})

  def testDwFar(self):
    self.out.output_row = 100
    self.context.labels = {"stuff": 399}
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 42, (100, 1): 99})

  def testDw_ErrorUnrecognizedLabel(self):
    self.out.output_row = 100
    self.context.assembler_pass = 1
    self.builtins.dispatch("", ".dw", "42, stuff")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized label 'stuff'")])

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
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid value '-51': underflow")])

  def testEqu_ErrorOverflow(self):
    self.builtins.dispatch("foo", ".equ", "100")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid value '100': overflow")])

  def testEqu_ErrorNoLabel(self):
    self.builtins.dispatch("", ".equ", "42")
    self.assertEqual(self.out.errors,
                     [("file", 1, "missing label for '.equ'")])

  def testEqu_ErrorLabelRedefinition(self):
    self.context.labels = {"foo": 27}
    self.builtins.dispatch("foo", ".equ", "42")
    self.assertEqual(self.out.errors,
                     [("file", 1, "redefinition of 'foo'")])

  def testEqu_ErrorUnrecognizedLabel(self):
    self.builtins.dispatch("foo", ".equ", "bar")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized label 'bar'")])

  def testIsa(self):
    self.builtins.dispatch("", ".isa", "v4")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.context.isa_version, "v4")

  def testIsa_ErrorInvalid(self):
    self.builtins.dispatch("", ".isa", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid isa 'bogus'")])

  def testIsa_ErrorMultipleSpecified(self):
    self.builtins.dispatch("", ".isa", "v4")
    self.context.line_number += 1
    self.builtins.dispatch("", ".isa", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 2, "saw isa 'bogus' but already selected isa 'v4'")])

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
                     [("file", 1, "invalid address '000': expect address between 100 and 399")])

  def testOrg_ErrorUnexpectedRelative(self):
    self.builtins.dispatch("", ".org", "00")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid address '00': relative address but no .org set")])

  def testOrg_ErrorInvalid(self):
    self.builtins.dispatch("", ".org", "pants")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid address 'pants': invalid literal for int() with base 10: 'pants'")])


class TestV4(unittest.TestCase):
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
                     [("file", 1, "unrecognized opcode 'bogus' (using isa v4)")])

  def testNop(self):
    self.isa.dispatch("", "nop", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 0})

  def testNop_ErrorArgument(self):
    self.isa.dispatch("", "nop", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testSwapBA(self):
    self.isa.dispatch("", "swap", "B, A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 1})

  def testSwapAB(self):
    self.isa.dispatch("", "swap", "A, B")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 1})

  def testSwapCA(self):
    self.isa.dispatch("", "swap", "C, A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 2})

  def testSwapAC(self):
    self.isa.dispatch("", "swap", "A, C")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 2})

  def testSwapDA(self):
    self.isa.dispatch("", "swap", "D, A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 3})

  def testSwapAD(self):
    self.isa.dispatch("", "swap", "A, D")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 3})

  def testSwapEA(self):
    self.isa.dispatch("", "swap", "E, A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 4})

  def testSwapAE(self):
    self.isa.dispatch("", "swap", "A, E")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 4})

  def testSwapZA(self):
    self.isa.dispatch("", "swap", "Z, A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 5})

  def testSwapAZ(self):
    self.isa.dispatch("", "swap", "A, Z")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 5})

  def testSwap_ErrorInvalidArgument(self):
    self.isa.dispatch("", "swap", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid swap argument 'bogus'")])

  def testLoadacc(self):
    self.isa.dispatch("", "loadacc", "A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 10})

  def testLoadacc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "loadacc", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'bogus'")])

  def testStoreacc(self):
    self.isa.dispatch("", "storeacc", "A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 11})

  def testStoreacc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "storeacc", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'bogus'")])

  def testSave(self):
    self.isa.dispatch("", "save", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 12})

  def testSave_ErrorArgument(self):
    self.isa.dispatch("", "save", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testRestore(self):
    self.isa.dispatch("", "restore", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 13})

  def testRestore_ErrorArgument(self):
    self.isa.dispatch("", "restore", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testSwapsave(self):
    self.isa.dispatch("", "swapsave", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 14})

  def testSwapsave_ErrorArgument(self):
    self.isa.dispatch("", "swapsave", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testFtl(self):
    self.isa.dispatch("", "ftl", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 15})

  def testFtl_ErrorArgument(self):
    self.isa.dispatch("", "ftl", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testMovAB(self):
    self.isa.dispatch("", "mov", "A, B")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 20})

  def testMovAC(self):
    self.isa.dispatch("", "mov", "A, C")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 21})

  def testMovAD(self):
    self.isa.dispatch("", "mov", "A, D")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 22})

  def testMovAE(self):
    self.isa.dispatch("", "mov", "A, E")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 23})

  def testMovAZ(self):
    self.isa.dispatch("", "mov", "A, Z")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 24})

  def testMovLoadImmediate(self):
    self.isa.dispatch("", "mov", "A, 99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 30, (100, 1): 99})

  def testMovLoadImmediateLabel(self):
    self.context.labels = {"label": 99}
    self.isa.dispatch("", "mov", "A, label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 30, (100, 1): 99})

  def testMovLoadDirect(self):
    self.isa.dispatch("", "mov", "A, [42]")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 31, (100, 1): 42})

  def testMovLoadDirectLabel(self):
    self.context.labels = {"label": 42}
    self.isa.dispatch("", "mov", "A, [label]")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 31, (100, 1): 42})

  def testMovLoadDirectLabel_ErrorOutOfRange(self):
    self.context.labels = {"label": 123}
    self.isa.dispatch("", "mov", "A, [label]")
    self.assertEqual(self.out.errors,
                     [("file", 1, "address out of mov range '123'")])

  def testMovStoreDirect(self):
    self.isa.dispatch("", "mov", "[42], A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 32, (100, 1): 42})

  def testMovStoreDirectLabel(self):
    self.context.labels = {"label": 42}
    self.isa.dispatch("", "mov", "[label], A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 32, (100, 1): 42})

  def testMovStoreDirectLabel_ErrorOutOfRange(self):
    self.context.labels = {"label": 123}
    self.isa.dispatch("", "mov", "A, [label]")
    self.assertEqual(self.out.errors,
                     [("file", 1, "address out of mov range '123'")])

  def testMovLoadDirectB(self):
    self.isa.dispatch("", "mov", "A, [B]")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 33})

  def testMovStoreDirectB(self):
    self.isa.dispatch("", "mov", "[B], A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 34})

  def testMov_ErrorInvalidArgument(self):
    self.isa.dispatch("", "mov", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid mov argument 'bogus'")])

  def testIndexhi(self):
    self.isa.dispatch("", "indexhi", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 40})

  def testIndexhi_ErrorArgument(self):
    self.isa.dispatch("", "indexhi", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testIndexlo(self):
    self.isa.dispatch("", "indexlo", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 41})

  def testIndexlo_ErrorArgument(self):
    self.isa.dispatch("", "indexlo", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testSelfmodify(self):
    self.isa.dispatch("", "selfmodify", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 42})

  def testSelfmodify_ErrorArgument(self):
    self.isa.dispatch("", "selfmodify", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testScan(self):
    self.isa.dispatch("", "scan", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 43})

  def testScan_ErrorArgument(self):
    self.isa.dispatch("", "scan", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testIncA(self):
    self.isa.dispatch("", "inc", "A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 50})

  def testIncB(self):
    self.isa.dispatch("", "inc", "B")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 51})

  def testInc_ErrorInvalidArgument(self):
    self.isa.dispatch("", "inc", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid inc argument 'bogus'")])

  def testDecA(self):
    self.isa.dispatch("", "dec", "A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 52})

  def testDec_ErrorInvalidArgument(self):
    self.isa.dispatch("", "dec", "B")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'B'")])

  def testAddAD(self):
    self.isa.dispatch("", "add", "A, D")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 70})

  def testAdd_ErrorInvalidArgument(self):
    self.isa.dispatch("", "add", "A, B")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'A, B'")])

  def testNeg(self):
    self.isa.dispatch("", "neg", "A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 71})

  def testNeg_ErrorInvalidArgument(self):
    self.isa.dispatch("", "neg", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'bogus'")])

  def testSubAD(self):
    self.isa.dispatch("", "sub", "A, D")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 72})

  def testSub_ErrorInvalidArgument(self):
    self.isa.dispatch("", "sub", "A, B")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'A, B'")])

  def testJmp(self):
    self.isa.dispatch("", "jmp", "99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 73, (100, 1): 99})

  def testJmpLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jmp", "label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 73, (100, 1): 99})

  def testJmpLabel_ErrorUnrecognized(self):
    self.isa.dispatch("", "jmp", "label")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized label 'label'")])

  def testJmpLabel_ErrorFar(self):
    self.context.labels = {"label": 399}
    self.isa.dispatch("", "jmp", "label")
    self.assertEqual(self.out.errors,
                     [("file", 1, "expecting address in current function table")])

  def testJmpFar(self):
    self.isa.dispatch("", "jmp", "far 399")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 74, (100, 1): 99, (100, 2): 3})

  def testJmpFarWithNearTarget(self):
    self.isa.dispatch("", "jmp", "far 99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 74, (100, 1): 99, (100, 2): 1})

  def testJmpFarLabel(self):
    self.context.labels = {"label": 399}
    self.isa.dispatch("", "jmp", "far label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 74, (100, 1): 99, (100, 2): 3})

  def testJmpFarLabel_ErrorUnrecognized(self):
    self.isa.dispatch("", "jmp", "far label")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized label 'label'")])

  def testJmpA(self):
    self.isa.dispatch("", "jmp", "+A")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 75})

  def testJn(self):
    self.isa.dispatch("", "jn", "199")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 80, (100, 1): 99})

  def testJnRelative(self):
    self.isa.dispatch("", "jn", "99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 80, (100, 1): 99})

  def testJnLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jn", "label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 80, (100, 1): 99})

  def testJn_ErrorFar(self):
    self.isa.dispatch("", "jn", "299")
    self.assertEqual(self.out.errors,
                     [("file", 1, "expecting address in current function table")])

  def testJz(self):
    self.isa.dispatch("", "jz", "199")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 81, (100, 1): 99})

  def testJzRelative(self):
    self.isa.dispatch("", "jz", "99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 81, (100, 1): 99})

  def testJzLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jz", "label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 81, (100, 1): 99})

  def testJz_ErrorFar(self):
    self.isa.dispatch("", "jz", "299")
    self.assertEqual(self.out.errors,
                     [("file", 1, "expecting address in current function table")])

  def testLoop(self):
    self.isa.dispatch("", "loop", "199")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 82, (100, 1): 99})

  def testLoopRelative(self):
    self.isa.dispatch("", "loop", "99")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 82, (100, 1): 99})

  def testLoopLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "loop", "label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 82, (100, 1): 99})

  def testLoop_ErrorFar(self):
    self.isa.dispatch("", "loop", "299")
    self.assertEqual(self.out.errors,
                     [("file", 1, "expecting address in current function table")])

  def testJsr(self):
    self.isa.dispatch("", "jsr", "399")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 83, (100, 1): 99, (100, 2): 3})

  def testJsrLabel(self):
    self.context.labels = {"label": 199}
    self.isa.dispatch("", "jsr", "label")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 83, (100, 1): 99, (100, 2): 1})

  def testJsr_ErrorUnrecognizedLabel(self):
    self.isa.dispatch("", "jsr", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unrecognized label 'bogus'")])

  def testRet(self):
    self.isa.dispatch("", "ret", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 84})

  def testRet_ErrorInvalidArgument(self):
    self.isa.dispatch("", "ret", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])

  def testReadAB(self):
    self.isa.dispatch("", "read", "AB")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 93})

  def testRead_ErrorInvalidArgument(self):
    self.isa.dispatch("", "read", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'bogus'")])

  def testPrintAB(self):
    self.isa.dispatch("", "print", "AB")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 94})

  def testPrint_ErrorInvalidArgument(self):
    self.isa.dispatch("", "print", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "invalid argument 'bogus'")])

  def testHalt(self):
    self.isa.dispatch("", "halt", "")
    self.assertFalse(self.out.errors)
    self.assertEqual(self.out.output, {(100, 0): 95})

  def testHalt_ErrorInvalidArgument(self):
    self.isa.dispatch("", "halt", "bogus")
    self.assertEqual(self.out.errors,
                     [("file", 1, "unexpected argument 'bogus'")])


if __name__ == "__main__":
  unittest.main()
