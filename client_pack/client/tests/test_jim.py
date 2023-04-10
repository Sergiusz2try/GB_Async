import unittest

from corelib.common.jim import pack, unpack


class TestJim(unittest.TestCase):

    def test_pack(self):
        self.assertEqual(pack("Hello"), b'"Hello"')

    def test_unpack(self):
        self.assertEqual(unpack(b'"Hello"'), "Hello")

    
if __name__ == "__main__":
    unittest.main()