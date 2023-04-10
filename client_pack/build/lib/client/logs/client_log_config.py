import logging


LOG = logging.getLogger("client")

FORMATTER = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")

FILE_HANDLER = logging.FileHandler(filename="logs/client.log", encoding="utf-8")

FILE_HANDLER.setFormatter(FORMATTER)

LOG.addHandler(FILE_HANDLER)
LOG.setLevel(logging.DEBUG)

if __name__ == "__main__":
    STREAM_HENDLER = logging.StreamHandler()
    STREAM_HENDLER.setFormatter(FORMATTER)
    LOG.addHandler(STREAM_HENDLER)
    LOG.debug("Отладочное сообщение.")
    