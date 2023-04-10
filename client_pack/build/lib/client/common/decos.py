import logging
import socket
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


def login_required(func):
    def checker(*args, **kwargs):
        from server.main import MessageProcessor
        from corelib.common.variables import ACTION, PRESENCE
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            for arg in args:
                if isinstance(arg, dict):
                    if ACTION in arg and arg[ACTION] == PRESENCE:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker