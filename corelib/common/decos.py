import logging
import sys


if sys.argv[0].find("client") == -1:
    LOG = logging.getLogger("server")
else:
    LOG = logging.getLogger("client")


def log(func_to_log):
    def wrapper(*args, **kwargs):
        r = func_to_log(*args, **kwargs)
        LOG.debug(f"Вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}")

        return r
    return wrapper