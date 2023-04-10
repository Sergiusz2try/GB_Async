import unittest

from corelib.server import response_200

class TestServer(unittest.TestCase):

    def test_response_200(self):
        self.assertEqual(response_200(), b'{"response": 200, "alert": "OK"}')


if __name__ == "__main__":
    unittest.main()