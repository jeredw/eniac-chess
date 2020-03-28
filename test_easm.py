import unittest
from easm import SymbolTable, OutOfResources

class TestSymbolTable(unittest.TestCase):

    def test_lookup(self):
      # if we allocate the same name twice, we should get the same number
      # but a new name needs a different number
      for typ in ['a','p','d','ad.s','ad.d','ad.dp','ad.sd']:
        s = SymbolTable()

        n1 = s.lookup(typ,'nameA')
        self.assertEqual(n1, 1)
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
        self.assertEqual(n1, 1)
        n2 = s.lookup_acc(acc_idx, typ,'nameA')
        self.assertEqual(n1, n2)
        n3 = s.lookup_acc(acc_idx, typ,'nameB')
        self.assertNotEqual(n1, n3)


    def test_acc_distinct(self):
      s = SymbolTable()
      n1 = s.lookup_acc(10,'r','receiver')
      n2 = s.lookup_acc(20,'r','receiver')
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


if __name__ == '__main__':
    unittest.main()
