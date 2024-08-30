import logging
from logging.handlers import RotatingFileHandler
import os
from config import Config

def setup_logger(name, log_file=Config.LOG_FILE, level=Config.LOG_LEVEL):
    """Function to set up as many loggers as you want"""

    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')

    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Create a default logger
logger = setup_logger('default')