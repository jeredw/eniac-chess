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

  # test several things for each type of resource:
  #  - intitial allocation of the first resource on the machine (e.g. 1-1)
  #  - replacement of the same name with same resource
  #  - allocation of a different name to a different resource
  #  - running out of resources

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

  def test_adapter(self):
      a = Assembler()
      self.assertEqual(
        a.assemble_line('p a20.A ad.s.{ad-name}.3'), format_comment('p a20.A ad.s.1.3','# ad-name=1'))
      self.assertEqual(
        a.assemble_line('p ad.s.{ad-other-name}.3 a11.g'), format_comment('p ad.s.2.3 a11.g','# ad-other-name=2'))
      self.assertEqual(
        a.assemble_line('p 2 ad.s.{ad-other-name}.4'), format_comment('p 2 ad.s.2.4','# ad-other-name=2'))
      self.run_out(a, 'p ad.s.{ad-', '}.1 a1.a', 38)

      self.assertEqual(
        a.assemble_line('p a20.A ad.d.{ad-name}.3'), format_comment('p a20.A ad.d.1.3','# ad-name=1'))
      self.assertEqual(
        a.assemble_line('p ad.d.{ad-other-name}.3 a11.g'), format_comment('p ad.d.2.3 a11.g','# ad-other-name=2'))
      self.assertEqual(
        a.assemble_line('p 3 ad.d.{ad-other-name}.3 '), format_comment('p 3 ad.d.2.3','# ad-other-name=2'))
      self.run_out(a, 'p ad.d.{ad-', '}.1 a1.a', 38)

      self.assertEqual(
        a.assemble_line('p a20.A ad.dp.{ad-name}.11'), format_comment('p a20.A ad.dp.1.11','# ad-name=1'))
      self.assertEqual(
        a.assemble_line('p a20.A ad.dp.{ad-other-name}.11'), format_comment('p a20.A ad.dp.2.11','# ad-other-name=2'))
      self.assertEqual(
        a.assemble_line('p ad.dp.{ad-other-name}.11 5-5'), format_comment('p ad.dp.2.11 5-5','# ad-other-name=2'))
      self.run_out(a, 'p ad.dp.{ad-', '}.11 5-5', 38)

      self.assertEqual(
        a.assemble_line('p a20.A ad.sd.{ad-name}.8'), format_comment('p a20.A ad.sd.1.8','# ad-name=1'))
      self.assertEqual(
        a.assemble_line('p a20.A ad.sd.{ad-other-name}.8'), format_comment('p a20.A ad.sd.2.8','# ad-other-name=2'))
      self.assertEqual(
        a.assemble_line('p ad.sd.{ad-other-name}.8 4'),format_comment('p ad.sd.2.8 4','# ad-other-name=2'))
      self.run_out(a, 'p ad.sd.{ad-', '}.8 1', 38)




if __name__ == '__main__':
    unittest.main()
