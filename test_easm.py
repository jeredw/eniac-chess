import unittest
from easm import SymbolTable, Assembler, format_comment, OutOfResources, SyntaxError

class TestSymbolTable(unittest.TestCase):

  def test_lookup(self):
    # if we allocate the same name twice, we should get the same number
    # but a new name needs a different number
    for typ in ['a','p','d','ad.s','ad.d','ad.dp','ad.sd']:
      s = SymbolTable()

      n1 = s.lookup(typ,'nameA')
      self.assertEqual(n1, 0)
      n2 = s.lookup(typ,'nameA')
      self.assertEqual(n1, n2)
      n3 = s.lookup(typ,'nameB')
      self.assertNotEqual(n1, n3)

  def test_lookup_acc(self):
    # like test_lookup but with the resources on an accumulator
    acc_idx = 5

    for typ in ['r','t','i']:
      s = SymbolTable()

      n1 = s.lookup_acc(acc_idx, typ,'nameA')
      self.assertEqual(n1, 0)
      n2 = s.lookup_acc(acc_idx, typ,'nameA')
      self.assertEqual(n1, n2)
      n3 = s.lookup_acc(acc_idx, typ,'nameB')
      self.assertNotEqual(n1, n3)

  def test_acc_distinct(self):
    s = SymbolTable()
    n1 = s.lookup_acc(9,'r','receiver')
    n2 = s.lookup_acc(19,'r','receiver')
    self.assertEqual(n1, n2) # should have same number, b/c different accs

  def test_out_of_resources(self):
      s = SymbolTable()
      for i in range(20):
        s.lookup('a','name' + str(i))
      with self.assertRaises(OutOfResources):
        s.lookup('a','onemore')


  def test_define(self):
      s = SymbolTable()
      s.define('p','myprogram',55)

      n = s.lookup('p','otherprogram')
      self.assertNotEqual(n, 55)        # shouldn't be the number we defined

      n = s.lookup('p','myprogram')
      self.assertEqual(n, 55)           # should still be at same value


class TestAssembler(unittest.TestCase):

  def test_literal(self):
      a = Assembler()
      self.assertEqual(a.assemble_line('p 1-1 a3.5i'),'p 1-1 a3.5i') 
      self.assertEqual(a.assemble_line('p 8 ad.dp.1.11'), 'p 8 ad.dp.1.11')

  def test_comment(self):
      a = Assembler()

      # test comment alignment
      self.assertEqual(a.assemble_line('s a2.cc7 C   # then clear'),'s a2.cc7 C                    # then clear') 

      # test leading ws
      self.assertEqual(a.assemble_line(' s a2.cc7 C   # then clear'),' s a2.cc7 C                   # then clear') 

      self.assertEqual(a.assemble_line(''), '')

  def test_define(self):
      a = Assembler()
      self.assertEqual(
        a.assemble_line('{p-name}=5-5'), '# {p-name}=5-5')
      self.assertEqual(
        a.assemble_line('p {p-name} a3.5i'), format_comment('p 5-5 a3.5i','# p-name=5-5'))
      self.assertEqual(
        a.assemble_line('{d-name}=5'), '# {d-name}=5')
      self.assertEqual(
        a.assemble_line('p {d-name} a3.g'), format_comment('p 5 a3.g','# d-name=5'))
      self.assertEqual(
        a.assemble_line('{a-name}=13'), '# {a-name}=13')
      self.assertEqual(
        a.assemble_line('p 1 a{a-name}.d'), format_comment('p 1 a13.d','# a-name=a13'))

  # test several things for each type of resource:
  #  - intitial allocation of the first resource on the machine (e.g. 1-1)
  #  - replacement of the same name with same resource
  #  - allocation of a different name to a different resource
  #  - running out of resources

  # test that there are exactly numleft resources, then we error
  def run_out(self, a, prefix, suffix, numleft):
    for i in range(numleft):
      a.assemble_line(prefix + str(i) + suffix)
    with self.assertRaises(OutOfResources):
      a.assemble_line(prefix + str(numleft) + suffix)

  def test_program_line(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {p-name} a3.5i'), format_comment('p 1-1 a3.5i','# p-name=1-1'))
    self.assertEqual(
      a.assemble_line('p {p-name} a4.1i'), format_comment('p 1-1 a4.1i','# p-name=1-1'))
    self.assertEqual(
      a.assemble_line('p a13.5o {p-other-name}'), format_comment('p a13.5o 1-2','# p-other-name=1-2'))
    self.assertEqual(
      a.assemble_line('p i.io {p-other-name}'), format_comment('p i.io 1-2','# p-other-name=1-2'))
    self.run_out(a, 'p {p-', '} a1.1i', 119)

  def test_data_trunk(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {d-name} a3.a'), format_comment('p 1 a3.a','# d-name=1')) 
    self.assertEqual(
      a.assemble_line('p a4.S {d-name}'),format_comment('p a4.S 1','# d-name=1')) 
    self.assertEqual(
      a.assemble_line('p a16.A {d-other-name} '),format_comment('p a16.A 2','# d-other-name=2'))
    self.run_out(a, 'p {d-', '} a1.a', 7)

  def test_shift_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.s.{ad-name}.3'), format_comment('p a20.A ad.s.1.3','# ad-name=1'))
    self.assertEqual(
      a.assemble_line('p ad.s.{ad-other-name}.3 a11.g'), format_comment('p ad.s.2.3 a11.g','# ad-other-name=2'))
    self.assertEqual(
      a.assemble_line('p 2 ad.s.{ad-other-name}.4'), format_comment('p 2 ad.s.2.4','# ad-other-name=2'))
    self.run_out(a, 'p ad.s.{ad-', '}.1 a1.a', 38)

  def test_deleter_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.d.{ad-name}.3'), format_comment('p a20.A ad.d.1.3','# ad-name=1'))
    self.assertEqual(
      a.assemble_line('p ad.d.{ad-other-name}.3 a11.g'), format_comment('p ad.d.2.3 a11.g','# ad-other-name=2'))
    self.assertEqual(
      a.assemble_line('p 3 ad.d.{ad-other-name}.3 '), format_comment('p 3 ad.d.2.3','# ad-other-name=2'))
    self.run_out(a, 'p ad.d.{ad-', '}.1 a1.a', 38)

  def test_digit_pulse_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.dp.{ad-name}.11'), format_comment('p a20.A ad.dp.1.11','# ad-name=1'))
    self.assertEqual(
      a.assemble_line('p a20.A ad.dp.{ad-other-name}.11'), format_comment('p a20.A ad.dp.2.11','# ad-other-name=2'))
    self.assertEqual(
      a.assemble_line('p ad.dp.{ad-other-name}.11 5-5'), format_comment('p ad.dp.2.11 5-5','# ad-other-name=2'))
    self.run_out(a, 'p ad.dp.{ad-', '}.11 5-5', 38)

  def test_special_digit_adapter(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a20.A ad.sd.{ad-name}.8'), format_comment('p a20.A ad.sd.1.8','# ad-name=1'))
    self.assertEqual(
      a.assemble_line('p a20.A ad.sd.{ad-other-name}.8'), format_comment('p a20.A ad.sd.2.8','# ad-other-name=2'))
    self.assertEqual(
      a.assemble_line('p ad.sd.{ad-other-name}.8 4'), format_comment('p ad.sd.2.8 4','# ad-other-name=2'))
    self.run_out(a, 'p ad.sd.{ad-', '}.8 1', 38)

  def test_ftable(self):
    # we don't currently track resources on ftables but we should be able to patch to named lines
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p {p-name} f1.1i'), format_comment('p 1-1 f1.1i','# p-name=1-1'))
    self.assertEqual(
      a.assemble_line('p f1.C {p-other-name}'), format_comment('p f1.C 1-2','# p-other-name=1-2'))
    self.assertEqual(
      a.assemble_line('p {d-name} f1.arg'), format_comment('p 1 f1.arg','# d-name=1'))
    self.assertEqual(
      a.assemble_line('p f1.A {d-other-name}'), format_comment('p f1.A 2','# d-other-name=2'))

  def test_accumulator_lookup(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p a{a-name}.A 8'), format_comment('p a1.A 8','# a-name=a1'))
    self.assertEqual(
      a.assemble_line('p a{a-other-name}.A 8'), format_comment('p a2.A 8','# a-other-name=a2'))
    self.assertEqual(
      a.assemble_line('p 8 a{a-other-name}.a'), format_comment('p 8 a2.a','# a-other-name=a2'))
    self.run_out(a, 'p a{a-', '}.A 1', 18)

  def test_accumulator_reciever(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{r-name}i'), format_comment('p 1-1 a1.1i','# r-name=1i'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{r-other-name}i'), format_comment('p 1-1 a1.2i','# r-other-name=2i'))
    self.assertEqual(
      a.assemble_line('p a1.{r-other-name}i 2-2'), format_comment('p a1.2i 2-2','# r-other-name=2i'))
    self.assertEqual(
      a.assemble_line('p {p-name} a1.{r-other-name}i'), format_comment('p 1-1 a1.2i','# p-name=1-1, r-other-name=2i'))
    self.assertEqual(
      a.assemble_line('p {p-name} a{a-name}.{r-other-name}i'), format_comment('p 1-1 a1.2i','# p-name=1-1, a-name=a1, r-other-name=2i'))
    self.run_out(a, 'p 1-1 a1.{r-', '}i', 2)

    # we've run out of recievers on a1, but should still be plenty on a2
    self.run_out(a, 'p 1-1 a2.{r-', '}i', 4)

  def test_accumulator_transciever(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{t-name}i'), format_comment('p 1-1 a1.5i','# t-name=5i'))
    self.assertEqual(
      a.assemble_line('p 1-1 a1.{t-other-name}i'), format_comment('p 1-1 a1.6i','# t-other-name=6i'))
    self.assertEqual(
      a.assemble_line('p a1.{t-other-name}o 2-2'), format_comment('p a1.6o 2-2','# t-other-name=6o'))
    self.run_out(a, 'p 1-1 a1.{t-', '}i', 6)

    # we've run out of transcievers on a1, but should still be plenty on a2
    self.run_out(a, 'p 1-1 a2.{t-', '}i', 8)

  def test_accumulator_inputs(self):
    a = Assembler()
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-name}'), format_comment('p 4 a1.a','# i-name=a'))
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-other-name}'), format_comment('p 4 a1.b','# i-other-name=b'))
    self.assertEqual(
      a.assemble_line('p 4 a1.{i-other-other-name}'), format_comment('p 4 a1.g','# i-other-other-name=g'))
    self.run_out(a, 'p 4 a1.{i-', '}', 2)

    # we've run out of inputs on a1, but should still be plenty on a2
    self.run_out(a, 'p 4 a2.{i-', '}', 5)

  def test_reciever_output_error(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{r-name}o 1-1')  # receivers do not have outputs

  def test_missing_io_error(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{r-name} 1-1')  # need i after receiver
    with self.assertRaises(SyntaxError):
      a.assemble_line('p a1.{t-name} 1-1')  # need i or after transceiver

  def test_switch_literal(self):
    a = Assembler()
    self.assertEqual(a.assemble_line('s cy.op 1a'), 's cy.op 1a')
    self.assertEqual(a.assemble_line('s i.io 1-1'), 's i.io 1-1')
    self.assertEqual(a.assemble_line('s a1.op5 a'), 's a1.op5 a')

  def test_switch_accumulator(self):
    a = Assembler()
    self.assertEqual(a.assemble_line('s a{a-name}.op5 a'), format_comment('s a1.op5 a','# a-name=a1'))
    self.assertEqual(a.assemble_line('s a{a-other-name}.op5 a'), format_comment('s a2.op5 a','# a-other-name=a2'))
    self.assertEqual(a.assemble_line('s a1.op{r-name} a'), format_comment('s a1.op1 a','# r-name=op1'))
    self.assertEqual(a.assemble_line('s a1.op{t-name} a'), format_comment('s a1.op5 a','# t-name=op5'))
    self.assertEqual(a.assemble_line('s a1.op1 {i-name}'), format_comment('s a1.op1 a','# i-name=a'))
    self.assertEqual(a.assemble_line('s a1.op2 {i-other-name}'), format_comment('s a1.op2 b','# i-other-name=b'))
    self.assertEqual(a.assemble_line('s a{a-name}.op{t-name} {i-other-name}'), format_comment('s a1.op5 b','# a-name=a1, t-name=op5, i-other-name=b'))

  def test_non_accumulator_switch_input(self):
    a = Assembler()
    with self.assertRaises(SyntaxError):
      a.assemble_line('s cy.op {i-name}')


if __name__ == '__main__':
    unittest.main()
