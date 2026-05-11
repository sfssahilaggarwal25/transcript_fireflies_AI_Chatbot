import logging
import sys

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(asctime)s  %(levelname)-8s  %(name)-22s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        _configured = True
    return logging.getLogger(name)
