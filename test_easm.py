import unittest
from easm import SymbolTable

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


if __name__ == '__main__':
    unittest.main()
