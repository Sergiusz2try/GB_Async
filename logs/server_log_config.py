import logging
from logging import handlers


LOG = logging.getLogger("server")

FORMATTER = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

FILE_HANDLER = logging.FileHandler(filename="logs/server.log", encoding="utf-8")

FILE_HANDLER.setFormatter(FORMATTER)

LOG.addHandler(FILE_HANDLER)
LOG.setLevel(logging.DEBUG)

if __name__ == "__main__":
    ROTATING_HENDLER = handlers.TimedRotatingFileHandler(
        filename="logs/server.log",
        when="midnight",
        interval=1,
        backupCount=2,
        encoding="utf-8",
    )
    ROTATING_HENDLER.setFormatter(FORMATTER)
    LOG.addHandler(ROTATING_HENDLER)
    LOG.debug("Отладочное сообщение.")
