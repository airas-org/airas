import logging


def setup_logging(level=logging.INFO):
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        logging.basicConfig(level=level, format="[%(levelname)s] %(name)s: %(message)s")
