#!/usr/bin/env python3
#
import unittest
from homogeneous import hlist, hdict

class TestHomogeneous(unittest.TestCase):

    def test_hlist_init(self):
        # Test initialization
        hl = hlist(valueType=int)
        self.assertIsInstance(hl, hlist)
        self.assertEqual(int, hl.valueType)
        self.assertFalse(hl.valueNone)
        self.assertIsNone(hl.valueTest)

    def test_hlist_setitem_valid(self):
        # Test setting valid items
        hl = hlist(valueType=int)
        hl.append(1)
        hl.append(2)
        self.assertEqual(len(hl), 2)
        self.assertEqual(hl[0], 1)
        self.assertEqual(hl[1], 2)

        hl.extend([ 3, 4, 5 ])
        self.assertEqual(len(hl), 5)
        self.assertEqual(hl[-1], 5)

        with self.assertRaises(TypeError):
            hl.extend([ 3.14 ])

    def test_hlist_setitem_invalid_type(self):
        # Test setting invalid type
        hl = hlist(valueType=int)
        with self.assertRaises(TypeError):
            hl.append("string")

    def test_hlist_setitem_none(self):
        # Test setting None
        hl = hlist(valueType=int, valueNone=False)
        with self.assertRaises(TypeError):
            hl.append(None)

        hl_allow_none = hlist(valueType=int, valueNone=True)
        hl_allow_none.append(None)
        self.assertIsNone(hl_allow_none[0])

    def test_hlist_valuetest(self):
        # Test value test function
        hl = hlist(valueType=int, valueTest=lambda x: x > 0)
        hl.append(1)
        with self.assertRaises(TypeError):
            hl.append(-1)

    def test_hdict_init(self):
        # Test initialization
        hd = hdict(keyType=str, valueType=int)
        self.assertIsInstance(hd, hdict)
        self.assertEqual(hd.keyType, str)
        self.assertEqual(hd.valueType, int)

    def test_hdict_setitem_valid(self):
        # Test setting valid items
        hd = hdict(keyType=str, valueType=int)
        hd['a'] = 1
        hd['b'] = 2
        self.assertEqual(len(hd), 2)
        self.assertEqual(hd['a'], 1)
        self.assertEqual(hd['b'], 2)

    def test_hdict_setitem_invalid_key(self):
        # Test setting invalid key type
        hd = hdict(keyType=str, valueType=int)
        with self.assertRaises(TypeError):
            hd[1] = 1

    def test_hdict_setitem_invalid_value(self):
        # Test setting invalid value type
        hd = hdict(keyType=str, valueType=int)
        with self.assertRaises(TypeError):
            hd['a'] = 'string'

    def test_hdict_setitem_none(self):
        # Test setting None
        hd = hdict(keyType=str, valueType=int, keyNone=False, valueNone=False)
        with self.assertRaises(TypeError):
            hd[None] = 1
        with self.assertRaises(TypeError):
            hd['a'] = None

        hd_allow_none = hdict(keyType=str, valueType=int, keyNone=True, valueNone=True)
        hd_allow_none[None] = None
        self.assertIsNone(hd_allow_none[None])

    def test_hdict_key_value_test(self):
        # Test key and value test functions
        hd = hdict(
            keyType=str, keyTest=lambda x: len(x) > 2,
            valueType=int, valueTest=lambda x: x > 0
        )
        hd['abc'] = 1
        with self.assertRaises(TypeError):
            hd['ab'] = 2  # key too short
        with self.assertRaises(TypeError):
            hd['abcd'] = -1  # negative value

if __name__ == '__main__':
    unittest.main()
