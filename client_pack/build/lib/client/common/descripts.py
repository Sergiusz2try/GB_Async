import sys
from logs.server_log_config import LOG


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            LOG.critical(
                f'Try to start server with incorrect port {value}. Available address 1024 to 65535.')
            sys.exit(1)
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name