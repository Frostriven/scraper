import logging
import sys
from datetime import datetime

_logger = logging.getLogger("releva-scraper")
_logger.setLevel(logging.INFO)

if not _logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s — %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    _logger.addHandler(handler)


def log(message: str, level: str = "info") -> None:
    getattr(_logger, level, _logger.info)(message)
