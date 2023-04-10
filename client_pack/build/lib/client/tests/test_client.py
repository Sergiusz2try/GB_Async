import unittest
from corelib.common.jim import pack, unpack

from client_pack.client.client_ import auth, get_options, get_user


class TestClient(unittest.TestCase):

    def test_get_options(self):
        options_conf = "/home/sergey/Документы/GB/GB_Async/config_client.json"
        options = get_options("", options_conf)
        self.assertEqual(options, {'DEFAULT': {'HOST': '127.0.0.1', 'PORT': 8010}})

    def test_get_user(self):
        user = get_user()
        self.assertEqual(user.name, "User")
        self.assertEqual(user.password, "Password")

    def test_auth(self):
        result = unpack(auth())
        result["time"] = 1.1
        result = pack(result)
        self.assertEqual(result, b'{"action": "authenticate", "time": 1.1, "user": {"account_name": "User", "password": "Password"}}')


if __name__ == "__main__":
    unittest.main()